#!/usr/bin/env python3
"""Render failure-taxonomy summary tables and SVG figures.

The script intentionally uses only the Python standard library so the failure
analysis lane can regenerate its evidence figures without notebook dependencies.
"""

from __future__ import annotations

import csv
import html
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METRICS_DIR = ROOT / "results" / "metrics"
FIGURES_DIR = ROOT / "results" / "figures"
EVIDENCE_CSV = METRICS_DIR / "failure_evidence_table.csv"

CELL_ORDER = ["A", "B", "C", "D", "Y", "Z", "ZSD"]
STAGE_ORDER = [
    "planning",
    "tool selection",
    "tool execution",
    "verification",
    "final answer",
]

MITIGATION_SPECS = [
    {
        "rank": "1",
        "lane": "evidence_grounding",
        "mitigation_name": "missing_evidence_final_answer_guard",
        "symptom": "missing-evidence final answer",
        "target_pattern": "final answer or work order emitted after required evidence is missing, empty, or untrusted",
        "primary_metric": "count of missing-evidence final answer rows after rerun",
        "secondary_metrics": "judge_pass_rate, success_rate, latency_seconds_mean",
        "stop_condition": "no reduction in target rows or low-value refusals without judge-pass improvement",
        "notes": "Selected first because it is the largest recurring class in the current evidence table.",
    },
    {
        "rank": "2",
        "lane": "routing_contract",
        "mitigation_name": "strict_tool_routing_contract",
        "symptom": "tool routing or argument-contract failure",
        "target_pattern": "bad tool aliases, invalid arguments, or routing-contract breaks",
        "primary_metric": "count of routing or argument-contract rows after rerun",
        "secondary_metrics": "tool_error_count, success_rate, judge_pass_rate",
        "stop_condition": "routing errors persist or failures are hidden behind clean completion bits",
        "notes": "Candidate lane; parts are already visible in the ZSD hardening history.",
    },
    {
        "rank": "3",
        "lane": "evidence_sequence",
        "mitigation_name": "required_evidence_sequence_guard",
        "symptom": "tool-call sequencing failure",
        "target_pattern": "inference, risk estimation, or work-order creation before required evidence is acquired",
        "primary_metric": "count of tool-call sequencing rows after rerun",
        "secondary_metrics": "history_length, failed_steps_mean, judge_pass_rate",
        "stop_condition": "agent still reasons past missing required evidence",
        "notes": "Candidate lane; overlaps with planner/verifier ordering and should follow the simpler final-answer guard.",
    },
    {
        "rank": "4",
        "lane": "fault_adjudication",
        "mitigation_name": "explicit_fault_risk_adjudication_step",
        "symptom": "under-constrained fault/risk adjudication",
        "target_pattern": "fault or risk choice remains under-justified when multiple evidence sources compete",
        "primary_metric": "count of under-constrained adjudication rows after rerun",
        "secondary_metrics": "clarity_and_justification judge dimension, judge_pass_rate",
        "stop_condition": "adjudication remains vague or does not cite deciding tool evidence",
        "notes": "Candidate lane; useful for paper framing but lower-count than evidence grounding.",
    },
]


def read_rows() -> list[dict[str, str]]:
    with EVIDENCE_CSV.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def pct(numerator: int, denominator: int) -> str:
    return f"{(100.0 * numerator / denominator):.1f}" if denominator else "0.0"


def xml(text: object) -> str:
    return html.escape(str(text), quote=True)


def write_taxonomy_counts(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    counts = Counter(r["taxonomy_label"] for r in rows)
    total = sum(counts.values())
    out = [
        {"taxonomy_label": label, "rows": count, "percent": pct(count, total)}
        for label, count in counts.most_common()
    ]
    write_csv(
        METRICS_DIR / "failure_taxonomy_counts.csv",
        ["taxonomy_label", "rows", "percent"],
        out,
    )
    return out


def write_symptom_counts(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    counts = Counter(r["symptom"] for r in rows)
    labels_by_symptom: dict[str, Counter[str]] = defaultdict(Counter)
    mitigations: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        labels_by_symptom[row["symptom"]][row["taxonomy_label"]] += 1
        mitigations[row["symptom"]][row["candidate_mitigation"]] += 1
    total = sum(counts.values())
    out = []
    for symptom, count in counts.most_common():
        out.append(
            {
                "symptom": symptom,
                "rows": count,
                "percent": pct(count, total),
                "dominant_taxonomy_label": labels_by_symptom[symptom].most_common(1)[0][
                    0
                ],
                "candidate_mitigation": mitigations[symptom].most_common(1)[0][0],
            }
        )
    write_csv(
        METRICS_DIR / "failure_symptom_counts.csv",
        [
            "symptom",
            "rows",
            "percent",
            "dominant_taxonomy_label",
            "candidate_mitigation",
        ],
        out,
    )
    return out


def write_stage_cell_counts(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    counts = Counter((r["failure_stage"], r["cell"]) for r in rows)
    out = []
    for stage in STAGE_ORDER:
        row: dict[str, object] = {"failure_stage": stage}
        total = 0
        for cell in CELL_ORDER:
            value = counts[(stage, cell)]
            row[cell] = value
            total += value
        row["total"] = total
        out.append(row)
    write_csv(
        METRICS_DIR / "failure_stage_cell_counts.csv",
        ["failure_stage", *CELL_ORDER, "total"],
        out,
    )
    return out


def write_mitigation_inventory(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    symptom_counts = Counter(r["symptom"] for r in rows)
    out = []
    for spec in MITIGATION_SPECS:
        evidence_rows = symptom_counts[spec["symptom"]]
        out.append(
            {
                "lane": spec["lane"],
                "mitigation_name": spec["mitigation_name"],
                "before_run": f"results/metrics/failure_evidence_table.csv:symptom={spec['symptom']}",
                "after_run": "",
                "before_status": f"current_count={evidence_rows}",
                "after_status": "pending_rerun",
                "notes": spec["notes"],
                "rank": spec["rank"],
                "target_pattern": spec["target_pattern"],
                "evidence_rows": evidence_rows,
                "primary_metric": spec["primary_metric"],
                "secondary_metrics": spec["secondary_metrics"],
                "stop_condition": spec["stop_condition"],
                "owner_issue": "#64 -> #65/#66",
                "implementation_status": (
                    "implemented_pending_rerun" if spec["rank"] == "1" else "candidate"
                ),
            }
        )
    fieldnames = [
        "lane",
        "mitigation_name",
        "before_run",
        "after_run",
        "before_status",
        "after_status",
        "notes",
        "rank",
        "target_pattern",
        "evidence_rows",
        "primary_metric",
        "secondary_metrics",
        "stop_condition",
        "owner_issue",
        "implementation_status",
    ]
    write_csv(METRICS_DIR / "mitigation_run_inventory.csv", fieldnames, out)
    return out


def svg_bar_chart(rows: list[dict[str, object]], path: Path) -> None:
    width, height = 980, 460
    left, top = 330, 76
    bar_h, gap = 58, 22
    max_count = max(int(r["rows"]) for r in rows) or 1
    palette = ["#1f6f78", "#c85a3a", "#7b8f2a"]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fbf7ef"/>',
        '<text x="40" y="42" font-family="Georgia, serif" font-size="28" fill="#1b1b1b">Failure taxonomy counts</text>',
        '<text x="40" y="68" font-family="Verdana, sans-serif" font-size="13" fill="#5b5147">Rows are judge-failed trials from failure_evidence_table.csv</text>',
    ]
    for i, row in enumerate(rows):
        y = top + i * (bar_h + gap)
        count = int(row["rows"])
        w = int((width - left - 110) * count / max_count)
        color = palette[i % len(palette)]
        parts.extend(
            [
                f'<text x="40" y="{y + 36}" font-family="Verdana, sans-serif" font-size="16" fill="#26231f">{xml(row["taxonomy_label"])}</text>',
                f'<rect x="{left}" y="{y}" width="{w}" height="{bar_h}" rx="8" fill="{color}"/>',
                f'<text x="{left + w + 14}" y="{y + 36}" font-family="Verdana, sans-serif" font-size="18" font-weight="700" fill="#26231f">{count}</text>',
            ]
        )
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n")


def svg_heatmap(rows: list[dict[str, object]], path: Path) -> None:
    cell_w, cell_h = 84, 48
    left, top = 190, 94
    width = left + cell_w * len(CELL_ORDER) + 80
    height = top + cell_h * len(rows) + 84
    max_value = max(int(row[cell]) for row in rows for cell in CELL_ORDER) or 1

    def color(value: int) -> str:
        intensity = int(245 - (155 * value / max_value))
        return f"rgb(255,{intensity},{intensity - 18})" if value else "#f2eadf"

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fbf7ef"/>',
        '<text x="40" y="42" font-family="Georgia, serif" font-size="28" fill="#1b1b1b">Failure stage by cell</text>',
        '<text x="40" y="68" font-family="Verdana, sans-serif" font-size="13" fill="#5b5147">Darker cells indicate more judge-failed rows in that stage/cell bucket</text>',
    ]
    for j, cell in enumerate(CELL_ORDER):
        x = left + j * cell_w
        parts.append(
            f'<text x="{x + cell_w/2}" y="{top - 18}" text-anchor="middle" font-family="Verdana, sans-serif" font-size="15" font-weight="700" fill="#26231f">{cell}</text>'
        )
    for i, row in enumerate(rows):
        y = top + i * cell_h
        parts.append(
            f'<text x="40" y="{y + 30}" font-family="Verdana, sans-serif" font-size="14" fill="#26231f">{xml(row["failure_stage"])}</text>'
        )
        for j, cell in enumerate(CELL_ORDER):
            x = left + j * cell_w
            value = int(row[cell])
            parts.extend(
                [
                    f'<rect x="{x}" y="{y}" width="{cell_w - 4}" height="{cell_h - 4}" rx="5" fill="{color(value)}" stroke="#d7c6b2"/>',
                    f'<text x="{x + (cell_w - 4)/2}" y="{y + 29}" text-anchor="middle" font-family="Verdana, sans-serif" font-size="15" fill="#26231f">{value}</text>',
                ]
            )
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n")


def svg_mitigation_table(rows: list[dict[str, object]], path: Path) -> None:
    width, row_h = 1220, 74
    height = 118 + row_h * len(rows)
    cols = [54, 310, 160, 520, 150]
    headings = ["#", "Mitigation", "Evidence rows", "Target pattern", "Status"]
    x_positions = [34]
    for w in cols[:-1]:
        x_positions.append(x_positions[-1] + w)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fbf7ef"/>',
        '<text x="34" y="42" font-family="Georgia, serif" font-size="28" fill="#1b1b1b">Mitigation inventory</text>',
        '<text x="34" y="68" font-family="Verdana, sans-serif" font-size="13" fill="#5b5147">Selected first lane plus queued candidates from mitigation_run_inventory.csv</text>',
    ]
    header_y = 92
    parts.append(
        f'<rect x="24" y="{header_y - 24}" width="{width - 48}" height="38" rx="6" fill="#263238"/>'
    )
    for x, heading in zip(x_positions, headings):
        parts.append(
            f'<text x="{x}" y="{header_y}" font-family="Verdana, sans-serif" font-size="14" font-weight="700" fill="#fff7ea">{heading}</text>'
        )
    for i, row in enumerate(rows):
        y = 118 + i * row_h
        fill = "#fffaf1" if i % 2 == 0 else "#f1e6d6"
        parts.append(
            f'<rect x="24" y="{y - 28}" width="{width - 48}" height="{row_h - 8}" rx="6" fill="{fill}" stroke="#dbc8af"/>'
        )
        values = [
            row["rank"],
            row["mitigation_name"],
            row["evidence_rows"],
            row["target_pattern"],
            row["implementation_status"],
        ]
        for x, value in zip(x_positions, values):
            font_size = 12 if x == x_positions[3] else 13
            parts.append(
                f'<text x="{x}" y="{y}" font-family="Verdana, sans-serif" font-size="{font_size}" fill="#26231f">{xml(value)}</text>'
            )
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n")


def main() -> None:
    rows = read_rows()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    taxonomy_counts = write_taxonomy_counts(rows)
    write_symptom_counts(rows)
    stage_cell_counts = write_stage_cell_counts(rows)
    mitigation_rows = write_mitigation_inventory(rows)

    svg_bar_chart(taxonomy_counts, FIGURES_DIR / "failure_taxonomy_counts.svg")
    svg_heatmap(stage_cell_counts, FIGURES_DIR / "failure_stage_cell_heatmap.svg")
    svg_mitigation_table(mitigation_rows, FIGURES_DIR / "mitigation_priority_table.svg")

    print(
        f"Rendered {len(taxonomy_counts)} taxonomy buckets, {len(stage_cell_counts)} stage rows, {len(mitigation_rows)} mitigation lanes."
    )


if __name__ == "__main__":
    main()
