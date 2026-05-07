#!/usr/bin/env python3
"""Build a run-level WandB/profiling inventory from benchmark metadata.

This intentionally inventories links and run summaries, not trace blobs. The
large profiler outputs stay in their original artifact stores; the CSV gives the
paper/class-grading path a compact "what exists and where" surface.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_BENCHMARKS = ROOT / "benchmarks"
DEFAULT_SCORES = ROOT / "results" / "metrics" / "scenario_scores.jsonl"
DEFAULT_REGISTRY = ROOT / "results" / "metrics" / "evidence_registry.csv"
DEFAULT_OUT = ROOT / "results" / "metrics" / "profiling_inventory.csv"

OUTPUT_COLUMNS = [
    "benchmark_run_dir",
    "run_name",
    "benchmark_cell_dir",
    "experiment_cell",
    "orchestration_mode",
    "mcp_mode",
    "model_id",
    "git_sha",
    "registry_status",
    "include_in_paper",
    "registry_reason",
    "run_status",
    "started_at",
    "finished_at",
    "total_runs",
    "pass",
    "fail",
    "has_wandb",
    "wandb_run_id",
    "wandb_run_url",
    "has_profiling",
    "profiling_dir",
    "profiling_artifact",
    "has_profiling_summary",
    "profiling_gpu_util_mean",
    "profiling_gpu_util_max",
    "profiling_gpu_mem_used_mib_mean",
    "profiling_gpu_mem_used_mib_max",
    "profiling_power_draw_w_mean",
    "profiling_power_draw_w_max",
    "profiling_nvidia_smi_samples",
    "notes",
]

CELL_DIR_FALLBACKS = {
    "cell_A_direct": "A",
    "cell_B_mcp_baseline": "B",
    "cell_C_mcp_optimized": "C",
    "cell_D": "D",
    "cell_ZSD": "ZSD",
}


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_score_lookup(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    lookup: dict[str, dict] = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            run_name = row.get("run_name")
            if run_name and run_name not in lookup:
                lookup[run_name] = {
                    "experiment_cell": row.get("experiment_cell"),
                    "orchestration_mode": row.get("orchestration_mode"),
                    "mcp_mode": row.get("mcp_mode"),
                    "model_id": row.get("model_id"),
                    "wandb_run_url": row.get("wandb_run_url"),
                }
    return lookup


def load_registry(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as f:
        return {row["run_name"]: row for row in csv.DictReader(f)}


def infer_cell(cell_dir: str, run_name: str) -> str:
    if cell_dir in CELL_DIR_FALLBACKS:
        return CELL_DIR_FALLBACKS[cell_dir]
    if cell_dir == "cell_Y_plan_execute":
        return "YS" if "self_ask" in run_name else "Y"
    if cell_dir == "cell_Z_hybrid":
        return "ZS" if "self_ask" in run_name else "Z"
    if cell_dir.startswith("cell_"):
        return cell_dir.removeprefix("cell_")
    return ""


def infer_orchestration(cell: str, run_name: str) -> str:
    if cell in {"A", "B", "C", "D"} or cell.endswith("70B"):
        return "agent_as_tool"
    if cell.startswith("Y"):
        return "plan_execute"
    if cell.startswith("Z"):
        return "verified_pe"
    if "verified_pe" in run_name:
        return "verified_pe"
    if "pe_" in run_name:
        return "plan_execute"
    if "aat" in run_name:
        return "agent_as_tool"
    return ""


def infer_mcp_mode(cell: str, run_name: str) -> str:
    if cell == "A" or cell == "A70B" or "_aat_direct" in run_name:
        return "direct"
    if "optimized" in run_name or cell in {"C", "D", "ZSD"}:
        return "optimized"
    if "baseline" in run_name or cell in {"B", "Y", "YS", "Z", "ZS"}:
        return "baseline"
    return ""


def wandb_run_id(url: str) -> str:
    if not url:
        return ""
    path = urlparse(url).path.rstrip("/")
    return path.rsplit("/", 1)[-1] if path else ""


def flatten_summary(summary: dict | None, key: str) -> object:
    if not isinstance(summary, dict):
        return ""
    return summary.get(key, "")


def bool_s(value: object) -> str:
    return "true" if bool(value) else "false"


def build_rows(
    benchmarks_dir: Path,
    scores_path: Path,
    registry_path: Path,
) -> list[dict[str, object]]:
    score_lookup = load_score_lookup(scores_path)
    registry = load_registry(registry_path)
    rows: list[dict[str, object]] = []

    for meta_path in sorted(benchmarks_dir.glob("*/raw/*/meta.json")):
        meta = load_json(meta_path)
        run_dir = meta_path.parent
        cell_dir = run_dir.parents[1].name
        run_name = meta.get("run_name") or run_dir.name
        score = score_lookup.get(run_name, {})
        reg = registry.get(run_name, {})

        inferred_cell = infer_cell(cell_dir, run_name)
        experiment_cell = (
            meta.get("experiment_cell") or inferred_cell or score.get("experiment_cell")
        )
        orchestration_mode = (
            meta.get("orchestration_mode")
            or score.get("orchestration_mode")
            or infer_orchestration(experiment_cell, run_name)
        )
        mcp_mode = (
            meta.get("mcp_mode")
            or score.get("mcp_mode")
            or infer_mcp_mode(experiment_cell, run_name)
        )
        wandb_url = meta.get("wandb_run_url") or score.get("wandb_run_url") or ""
        profiling_dir = meta.get("profiling_dir") or ""
        profiling_artifact = meta.get("profiling_artifact") or ""
        profiling_summary = meta.get("profiling_summary")
        has_profiling_summary = isinstance(profiling_summary, dict) and bool(
            profiling_summary
        )
        has_profiling = bool(
            profiling_dir or profiling_artifact or has_profiling_summary
        )

        notes = ""
        if has_profiling_summary:
            notes = "profiling summary present in meta.json"
        elif has_profiling:
            notes = "profiling artifact linked; summary stats absent from meta.json"
        elif wandb_url:
            notes = "wandb only"

        rows.append(
            {
                "benchmark_run_dir": run_dir.relative_to(ROOT).as_posix(),
                "run_name": run_name,
                "benchmark_cell_dir": cell_dir,
                "experiment_cell": experiment_cell,
                "orchestration_mode": orchestration_mode,
                "mcp_mode": mcp_mode,
                "model_id": meta.get("model_id") or score.get("model_id") or "",
                "git_sha": meta.get("git_sha", ""),
                "registry_status": reg.get("status", ""),
                "include_in_paper": reg.get("include_in_paper", ""),
                "registry_reason": reg.get("reason", ""),
                "run_status": meta.get("run_status", ""),
                "started_at": meta.get("started_at", ""),
                "finished_at": meta.get("finished_at", ""),
                "total_runs": meta.get("total_runs", ""),
                "pass": meta.get("pass", ""),
                "fail": meta.get("fail", ""),
                "has_wandb": bool_s(wandb_url),
                "wandb_run_id": wandb_run_id(wandb_url),
                "wandb_run_url": wandb_url,
                "has_profiling": bool_s(has_profiling),
                "profiling_dir": profiling_dir,
                "profiling_artifact": profiling_artifact,
                "has_profiling_summary": bool_s(has_profiling_summary),
                "profiling_gpu_util_mean": flatten_summary(
                    profiling_summary, "profiling/gpu_util_mean"
                ),
                "profiling_gpu_util_max": flatten_summary(
                    profiling_summary, "profiling/gpu_util_max"
                ),
                "profiling_gpu_mem_used_mib_mean": flatten_summary(
                    profiling_summary, "profiling/gpu_mem_used_mib_mean"
                ),
                "profiling_gpu_mem_used_mib_max": flatten_summary(
                    profiling_summary, "profiling/gpu_mem_used_mib_max"
                ),
                "profiling_power_draw_w_mean": flatten_summary(
                    profiling_summary, "profiling/power_draw_w_mean"
                ),
                "profiling_power_draw_w_max": flatten_summary(
                    profiling_summary, "profiling/power_draw_w_max"
                ),
                "profiling_nvidia_smi_samples": flatten_summary(
                    profiling_summary, "profiling/nvidia_smi_samples"
                ),
                "notes": notes,
            }
        )

    rows.sort(
        key=lambda row: (
            row["experiment_cell"] or "",
            row["run_name"] or "",
            row["benchmark_run_dir"] or "",
        )
    )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmarks", type=Path, default=DEFAULT_BENCHMARKS)
    parser.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    rows = build_rows(args.benchmarks, args.scores, args.registry)
    write_csv(args.out, rows)
    print(f"wrote {len(rows)} rows to {display_path(args.out)}")
    print(
        "coverage: "
        f"{sum(r['has_wandb'] == 'true' for r in rows)} W&B-linked, "
        f"{sum(r['has_profiling'] == 'true' for r in rows)} profiler-linked, "
        f"{sum(r['has_profiling_summary'] == 'true' for r in rows)} with summary stats"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
