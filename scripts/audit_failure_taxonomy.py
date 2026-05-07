"""Hand-audit support for the post-PR175 failure taxonomy (#194).

PR #193 produced `results/metrics/failure_taxonomy_current.csv` with
46 rows flagged `audit_status='stratified_sample'` (one per non-empty
`(experiment_cell, auto_taxonomy_label)` stratum across paper-eligible
failures). This script is the audit-side companion: it joins each
sample row to its judge log, extracts the agent trajectory + judge
verdict, and emits a per-row brief the auditor reads to decide:

    audit_decision         confirmed | relabel_suggested | evidence_thin
    audit_note             one-sentence concrete observation
    berkeley_label         specification | inter_agent_orchestration | task_verification
    failure_stage          planning | tool_selection | tool_execution | verification | final_answer
    audit_decision_source  "<reviewer>:<YYYY-MM-DD>"

Subcommands:

    briefs       — emit per-row briefs to stdout or --out for the auditor.
                   By default reads both `stratified_sample` and
                   `manual_confirmed` rows; filter via `--status`.
    add-columns  — merge a hand-edited audit-decisions sidecar TSV into
                   the CSV (defaults to `data/audit/issue194_decisions.tsv`,
                   which IS committed so the audit is reproducible from
                   inputs). Sets `audit_status` to `manual_confirmed` for
                   audited rows; idempotent on re-runs. Validates
                   audit_decision / berkeley_label / failure_stage
                   against the canonical vocab AND
                   audit_decision_source against `<handle>:<YYYY-MM-DD>`.
                   Fails loudly on unmatched keys or zero updates.
    render       — write the Markdown audit summary by reading the
                   augmented CSV plus
                   `data/audit/issue194_recurring_patterns.json` (also
                   committed) for the methodology paragraph, the
                   Berkeley-mapping rule, the recurring-patterns
                   section, and the v2->v3 tie-break-relabel callout.
                   Reproducible: re-running render over committed
                   inputs is byte-identical to the committed doc.

Mirrors `scripts/audit_failure_evidence.py` (PR #189) but targets the
new failure_taxonomy_current.csv schema instead of the preliminary
PR #151 35-row table.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_CSV = REPO_ROOT / "results" / "metrics" / "failure_taxonomy_current.csv"
JUDGE_LOGS_ROOT = REPO_ROOT / "results" / "judge_logs"
DECISIONS_TSV = REPO_ROOT / "data" / "audit" / "issue194_decisions.tsv"
PATTERNS_JSON = REPO_ROOT / "data" / "audit" / "issue194_recurring_patterns.json"


def _long(p: Path) -> str:
    """Return a Windows long-path-prefixed string for file ops.

    Some `run_name` values push the absolute judge-log path past Windows'
    260-character MAX_PATH limit, which makes `Path.exists()` and
    `Path.read_text()` silently report not-found. The `\\\\?\\` prefix
    bypasses MAX_PATH on Win32 file APIs. POSIX is unaffected.
    """
    if os.name != "nt":
        return str(p)
    s = str(p.resolve())
    return s if s.startswith("\\\\?\\") else "\\\\?\\" + s


def _exists(p: Path) -> bool:
    return os.path.exists(_long(p))


def _read_text(p: Path, encoding: str = "utf-8") -> str:
    with open(_long(p), encoding=encoding) as f:
        return f.read()


AUDIT_COLUMNS = [
    "audit_decision",
    "berkeley_label",
    "failure_stage",
    "audit_note",
    "audit_decision_source",
]

BERKELEY_LABELS = {
    "specification",
    "inter_agent_orchestration",
    "task_verification",
}
FAILURE_STAGES = {
    "planning",
    "tool_selection",
    "tool_execution",
    "verification",
    "final_answer",
}
AUDIT_DECISIONS = {"confirmed", "relabel_suggested", "evidence_thin"}

# `audit_decision_source` should be `<reviewer-handle>:<YYYY-MM-DD>` per the
# audit-tooling docstring. Without validation, typos like `Akshat:2026-5-7`
# silently merge and break later programmatic provenance walks.
AUDIT_SOURCE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*:\d{4}-\d{2}-\d{2}$")


def _judge_log_path(run_name: str, scenario_id: str, trial_index: str) -> Path:
    """Locate the judge log file for one (run, scenario, trial)."""
    pad = f"{int(trial_index):02d}" if str(trial_index).isdigit() else trial_index
    return JUDGE_LOGS_ROOT / run_name / f"{scenario_id}_run{pad}_judge_log.json"


def _load_taxonomy_rows() -> tuple[list[str], list[dict]]:
    with TAXONOMY_CSV.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return list(rows[0].keys()), rows


def _extract_tool_call_summary(prompt_user: str) -> list[str]:
    """Pull the agent's tool-call sequence out of the judge prompt.

    The judge prompt embeds the trajectory as a JSON array under
    `## Agent Trajectory (tool calls and results)`. We don't need a
    perfect parse — a one-line summary per tool call (name + a hint
    of the arguments) is enough for an audit brief.
    """
    marker = "## Agent Trajectory (tool calls and results)"
    if marker not in prompt_user:
        return []
    after = prompt_user.split(marker, 1)[1]
    end_markers = [
        "## Agent Final Answer",
        "## Final Answer",
        "## Agent Answer",
        "Evaluate across",
    ]
    end_idx = len(after)
    for em in end_markers:
        i = after.find(em)
        if i != -1 and i < end_idx:
            end_idx = i
    body = after[:end_idx].strip()
    # Try to parse as JSON; if that fails, do a permissive name-extract.
    try:
        traj = json.loads(body)
    except Exception:
        # Permissive fallback: find every `"name": "..."`.
        out = []
        i = 0
        while True:
            i = body.find('"name":', i)
            if i == -1:
                break
            j = body.find('"', i + 7)
            k = body.find('"', j + 1)
            if j == -1 or k == -1:
                break
            out.append(body[j + 1 : k])
            i = k + 1
        return out

    out = []
    if isinstance(traj, list):
        for turn in traj:
            for tc in (turn or {}).get("tool_calls", []) or []:
                name = tc.get("name", "?")
                args = tc.get("arguments", {}) or {}
                arg_hint = (
                    ", ".join(f"{k}={args[k]!r}" for k in list(args)[:2])
                    if isinstance(args, dict)
                    else ""
                )
                out.append(f"{name}({arg_hint})" if arg_hint else name)
    return out


def _extract_final_answer(prompt_user: str, raw_response: str) -> str:
    """Best-effort extract of the agent's final answer from the prompt."""
    for marker in ("## Agent Final Answer", "## Final Answer", "## Agent Answer"):
        if marker in prompt_user:
            after = prompt_user.split(marker, 1)[1]
            end = after.find("Evaluate across")
            return (after[:end] if end != -1 else after).strip()[:1500]
    return ""


def _row_brief(row: dict) -> dict:
    """Build a compact audit brief for one taxonomy row.

    Returns a dict with the source row plus extracted judge-log signals.
    Missing judge log -> brief flagged `judge_log_present=False`. Uses
    `_exists` / `_read_text` so Windows long paths work the same as POSIX.
    """
    log_path = _judge_log_path(row["run_name"], row["scenario_id"], row["trial_index"])
    present = _exists(log_path)
    out = {
        "source_row": row,
        "judge_log_path": (
            str(log_path.relative_to(REPO_ROOT).as_posix()) if present else None
        ),
        "judge_log_present": present,
        "tool_calls": [],
        "final_answer": "",
        "judge_suggestions": "",
        "judge_parsed_dims": {},
    }
    if not present:
        return out
    log = json.loads(_read_text(log_path))
    out["tool_calls"] = _extract_tool_call_summary(log.get("prompt_user", ""))
    out["final_answer"] = _extract_final_answer(
        log.get("prompt_user", ""), log.get("raw_response", "")
    )
    out["judge_suggestions"] = (log.get("parsed_dims") or {}).get("suggestions", "")
    out["judge_parsed_dims"] = {
        k: v for k, v in (log.get("parsed_dims") or {}).items() if k != "suggestions"
    }
    return out


def cmd_briefs(args: argparse.Namespace) -> int:
    fields, rows = _load_taxonomy_rows()
    statuses = (
        {args.status} if args.status else {"stratified_sample", "manual_confirmed"}
    )
    sample = [r for r in rows if r["audit_status"] in statuses]
    if args.cell:
        sample = [r for r in sample if r["experiment_cell"] == args.cell]
    if args.label:
        sample = [r for r in sample if r["auto_taxonomy_label"] == args.label]
    out_lines: list[str] = []
    for r in sample:
        b = _row_brief(r)
        sr = b["source_row"]
        out_lines.append(
            f"=== {sr['run_name']} / {sr['scenario_id']} run{int(sr['trial_index']):02d} ==="
        )
        out_lines.append(
            f"cell={sr['experiment_cell']}  orch={sr['orchestration_mode']}  "
            f"model={sr['model_id']}  judge={sr['judge_model']}"
        )
        out_lines.append(
            f"auto_taxonomy_label={sr['auto_taxonomy_label']}  "
            f"failed_dims=({sr['failed_dim_count']}) {sr['failed_dims']}"
        )
        if not b["judge_log_present"]:
            out_lines.append("  [WARN] judge log MISSING at expected path")
            out_lines.append("")
            continue
        out_lines.append(f"  judge_log: {b['judge_log_path']}")
        out_lines.append(f"  parsed_dims: {b['judge_parsed_dims']}")
        if b["tool_calls"]:
            out_lines.append(
                f"  tool_calls ({len(b['tool_calls'])}): "
                + ", ".join(b["tool_calls"][:8])
            )
            if len(b["tool_calls"]) > 8:
                out_lines.append(f"    ... and {len(b['tool_calls']) - 8} more")
        else:
            out_lines.append("  tool_calls: (none extracted)")
        fa = b["final_answer"].strip().replace("\n", " ")[:240]
        if fa:
            out_lines.append(f"  final_answer: {fa}")
        sug = (b["judge_suggestions"] or "").strip().replace("\n", " ")[:300]
        if sug:
            out_lines.append(f"  judge_suggestion: {sug}")
        out_lines.append("")

    text = "\n".join(out_lines)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out}: {len(sample)} briefs", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


def cmd_add_columns(args: argparse.Namespace) -> int:
    """Merge an audit-decisions sidecar TSV/JSONL into the taxonomy CSV.

    Sidecar shape (TSV):
        run_name<TAB>scenario_id<TAB>trial_index<TAB>audit_decision
        <TAB>berkeley_label<TAB>failure_stage<TAB>audit_note
        <TAB>audit_decision_source

    Default sidecar path is `data/audit/issue194_decisions.tsv` (committed
    so the audit is reproducible from inputs); override with --decisions.

    Eligible rows: `audit_status` is `stratified_sample` (initial pass)
    or `manual_confirmed` (re-merge from the same sidecar after the
    initial flip). Matching keys are `(run_name, scenario_id,
    int(trial_index))`. After merge, `audit_status` is set to
    `manual_confirmed` (idempotent on re-runs). The other 1,920+ rows
    are left alone.

    Fails if the sidecar references a key that doesn't match any
    eligible row, or if zero rows would be updated — silent no-op
    re-runs were a v1 review-finding hazard.
    """
    fields, rows = _load_taxonomy_rows()
    if any(c not in fields for c in AUDIT_COLUMNS):
        # Insert the new columns just after audit_status for grouping.
        idx = fields.index("audit_status") + 1
        for new_col in reversed(AUDIT_COLUMNS):
            if new_col not in fields:
                fields.insert(idx, new_col)
        for r in rows:
            for new_col in AUDIT_COLUMNS:
                r.setdefault(new_col, "")

    # Load sidecar.
    sidecar = Path(args.decisions) if args.decisions else DECISIONS_TSV
    decisions: dict[tuple[str, str, int], dict[str, str]] = {}
    with sidecar.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            key = (row["run_name"], row["scenario_id"], int(row["trial_index"]))
            decisions[key] = row

    eligible_statuses = {"stratified_sample", "manual_confirmed"}
    n_updated = 0
    matched_keys: set[tuple[str, str, int]] = set()
    for r in rows:
        if r["audit_status"] not in eligible_statuses:
            continue
        key = (r["run_name"], r["scenario_id"], int(r["trial_index"]))
        d = decisions.get(key)
        if not d:
            continue
        if d["audit_decision"] not in AUDIT_DECISIONS:
            raise ValueError(
                f"invalid audit_decision {d['audit_decision']!r} for {key}; "
                f"must be one of {sorted(AUDIT_DECISIONS)}"
            )
        if d.get("berkeley_label") and d["berkeley_label"] not in BERKELEY_LABELS:
            raise ValueError(
                f"invalid berkeley_label {d['berkeley_label']!r} for {key}; "
                f"must be one of {sorted(BERKELEY_LABELS)}"
            )
        if d.get("failure_stage") and d["failure_stage"] not in FAILURE_STAGES:
            raise ValueError(
                f"invalid failure_stage {d['failure_stage']!r} for {key}; "
                f"must be one of {sorted(FAILURE_STAGES)}"
            )
        src = d.get("audit_decision_source") or ""
        if src and not AUDIT_SOURCE_PATTERN.match(src):
            raise ValueError(
                f"invalid audit_decision_source {src!r} for {key}; expected "
                f"`<reviewer-handle>:<YYYY-MM-DD>` (lowercase handle, ISO date)"
            )
        for col in AUDIT_COLUMNS:
            r[col] = d.get(col, "") or ""
        r["audit_status"] = "manual_confirmed"
        matched_keys.add(key)
        n_updated += 1

    unmatched = set(decisions.keys()) - matched_keys
    if unmatched:
        raise ValueError(
            f"sidecar has {len(unmatched)} key(s) that don't match any eligible "
            f"row in {TAXONOMY_CSV.relative_to(REPO_ROOT)}: "
            f"{sorted(unmatched)[:5]}"
        )
    if n_updated == 0:
        raise ValueError(
            f"sidecar at {sidecar} updated zero rows; either the sidecar is "
            f"empty or no rows are in eligible audit_status "
            f"{sorted(eligible_statuses)}."
        )

    with TAXONOMY_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(
        f"merged {n_updated} audit decisions into {TAXONOMY_CSV.relative_to(REPO_ROOT)}",
        file=sys.stderr,
    )
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    fields, rows = _load_taxonomy_rows()
    audited = [r for r in rows if r["audit_status"] == "manual_confirmed"]
    out: list[str] = []
    out.append("# Failure taxonomy hand-audit — stratified sample (#194)")
    out.append("")
    out.append(
        f"*Audit pass over the {sum(1 for r in rows if r['audit_status'] in ('manual_confirmed', 'stratified_sample'))}"
        "-row stratified sample drawn by `scripts/build_failure_taxonomy.py` "
        "from PR #193's `results/metrics/failure_taxonomy_current.csv`. "
        f"Audited rows: {len(audited)}.*"
    )
    out.append("")
    out.append(
        "Auditor walked each row's judge log under `results/judge_logs/<run_name>"
        "/<scenario_id>_run<NN>_judge_log.json`, which embeds the agent's full "
        "trajectory + final answer. For each row the auditor decided: "
        "(a) `audit_decision` — `confirmed` (auto-label and trajectory symptoms "
        "agree), `relabel_suggested` (a concrete better label), or "
        "`evidence_thin` (judge symptom too weak/ambiguous to cite); (b) "
        "`berkeley_label` — `specification` / `inter_agent_orchestration` / "
        "`task_verification` per `docs/failure_taxonomy_evidence.md`; (c) "
        "`failure_stage` — earliest stage where the run becomes unrecoverable."
    )
    out.append("")

    # Methodology + Berkeley mapping rule come from the patterns sidecar so
    # the rendered doc is reproducible from committed inputs.
    patterns_json = (
        json.loads(_read_text(PATTERNS_JSON)) if _exists(PATTERNS_JSON) else {}
    )

    methodology = patterns_json.get("methodology") or {}
    if methodology:
        out.append(f"## {methodology.get('title', 'Methodology')}")
        out.append("")
        out.append(methodology.get("body", ""))
        out.append("")

    rule = patterns_json.get("berkeley_mapping_rule") or {}
    if rule:
        out.append(f"## {rule.get('title', 'Berkeley-label mapping rule')}")
        out.append("")
        out.append(rule.get("body", ""))
        out.append("")

    out.append("## Decision counts")
    out.append("")
    decisions = Counter(r["audit_decision"] for r in audited if r["audit_decision"])
    out.append("| audit_decision | count |")
    out.append("|---|---:|")
    for k in ("confirmed", "relabel_suggested", "evidence_thin"):
        out.append(f"| `{k}` | {decisions.get(k, 0)} |")
    out.append("")

    out.append("## Berkeley taxonomy distribution (audited rows)")
    out.append("")
    berkeley = Counter(r["berkeley_label"] for r in audited if r["berkeley_label"])
    out.append("| berkeley_label | count |")
    out.append("|---|---:|")
    for k, v in berkeley.most_common():
        out.append(f"| `{k}` | {v} |")
    out.append("")

    out.append("## Failure-stage distribution (audited rows)")
    out.append("")
    stages = Counter(r["failure_stage"] for r in audited if r["failure_stage"])
    out.append("| failure_stage | count |")
    out.append("|---|---:|")
    for k, v in stages.most_common():
        out.append(f"| `{k}` | {v} |")
    out.append("")

    if patterns_json:
        out.append("## Recurring failure patterns")
        out.append("")
        out.append(
            patterns_json.get(
                "lead",
                "These patterns recur across multiple audited rows and are the "
                "strongest paper-citable signals.",
            )
        )
        out.append("")
        for i, p in enumerate(patterns_json.get("patterns", []), 1):
            cells = ", ".join(p.get("cells", []))
            distinct = p.get("distinct_scenarios_count")
            distinct_ids = ", ".join(p.get("distinct_scenarios", []))
            scope = (
                f"{p['count']} rows across {distinct} distinct scenario{'s' if distinct != 1 else ''}"
                f" ({distinct_ids})"
                if distinct is not None
                else f"{p['count']} rows"
            )
            out.append(
                f"{i}. **{p['title']}** — {scope}. {p['description']} "
                f"Cells: {cells}. Mitigation candidate: {p['mitigation']}"
            )
        if "summary_note" in patterns_json:
            out.append("")
            out.append(patterns_json["summary_note"])
        out.append("")

        relabels = patterns_json.get("tie_break_relabels") or {}
        if relabels.get("rows"):
            out.append("## Tie-break relabels (v2 → v3)")
            out.append("")
            out.append(
                "Six rows were relabeled in v3 to apply the team's tie-break rule "
                "consistently (latest irreversible mistake). v2's labels reflected "
                "the auditor's first-pass 'first irreversible mistake' reading; "
                "v3 corrects this against `docs/failure_taxonomy_evidence.md:139-145`."
            )
            out.append("")
            out.append(
                "| cell | scenario | trial | v2 berkeley / stage | v3 berkeley / stage | rationale |"
            )
            out.append("|---|---|---:|---|---|---|")
            for r in relabels["rows"]:
                v2 = r["v2"]
                v3 = r["v3"]
                rationale = r["rationale"].replace("|", "\\|")
                out.append(
                    f"| {r['cell']} | {r['scenario_id']} | {r['trial_index']} | "
                    f"`{v2['berkeley']}` / `{v2['stage']}` | "
                    f"`{v3['berkeley']}` / `{v3['stage']}` | {rationale} |"
                )
            out.append("")

    out.append("## Per-row audit table")
    out.append("")
    out.append(
        "| cell | run | scenario | trial | auto_label | decision | berkeley | stage | note |"
    )
    out.append("|---|---|---|---:|---|---|---|---|---|")
    for r in audited:
        run_short = r["run_name"]
        if len(run_short) > 60:
            run_short = "..." + run_short[-58:]
        note = (r["audit_note"] or "").replace("|", "\\|")
        out.append(
            f"| {r['experiment_cell']} | `{run_short}` | {r['scenario_id']} | "
            f"{r['trial_index']} | `{r['auto_taxonomy_label'].removeprefix('low_')}` | "
            f"`{r['audit_decision']}` | `{r['berkeley_label']}` | "
            f"`{r['failure_stage']}` | {note} |"
        )
    out.append("")

    # Paper-cite candidates: confirmed rows with a clear concrete note.
    cited = [
        r
        for r in audited
        if r.get("audit_decision") == "confirmed"
        and (r.get("berkeley_label") or "")
        and (r.get("failure_stage") or "")
    ][: args.paper_cite_n]
    out.append(f"## Paper-cite candidates (top {len(cited)})")
    out.append("")
    out.append(
        "These rows have a confirmed auto-label, a concrete trajectory-grounded "
        "note, and a balanced cell/orchestration/symptom mix. Recommended "
        "examples for the paper's failure-analysis section."
    )
    out.append("")
    for i, r in enumerate(cited, 1):
        out.append(
            f"{i}. **Cell {r['experiment_cell']} / {r['orchestration_mode']} / "
            f"{r['scenario_id']} run{int(r['trial_index']):02d}** — "
            f"{r['auto_taxonomy_label']} -> `{r['berkeley_label']}` "
            f"({r['failure_stage']}). {r['audit_note']} "
            f"Source: `{r['trajectory_file']}`."
        )
    out.append("")

    text = "\n".join(out)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(
            f"wrote {args.out}: {len(audited)} audited rows, {len(cited)} paper-cite candidates",
            file=sys.stderr,
        )
    else:
        sys.stdout.write(text)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sp = p.add_subparsers(dest="cmd", required=True)

    pb = sp.add_parser("briefs", help="emit per-row briefs for the auditor")
    pb.add_argument("--out", type=str, default=None)
    pb.add_argument("--cell", type=str, default=None, help="filter by experiment_cell")
    pb.add_argument(
        "--label", type=str, default=None, help="filter by auto_taxonomy_label"
    )
    pb.add_argument(
        "--status",
        type=str,
        default=None,
        choices=("stratified_sample", "manual_confirmed"),
        help="filter by audit_status (default: include both)",
    )
    pb.set_defaults(fn=cmd_briefs)

    pa = sp.add_parser(
        "add-columns",
        help="merge a hand-edited audit-decisions sidecar TSV into the taxonomy CSV",
    )
    pa.add_argument(
        "--decisions",
        type=str,
        default=None,
        help=(
            "path to the audit-decisions TSV; defaults to "
            "data/audit/issue194_decisions.tsv (committed)"
        ),
    )
    pa.set_defaults(fn=cmd_add_columns)

    pr = sp.add_parser(
        "render", help="render markdown audit summary from the augmented CSV"
    )
    pr.add_argument("--out", type=str, default=None)
    pr.add_argument(
        "--paper-cite-n",
        type=int,
        default=10,
        help="max paper-cite candidates to surface",
    )
    pr.set_defaults(fn=cmd_render)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
