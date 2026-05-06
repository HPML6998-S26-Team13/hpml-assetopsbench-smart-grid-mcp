"""Paired audit-brief renderer for the failure-taxonomy evidence table (#35).

Subcommands:

    briefs   — for each row in `failure_evidence_table.csv`, print a side-by-side
               brief joining the JSONL judge record and the trajectory tool calls.
               Reviewer reads these to apply the strict criteria from
               `docs/failure_evidence_audit_2026-05-05.md` and hand-edits the CSV
               to fill in the `audit_status` / `audit_note` / `audit_decision_source`
               columns.

    render   — reads the augmented `failure_evidence_table.csv` (after audit
               columns are populated) and writes the Markdown audit summary.

Audit columns added by `add-columns`:
    audit_status            confirmed | relabel_suggested | evidence_thin
    audit_note              free-text reviewer note (one sentence)
    audit_decision_source   "<reviewer>:<YYYY-MM-DD>" (e.g. "akshat:2026-05-05")
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_CSV = REPO_ROOT / "results" / "metrics" / "failure_evidence_table.csv"
SCORES_JSONL = REPO_ROOT / "results" / "metrics" / "scenario_scores.jsonl"
BENCHMARK_ROOTS = {
    "A": REPO_ROOT / "benchmarks" / "cell_A_direct" / "raw",
    "B": REPO_ROOT / "benchmarks" / "cell_B_mcp_baseline" / "raw",
    "C": REPO_ROOT / "benchmarks" / "cell_C_mcp_optimized" / "raw",
    "D": REPO_ROOT / "benchmarks" / "cell_D" / "raw",
    "Y": REPO_ROOT / "benchmarks" / "cell_Y_plan_execute" / "raw",
    "Z": REPO_ROOT / "benchmarks" / "cell_Z_hybrid" / "raw",
    "ZSD": REPO_ROOT / "benchmarks" / "cell_ZSD" / "raw",
}

AUDIT_COLUMNS = ["audit_status", "audit_note", "audit_decision_source"]


def _load_evidence_rows() -> list[dict]:
    with EVIDENCE_CSV.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _load_scores_index() -> dict[tuple[str, str, int], dict]:
    idx: dict[tuple[str, str, int], dict] = {}
    with SCORES_JSONL.open(encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            key = (d["run_name"], d["scenario_id"], int(d["trial_index"]))
            idx[key] = d
    return idx


CLUSTER_PATH_PREFIX = (
    "/insomnia001/depts/edu/users/team13/hpml-assetopsbench-smart-grid-mcp/"
)


def _exists_long(p: Path) -> bool:
    """`Path.is_file` but works around Windows MAX_PATH (260 char) limit.

    Cell Y / Cell Z trajectory filenames push absolute paths past 260 chars on
    this Windows checkout; without the `\\\\?\\` extended-length prefix Python
    treats them as nonexistent.
    """
    if sys.platform.startswith("win"):
        ext = "\\\\?\\" + str(p.resolve())
        try:
            return Path(ext).is_file() or __import__("os").path.exists(ext)
        except OSError:
            return False
    return p.is_file()


def _read_text_long(p: Path) -> str:
    """Read text from a path that may exceed Windows MAX_PATH."""
    if sys.platform.startswith("win"):
        ext = "\\\\?\\" + str(p.resolve())
        with open(ext, encoding="utf-8") as f:
            return f.read()
    return p.read_text(encoding="utf-8")


def _resolve_trajectory_path(score: dict | None) -> Path | None:
    """Translate the JSONL record's `trajectory_file` (cluster path) to local."""
    if not score:
        return None
    raw = score.get("trajectory_file") or ""
    if not raw:
        return None
    # The cluster's checkout lives at /insomnia001/.../hpml-assetopsbench-smart-grid-mcp;
    # the local checkout has the same suffix relative to REPO_ROOT. Some JSONL
    # rows store the path already-relative (`benchmarks/...`) instead.
    if raw.startswith(CLUSTER_PATH_PREFIX):
        rel = raw[len(CLUSTER_PATH_PREFIX) :]
    else:
        rel = raw.lstrip("/")
    candidate = REPO_ROOT / rel
    return candidate if _exists_long(candidate) else None


def _extract_aat_calls(traj: dict) -> list[tuple[str, dict, str]]:
    """Cell A/B/C/D agent_as_tool schema: top-level `history` of role/tool_calls turns.

    Tool outputs are stored two ways: (a) inline on each tool_call dict via
    `tc["output"]` (current AAT trajectory format — Cells A/B/C/D), or (b) in
    a subsequent `role: "tool"` history entry whose `content` is the result
    (older fallback). Capture both so briefs are reproducible regardless of
    which schema variant the trajectory uses (PR #189 v2 H1).
    """
    history = traj.get("history") or []
    out: list[tuple[str, dict, str]] = []
    if not isinstance(history, list):
        return out
    for entry in history:
        if not isinstance(entry, dict):
            continue
        for tc in entry.get("tool_calls") or []:
            if isinstance(tc, dict):
                fn = tc.get("function") or tc
                name = fn.get("name", "?") if isinstance(fn, dict) else "?"
                args = fn.get("arguments") if isinstance(fn, dict) else {}
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {"_raw": args}
                # Inline output, if present (current AAT schema).
                output = tc.get("output", "")
                if isinstance(output, (dict, list)):
                    output = json.dumps(output)
                out.append((name, args or {}, str(output)))
        # Older fallback: role:"tool" message attached to the most recent call.
        if entry.get("role") == "tool" and out:
            name, args, existing = out[-1]
            if not existing:
                out[-1] = (name, args, entry.get("content") or "")
    return out


def _extract_pe_calls(traj: dict) -> list[tuple[str, dict, str]]:
    """Cell Y/Z/ZSD plan_execute / verified_pe schema: top-level `trajectory` list of step dicts."""
    steps = traj.get("trajectory") or []
    out: list[tuple[str, dict, str]] = []
    if not isinstance(steps, list):
        return out
    for s in steps:
        if not isinstance(s, dict):
            continue
        tool = s.get("tool") or "?"
        args = s.get("tool_args") or {}
        if isinstance(args, str):
            try:
                args = json.loads(args.replace("'", '"'))
            except json.JSONDecodeError:
                args = {"_raw": args}
        success = s.get("success")
        error = s.get("error")
        result = s.get("response") or ""
        if isinstance(result, dict):
            result = json.dumps(result)
        result_str = str(result)
        prefix = ""
        if success in (False, "False", "false") or (
            error and error not in ("None", None)
        ):
            prefix = f"[FAILED: {error}] "
        out.append((tool, args or {}, prefix + result_str))
    return out


def _trajectory_brief(traj_path: Path | None) -> str:
    if traj_path is None:
        return "(trajectory file not found locally)"
    try:
        traj = json.loads(_read_text_long(traj_path))
    except (json.JSONDecodeError, OSError) as exc:
        return f"(failed to read trajectory: {exc})"
    lines = [f"  trajectory_file = {traj_path.relative_to(REPO_ROOT).as_posix()}"]
    if not isinstance(traj, dict):
        return "\n".join(lines + ["  (trajectory file is not a dict)"])
    # Schema detection by content shape, not key name. PE-style history (Y/Z/ZSD)
    # uses `history` with `tool`/`tool_args` per-step entries; AAT-style (A/B/C/D)
    # uses `history` with `role`/`tool_calls` per-turn entries.
    history = traj.get("history") if isinstance(traj.get("history"), list) else None
    pe_traj = (
        traj.get("trajectory") if isinstance(traj.get("trajectory"), list) else None
    )
    if (
        history
        and history
        and isinstance(history[0], dict)
        and "tool_calls" in history[0]
    ):
        tool_calls = _extract_aat_calls(traj)
        schema = "aat"
    elif history and history and isinstance(history[0], dict) and "tool" in history[0]:
        tool_calls = _extract_pe_calls({"trajectory": history})
        schema = "pe-history"
    elif pe_traj is not None:
        tool_calls = _extract_pe_calls(traj)
        schema = "pe"
    else:
        tool_calls = []
        schema = "?"
    summary = traj.get("answer") or ""
    success = traj.get("success")
    failed_tools = traj.get("failed_tools") or []
    plan = traj.get("plan") or []
    lines.append(
        f"  schema={schema}; success={success}; "
        f"turn_count={traj.get('turn_count')}; "
        f"tool_call_count={traj.get('tool_call_count')}; "
        f"failed_tools={len(failed_tools)}; "
        f"plan_steps={len(plan) if isinstance(plan, list) else 0}"
    )
    if isinstance(plan, list) and plan:
        lines.append(f"  plan ({len(plan)} steps):")
        for s in plan:
            if isinstance(s, dict):
                lines.append(
                    f"    [{s.get('step')}] {s.get('tool')} ({s.get('server')}) — {s.get('task', '')[:80]}"
                )
    lines.append(f"  tool_calls ({len(tool_calls)}):")
    for name, args, result in tool_calls:
        arg_str = ", ".join(f"{k}={v!r}" for k, v in args.items())
        if len(arg_str) > 120:
            arg_str = arg_str[:117] + "..."
        lines.append(f"    - {name}({arg_str})")
        if result:
            r = str(result).replace("\n", " ").strip()
            r = r if len(r) <= 160 else r[:157] + "..."
            lines.append(f"        -> {r}")
    if failed_tools:
        lines.append(f"  failed_tool_records: {failed_tools[:3]}")
    if summary:
        s = summary.strip()
        snippet = s if len(s) <= 400 else s[:400] + "..."
        lines.append(f"  final_answer: {snippet}")
    else:
        lines.append("  final_answer: (none)")
    return "\n".join(lines)


def _format_brief(row: dict, score: dict | None, traj_path: Path | None) -> str:
    out: list[str] = []
    out.append("=" * 88)
    out.append(
        f"[{row['cell']}] {row['run_name']}  {row['scenario_id']}  trial_index={row['trial_index']}"
    )
    out.append(f"  CSV taxonomy_label = {row['taxonomy_label']!r}")
    out.append(f"  CSV symptom        = {row['symptom']!r}")
    out.append(f"  CSV mitigation     = {row['candidate_mitigation']!r}")
    out.append(f"  CSV evidence_note  = {row['evidence_note']}")
    if score is not None:
        failed = sorted(
            k.replace("dim_", "")
            for k, v in score.items()
            if k.startswith("dim_") and v is False
        )
        out.append(
            f"  JSONL score_6d={score.get('score_6d')}; failed_dims={'+'.join(failed) or '(none)'}"
        )
        out.append(f"  JSONL suggestions: {score.get('suggestions', '')}")
    else:
        out.append("  JSONL: (no matching record for run+scenario+trial)")
    out.append(_trajectory_brief(traj_path))
    return "\n".join(out)


def cmd_briefs(args: argparse.Namespace) -> int:
    rows = _load_evidence_rows()
    scores = _load_scores_index()
    out_lines: list[str] = []
    out_lines.append(f"# Failure-evidence audit briefs ({len(rows)} rows)")
    out_lines.append("")
    for row in rows:
        key = (row["run_name"], row["scenario_id"], int(row["trial_index"]))
        score = scores.get(key)
        traj = _resolve_trajectory_path(score)
        out_lines.append(_format_brief(row, score, traj))
        out_lines.append("")
    text = "\n".join(out_lines)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"Wrote {args.out} ({len(rows)} briefs)")
    else:
        print(text)
    return 0


def cmd_add_columns(args: argparse.Namespace) -> int:
    rows = _load_evidence_rows()
    if not rows:
        return 0
    fieldnames = list(rows[0].keys())
    added = []
    for col in AUDIT_COLUMNS:
        if col not in fieldnames:
            fieldnames.append(col)
            added.append(col)
    for row in rows:
        for col in AUDIT_COLUMNS:
            row.setdefault(col, "")
    with EVIDENCE_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow(row)
    print(f"Added columns: {added or '(none — already present)'}")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    rows = _load_evidence_rows()
    if not rows or "audit_status" not in rows[0]:
        print("ERROR: failure_evidence_table.csv has no audit_status column.")
        print("Run `python scripts/audit_failure_evidence.py add-columns` first,")
        print("then hand-fill the columns before rendering.")
        return 1
    by_status: dict[str, list[dict]] = {}
    by_taxonomy: dict[str, dict[str, int]] = {}
    for row in rows:
        status = row.get("audit_status") or "(unfilled)"
        by_status.setdefault(status, []).append(row)
        tax = row["taxonomy_label"]
        by_taxonomy.setdefault(tax, {}).setdefault(status, 0)
        by_taxonomy[tax][status] += 1
    n = len(rows)
    confirmed = len(by_status.get("confirmed", []))
    relabel = len(by_status.get("relabel_suggested", []))
    thin = len(by_status.get("evidence_thin", []))
    unfilled = len(by_status.get("(unfilled)", []))
    out: list[str] = []
    out.append("# Failure-evidence audit — 2026-05-05")
    out.append("")
    out.append(
        "Audit of `results/metrics/failure_evidence_table.csv` (35 rows from PR #151) "
        "against per-trial judge data in `results/metrics/scenario_scores.jsonl` and the "
        "mirrored trajectory files under `benchmarks/cell_*/raw/<run_name>/`."
    )
    out.append("")
    out.append("## Method")
    out.append("")
    out.append(
        "For each row, the audit applied the strict criteria locked at issue #35 review time:"
    )
    out.append("")
    out.append(
        "- `confirmed` — judge log shows the cited failed dimensions, the symptom matches "
        "what the trajectory exhibits, AND the candidate mitigation would plausibly catch it."
    )
    out.append(
        "- `relabel_suggested` — taxonomy label or symptom is wrong; row should be reclassified."
    )
    out.append(
        "- `evidence_thin` — judge log exists but the suggested failure pattern is ambiguous "
        "or the trajectory does not strongly demonstrate it."
    )
    out.append("")
    out.append(
        "**Flag-only policy.** This audit records `audit_status` and `audit_note` "
        "but does not modify the original `taxonomy_label` / `symptom` / "
        "`candidate_mitigation` columns landed in PR #151. Relabel suggestions "
        "are surfaced for #64 (visuals + mitigation plan) and #66 (mitigation "
        "before/after) to consume; applying them is out of scope for issue #35, "
        "which owns the evidence-table audit, not the taxonomy revision."
    )
    out.append("")
    out.append("## Summary")
    out.append("")
    out.append(f"| Status | Count | Share |")
    out.append(f"|--------|------:|------:|")
    out.append(f"| confirmed | {confirmed} | {confirmed/n:.0%} |")
    out.append(f"| relabel_suggested | {relabel} | {relabel/n:.0%} |")
    out.append(f"| evidence_thin | {thin} | {thin/n:.0%} |")
    if unfilled:
        out.append(f"| (unfilled) | {unfilled} | {unfilled/n:.0%} |")
    out.append(f"| **total** | **{n}** | 100% |")
    out.append("")
    out.append("## Per-taxonomy confirmation rate")
    out.append("")
    out.append("| Taxonomy label | Total | Confirmed | Relabel | Evidence thin |")
    out.append("|---|---:|---:|---:|---:|")
    for tax in sorted(by_taxonomy):
        b = by_taxonomy[tax]
        out.append(
            f"| {tax} | {sum(b.values())} | {b.get('confirmed', 0)} | "
            f"{b.get('relabel_suggested', 0)} | {b.get('evidence_thin', 0)} |"
        )
    out.append("")
    if relabel:
        out.append("## Relabel suggestions")
        out.append("")
        out.append("| Run | Scenario | Trial | Current label | Suggested fix |")
        out.append("|---|---|---:|---|---|")
        for row in by_status.get("relabel_suggested", []):
            out.append(
                f"| `{row['run_name']}` | {row['scenario_id']} | {row['trial_index']} | "
                f"{row['taxonomy_label']} / {row['symptom']} | {row['audit_note']} |"
            )
        out.append("")
    if thin:
        out.append("## Evidence-thin rows")
        out.append("")
        out.append("| Run | Scenario | Trial | Note |")
        out.append("|---|---|---:|---|")
        for row in by_status.get("evidence_thin", []):
            out.append(
                f"| `{row['run_name']}` | {row['scenario_id']} | {row['trial_index']} | "
                f"{row['audit_note']} |"
            )
        out.append("")
    out.append("## Reproducibility")
    out.append("")
    out.append(
        "Regenerate briefs locally with `python scripts/audit_failure_evidence.py "
        "briefs --out <path>` (the briefs file is a transient review aid and is "
        "not committed); audit decisions are written into "
        "`results/metrics/failure_evidence_table.csv` and this Markdown is "
        "regenerated via `python scripts/audit_failure_evidence.py render`."
    )
    out.append("")
    Path(args.out).write_text("\n".join(out), encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_briefs = sub.add_parser("briefs", help="emit per-row audit briefs")
    p_briefs.add_argument(
        "--out", default=None, help="write briefs to file (default: stdout)"
    )
    p_briefs.set_defaults(func=cmd_briefs)
    p_add = sub.add_parser(
        "add-columns", help="add audit columns to the CSV (idempotent)"
    )
    p_add.set_defaults(func=cmd_add_columns)
    p_render = sub.add_parser(
        "render", help="render the audit Markdown summary from the augmented CSV"
    )
    p_render.add_argument(
        "--out",
        default=str(REPO_ROOT / "docs" / "failure_evidence_audit_2026-05-05.md"),
    )
    p_render.set_defaults(func=cmd_render)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
