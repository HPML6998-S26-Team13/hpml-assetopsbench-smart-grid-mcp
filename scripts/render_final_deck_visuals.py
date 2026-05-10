#!/usr/bin/env python3
"""Render CSV-backed visual assets for the final HPML presentation deck."""

from __future__ import annotations

import csv
import textwrap
from datetime import UTC, datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "smartgridbench-final-deck"

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

ROOT = Path(__file__).resolve().parents[1]
FIGURES_DIR = ROOT / "results" / "figures"
METRICS_DIR = ROOT / "results" / "metrics"
PROFILING_DIR = ROOT / "profiling" / "traces"

TEAL = "#1f6f78"
ORANGE = "#c85a3a"
GREEN = "#6f7d2a"
BLUE = "#4c6f9f"
GOLD = "#b8860b"
INK = "#1f2328"
MUTED = "#5b6670"
GRID = "#d8dee4"
BG = "#fbfbf8"


def save_figure(fig: plt.Figure, stem: str) -> list[Path]:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    outputs = []
    for suffix in ("png", "svg"):
        path = FIGURES_DIR / f"{stem}.{suffix}"
        metadata = {"Date": None} if suffix == "svg" else None
        fig.savefig(
            path,
            dpi=220,
            bbox_inches="tight",
            facecolor="white",
            metadata=metadata,
        )
        outputs.append(path)
    plt.close(fig)
    # Strip trailing whitespace from generated SVGs so `git diff --check` is clean.
    for path in outputs:
        if path.suffix == ".svg":
            text = path.read_text(encoding="utf-8")
            stripped = "\n".join(line.rstrip() for line in text.split("\n"))
            path.write_text(stripped, encoding="utf-8")
    return outputs


# Paper-grade corpus floor frozen at NeurIPS submission (2026-05-07).
# Anything beyond this in data/scenarios/ is post-submission stretch (PR #199) and
# is NOT in paper claims. Renderer keeps paper-grade as the load-bearing figure
# and shows total-corpus growth as informational context only.
PAPER_GRADE_POSITIVE = 36
PAPER_GRADE_NEGATIVE = 5
PAPER_GRADE_HAND_AUTHORED = 31
PROPOSAL_FLOOR = 30


def pct_label(value: float) -> str:
    return f"{value * 100:.0f}%"


def configure_axis(ax: plt.Axes) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRID)
    ax.tick_params(colors=MUTED)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8, alpha=0.65)
    ax.set_axisbelow(True)


def render_mitigation_before_after() -> list[Path]:
    source = METRICS_DIR / "mitigation_before_after.csv"
    df = pd.read_csv(source)
    df = df[df["comparison_status"] == "paper_grade_post175_matched"].copy()
    phase_order = ["baseline", "guard", "repair", "adjudication"]
    phase_labels = ["baseline", "guard", "repair", "adjud."]
    colors = {"YS": TEAL, "ZS": ORANGE}

    fig, axes = plt.subplots(1, 2, figsize=(14, 7.2), constrained_layout=True)
    fig.patch.set_facecolor("white")
    fig.suptitle(
        "Mitigation ladder: mixed effects, not universal lift",
        fontsize=20,
        fontweight="bold",
        color=INK,
    )

    for ax, metric, title, ylim in [
        (axes[0], "judge_pass_rate", "Judge pass rate", (0, 0.72)),
        (axes[1], "judge_score_mean", "Mean judge score", (0, 0.72)),
    ]:
        width = 0.34
        x = range(len(phase_order))
        for offset, lane in [(-width / 2, "YS"), (width / 2, "ZS")]:
            lane_df = df[df["lane"] == lane].set_index("phase").reindex(phase_order)
            values = lane_df[metric].astype(float).tolist()
            bars = ax.bar(
                [i + offset for i in x],
                values,
                width=width,
                label=lane,
                color=colors[lane],
                alpha=0.92,
            )
            for bar, value in zip(bars, values):
                text = (
                    pct_label(value) if metric == "judge_pass_rate" else f"{value:.3f}"
                )
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.014,
                    text,
                    ha="center",
                    va="bottom",
                    fontsize=9,
                    color=INK,
                    fontweight="bold",
                )
        ax.set_title(title, fontsize=14, fontweight="bold", color=INK)
        ax.set_xticks(list(x), phase_labels)
        ax.set_ylim(*ylim)
        ax.legend(frameon=False, loc="upper right")
        configure_axis(ax)

    fig.text(
        0.01,
        -0.03,
        "Source: results/metrics/mitigation_before_after.csv; post-PR175 cohort; "
        "8 row groups, n=75 judged trajectories per row. ZS repair is the only "
        "small positive lift; guard/adjudication are lower than baseline.",
        ha="left",
        fontsize=10,
        color=MUTED,
    )
    return save_figure(fig, "final_deck_mitigation_before_after")


def trace_count_for_run(run_name: str) -> int:
    slug = run_name.removeprefix("profile_spotcheck_20260507T0604Z_")
    trace_dir = PROFILING_DIR / f"profile_spotcheck_20260507T0604Z_{slug}_torch"
    return len(list(trace_dir.glob("*.pt.trace.json.gz")))


def render_profiling_summary() -> list[Path]:
    source = METRICS_DIR / "profiling_inventory.csv"
    df = pd.read_csv(source).fillna("")
    df = df[df["run_name"].str.startswith("profile_spotcheck_20260507T0604Z")].copy()
    order = ["AT_M", "AT_T", "PE_S_M", "V_S_M"]
    df["order"] = df["experiment_cell"].map({cell: i for i, cell in enumerate(order)})
    df = df.sort_values("order")

    columns = [
        ("Cell", 0.08),
        ("W&B run", 0.16),
        ("nvidia-smi\nsamples", 0.14),
        ("GPU util\nmean", 0.13),
        ("VRAM max\nGiB", 0.13),
        ("Power max\nW", 0.13),
        ("Torch trace\nfiles", 0.13),
    ]
    starts = [0.04]
    for _, width in columns[:-1]:
        starts.append(starts[-1] + width)

    fig, ax = plt.subplots(figsize=(13.5, 7.2))
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(
        0.04,
        0.93,
        "Profiler spot-check coverage",
        fontsize=22,
        fontweight="bold",
        color=INK,
    )
    ax.text(
        0.04,
        0.885,
        "Four current-code rows have W&B links and nvidia-smi summaries; "
        "AT rows also emitted torch traces.",
        fontsize=12,
        color=MUTED,
    )

    header_y = 0.78
    row_h = 0.105
    header_color = "#e9f1f2"
    row_colors = ["#ffffff", "#f7f9fa"]

    for start, (label, width) in zip(starts, columns):
        ax.add_patch(Rectangle((start, header_y), width, row_h, color=header_color))
        ax.text(
            start + 0.012,
            header_y + row_h / 2,
            label,
            va="center",
            fontsize=11,
            fontweight="bold",
            color=INK,
        )

    for i, row in enumerate(df.to_dict("records")):
        y = header_y - (i + 1) * row_h
        for start, (_, width) in zip(starts, columns):
            ax.add_patch(Rectangle((start, y), width, row_h, color=row_colors[i % 2]))
            ax.add_patch(
                Rectangle(
                    (start, y), width, row_h, fill=False, edgecolor=GRID, linewidth=0.7
                )
            )
        trace_count = trace_count_for_run(row["run_name"])
        values = [
            row["experiment_cell"].replace("_", "-"),
            row["wandb_run_id"],
            str(int(float(row["profiling_nvidia_smi_samples"]))),
            f"{float(row['profiling_gpu_util_mean']):.1f}%",
            f"{float(row['profiling_gpu_mem_used_mib_max']) / 1024:.1f}",
            f"{float(row['profiling_power_draw_w_max']):.0f}",
            str(trace_count),
        ]
        for start, value in zip(starts, values):
            ax.text(
                start + 0.012, y + row_h / 2, value, va="center", fontsize=12, color=INK
            )

    ax.text(
        0.04,
        0.18,
        "Inventory totals: 104 run rows, 63 W&B-linked rows, 13 profiler-linked rows, "
        "6 rows with profiling summary stats.",
        fontsize=12,
        color=INK,
        fontweight="bold",
    )
    ax.text(
        0.04,
        0.12,
        "Source: results/metrics/profiling_inventory.csv plus profiling/traces/profile_spotcheck_20260507T0604Z_*.",
        fontsize=10,
        color=MUTED,
    )
    return save_figure(fig, "final_deck_profiling_spotcheck_summary")


def parse_percent(value: str) -> float:
    return float(value.replace("%", "").strip())


def parse_watts(value: str) -> float:
    return float(value.replace("W", "").strip())


def parse_mib(value: str) -> float:
    return float(value.replace("MiB", "").strip())


def read_nvidia_smi_trace(path: Path) -> pd.DataFrame:
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f, skipinitialspace=True))
    out = pd.DataFrame(rows)
    out["timestamp"] = pd.to_datetime(out["timestamp"])
    start = out["timestamp"].iloc[0]
    out["seconds"] = (out["timestamp"] - start).dt.total_seconds()
    out["gpu_util"] = out["utilization.gpu [%]"].map(parse_percent)
    out["memory_gib"] = out["memory.used [MiB]"].map(parse_mib) / 1024.0
    out["power_w"] = out["power.draw [W]"].map(parse_watts)
    return out


def render_profiling_timeseries() -> list[Path]:
    run_map = {
        "AT-M": PROFILING_DIR
        / "profile_spotcheck_20260507T0604Z_at_m_nvidia_smi"
        / "nvidia_smi.csv",
        "AT-T": PROFILING_DIR
        / "profile_spotcheck_20260507T0604Z_at_t_nvidia_smi"
        / "nvidia_smi.csv",
        "PE-S-M": PROFILING_DIR
        / "profile_spotcheck_20260507T0604Z_pe_s_m_nvidia_smi"
        / "nvidia_smi.csv",
        "V-S-M": PROFILING_DIR
        / "profile_spotcheck_20260507T0604Z_v_s_m_nvidia_smi"
        / "nvidia_smi.csv",
    }

    # `profiling/traces/` is gitignored. Bail out before rewriting any committed
    # figure if any required CSV is missing on this checkout, so a fresh-clone
    # `python3 scripts/render_final_deck_visuals.py` neither crashes mid-write
    # nor leaves a partially regenerated set of profiling figures on disk.
    missing = [
        f"{label}: {path}" for label, path in run_map.items() if not path.exists()
    ]
    if missing:
        print(
            "Skipping render_profiling_timeseries: "
            "required nvidia_smi traces under profiling/traces/ are not present in "
            "this checkout (the directory is gitignored). "
            "Re-run after restoring the trace bundle.",
        )
        for entry in missing:
            print(f"  missing: {entry}")
        return []

    colors = [TEAL, BLUE, GREEN, ORANGE]
    fig, axes = plt.subplots(
        3, 1, figsize=(13.5, 7.6), sharex=True, constrained_layout=True
    )
    fig.suptitle(
        "Profiler spot-check: A100 telemetry over one-scenario runs",
        fontsize=19,
        fontweight="bold",
        color=INK,
    )
    metrics = [
        ("gpu_util", "GPU util (%)", (0, 105)),
        ("memory_gib", "VRAM used (GiB)", (0, 42)),
        ("power_w", "Power draw (W)", (0, 470)),
    ]
    for ax, (metric, ylabel, ylim) in zip(axes, metrics):
        for (label, path), color in zip(run_map.items(), colors):
            trace = read_nvidia_smi_trace(path)
            ax.plot(
                trace["seconds"], trace[metric], label=label, color=color, linewidth=1.8
            )
        ax.set_ylabel(ylabel, color=INK)
        ax.set_ylim(*ylim)
        configure_axis(ax)
    axes[-1].set_xlabel("seconds since capture start", color=INK)
    axes[0].legend(frameon=False, ncol=4, loc="upper right")
    fig.text(
        0.01,
        -0.02,
        "Source: profiling/traces/profile_spotcheck_20260507T0604Z_*_nvidia_smi/nvidia_smi.csv. "
        "Use as profiling/observability evidence, not judged quality evidence.",
        ha="left",
        fontsize=10,
        color=MUTED,
    )
    return save_figure(fig, "final_deck_profiling_nvidia_smi_timeseries")


def render_scenario_corpus_status() -> list[Path]:
    total_positive = len(list((ROOT / "data" / "scenarios").glob("*.json")))
    total_negative = len(
        list((ROOT / "data" / "scenarios" / "negative_checks").glob("*.json"))
    )
    post_submission_stretch = max(0, total_positive - PAPER_GRADE_POSITIVE)

    # Axis spans the larger of paper-grade or current total so both bars fit.
    axis_max = max(PAPER_GRADE_POSITIVE + 4, total_positive + 4)

    fig, ax = plt.subplots(figsize=(13.5, 5.8))
    ax.set_axis_off()
    ax.set_xlim(0, axis_max)
    ax.set_ylim(0, 1)
    ax.text(
        0.2,
        0.88,
        "Scenario corpus: paper-grade floor + post-submission stretch separated",
        fontsize=17,
        fontweight="bold",
        color=INK,
    )
    ax.text(
        0.2,
        0.78,
        (
            f"Paper-grade canonical: {PAPER_GRADE_POSITIVE} positive "
            f"({PAPER_GRADE_HAND_AUTHORED} hand-authored + "
            f"{PAPER_GRADE_POSITIVE - PAPER_GRADE_HAND_AUTHORED} promoted generated) "
            f"+ {PAPER_GRADE_NEGATIVE} negative fixtures. "
            f"Repo currently has {total_positive} positive + {total_negative} negative "
            f"({post_submission_stretch} post-submission via PR #199; not in paper claims)."
        ),
        fontsize=12,
        color=MUTED,
    )

    y = 0.48
    ax.add_patch(Rectangle((0, y - 0.06), total_positive, 0.12, color="#e9f1f2"))
    ax.add_patch(Rectangle((0, y - 0.06), PROPOSAL_FLOOR, 0.12, color=TEAL, alpha=0.72))
    ax.add_patch(Rectangle((PROPOSAL_FLOOR, y - 0.06), 1, 0.12, color=BLUE, alpha=0.78))
    ax.add_patch(
        Rectangle(
            (PAPER_GRADE_HAND_AUTHORED, y - 0.06),
            max(0, PAPER_GRADE_POSITIVE - PAPER_GRADE_HAND_AUTHORED),
            0.12,
            color=ORANGE,
            alpha=0.82,
        )
    )
    if post_submission_stretch > 0:
        ax.add_patch(
            Rectangle(
                (PAPER_GRADE_POSITIVE, y - 0.06),
                post_submission_stretch,
                0.12,
                color=GOLD,
                alpha=0.45,
            )
        )

    markers: list[tuple[int, str, float]] = [
        (PROPOSAL_FLOOR, f"{PROPOSAL_FLOOR} required", 0.30),
        (PAPER_GRADE_HAND_AUTHORED, f"{PAPER_GRADE_HAND_AUTHORED} hand-authored", 0.64),
        (PAPER_GRADE_POSITIVE, f"{PAPER_GRADE_POSITIVE} paper-grade", 0.30),
    ]
    if post_submission_stretch > 0:
        markers.append((total_positive, f"{total_positive} repo total", 0.64))

    for value, label, ypos in markers:
        ax.plot([value, value], [y - 0.12, y + 0.12], color=INK, linewidth=1.2)
        ax.text(
            value, ypos, label, ha="center", fontsize=12, color=INK, fontweight="bold"
        )
    ax.text(
        PAPER_GRADE_HAND_AUTHORED,
        0.16,
        f"post-PR175 paper-grade result floor: {PAPER_GRADE_HAND_AUTHORED} scenarios",
        ha="center",
        fontsize=12,
        color=INK,
        bbox={"boxstyle": "round,pad=0.45", "facecolor": "#fff3cd", "edgecolor": GOLD},
    )
    ax.text(
        0.2,
        0.04,
        "Source: data/scenarios/*.json, data/scenarios/negative_checks/*.json, docs/final_presentation_deck.md.",
        fontsize=10,
        color=MUTED,
    )
    return save_figure(fig, "final_deck_scenario_corpus_status")


def wrapped(value: str, width: int) -> str:
    return "\n".join(
        textwrap.fill(line, width=width, break_long_words=False)
        for line in value.splitlines()
    )


def draw_box(
    ax: plt.Axes,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    body: str,
    color: str,
    *,
    body_width: int = 28,
    body_fontsize: float = 9.5,
) -> None:
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.025",
        linewidth=1.2,
        edgecolor=color,
        facecolor="#ffffff",
    )
    ax.add_patch(patch)
    ax.text(x + 0.03, y + h - 0.08, title, fontsize=13, fontweight="bold", color=color)
    ax.text(
        x + 0.03,
        y + h - 0.16,
        wrapped(body, body_width),
        fontsize=body_fontsize,
        color=INK,
        va="top",
        linespacing=1.25,
    )


def render_artifact_lineage() -> list[Path]:
    fig, ax = plt.subplots(figsize=(14, 7.2))
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(
        0.04,
        0.92,
        "Artifact lineage: one evidence contract from scenario to slide",
        fontsize=20,
        fontweight="bold",
        color=INK,
    )
    ax.text(
        0.04,
        0.865,
        "Every result shown in the deck should trace back to scenario files, raw trajectories, judge rows, and current metrics exports.",
        fontsize=12,
        color=MUTED,
    )

    boxes = [
        (
            0.04,
            0.55,
            0.17,
            0.22,
            "Scenario",
            f"{PAPER_GRADE_POSITIVE} paper-grade\n{PAPER_GRADE_NEGATIVE} negative fixtures",
            TEAL,
        ),
        (
            0.25,
            0.55,
            0.17,
            0.22,
            "Tools",
            "MCP or direct\n4 tool domains",
            BLUE,
        ),
        (
            0.46,
            0.55,
            0.17,
            0.22,
            "Trajectory",
            "raw trial JSON\nlatencies.jsonl",
            GREEN,
        ),
        (
            0.67,
            0.55,
            0.17,
            0.22,
            "Judge",
            "scenario scores\njudge logs",
            ORANGE,
        ),
        (
            0.76,
            0.20,
            0.19,
            0.23,
            "Deck",
            "metrics CSVs\nfigures\nPPT slides",
            GOLD,
        ),
    ]
    for x, y, w, h, title, body, color in boxes:
        draw_box(ax, x, y, w, h, title, body, color, body_width=20, body_fontsize=9.0)
    arrow_pairs = [
        ((0.21, 0.66), (0.25, 0.66)),
        ((0.42, 0.66), (0.46, 0.66)),
        ((0.63, 0.66), (0.67, 0.66)),
    ]
    for start, end in arrow_pairs:
        ax.add_patch(
            FancyArrowPatch(
                start,
                end,
                arrowstyle="-|>",
                mutation_scale=16,
                color=MUTED,
                linewidth=1.4,
            )
        )
    ax.add_patch(
        FancyArrowPatch(
            (0.78, 0.55),
            (0.84, 0.43),
            arrowstyle="-|>",
            mutation_scale=16,
            color=MUTED,
            linewidth=1.4,
        )
    )
    ax.add_patch(
        FancyBboxPatch(
            (0.08, 0.19),
            0.55,
            0.23,
            boxstyle="round,pad=0.02,rounding_size=0.025",
            linewidth=1.2,
            edgecolor=INK,
            facecolor=BG,
        )
    )
    ax.text(
        0.11,
        0.35,
        "Evidence registry filter",
        fontsize=13,
        fontweight="bold",
        color=INK,
    )
    ax.text(
        0.11,
        0.295,
        "Rows are tagged as paper_grade, superseded, diagnostic, or invalid.",
        fontsize=9.4,
        color=INK,
    )
    ax.text(
        0.11,
        0.245,
        "Deck and paper tables use paper_grade unless a slide is explicitly diagnostic.",
        fontsize=9.4,
        color=INK,
    )
    ax.add_patch(
        FancyArrowPatch(
            (0.55, 0.55),
            (0.39, 0.42),
            arrowstyle="-|>",
            mutation_scale=16,
            color=MUTED,
            linewidth=1.2,
        )
    )
    ax.add_patch(
        FancyArrowPatch(
            (0.63, 0.31),
            (0.76, 0.31),
            arrowstyle="-|>",
            mutation_scale=16,
            color=MUTED,
            linewidth=1.2,
        )
    )
    ax.text(
        0.04,
        0.08,
        "Source: docs/runbook.md, results/metrics/evidence_registry.csv, results/metrics/scenario_scores.jsonl.",
        fontsize=10,
        color=MUTED,
    )
    return save_figure(fig, "final_deck_artifact_lineage")


def main() -> None:
    outputs: list[Path] = []
    outputs.extend(render_mitigation_before_after())
    outputs.extend(render_profiling_summary())
    outputs.extend(render_profiling_timeseries())
    outputs.extend(render_scenario_corpus_status())
    outputs.extend(render_artifact_lineage())
    rel_outputs = [path.relative_to(ROOT) for path in outputs]
    print("Rendered final deck visuals:")
    for path in rel_outputs:
        print(f"- {path}")
    generated_at = (
        datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    )
    print(f"Generated at {generated_at}")


if __name__ == "__main__":
    main()
