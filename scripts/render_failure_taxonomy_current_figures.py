#!/usr/bin/env python3
"""Render current failure-taxonomy summary tables and SVG figures.

The legacy renderer uses the 35-row preliminary evidence table. This renderer
uses the post-PR193 paper-grade taxonomy surface so paper/deck figures can cite
the same CSV as the current failure-analysis text.
"""

from __future__ import annotations

import csv
import html
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METRICS_DIR = ROOT / "results" / "metrics"
FIGURES_DIR = ROOT / "results" / "figures"
SOURCE_CSV = METRICS_DIR / "failure_taxonomy_current.csv"

LABELS = {
    "low_task_completion": "Task completion",
    "low_data_retrieval_accuracy": "Data retrieval accuracy",
    "low_agent_sequence_correct": "Agent sequence correctness",
    "low_generalized_result_verification": "Result verification",
}

PALETTE = ["#1f6f78", "#c85a3a", "#6f7d2a", "#5b6aa8"]


def read_rows() -> list[dict[str, str]]:
    with SOURCE_CSV.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def pct(numerator: int, denominator: int) -> str:
    return f"{(100.0 * numerator / denominator):.1f}" if denominator else "0.0"


def xml(value: object) -> str:
    return html.escape(str(value), quote=True)


def write_auto_label_counts(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    paper_failed = [r for r in rows if r["paper_eligible"] == "true"]
    counts = Counter(r["auto_taxonomy_label"] for r in paper_failed)
    total = len(paper_failed)
    out = []
    for label, count in counts.most_common():
        out.append(
            {
                "auto_taxonomy_label": label,
                "display_label": LABELS.get(label, label.replace("_", " ")),
                "rows": count,
                "percent_of_paper_failures": pct(count, total),
                "source_rows": total,
                "source_csv": "results/metrics/failure_taxonomy_current.csv",
            }
        )
    write_csv(
        METRICS_DIR / "failure_taxonomy_current_auto_label_counts.csv",
        [
            "auto_taxonomy_label",
            "display_label",
            "rows",
            "percent_of_paper_failures",
            "source_rows",
            "source_csv",
        ],
        out,
    )
    return out


def write_failed_dim_counts(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    paper_failed = [r for r in rows if r["paper_eligible"] == "true"]
    counts = Counter(r["failed_dim_count"] for r in paper_failed)
    total = len(paper_failed)
    out = []
    for failed_dim_count in sorted(counts, key=lambda v: int(v)):
        count = counts[failed_dim_count]
        out.append(
            {
                "failed_dim_count": failed_dim_count,
                "rows": count,
                "percent_of_paper_failures": pct(count, total),
                "source_rows": total,
                "source_csv": "results/metrics/failure_taxonomy_current.csv",
            }
        )
    write_csv(
        METRICS_DIR / "failure_taxonomy_current_failed_dim_counts.csv",
        [
            "failed_dim_count",
            "rows",
            "percent_of_paper_failures",
            "source_rows",
            "source_csv",
        ],
        out,
    )
    return out


def write_manual_audit_counts(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    audited = [r for r in rows if r["audit_status"] == "manual_confirmed"]
    categories = [
        ("audit_decision", "audit_decision"),
        ("berkeley_label", "berkeley_label"),
        ("failure_stage", "failure_stage"),
    ]
    out = []
    for section, column in categories:
        counts = Counter(r[column] or "blank" for r in audited)
        for value, count in counts.most_common():
            out.append(
                {
                    "section": section,
                    "value": value,
                    "rows": count,
                    "percent_of_manual_sample": pct(count, len(audited)),
                    "source_rows": len(audited),
                    "source_csv": "results/metrics/failure_taxonomy_current.csv",
                }
            )
    write_csv(
        METRICS_DIR / "failure_taxonomy_current_manual_audit_counts.csv",
        [
            "section",
            "value",
            "rows",
            "percent_of_manual_sample",
            "source_rows",
            "source_csv",
        ],
        out,
    )
    return out


def svg_auto_label_bar_chart(rows: list[dict[str, object]], path: Path) -> None:
    width, height = 1080, 520
    left, top = 390, 118
    bar_h, gap = 56, 24
    max_count = max(int(r["rows"]) for r in rows) or 1
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fbf7ef"/>',
        '<text x="40" y="46" font-family="Georgia, serif" font-size="30" fill="#1b1b1b">Current paper-grade failure taxonomy</text>',
        '<text x="40" y="76" font-family="Verdana, sans-serif" font-size="14" fill="#5b5147">1,276 paper-eligible failed judge rows from failure_taxonomy_current.csv</text>',
        '<text x="40" y="98" font-family="Verdana, sans-serif" font-size="13" fill="#5b5147">Auto label is the highest-priority failed judge dimension; manual audit sample is tracked separately.</text>',
    ]
    for i, row in enumerate(rows):
        y = top + i * (bar_h + gap)
        count = int(row["rows"])
        bar_w = int((width - left - 150) * count / max_count)
        color = PALETTE[i % len(PALETTE)]
        percent = row["percent_of_paper_failures"]
        parts.extend(
            [
                f'<text x="40" y="{y + 35}" font-family="Verdana, sans-serif" font-size="16" fill="#26231f">{xml(row["display_label"])}</text>',
                f'<rect x="{left}" y="{y}" width="{bar_w}" height="{bar_h}" rx="6" fill="{color}"/>',
                f'<text x="{left + bar_w + 14}" y="{y + 34}" font-family="Verdana, sans-serif" font-size="18" font-weight="700" fill="#26231f">{count} ({percent}%)</text>',
            ]
        )
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n")


def main() -> None:
    rows = read_rows()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    auto_label_counts = write_auto_label_counts(rows)
    failed_dim_counts = write_failed_dim_counts(rows)
    manual_counts = write_manual_audit_counts(rows)
    svg_auto_label_bar_chart(
        auto_label_counts,
        FIGURES_DIR / "failure_taxonomy_current_auto_label_counts.svg",
    )
    print(
        "Rendered "
        f"{len(auto_label_counts)} auto-label rows, "
        f"{len(failed_dim_counts)} failed-dim rows, "
        f"{len(manual_counts)} manual-audit rows."
    )


if __name__ == "__main__":
    main()
