#!/usr/bin/env python3
"""Backfill canonical scenario field into existing per-trial JSON captures.

Notebook 03's `canonical_rows` gate requires each per-trial output JSON to carry
`data["scenario"] = <input scenario object>` (with at least an `id` key). The
runners and the upstream AOB `plan-execute` CLI did not propagate this until
the run_experiment.sh post-processing step landed; pre-existing captures are
all classified as `legacy` and excluded from cross-cell aggregation.

This script walks each `benchmarks/cell_<X>/raw/<run_id>/` directory, reads the
companion `latencies.jsonl` to map output path -> source scenario file, opens
each per-trial JSON and injects `data["scenario"]` from the source scenario
file. Idempotent: if `data["scenario"]` is already a dict with an `id`, the
file is left alone.

Usage:
  python3 scripts/backfill_canonical_scenario.py            # dry-run, all cells
  python3 scripts/backfill_canonical_scenario.py --apply    # write changes
  python3 scripts/backfill_canonical_scenario.py --apply --cell B  # one cell

Exit codes: 0 always (parse errors are reported but do not fail the sweep).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

CELL_DIRS = {
    "A": "benchmarks/cell_A_direct",
    "B": "benchmarks/cell_B_mcp_baseline",
    "Y": "benchmarks/cell_Y_plan_execute",
    "Z": "benchmarks/cell_Z_hybrid",
    "C": "benchmarks/cell_C_mcp_optimized",
}


def repo_root_from(start: pathlib.Path) -> pathlib.Path:
    cur = start.resolve()
    for cand in [cur, *cur.parents]:
        if (cand / "benchmarks").exists() and (cand / "data" / "scenarios").exists():
            return cand
    raise SystemExit(f"Could not locate repo root from {start}")


def load_json(path: pathlib.Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def map_output_to_scenario(
    run_dir: pathlib.Path, repo_root: pathlib.Path
) -> dict[pathlib.Path, pathlib.Path]:
    """Read latencies.jsonl and return {resolved_trial_output -> resolved_scenario_file}."""
    latencies_file = run_dir / "latencies.jsonl"
    out: dict[pathlib.Path, pathlib.Path] = {}
    if not latencies_file.exists():
        return out
    for line_num, line in enumerate(
        latencies_file.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            print(
                f"  WARN: {latencies_file}:{line_num} unparseable, skipping",
                file=sys.stderr,
            )
            continue
        out_path_raw = row.get("output_path")
        scen_path_raw = row.get("scenario_file")
        if not out_path_raw or not scen_path_raw:
            continue
        out_path = (
            (repo_root / out_path_raw)
            if not pathlib.Path(out_path_raw).is_absolute()
            else pathlib.Path(out_path_raw)
        )
        scen_path = (
            (repo_root / scen_path_raw)
            if not pathlib.Path(scen_path_raw).is_absolute()
            else pathlib.Path(scen_path_raw)
        )
        try:
            out_path = out_path.resolve()
        except OSError:
            pass
        try:
            scen_path = scen_path.resolve()
        except OSError:
            pass
        out[out_path] = scen_path
    return out


def _step_failed(step: dict) -> bool:
    if not isinstance(step, dict):
        return False
    if step.get("success") is False:
        return True
    if step.get("error"):
        return True
    resp = step.get("response")
    if isinstance(resp, dict) and resp.get("error"):
        return True
    return False


def _derive_success(data: dict) -> bool | None:
    raw = data.get("success")
    if isinstance(raw, bool):
        return raw
    # Match Notebook 03's history-first precedence so all three call sites
    # (run_experiment.sh post-process, this backfill, notebook
    # load_*_records) walk the same step array.
    steps = data.get("history") or data.get("trajectory") or []
    if not steps and not data.get("answer"):
        return None
    for step in steps:
        if _step_failed(step):
            return False
    return bool(data.get("answer"))


def backfill_run_dir(
    run_dir: pathlib.Path, repo_root: pathlib.Path, apply: bool
) -> dict:
    stats = {
        "checked": 0,
        "already_canonical": 0,
        "backfilled_scenario": 0,
        "backfilled_success": 0,
        "skipped_no_mapping": 0,
        "skipped_no_scenario": 0,
        "errors": 0,
    }
    if not run_dir.is_dir():
        return stats
    output_to_scenario = map_output_to_scenario(run_dir, repo_root)
    for trial_file in sorted(run_dir.glob("*.json")):
        if trial_file.name in ("meta.json", "config.json", "summary.json"):
            continue
        stats["checked"] += 1
        try:
            resolved = trial_file.resolve()
        except OSError:
            resolved = trial_file
        scen_path = output_to_scenario.get(resolved)
        if scen_path is None:
            stats["skipped_no_mapping"] += 1
            continue
        scenario = load_json(scen_path)
        if scenario is None:
            stats["skipped_no_scenario"] += 1
            continue
        payload = load_json(trial_file)
        if payload is None or not isinstance(payload, dict):
            stats["errors"] += 1
            continue

        existing = payload.get("scenario")
        scenario_already = isinstance(existing, dict) and existing.get("id")
        success_already = isinstance(payload.get("success"), bool)

        if scenario_already and success_already:
            stats["already_canonical"] += 1
            continue

        changed = False
        if not scenario_already:
            payload["scenario"] = scenario
            stats["backfilled_scenario"] += 1
            changed = True
        if not success_already:
            derived = _derive_success(payload)
            if derived is not None:
                payload["success"] = derived
                stats["backfilled_success"] += 1
                changed = True
        if changed and apply:
            trial_file.write_text(
                json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8"
            )
    return stats


def backfill_cell(
    cell_label: str, cell_path: pathlib.Path, repo_root: pathlib.Path, apply: bool
) -> dict:
    raw_dir = cell_path / "raw"
    totals = {
        "runs": 0,
        "checked": 0,
        "already_canonical": 0,
        "backfilled_scenario": 0,
        "backfilled_success": 0,
        "skipped_no_mapping": 0,
        "skipped_no_scenario": 0,
        "errors": 0,
    }
    if not raw_dir.is_dir():
        return totals
    for run_dir in sorted(p for p in raw_dir.iterdir() if p.is_dir()):
        stats = backfill_run_dir(run_dir, repo_root, apply)
        totals["runs"] += 1
        for k in (
            "checked",
            "already_canonical",
            "backfilled_scenario",
            "backfilled_success",
            "skipped_no_mapping",
            "skipped_no_scenario",
            "errors",
        ):
            totals[k] += stats[k]
        if stats["checked"]:
            print(
                f"  {cell_label}/{run_dir.name}: checked={stats['checked']} "
                f"+scen={stats['backfilled_scenario']} +success={stats['backfilled_success']} "
                f"canonical={stats['already_canonical']} no_map={stats['skipped_no_mapping']} "
                f"no_scen={stats['skipped_no_scenario']} errors={stats['errors']}"
            )
    return totals


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply", action="store_true", help="Actually write changes (default: dry-run)"
    )
    parser.add_argument(
        "--cell",
        action="append",
        choices=sorted(CELL_DIRS),
        help="Limit to one or more cells (default: all)",
    )
    parser.add_argument(
        "--repo-root",
        type=pathlib.Path,
        default=None,
        help="Override repo root detection",
    )
    args = parser.parse_args()

    repo_root = (
        args.repo_root.resolve()
        if args.repo_root
        else repo_root_from(pathlib.Path.cwd())
    )
    print(f"Repo root: {repo_root}")
    print(f"Mode:      {'APPLY (writing)' if args.apply else 'DRY-RUN (no changes)'}")

    cells_to_process = args.cell or sorted(CELL_DIRS)
    grand = {
        "runs": 0,
        "checked": 0,
        "already_canonical": 0,
        "backfilled_scenario": 0,
        "backfilled_success": 0,
        "skipped_no_mapping": 0,
        "skipped_no_scenario": 0,
        "errors": 0,
    }
    for cell in cells_to_process:
        cell_path = repo_root / CELL_DIRS[cell]
        print(f"== Cell {cell}: {cell_path.relative_to(repo_root)} ==")
        totals = backfill_cell(cell, cell_path, repo_root, args.apply)
        for k in grand:
            grand[k] += totals[k]
        print(
            f"  cell totals: runs={totals['runs']} checked={totals['checked']} "
            f"+scen={totals['backfilled_scenario']} +success={totals['backfilled_success']} "
            f"canonical={totals['already_canonical']}"
        )
    print("\n== Sweep totals ==")
    for k, v in grand.items():
        print(f"  {k:24s} {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
