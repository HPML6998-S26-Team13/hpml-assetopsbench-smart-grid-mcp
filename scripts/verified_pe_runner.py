from __future__ import annotations

import asyncio
import json
import logging
from types import SimpleNamespace

from orchestration_utils import (
    available_sensor_ids,
    build_llm,
    build_parser,
    build_planner_descriptions,
    build_planning_question,
    build_retry_question,
    bootstrap_aob,
    build_suffix_replan_question,
    build_tool_catalog,
    canonicalize_step_result,
    compact_step_for_context,
    effective_server_paths,
    generate_suffix_plan,
    maybe_self_ask,
    normalize_plan_steps,
    preflight_aob_runtime_dependencies,
    print_history,
    print_plan,
    repair_sensor_task_text,
    renumber_plan,
    resolve_aob_path,
    resolve_repo_root,
    serialize_steps,
    serialize_step_result,
    SelfAskDecision,
    should_skip_invalid_sensor_step,
    setup_logging,
    summarize_answer,
    summarize_terminal_failures,
    tool_schema_for_step,
    VerificationDecision,
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

    from plan_execute.executor import Executor
    from plan_execute.planner import Planner

    llm = build_llm(args.model_id)
    server_paths = effective_server_paths(args.servers, repo_root)
    planner = Planner(llm)
    executor = Executor(llm, server_paths)

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
    tool_catalog = await build_tool_catalog(server_paths)
    planner_descriptions = build_planner_descriptions(descriptions, tool_catalog)
    planning_question = build_planning_question(self_ask.augmented_question)

    initial_plan = planner.generate_plan(planning_question, planner_descriptions)
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

        while True:
            sensors = available_sensor_ids(context)
            step.task, repair_warning = repair_sensor_task_text(step.task, sensors)
            if repair_warning:
                _LOG.info("%s", repair_warning)
            should_skip, skip_reason = should_skip_invalid_sensor_step(step, sensors)
            if should_skip:
                result = SimpleNamespace(
                    step_number=step.step_number,
                    task=step.task,
                    server=step.server,
                    tool=step.tool,
                    tool_args={},
                    response=skip_reason,
                    error=None,
                    success=True,
                )
                context[step.step_number] = result
                history.append(
                    serialize_step_result(
                        result,
                        verifier_decision="continue",
                        verifier_reason=skip_reason,
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

            if not result.success:
                entry = serialize_step_result(
                    result,
                    verifier_decision="error",
                    verifier_reason=result.error or "Step failed before verification.",
                )
                history.append(entry)
                context[step.step_number] = result
                break

            provisional_entry = serialize_step_result(result)
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

            verdict = verify_step(
                args.question,
                self_ask.augmented_question,
                step,
                provisional_entry,
                history,
                remaining_steps,
                llm,
            )

            if verdict.decision == "retry" and retries_used < args.max_retries_per_step:
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
                else:
                    suffix_warnings = normalize_plan_steps(suffix_plan, tool_catalog)
                    for warning in suffix_warnings:
                        _LOG.info("%s", warning)
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

    answer = summarize_answer(args.question, history, llm)
    failed_steps = summarize_terminal_failures(history)
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
        "plan": serialize_steps(all_plan_steps),
        "history": history,
    }

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
