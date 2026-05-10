#!/usr/bin/env python3
"""Print archived SmartGridBench demo artifacts for screen recording.

This intentionally makes no live model or WatsonX calls. It reads existing
trajectory JSON and judge-log JSON from the final 8B ZS A100 run and prints a
terminal-friendly playback.
"""

from __future__ import annotations

import argparse
import json
import textwrap
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

CASES = [
    {
        "label": "SGT-009 | All-domain incident response",
        "aliases": ["SGT-009", "all-domain"],
        "domains": "IoT, FMSR, TSFM, WO",
        "cell": "ZS / Llama-3.1-8B-Instruct / verified PE + Self-Ask + MCP baseline",
        "trajectory": "benchmarks/cell_Z_hybrid/raw/9125463_replicate_zs_h100_2x3/2026-05-03_Z_llama-3-1-8b-instruct_verified_pe_baseline_multi_01_end_to_end_fault_response_run01.json",
        "judge": "results/judge_logs/9125463_replicate_zs_h100_2x3/SGT-009_run01_judge_log.json",
    },
    {
        "label": "SGT-010 | FMSR + TSFM decision",
        "aliases": ["SGT-010"],
        "domains": "FMSR, TSFM, WO decision context",
        "cell": "ZS / Llama-3.1-8B-Instruct / verified PE + Self-Ask + MCP baseline",
        "trajectory": "benchmarks/cell_Z_hybrid/raw/core15x5_post175_a100_ixqt_west4_20260505T0724Z_ZS_post175_15x5_exp2_cell_ZS_verified_pe_self_ask_mcp_baseline/2026-05-05_Z_llama-3-1-8b-instruct_verified_pe_baseline_multi_02_dga_to_workorder_pipeline_run05.json",
        "judge": "results/judge_logs/core15x5_post175_a100_ixqt_west4_20260505T0724Z_ZS_post175_15x5_exp2_cell_ZS_verified_pe_self_ask_mcp_baseline/SGT-010_run05_judge_log.json",
    },
    {
        "label": "SGT-012 | IoT load-current anomaly",
        "aliases": ["SGT-012"],
        "domains": "IoT, TSFM",
        "cell": "ZS / Llama-3.1-8B-Instruct / verified PE + Self-Ask + MCP baseline",
        "trajectory": "benchmarks/cell_Z_hybrid/raw/core15x5_post175_a100_ixqt_west4_20260505T0724Z_ZS_post175_15x5_exp2_cell_ZS_verified_pe_self_ask_mcp_baseline/2026-05-05_Z_llama-3-1-8b-instruct_verified_pe_baseline_iot_04_load_current_overload_check_run01.json",
        "judge": "results/judge_logs/core15x5_post175_a100_ixqt_west4_20260505T0724Z_ZS_post175_15x5_exp2_cell_ZS_verified_pe_self_ask_mcp_baseline/SGT-012_run01_judge_log.json",
    },
    {
        "label": "SGT-030 | RUL forecast to work order",
        "aliases": ["SGT-030"],
        "domains": "TSFM, WO",
        "cell": "ZS / Llama-3.1-8B-Instruct / verified PE + Self-Ask + MCP baseline",
        "trajectory": "benchmarks/cell_Z_hybrid/raw/core15x5_post175_a100_ixqt_west4_20260505T0724Z_ZS_post175_15x5_exp2_cell_ZS_verified_pe_self_ask_mcp_baseline/2026-05-05_Z_llama-3-1-8b-instruct_verified_pe_baseline_multi_06_anomaly_to_rul_to_workorder_run01.json",
        "judge": "results/judge_logs/core15x5_post175_a100_ixqt_west4_20260505T0724Z_ZS_post175_15x5_exp2_cell_ZS_verified_pe_self_ask_mcp_baseline/SGT-030_run01_judge_log.json",
    },
]


def load_json(relpath: str) -> dict:
    path = REPO_ROOT / relpath
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def wrap(text: str, width: int = 92, indent: str = "") -> str:
    return "\n".join(
        (
            textwrap.fill(
                line, width=width, subsequent_indent=indent, initial_indent=indent
            )
            if line.strip()
            else ""
        )
        for line in str(text).splitlines()
    )


def hr(title: str = "") -> None:
    if title:
        print(f"\n=== {title} ===")
    else:
        print("\n" + "=" * 78)


def maybe_sleep(seconds: float) -> None:
    if seconds > 0:
        time.sleep(seconds)


def scenario_id(trajectory: dict, judge: dict) -> str:
    scenario = trajectory.get("scenario") or {}
    return scenario.get("id") or judge.get("scenario_id") or "unknown"


def scenario_task(trajectory: dict) -> str:
    scenario = trajectory.get("scenario") or {}
    return scenario.get("text") or trajectory.get("question") or ""


def scenario_expected(trajectory: dict) -> str:
    scenario = trajectory.get("scenario") or {}
    return scenario.get("characteristic_form") or ""


def print_plan(trajectory: dict) -> None:
    plan = trajectory.get("plan") or []
    print("\nPlan:")
    for step in plan:
        server = step.get("server", "?")
        tool = step.get("tool", "?")
        task = step.get("task", "")
        print(f"  {step.get('step', '?')}. [{server}] {tool} :: {task}")


def print_tools(trajectory: dict) -> None:
    history = trajectory.get("history") or []
    print("\nObserved tool calls:")
    for i, item in enumerate(history, 1):
        server = item.get("server", "?")
        tool = item.get("tool", "?")
        ok = (
            "ok"
            if item.get("success", item.get("executor_success", False))
            else "check"
        )
        args = item.get("tool_args") or {}
        print(f"  {i}. {server}.{tool} [{ok}] args={json.dumps(args, sort_keys=True)}")
        response = str(item.get("response", "")).strip()
        if response:
            compact = " ".join(response.split())
            print(wrap(f"     result: {compact[:260]}", width=100, indent="     "))


def print_judge(judge: dict) -> None:
    dims = judge.get("parsed_dims") or {}
    print("\nArchived judge output:")
    print(f"  scored_at: {judge.get('scored_at')}")
    print(f"  judge_model: {judge.get('judge_model')}")
    print(f"  score_6d: {judge.get('score_6d')}")
    print(f"  pass: {judge.get('pass')}")
    for key in (
        "task_completion",
        "data_retrieval_accuracy",
        "generalized_result_verification",
        "agent_sequence_correct",
        "clarity_and_justification",
        "hallucinations",
    ):
        print(f"  {key}: {dims.get(key)}")
    suggestions = dims.get("suggestions")
    if suggestions:
        print(wrap(f"  suggestions: {suggestions}", width=100, indent="  "))

    raw = judge.get("raw_response")
    if raw:
        try:
            parsed = json.loads(raw)
            raw = json.dumps(parsed, indent=2, sort_keys=True)
        except json.JSONDecodeError:
            pass
        print("\nJudge raw JSON:")
        print(textwrap.indent(raw.strip(), "  "))


_PLACEHOLDER_TOOLS = {"", "none", "None", "NONE", "null", "unknown"}


def grouped_tools(steps: list[dict]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for step in steps:
        server = step.get("server") or "other"
        tool = step.get("tool") or "unknown"
        # Suppress placeholder/null tool entries so the demo recording does not
        # display empty pseudo-tools as if they were real tool calls.
        if tool in _PLACEHOLDER_TOOLS:
            continue
        grouped.setdefault(server.upper(), []).append(tool)
    return grouped


def format_tool_chain(tools: list[str]) -> str:
    cleaned: list[str] = []
    for tool in tools:
        if tool in _PLACEHOLDER_TOOLS:
            continue
        if tool not in cleaned:
            cleaned.append(tool)
    return " -> ".join(cleaned)


def success_count(history: list[dict]) -> tuple[int, int]:
    total = len(history)
    ok = sum(
        1
        for item in history
        if item.get("success", item.get("executor_success", False))
    )
    return ok, total


def print_brief_case(case: dict, pause: float) -> None:
    trajectory = load_json(case["trajectory"])
    judge = load_json(case["judge"])
    plan = trajectory.get("plan") or []
    history = trajectory.get("history") or []
    dims = judge.get("parsed_dims") or {}

    hr(case["label"])
    print(f"Scenario: {scenario_id(trajectory, judge)}")
    print(f"Model/run: {case['cell']}")
    print(f"Coverage: {case['domains']}")
    print("Playback: archived trajectory + archived WatsonX judge log; no live calls")
    print(f"Judge: score={judge.get('score_6d')} pass={judge.get('pass')}")
    maybe_sleep(pause)

    print("\nTask")
    print(wrap(scenario_task(trajectory), width=96))
    maybe_sleep(pause)

    print("\nPlan")
    for domain in ("IOT", "FMSR", "TSFM", "WO"):
        chain = format_tool_chain(grouped_tools(plan).get(domain, []))
        if chain:
            print(f"  {domain:<4} {chain}")
    maybe_sleep(pause)

    ok, total = success_count(history)
    print(f"\nTool trace: {ok}/{total} calls succeeded")
    for domain in ("IOT", "FMSR", "TSFM", "WO"):
        chain = format_tool_chain(grouped_tools(history).get(domain, []))
        if chain:
            print(f"  {domain:<4} {chain}")
    maybe_sleep(pause)

    print("\nFinal answer")
    print(wrap(trajectory.get("answer", ""), width=96))
    print("\nJudge dimensions")
    for key in (
        "task_completion",
        "data_retrieval_accuracy",
        "generalized_result_verification",
        "agent_sequence_correct",
        "clarity_and_justification",
        "hallucinations",
    ):
        print(f"  {key}: {dims.get(key)}")


def print_full_case(case: dict, pause: float) -> None:
    trajectory = load_json(case["trajectory"])
    judge = load_json(case["judge"])

    hr(case["label"])
    print("archived: true")
    print("live_model_call: false")
    print("live_judge_call: false")
    print(f"cell: {case['cell']}")
    print(f"coverage: {case['domains']}")
    print(f"scenario_id: {scenario_id(trajectory, judge)}")
    print(f"trajectory_file: {case['trajectory']}")
    print(f"judge_log: {case['judge']}")
    maybe_sleep(pause)

    print("\nTask:")
    print(wrap(scenario_task(trajectory)))
    print("\nExpected behavior:")
    print(wrap(scenario_expected(trajectory)))
    maybe_sleep(pause)

    print_plan(trajectory)
    maybe_sleep(pause)
    print_tools(trajectory)
    maybe_sleep(pause)

    print("\nFinal answer:")
    print(wrap(trajectory.get("answer", "")))
    maybe_sleep(pause)
    print_judge(judge)


def print_case(case: dict, pause: float, mode: str) -> None:
    if mode == "full":
        print_full_case(case, pause)
    else:
        print_brief_case(case, pause)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case",
        choices=["all", "all-domain", "SGT-009", "SGT-010", "SGT-012", "SGT-030"],
        default="all-domain",
        help="Which archived scenario to print.",
    )
    parser.add_argument(
        "--mode",
        choices=["brief", "summary", "full"],
        default="brief",
        help="Output detail. brief/summary are recording-friendly; full includes paths and raw judge JSON.",
    )
    parser.add_argument(
        "--pause",
        type=float,
        default=0.0,
        help="Seconds to pause between blocks for screen recording.",
    )
    args = parser.parse_args()

    print("SmartGridBench static demo playback")
    print("Source: archived 8B ZS-family trajectories + archived WatsonX judge logs")
    print("No live WatsonX call is made in this playback.")

    selected = CASES
    if args.case == "all-domain":
        selected = [case for case in CASES if "all-domain" in case["aliases"]]
    if args.case != "all":
        selected = [case for case in selected if args.case in case["aliases"]]

    for case in selected:
        print_case(case, args.pause, args.mode)

    hr("Coverage Summary")
    if args.case == "all-domain":
        print(
            "This one archived scenario covers IoT + FMSR + TSFM + WO in both plan and trace."
        )
    else:
        print(
            "Across these archived snapshots: IoT + FMSR + TSFM + WO are all represented."
        )
    print("Use this for recording when live judge credentials are unavailable.")


if __name__ == "__main__":
    main()
