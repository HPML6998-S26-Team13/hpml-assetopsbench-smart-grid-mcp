#!/usr/bin/env python3
"""Render the #66 mitigation before/after comparison export.

The source of truth is the paper-grade post-PR175 mitigation cohort summary plus
the tracked raw benchmark artifacts. This keeps
``results/metrics/mitigation_before_after.csv`` as the stable paper-facing
comparison path without preserving superseded post-PR180 diagnostic rows.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
METRICS_DIR = ROOT / "results" / "metrics"
SOURCE_SUMMARY = METRICS_DIR / "gcp_post175_mitigation_4tier_summary.csv"
SCORE_SOURCE = METRICS_DIR / "scenario_scores.jsonl"
OUTPUT_CSV = METRICS_DIR / "mitigation_before_after.csv"

FIELDNAMES = [
    "lane",
    "phase",
    "run_name",
    "cell",
    "orchestration_mode",
    "mcp_mode",
    "model_id",
    "slurm_job_id",
    "git_sha",
    "scenario_set_name",
    "scenario_set_hash",
    "experiment_family",
    "experiment_cell",
    "wandb_run_url",
    "benchmark_config_path",
    "benchmark_summary_path",
    "host_name",
    "gpu_type",
    "run_status",
    "finished_at",
    "scenarios_attempted",
    "scenarios_completed",
    "success_rate",
    "failure_count",
    "wall_clock_seconds_total",
    "latency_seconds_mean",
    "latency_seconds_p50",
    "latency_seconds_p95",
    "mcp_latency_seconds_mean",
    "mcp_latency_seconds_p95",
    "tool_latency_seconds_mean",
    "tool_call_count_total",
    "tool_call_count_mean",
    "tool_error_count",
    "input_tokens_total",
    "output_tokens_total",
    "tokens_per_second_mean",
    "judge_score_mean",
    "judge_score_p50",
    "judge_score_p95",
    "judge_score_p5",
    "judge_pass_rate",
    "benchmark_run_dir",
    "profiling_dir",
    "torch_profile_dir",
    "replay_dir",
    "profiling_summary",
    "profiling_gpu_util_mean",
    "profiling_gpu_util_max",
    "profiling_gpu_mem_used_mib_mean",
    "profiling_gpu_mem_used_mib_max",
    "profiling_power_draw_w_mean",
    "profiling_power_draw_w_max",
    "mitigation_name",
    "mitigation_enabled",
    "mitigation_guard_triggered",
    "mitigation_guard_blocked_final_answer",
    "mitigation_guard_blocked_work_order",
    "repair_attempt_count",
    "repair_success_rate",
    "supported_success_after_repair_rate",
    "fault_risk_adjudication_decision",
    "comparison_status",
    "notes",
]

PHASE_BY_ROW_GROUP = {
    "YS_BASELINE": "baseline",
    "YS_GUARD": "guard",
    "YS_REPAIR": "repair",
    "YS_ADJ": "adjudication",
    "ZS_BASELINE": "baseline",
    "ZS_GUARD": "guard",
    "ZS_REPAIR": "repair",
    "ZS_ADJ": "adjudication",
}

MITIGATION_BY_PHASE = {
    "baseline": "baseline",
    "guard": "missing_evidence_final_answer_guard",
    "repair": "missing_evidence_retry_replan_guard",
    "adjudication": "explicit_fault_risk_adjudication_step",
}

DISPLAY_CELL_BY_LANE = {
    "YS": "PE-S-M",
    "ZS": "V-S-M",
}

ORDER = {
    "YS_BASELINE": 0,
    "YS_GUARD": 1,
    "YS_REPAIR": 2,
    "YS_ADJ": 3,
    "ZS_BASELINE": 4,
    "ZS_GUARD": 5,
    "ZS_REPAIR": 6,
    "ZS_ADJ": 7,
}

HOST_NAME = "smartgrid-a100-ixqt-uswest3-20260503-2116"
GPU_TYPE = "NVIDIA A100-SXM4-40GB"
SCENARIO_SET_NAME = "mitigation15_4tier"
COMPARISON_STATUS = "paper_grade_post175_matched"


def fmt(value: Any, digits: int = 6) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return f"{value:.{digits}f}".rstrip("0").rstrip(".")
    return str(value)


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * q
    low = int(pos)
    high = min(low + 1, len(ordered) - 1)
    frac = pos - low
    return ordered[low] * (1 - frac) + ordered[high] * frac


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return json.load(f)


def load_scores_by_run() -> dict[str, list[dict[str, Any]]]:
    scores: dict[str, list[dict[str, Any]]] = {}
    with SCORE_SOURCE.open() as f:
        for line in f:
            row = json.loads(line)
            scores.setdefault(row["run_name"], []).append(row)
    return scores


def load_latencies(run_dir: Path) -> list[float]:
    latencies_path = run_dir / "latencies.jsonl"
    values: list[float] = []
    with latencies_path.open() as f:
        for line in f:
            row = json.loads(line)
            values.append(float(row["latency_seconds"]))
    return values


def iter_trial_json(run_dir: Path) -> list[Path]:
    return sorted(run_dir.glob("*_run[0-9][0-9].json"))


def wall_clock_seconds(meta: dict[str, Any]) -> float | None:
    started = meta.get("started_at")
    finished = meta.get("finished_at")
    if not started or not finished:
        return None
    start_dt = datetime.fromisoformat(started)
    finish_dt = datetime.fromisoformat(finished)
    return (finish_dt - start_dt).total_seconds()


def response_has_error(response: Any) -> bool:
    if isinstance(response, dict):
        return bool(response.get("error"))
    return False


def aggregate_trials(run_dir: Path) -> dict[str, Any]:
    tool_calls = 0
    tool_errors = 0
    guard = Counter()
    repair_records = 0
    repair_triggered = 0
    repair_attempts = 0
    repair_successes = 0
    repaired_successful_trials = 0
    adjudication_decisions: Counter[str] = Counter()

    for path in iter_trial_json(run_dir):
        data = load_json(path)
        for step in data.get("history") or []:
            tool_calls += 1
            if (
                step.get("success") is False
                or step.get("executor_success") is False
                or step.get("error")
                or response_has_error(step.get("response"))
            ):
                tool_errors += 1

        guard_payload = data.get("mitigation_guard") or {}
        if guard_payload:
            guard["records"] += 1
            for key in ("triggered", "blocked_final_answer", "blocked_work_order"):
                if guard_payload.get(key):
                    guard[key] += 1

        repair_payload = data.get("mitigation_repair") or {}
        if repair_payload:
            repair_records += 1
            if repair_payload.get("triggered"):
                repair_triggered += 1
            attempts = repair_payload.get("attempts") or []
            repair_attempts += len(attempts)
            if repair_payload.get("repaired"):
                repair_successes += 1
                if data.get("success"):
                    repaired_successful_trials += 1

        adjudication_payload = data.get("fault_risk_adjudication") or {}
        if adjudication_payload:
            decision = adjudication_payload.get("decision") or "unknown"
            adjudication_decisions[decision] += 1

    return {
        "tool_call_count_total": tool_calls,
        "tool_error_count": tool_errors,
        "mitigation_guard_triggered": guard.get("triggered", 0),
        "mitigation_guard_blocked_final_answer": guard.get("blocked_final_answer", 0),
        "mitigation_guard_blocked_work_order": guard.get("blocked_work_order", 0),
        "repair_records": repair_records,
        "repair_triggered": repair_triggered,
        "repair_attempt_count": repair_attempts,
        "repair_success_count": repair_successes,
        "repaired_successful_trials": repaired_successful_trials,
        "fault_risk_adjudication_decision": ";".join(
            f"{key}={adjudication_decisions[key]}"
            for key in sorted(adjudication_decisions)
        ),
    }


def validate_count(label: str, actual: int, expected: str, field: str) -> None:
    expected_int = int(expected)
    if actual != expected_int:
        raise ValueError(
            f"{label}: {field} count mismatch, expected {expected_int}, got {actual}"
        )


def build_row(
    source_row: dict[str, str],
    scores_by_run: dict[str, list[dict[str, Any]]],
) -> dict[str, str]:
    label = source_row["row_group"]
    run_name = source_row["run_name"]
    run_dir = ROOT / source_row["run_dir"]
    meta = load_json(run_dir / "meta.json")
    latencies = load_latencies(run_dir)
    scores = scores_by_run.get(run_name, [])
    trials = iter_trial_json(run_dir)

    validate_count(label, len(trials), source_row["raw_json_count"], "raw JSON")
    validate_count(label, len(latencies), source_row["latency_count"], "latency")
    validate_count(label, len(scores), source_row["judge_count"], "judge")

    aggregates = aggregate_trials(run_dir)
    score_values = [float(row["score_6d"]) for row in scores]
    lane = label.split("_", 1)[0]
    phase = PHASE_BY_ROW_GROUP[label]
    attempted = int(meta.get("total_runs") or source_row["raw_json_count"])
    completed = int(meta.get("pass") or 0)
    failed = int(meta.get("fail") or (attempted - completed))

    repair_success_rate = ""
    supported_success_after_repair_rate = ""
    if phase in {"repair", "adjudication"}:
        repair_triggered = aggregates["repair_triggered"]
        if repair_triggered:
            repair_success_rate = fmt(
                aggregates["repair_success_count"] / repair_triggered
            )
        supported_success_after_repair_rate = fmt(
            aggregates["repaired_successful_trials"] / attempted
        )

    notes_parts = [
        f"label={label}",
        f"cohort={source_row['cohort']}",
        f"batch={source_row['batch_prefix']}",
        f"raw_json_count={source_row['raw_json_count']}",
        f"latency_count={source_row['latency_count']}",
        f"judge_count={source_row['judge_count']}",
    ]
    if source_row.get("baseline_row_group") and phase != "baseline":
        notes_parts.append(f"baseline_row_group={source_row['baseline_row_group']}")
    if source_row.get("pass_rate_lift_vs_baseline"):
        notes_parts.append(
            f"pass_rate_lift_vs_baseline={source_row['pass_rate_lift_vs_baseline']}"
        )
    if source_row.get("score_mean_lift_vs_baseline"):
        notes_parts.append(
            f"score_mean_lift_vs_baseline={source_row['score_mean_lift_vs_baseline']}"
        )

    row = {field: "" for field in FIELDNAMES}
    row.update(
        {
            "lane": lane,
            "phase": phase,
            "run_name": run_name,
            "cell": DISPLAY_CELL_BY_LANE[lane],
            "orchestration_mode": meta.get("orchestration_mode", ""),
            "mcp_mode": meta.get("mcp_mode", ""),
            "model_id": source_row["model_id"],
            "git_sha": source_row["git_sha"],
            "scenario_set_name": SCENARIO_SET_NAME,
            "experiment_family": meta.get("experiment_family", ""),
            "experiment_cell": meta.get("experiment_cell", ""),
            "wandb_run_url": meta.get("wandb_run_url", ""),
            "benchmark_config_path": meta.get("benchmark_config_path", ""),
            "benchmark_summary_path": meta.get("benchmark_summary_path", ""),
            "host_name": HOST_NAME,
            "gpu_type": GPU_TYPE,
            "run_status": meta.get("run_status", ""),
            "finished_at": meta.get("finished_at", ""),
            "scenarios_attempted": fmt(attempted),
            "scenarios_completed": fmt(completed),
            "success_rate": fmt(completed / attempted if attempted else None),
            "failure_count": fmt(failed),
            "wall_clock_seconds_total": fmt(wall_clock_seconds(meta), 2),
            "latency_seconds_mean": fmt(sum(latencies) / len(latencies), 4),
            "latency_seconds_p50": fmt(percentile(latencies, 0.50), 4),
            "latency_seconds_p95": fmt(percentile(latencies, 0.95), 4),
            "tool_call_count_total": fmt(aggregates["tool_call_count_total"]),
            "tool_call_count_mean": fmt(
                aggregates["tool_call_count_total"] / attempted if attempted else None
            ),
            "tool_error_count": fmt(aggregates["tool_error_count"]),
            "judge_score_mean": source_row["judge_score_mean"],
            "judge_score_p50": source_row["judge_score_p50"],
            "judge_score_p95": fmt(percentile(score_values, 0.95), 4),
            "judge_score_p5": fmt(percentile(score_values, 0.05), 4),
            "judge_pass_rate": source_row["judge_pass_rate"],
            "benchmark_run_dir": source_row["run_dir"],
            "mitigation_name": MITIGATION_BY_PHASE[phase],
            "mitigation_enabled": fmt(phase != "baseline"),
            "mitigation_guard_triggered": (
                fmt(aggregates["mitigation_guard_triggered"])
                if phase != "baseline"
                else ""
            ),
            "mitigation_guard_blocked_final_answer": (
                fmt(aggregates["mitigation_guard_blocked_final_answer"])
                if phase != "baseline"
                else ""
            ),
            "mitigation_guard_blocked_work_order": (
                fmt(aggregates["mitigation_guard_blocked_work_order"])
                if phase != "baseline"
                else ""
            ),
            "repair_attempt_count": (
                fmt(aggregates["repair_attempt_count"])
                if phase in {"repair", "adjudication"}
                else ""
            ),
            "repair_success_rate": repair_success_rate,
            "supported_success_after_repair_rate": supported_success_after_repair_rate,
            "fault_risk_adjudication_decision": (
                aggregates["fault_risk_adjudication_decision"]
                if phase == "adjudication"
                else ""
            ),
            "comparison_status": COMPARISON_STATUS,
            "notes": "; ".join(notes_parts),
        }
    )
    return row


def main() -> None:
    scores_by_run = load_scores_by_run()
    with SOURCE_SUMMARY.open() as f:
        source_rows = sorted(csv.DictReader(f), key=lambda row: ORDER[row["row_group"]])

    rows = [build_row(row, scores_by_run) for row in source_rows]

    with OUTPUT_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {OUTPUT_CSV.relative_to(ROOT)} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
