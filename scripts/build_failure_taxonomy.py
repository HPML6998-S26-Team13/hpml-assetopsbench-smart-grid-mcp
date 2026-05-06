#!/usr/bin/env python3
"""
Build `results/metrics/failure_taxonomy_current.csv`: programmatic
auto-classification of every failure in `scenario_scores.jsonl`,
joined to `evidence_registry.csv` for paper-eligibility provenance.

This is the post-PR188 #35 deliverable. PR #189 audits the preliminary
PR #151 35-row table by hand; this artifact covers the full paper-grade
1,276 failure rows (and the 690 non-paper-eligible failures alongside,
flagged for completeness) without hand-auditing each one.

Auto-taxonomy:
  The six `dim_*` fields are booleans (True = the rubric dimension
  passed). For each failure row, the auto-label is the highest-priority
  failed dim per CANONICAL_DIM_ORDER (`low_<dim_root>`, e.g.
  `low_task_completion`). Failure rows have between 2 and 6 failed dims —
  the full set is preserved alongside the label in `failed_dims` and
  `failed_dim_count`, so downstream audits and the paper's failure
  section can see both the dominant problem and the co-occurring ones.
  The auditor decides the final taxonomy on the stratified sample.

Audit status:
  - `auto_only`           — programmatic label only
  - `stratified_sample`   — flagged for hand-pass (one per non-empty
                            (experiment_cell, auto_taxonomy_label) stratum,
                            drawn deterministically from paper-eligible
                            failures, capped at --sample-size).
  - `paper_cited`         — manually set by the auditor when a row appears
                            in the paper.
  - `manual_confirmed`    — manually set after the auditor agrees with
                            (or overrides) the auto label.

Reproducibility:
  --seed makes the stratified sample deterministic. Default seed=20260506.

Usage:
  python scripts/build_failure_taxonomy.py \\
      --input    results/metrics/scenario_scores.jsonl \\
      --registry results/metrics/evidence_registry.csv \\
      --out      results/metrics/failure_taxonomy_current.csv

Closes the build half of issue #35; the manual audit on the stratified
sample + paper-cited rows is the remaining half.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

# Canonical tie-break order for auto-taxonomy. Earlier dimensions win
# ties, so dim_task_completion (bottom-line outcome) wins over the more
# downstream dimensions when scores are equal.
CANONICAL_DIM_ORDER = [
    "dim_task_completion",
    "dim_data_retrieval_accuracy",
    "dim_agent_sequence_correct",
    "dim_hallucinations",
    "dim_generalized_result_verification",
    "dim_clarity_and_justification",
]

OUTPUT_COLUMNS = [
    "paper_eligible",
    "exclude_reason",
    "auto_taxonomy_label",
    "failed_dims",
    "failed_dim_count",
    "audit_status",
    "score_6d",
    "pass",
    "pass_threshold",
    "dim_task_completion",
    "dim_data_retrieval_accuracy",
    "dim_agent_sequence_correct",
    "dim_clarity_and_justification",
    "dim_generalized_result_verification",
    "dim_hallucinations",
    "run_name",
    "cohort_id",
    "experiment_cell",
    "orchestration_mode",
    "mcp_mode",
    "model_id",
    "judge_model",
    "scenario_id",
    "scenario_file",
    "trial_index",
    "trajectory_file",
    "wandb_run_url",
    "suggestions",
    "scored_at",
    "schema_version",
]


def load_registry(path: Path) -> dict[str, dict[str, str]]:
    """Map run_name -> registry row. Each run_name is unique in the registry."""
    out: dict[str, dict[str, str]] = {}
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            out[row["run_name"]] = row
    return out


def auto_taxonomy(row: dict) -> tuple[str, list[str]]:
    """Return (label, failed_dims).

    `dim_*` fields are booleans where True == that rubric dimension passed.
    Failed dims are the False ones. Label = `low_<root>` for the highest-
    priority failed dim per CANONICAL_DIM_ORDER. `failed_dims` is the full
    list of failed dim roots in canonical order (preserves the co-occurring
    failure pattern that the single label drops).
    """
    failed = [d for d in CANONICAL_DIM_ORDER if row.get(d) is False]
    if not failed:
        return "low_unknown", []
    winner = failed[0]
    label = "low_" + winner.removeprefix("dim_")
    failed_roots = [d.removeprefix("dim_") for d in failed]
    return label, failed_roots


def is_failure(row: dict) -> bool:
    """A row is a failure iff `pass` is False (mirrors the registry's claim)."""
    return row.get("pass") is False


def is_paper_eligible(reg_row: dict | None) -> bool:
    if reg_row is None:
        return False
    return reg_row.get("include_in_paper", "").strip().lower() in {
        "true",
        "yes",
        "1",
        "y",
    }


def stratified_sample(rows: list[dict], sample_size: int, seed: int) -> set[int]:
    """Pick row indices for the stratified sample.

    Strata = (experiment_cell, auto_taxonomy_label) over paper-eligible
    failures only. One row per non-empty stratum, deterministic per seed.
    Capped at sample_size — strata are visited in shuffled order so the
    cap doesn't bias toward the first-seen cells.
    """
    rng = random.Random(seed)
    eligible = [(i, r) for i, r in enumerate(rows) if r["paper_eligible"] == "true"]
    buckets: dict[tuple[str, str], list[int]] = defaultdict(list)
    for i, r in eligible:
        buckets[(r["experiment_cell"], r["auto_taxonomy_label"])].append(i)
    # Deterministic stratum order (sorted), then deterministic shuffle.
    stratum_keys = sorted(buckets.keys())
    rng.shuffle(stratum_keys)
    picked: set[int] = set()
    for key in stratum_keys:
        if len(picked) >= sample_size:
            break
        candidates = sorted(buckets[key])
        # Pick one row per stratum, deterministically.
        idx = candidates[rng.randrange(len(candidates))]
        picked.add(idx)
    return picked


def build_rows(scores_path: Path, registry_path: Path) -> list[dict]:
    registry = load_registry(registry_path)
    out: list[dict] = []
    with scores_path.open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            if not is_failure(row):
                continue
            run_name = row["run_name"]
            reg_row = registry.get(run_name)
            paper_eligible = is_paper_eligible(reg_row)
            exclude_reason = ""
            if reg_row is None:
                exclude_reason = "run_name not present in evidence_registry.csv"
            elif not paper_eligible:
                exclude_reason = reg_row.get("reason", "").strip()
            label, failed_dims = auto_taxonomy(row)
            out.append(
                {
                    "paper_eligible": "true" if paper_eligible else "false",
                    "exclude_reason": exclude_reason,
                    "auto_taxonomy_label": label,
                    "failed_dims": ",".join(failed_dims),
                    "failed_dim_count": len(failed_dims),
                    "audit_status": "auto_only",
                    "score_6d": row.get("score_6d"),
                    "pass": row.get("pass"),
                    "pass_threshold": row.get("pass_threshold"),
                    "dim_task_completion": row.get("dim_task_completion"),
                    "dim_data_retrieval_accuracy": row.get(
                        "dim_data_retrieval_accuracy"
                    ),
                    "dim_agent_sequence_correct": row.get("dim_agent_sequence_correct"),
                    "dim_clarity_and_justification": row.get(
                        "dim_clarity_and_justification"
                    ),
                    "dim_generalized_result_verification": row.get(
                        "dim_generalized_result_verification"
                    ),
                    "dim_hallucinations": row.get("dim_hallucinations"),
                    "run_name": run_name,
                    "cohort_id": (reg_row or {}).get("cohort_id", ""),
                    "experiment_cell": row.get("experiment_cell"),
                    "orchestration_mode": row.get("orchestration_mode"),
                    "mcp_mode": row.get("mcp_mode"),
                    "model_id": row.get("model_id"),
                    "judge_model": row.get("judge_model"),
                    "scenario_id": row.get("scenario_id"),
                    "scenario_file": row.get("scenario_file"),
                    "trial_index": row.get("trial_index"),
                    "trajectory_file": row.get("trajectory_file"),
                    "wandb_run_url": row.get("wandb_run_url"),
                    "suggestions": row.get("suggestions"),
                    "scored_at": row.get("scored_at"),
                    "schema_version": row.get("schema_version"),
                }
            )
    # Deterministic sort: paper-eligible first (so the head of the file is the
    # paper-grade evidence), then by run_name, scenario_id, trial_index.
    out.sort(
        key=lambda r: (
            0 if r["paper_eligible"] == "true" else 1,
            r["run_name"] or "",
            r["scenario_id"] or "",
            r["trial_index"] if r["trial_index"] is not None else -1,
        )
    )
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--input",
        type=Path,
        default=Path("results/metrics/scenario_scores.jsonl"),
        help="Path to scenario_scores.jsonl",
    )
    p.add_argument(
        "--registry",
        type=Path,
        default=Path("results/metrics/evidence_registry.csv"),
        help="Path to evidence_registry.csv",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=Path("results/metrics/failure_taxonomy_current.csv"),
        help="Output CSV path",
    )
    p.add_argument(
        "--sample-size",
        type=int,
        default=50,
        help="Target number of paper-eligible rows to flag as "
        "audit_status='stratified_sample' (one per (cell, label) stratum, "
        "capped at this size). Default 50.",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=20260506,
        help="Deterministic-sample seed. Default 20260506.",
    )
    args = p.parse_args(argv)

    rows = build_rows(args.input, args.registry)
    sample_idx = stratified_sample(rows, args.sample_size, args.seed)
    for i in sample_idx:
        rows[i]["audit_status"] = "stratified_sample"

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    n_total = len(rows)
    n_paper = sum(1 for r in rows if r["paper_eligible"] == "true")
    n_sample = sum(1 for r in rows if r["audit_status"] == "stratified_sample")
    print(
        f"wrote {args.out}: {n_total} failure rows "
        f"({n_paper} paper-eligible, {n_total - n_paper} non-paper-eligible); "
        f"{n_sample} flagged for hand-audit",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
