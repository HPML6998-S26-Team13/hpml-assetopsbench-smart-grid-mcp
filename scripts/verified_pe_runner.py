from __future__ import annotations

import asyncio
import json
import logging
from types import SimpleNamespace

from orchestration_utils import (
    SelfAskDecision,
    VerificationDecision,
    available_sensor_ids,
    bootstrap_aob,
    build_executor,
    build_fault_risk_adjudication_state,
    build_llm,
    build_parser,
    build_planner_descriptions,
    build_planning_question,
    build_missing_evidence_repair_state,
    build_retry_question,
    build_suffix_replan_question,
    build_tool_catalog_for_executor,
    canonicalize_step_result,
    can_retry_missing_evidence,
    close_executor,
    compact_step_for_context,
    current_missing_evidence_hit,
    effective_server_paths,
    fault_risk_adjudication_failed_step,
    finalize_missing_evidence_repair_state,
    generate_suffix_plan,
    load_fault_risk_adjudication_config,
    load_missing_evidence_repair_config,
    load_plan_execute_planner,
    mark_missing_evidence_attempt_result,
    mark_missing_evidence_unrepaired,
    maybe_self_ask,
    normalize_plan_steps,
    preflight_aob_runtime_dependencies,
    print_history,
    print_plan,
    record_missing_evidence_retry_attempt,
    repair_target_key,
    renumber_plan,
    repair_sensor_task_text,
    resolve_aob_path,
    resolve_repo_root,
    serialize_step_result,
    serialize_steps,
    setup_logging,
    should_skip_invalid_sensor_step,
    summarize_answer,
    summarize_terminal_failures,
    tool_schema_for_step,
    verify_step,
)

_LOG = logging.getLogger(__name__)


def _extend_parser():
    parser = build_parser(
        "verified-pe",
        "Run the Verified PE / Plan-Execute-Verify-Replan workflow.",
    )
    parser.add_argument(
        "--max-replans",
        type=int,
        default=2,
        help="Maximum number of suffix replans to allow.",
    )
    parser.add_argument(
        "--max-retries-per-step",
        type=int,
        default=1,
        help="Maximum number of verifier-triggered retries per step.",
    )
    parser.add_argument(
        "--disable-self-ask",
        action="store_true",
        help="Skip the pre-plan Self-Ask clarification pass for this run.",
    )
    return parser


async def _run(args) -> None:
    repo_root = resolve_repo_root()
    aob_path = resolve_aob_path(repo_root, args.aob_path)
    bootstrap_aob(aob_path)
    preflight_aob_runtime_dependencies()

    llm = build_llm(args.model_id)
    server_paths = effective_server_paths(args.servers, repo_root)
    Planner = load_plan_execute_planner()
    planner = Planner(llm)
    executor = build_executor(llm, server_paths, mcp_mode=args.mcp_mode)
    repair_config = load_missing_evidence_repair_config()
    adjudication_config = load_fault_risk_adjudication_config()
    repair_state = build_missing_evidence_repair_state(repair_config)
    repair_attempts_by_target = {}

    try:
        self_ask = (
            SelfAskDecision(
                needs_self_ask=False,
                clarifying_questions=[],
                assumptions=[],
                augmented_question=args.question,
            )
            if args.disable_self_ask
            else maybe_self_ask(args.question, llm)
        )
        descriptions = await executor.get_server_descriptions()
        tool_catalog = await build_tool_catalog_for_executor(executor, server_paths)
        planner_descriptions = build_planner_descriptions(descriptions, tool_catalog)
        planning_question = build_planning_question(self_ask.augmented_question)

        initial_plan = planner.generate_plan(planning_question, planner_descriptions)
        raw_plan_payload = serialize_steps(initial_plan.steps)
        normalization_warnings = normalize_plan_steps(initial_plan, tool_catalog)
        for warning in normalization_warnings:
            _LOG.info("%s", warning)
        active_steps = list(initial_plan.resolved_order())
        all_plan_steps = list(active_steps)
        history = []
        context = {}
        replans_used = 0

        step_index = 0
        while step_index < len(active_steps):
            step = active_steps[step_index]
            retries_used = 0
            step_question = self_ask.augmented_question
            pending_repair_attempt = None

            while True:
                sensors = available_sensor_ids(context)
                step.task, repair_warning = repair_sensor_task_text(step.task, sensors)
                if repair_warning:
                    _LOG.info("%s", repair_warning)
                should_skip, skip_reason = should_skip_invalid_sensor_step(
                    step, sensors
                )
                if should_skip:
                    result = SimpleNamespace(
                        step_number=step.step_number,
                        task=step.task,
                        server=step.server,
                        tool=step.tool,
                        tool_args=getattr(step, "tool_args", {}),
                        response=skip_reason,
                        error=None,
                        success=True,
                    )
                    context[step.step_number] = result
                    history.append(
                        serialize_step_result(
                            result,
                            verifier_decision="runner_skip",
                            verifier_reason=skip_reason,
                            runner_repair="invalid_iot_dga_sensor_lookup",
                        )
                    )
                    _LOG.info("%s", skip_reason)
                    break
                tool_schema = tool_schema_for_step(tool_catalog, step.server, step.tool)
                result = await executor.execute_step(
                    step,
                    context,
                    step_question,
                    tool_schema=tool_schema,
                )
                canonicalize_step_result(result)
                compact_step_for_context(result)
                remaining_steps = active_steps[step_index + 1 :]
                base_entry = serialize_step_result(result)
                repair_hit = (
                    current_missing_evidence_hit(history + [base_entry], base_entry)
                    if repair_config.enabled
                    else None
                )

                if pending_repair_attempt and not repair_hit:
                    mark_missing_evidence_attempt_result(
                        repair_state,
                        pending_repair_attempt,
                        "repaired",
                        new_step=step.step_number,
                    )

                if repair_hit and can_retry_missing_evidence(
                    repair_config,
                    repair_state,
                    repair_hit,
                    repair_attempts_by_target,
                ):
                    key = repair_target_key(repair_hit)
                    repair_attempts_by_target[key] = (
                        repair_attempts_by_target.get(key, 0) + 1
                    )
                    pending_repair_attempt = record_missing_evidence_retry_attempt(
                        repair_state,
                        repair_hit,
                    )
                    retries_used = max(retries_used, repair_attempts_by_target[key])
                    history.append(
                        serialize_step_result(
                            result,
                            verifier_decision="missing_evidence_retry",
                            verifier_reason=repair_hit.get("reason")
                            or "Missing evidence detected before finalization.",
                            retries_used=retries_used,
                        )
                    )
                    step_question = build_retry_question(
                        args.question,
                        self_ask.augmented_question,
                        step,
                        base_entry,
                        VerificationDecision(
                            decision="retry",
                            reason=repair_hit.get("reason")
                            or "Missing evidence detected before finalization.",
                            updated_focus="Repair the missing evidence before answering.",
                        ),
                        retries_used,
                    )
                    _LOG.info(
                        "Missing-evidence repair scheduled retry for step %d.",
                        step.step_number,
                    )
                    continue

                if not result.success:
                    entry = serialize_step_result(
                        result,
                        verifier_decision="error",
                        verifier_reason=result.error
                        or "Step failed before verification.",
                    )
                    history.append(entry)
                    context[step.step_number] = result
                    break

                provisional_entry = base_entry
                if not provisional_entry["success"]:
                    history.append(
                        serialize_step_result(
                            result,
                            verifier_decision="error",
                            verifier_reason=provisional_entry.get("error")
                            or result.error
                            or "Step failed before verification.",
                        )
                    )
                    context[step.step_number] = result
                    break

                detector_replan_verdict = None
                detector_replan_attempt = None
                if repair_hit:
                    mark_missing_evidence_attempt_result(
                        repair_state,
                        pending_repair_attempt,
                        "unrepaired",
                        new_step=step.step_number,
                    )
                    if (
                        remaining_steps
                        and replans_used < args.max_replans
                        and can_retry_missing_evidence(
                            repair_config,
                            repair_state,
                            repair_hit,
                            repair_attempts_by_target,
                        )
                    ):
                        key = repair_target_key(repair_hit)
                        repair_attempts_by_target[key] = (
                            repair_attempts_by_target.get(key, 0) + 1
                        )
                        detector_replan_attempt = record_missing_evidence_retry_attempt(
                            repair_state,
                            repair_hit,
                            action="replan_suffix",
                        )
                        detector_replan_verdict = VerificationDecision(
                            decision="replan_suffix",
                            reason=(
                                repair_hit.get("reason")
                                or "Missing evidence detected before finalization."
                            ),
                            updated_focus=(
                                "Repair the unresolved evidence gap before final answer "
                                "or work-order creation."
                            ),
                        )
                    else:
                        mark_missing_evidence_unrepaired(repair_state, repair_hit)

                if detector_replan_verdict is not None:
                    verdict = detector_replan_verdict
                else:
                    verdict = verify_step(
                        args.question,
                        self_ask.augmented_question,
                        step,
                        provisional_entry,
                        history,
                        remaining_steps,
                        llm,
                    )

                if (
                    verdict.decision == "retry"
                    and retries_used < args.max_retries_per_step
                ):
                    retries_used += 1
                    history.append(
                        serialize_step_result(
                            result,
                            verifier_decision="retry",
                            verifier_reason=verdict.reason,
                            retries_used=retries_used,
                        )
                    )
                    retry_question = build_retry_question(
                        args.question,
                        self_ask.augmented_question,
                        step,
                        provisional_entry,
                        verdict,
                        retries_used,
                    )
                    _LOG.info(
                        "Verifier requested retry for step %d; retrying with guided context.",
                        step.step_number,
                    )
                    step_question = retry_question
                    continue

                if verdict.decision == "retry":
                    verdict = VerificationDecision(
                        decision="continue",
                        reason=(
                            f"{verdict.reason} Retry budget exhausted; continuing with the current result."
                        ),
                        updated_focus=verdict.updated_focus,
                    )

                context[step.step_number] = result
                entry = serialize_step_result(
                    result,
                    verifier_decision=verdict.decision,
                    verifier_reason=verdict.reason,
                    verifier_updated_focus=verdict.updated_focus,
                    retries_used=retries_used,
                )
                history.append(entry)

                if (
                    verdict.decision == "replan_suffix"
                    and remaining_steps
                    and replans_used < args.max_replans
                ):
                    replans_used += 1
                    replan_question = build_suffix_replan_question(
                        args.question,
                        self_ask.augmented_question,
                        history,
                        remaining_steps,
                        verdict,
                    )
                    suffix_plan, replan_error = generate_suffix_plan(
                        planner,
                        replan_question,
                        planner_descriptions,
                    )
                    if suffix_plan is None:
                        history[-1]["verifier_replan_error"] = replan_error
                        mark_missing_evidence_attempt_result(
                            repair_state,
                            detector_replan_attempt,
                            "replan_failed",
                            new_step=step.step_number,
                        )
                    else:
                        mark_missing_evidence_attempt_result(
                            repair_state,
                            detector_replan_attempt,
                            "suffix_replanned",
                            new_step=step.step_number,
                        )
                        history[-1]["verifier_replan_raw_plan"] = serialize_steps(
                            suffix_plan.steps
                        )
                        suffix_warnings = normalize_plan_steps(
                            suffix_plan, tool_catalog
                        )
                        for warning in suffix_warnings:
                            _LOG.info("%s", warning)
                        if suffix_warnings:
                            history[-1][
                                "verifier_replan_normalization_warnings"
                            ] = suffix_warnings
                        shifted_plan = renumber_plan(
                            suffix_plan, max(p.step_number for p in all_plan_steps)
                        )
                        suffix_steps = list(shifted_plan.resolved_order())
                        all_plan_steps.extend(suffix_steps)
                        active_steps = active_steps[: step_index + 1] + suffix_steps
                        _LOG.info(
                            "Verifier triggered suffix replan with %d new step(s).",
                            len(suffix_steps),
                        )

                break

            step_index += 1
    finally:
        await close_executor(executor)

    if repair_config.enabled:
        finalize_missing_evidence_repair_state(repair_state, history)
    adjudication = build_fault_risk_adjudication_state(
        args.question,
        history,
        adjudication_config,
    )
    answer = summarize_answer(
        args.question,
        history,
        llm,
        fault_risk_adjudication=adjudication,
    )
    failed_steps = summarize_terminal_failures(history)
    adjudication_failure = fault_risk_adjudication_failed_step(adjudication)
    if adjudication_failure:
        failed_steps.append(adjudication_failure)
    output = {
        "question": args.question,
        "effective_question": self_ask.augmented_question,
        "self_ask": {
            "enabled": not args.disable_self_ask,
            "needs_self_ask": self_ask.needs_self_ask,
            "clarifying_questions": self_ask.clarifying_questions,
            "assumptions": self_ask.assumptions,
        },
        "verification": {
            "max_replans": args.max_replans,
            "max_retries_per_step": args.max_retries_per_step,
            "replans_used": replans_used,
        },
        "answer": answer,
        "success": not failed_steps,
        "failed_steps": failed_steps,
        "raw_plan": raw_plan_payload,
        "plan": serialize_steps(all_plan_steps),
        "plan_normalization_warnings": normalization_warnings,
        "history": history,
    }
    if repair_config.enabled:
        output["mitigation_repair"] = repair_state
    if adjudication_config.enabled:
        output["fault_risk_adjudication"] = adjudication

    if args.output_json:
        print(json.dumps(output, indent=2))
        if failed_steps:
            raise SystemExit(1)
        return

    if args.show_plan:
        print_plan(output["plan"])
    if args.show_trajectory:
        print_history(history)
    print("\n" + "─" * 60)
    print("  Answer")
    print("─" * 60)
    print(answer)
    if failed_steps:
        raise SystemExit(1)


def main() -> None:
    parser = _extend_parser()
    args = parser.parse_args()
    setup_logging(args.verbose)
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
