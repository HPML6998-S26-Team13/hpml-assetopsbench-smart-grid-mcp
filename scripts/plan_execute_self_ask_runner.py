from __future__ import annotations

import asyncio
import json
import logging
from types import SimpleNamespace

from orchestration_utils import (
    available_sensor_ids,
    build_executor,
    build_llm,
    build_parser,
    build_fault_risk_adjudication_state,
    build_planner_descriptions,
    build_planning_question,
    build_missing_evidence_repair_state,
    build_retry_question,
    build_tool_catalog_for_executor,
    bootstrap_aob,
    canonicalize_step_result,
    close_executor,
    compact_step_for_context,
    can_retry_missing_evidence,
    current_missing_evidence_hit,
    effective_server_paths,
    fault_risk_adjudication_failed_step,
    finalize_missing_evidence_repair_state,
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
    repair_sensor_task_text,
    resolve_aob_path,
    resolve_repo_root,
    serialize_plan,
    serialize_step_result,
    should_skip_invalid_sensor_step,
    summarize_terminal_failures,
    setup_logging,
    summarize_answer,
    tool_schema_for_step,
    VerificationDecision,
)

_LOG = logging.getLogger(__name__)


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
            SimpleNamespace(
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
        plan = planner.generate_plan(planning_question, planner_descriptions)
        raw_plan_payload = serialize_plan(plan)
        normalization_warnings = normalize_plan_steps(plan, tool_catalog)
        for warning in normalization_warnings:
            _LOG.info("%s", warning)

        ordered_steps = plan.resolved_order()
        context = {}
        trajectory = []
        for step in ordered_steps:
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
                        runner_repair="invalid_iot_dga_sensor_lookup",
                        runner_repair_reason=skip_reason,
                    )
                    context[step.step_number] = result
                    trajectory.append(result)
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
                entry = serialize_step_result(result)
                partial_history = [
                    serialize_step_result(prior) for prior in trajectory
                ] + [entry]
                hit = (
                    current_missing_evidence_hit(partial_history, entry)
                    if repair_config.enabled
                    else None
                )

                if pending_repair_attempt and not hit:
                    mark_missing_evidence_attempt_result(
                        repair_state,
                        pending_repair_attempt,
                        "repaired",
                        new_step=step.step_number,
                    )

                if hit and can_retry_missing_evidence(
                    repair_config,
                    repair_state,
                    hit,
                    repair_attempts_by_target,
                ):
                    key = repair_target_key(hit)
                    repair_attempts_by_target[key] = (
                        repair_attempts_by_target.get(key, 0) + 1
                    )
                    pending_repair_attempt = record_missing_evidence_retry_attempt(
                        repair_state,
                        hit,
                    )
                    retries_used = repair_attempts_by_target[key]
                    step_question = build_retry_question(
                        args.question,
                        self_ask.augmented_question,
                        step,
                        entry,
                        VerificationDecision(
                            decision="retry",
                            reason=hit.get("reason")
                            or "Missing evidence detected before finalization.",
                            updated_focus="Repair the missing evidence before answering.",
                        ),
                        retries_used,
                    )
                    trajectory.append(result)
                    _LOG.info(
                        "Missing-evidence repair scheduled retry for step %d.",
                        step.step_number,
                    )
                    continue

                if hit:
                    mark_missing_evidence_attempt_result(
                        repair_state,
                        pending_repair_attempt,
                        "unrepaired",
                        new_step=step.step_number,
                    )
                    mark_missing_evidence_unrepaired(repair_state, hit)

                context[step.step_number] = result
                trajectory.append(result)
                break

        plan_payload = serialize_plan(plan)
        history_payload = [serialize_step_result(result) for result in trajectory]
        if repair_config.enabled:
            finalize_missing_evidence_repair_state(repair_state, history_payload)
        failed_steps = summarize_terminal_failures(history_payload)
        adjudication = build_fault_risk_adjudication_state(
            args.question,
            history_payload,
            adjudication_config,
        )
        adjudication_failure = fault_risk_adjudication_failed_step(adjudication)
        if adjudication_failure:
            failed_steps.append(adjudication_failure)
        answer = summarize_answer(
            args.question,
            history_payload,
            llm,
            fault_risk_adjudication=adjudication,
        )

        output = {
            "question": args.question,
            "effective_question": self_ask.augmented_question,
            "self_ask": {
                "enabled": not args.disable_self_ask,
                "needs_self_ask": self_ask.needs_self_ask,
                "clarifying_questions": self_ask.clarifying_questions,
                "assumptions": self_ask.assumptions,
            },
            "answer": answer,
            "success": not failed_steps,
            "failed_steps": failed_steps,
            "raw_plan": raw_plan_payload,
            "plan": plan_payload,
            "plan_normalization_warnings": normalization_warnings,
            "history": history_payload,
        }
        if repair_config.enabled:
            output["mitigation_repair"] = repair_state
        if adjudication_config.enabled:
            output["fault_risk_adjudication"] = adjudication
    finally:
        await close_executor(executor)

    if args.output_json:
        print(json.dumps(output, indent=2))
        if failed_steps:
            raise SystemExit(1)
        return

    if args.show_plan:
        print_plan(plan_payload)
    if args.show_trajectory:
        print_history(history_payload)
    print("\n" + "─" * 60)
    print("  Answer")
    print("─" * 60)
    print(answer)
    if failed_steps:
        raise SystemExit(1)


def main() -> None:
    parser = build_parser(
        "plan-execute-self-ask",
        "Run the PE workflow with a lightweight Self-Ask clarification pass.",
    )
    parser.add_argument(
        "--disable-self-ask",
        action="store_true",
        help="Skip the pre-plan Self-Ask clarification pass for this run.",
    )
    args = parser.parse_args()
    setup_logging(args.verbose)
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
