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
    build_tool_catalog,
    bootstrap_aob,
    canonicalize_step_result,
    compact_step_for_context,
    effective_server_paths,
    maybe_self_ask,
    normalize_plan_steps,
    preflight_aob_runtime_dependencies,
    print_history,
    print_plan,
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
)

_LOG = logging.getLogger(__name__)


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

    self_ask = maybe_self_ask(args.question, llm)
    descriptions = await executor.get_server_descriptions()
    tool_catalog = await build_tool_catalog(server_paths)
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
            continue
        tool_schema = tool_schema_for_step(tool_catalog, step.server, step.tool)
        result = await executor.execute_step(
            step,
            context,
            self_ask.augmented_question,
            tool_schema=tool_schema,
        )
        canonicalize_step_result(result)
        compact_step_for_context(result)
        context[step.step_number] = result
        trajectory.append(result)

    plan_payload = serialize_plan(plan)
    history_payload = [serialize_step_result(result) for result in trajectory]
    failed_steps = summarize_terminal_failures(history_payload)
    answer = summarize_answer(args.question, history_payload, llm)

    output = {
        "question": args.question,
        "effective_question": self_ask.augmented_question,
        "self_ask": {
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
    args = parser.parse_args()
    setup_logging(args.verbose)
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
