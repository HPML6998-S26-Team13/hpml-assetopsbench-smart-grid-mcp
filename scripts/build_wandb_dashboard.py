"""
Build the SmartGridBench Final Evidence Dashboard on W&B.
Closes #45.

Steps:
  1. Identify the canonical post-PR175 run families from W&B.
  2. Tag each run with smartgrid-final, courseworks, family-specific tags.
  3. Create a W&B Report with sections for each run family.
  4. Print the report URL.
"""

import wandb
import wandb_workspaces.reports.v2 as wr
from wandb_workspaces.expr import Tags

ENTITY = "assetopsbench-smartgrid"
PROJECT = "assetopsbench-smartgrid"

# ---------------------------------------------------------------------------
# Run family matchers and their tag sets
# ---------------------------------------------------------------------------
FAMILIES = [
    {
        "prefix": ["core15x5_post175", "core_rem16x5_post175"],
        "tags": ["smartgrid-final", "courseworks", "paper-grade", "post-pr175"],
        "config": {
            "evidence_tier": "paper_grade",
            "submission_surface": "courseworks_2026",
        },
        "label": "core",
    },
    {
        "prefix": ["mitigation15x5_4tier_post175"],
        "tags": [
            "smartgrid-final",
            "courseworks",
            "paper-grade",
            "post-pr175",
            "mitigation-ladder",
        ],
        "config": {
            "evidence_tier": "paper_grade",
            "submission_surface": "courseworks_2026",
        },
        "label": "mitigation",
    },
    {
        "prefix": ["profile_spotcheck_20260507T0604Z"],
        "tags": ["smartgrid-final", "courseworks", "post-pr175", "profiling-spotcheck"],
        "config": {
            "evidence_tier": "profiling_observability",
            "caveat": "unjudged_profiling",
            "submission_surface": "courseworks_2026",
        },
        "label": "profiling",
    },
    {
        "prefix": ["followon15x5_post175", "extra15x5_post175"],
        "tags": ["smartgrid-final", "courseworks", "paper-grade", "post-pr175"],
        "config": {
            "evidence_tier": "paper_grade",
            "submission_surface": "courseworks_2026",
        },
        "label": "followon-extra",
    },
]

EXCLUDE_PREFIXES = [
    "smoke",
    "8848",
    "8850",
    "8851",
    "8852",
    "8853",
    "8854",
    "8857",
    "local-20260413",
    "local-20260501",
    "mitigation_final6_",
    "final5x6_a100_20260503",
    "final5x6_extra_a100_20260503",
    "full21x3_",
    "all21x3_",
    "final5x6_post174",
    "final5x6_followon",
    "final5x6_extra_variants",
    "context_",
    "9125",
    "9097",
    "9106",
    "9108",
    "9073",
    "9074",
    "9071",
    "8978",
    "8979",
    "8993",
    "8994",
    "8998",
    "vq976ljq",
    "qejvnoug",
]


def matches_family(name, prefixes):
    return any(name.startswith(p) for p in prefixes)


def should_exclude(name):
    return any(name.startswith(p) or p in name for p in EXCLUDE_PREFIXES)


# ---------------------------------------------------------------------------
# 1. Fetch all runs and tag canonical families
# ---------------------------------------------------------------------------
api = wandb.Api()
all_runs = api.runs(f"{ENTITY}/{PROJECT}", per_page=300)

family_runs = {f["label"]: [] for f in FAMILIES}
tagged_count = 0

print("Tagging canonical runs...")
for run in all_runs:
    if should_exclude(run.name):
        continue
    for fam in FAMILIES:
        if matches_family(run.name, fam["prefix"]):
            existing_tags = set(run.tags or [])
            new_tags = existing_tags | set(fam["tags"])
            if new_tags != existing_tags:
                run.tags = list(new_tags)
                run.save()
                tagged_count += 1
            # store config metadata
            for k, v in fam["config"].items():
                if run.config.get(k) != v:
                    run.config[k] = v
                    run.save()
            family_runs[fam["label"]].append(run)
            break

for label, runs in family_runs.items():
    print(f"  {label}: {len(runs)} runs tagged")
print(f"Total newly tagged: {tagged_count}")

# ---------------------------------------------------------------------------
# 2. Build W&B Report
# ---------------------------------------------------------------------------
print("\nBuilding W&B Report...")


def runset(name, tag):
    return wr.Runset(
        entity=ENTITY,
        project=PROJECT,
        name=name,
        filters=[Tags().isin([tag])],
    )


report = wr.Report(
    project=PROJECT,
    entity=ENTITY,
    title="SmartGridBench Final Evidence Dashboard",
    description=(
        "Reviewer-facing evidence dashboard for SmartGridBench (HPML Spring 2026, Team 13). "
        "Post-PR175 canonical runs, mitigation ladder, and profiling spot-checks. "
        "Smoke runs and pre-PR175 diagnostic cohorts are excluded. "
        "Profiling spot-check rows are observability evidence only."
    ),
)

blocks = []

# --- Overview ---
blocks.append(wr.H1(text="Overview"))
blocks.append(
    wr.MarkdownBlock(
        text=(
            "**SmartGridBench — HPML Spring 2026, Team 13**\n\n"
            "This dashboard is the final evidence surface submitted to CourseWorks.\n\n"
            "**Run families included:**\n"
            "- **Core post-PR175** (`core15x5_post175`, `core_rem16x5_post175`): "
            "cells A/B/C (transport) and B/Y/YS/Z/ZS (orchestration) on the 31-scenario evidence floor\n"
            "- **Mitigation ladder** (`mitigation15x5_4tier_post175`): "
            "4-tier (baseline → guard → repair → adjudication) on YS and ZS\n"
            "- **Profiling spot-check** (`profile_spotcheck_20260507T0604Z`): "
            "4 runs with W&B system metrics, nvidia-smi, and torch-trace — observability only\n"
            "- **Follow-on/extra** (`followon15x5_post175`, `extra15x5_post175`): "
            "transport follow-ons (YS-TP, ZS-TP) and INT8/BF16 KV variants (D, ZSD)\n\n"
            "**Excluded:** smoke runs, pre-PR175 diagnostic cohorts, historical `mitigation_final6_*`.\n\n"
            "**Source inventory:** `results/metrics/profiling_inventory.csv`\n"
            "**Scenario corpus:** 36 canonical scenarios + 5 negative fixtures "
            "(result tables use 31-scenario post-PR175 floor)"
        )
    )
)

# --- Core benchmark runs ---
blocks.append(wr.HorizontalRule())
blocks.append(wr.H1(text="Core Benchmark Runs — post-PR175"))
blocks.append(
    wr.MarkdownBlock(
        text=(
            "Transport axis (A/B/C) and orchestration axis (B/Y/YS/Z/ZS) "
            "on the post-PR175 31-scenario evidence floor. "
            "Both `core15x5_post175` and `core_rem16x5_post175` batches are shown. "
            "Tag filter: `paper-grade`."
        )
    )
)
blocks.append(
    wr.PanelGrid(
        runsets=[runset("Core + follow-on runs", "paper-grade")],
        panels=[
            wr.ScalarChart(
                title="Mean latency (s)",
                metric="latency_seconds_mean",
                groupby_aggfunc="mean",
            ),
            wr.ScalarChart(
                title="p50 latency (s)",
                metric="latency_seconds_p50",
                groupby_aggfunc="mean",
            ),
            wr.ScalarChart(
                title="Judge score mean",
                metric="score_6d_mean",
                groupby_aggfunc="mean",
            ),
            wr.ScalarChart(
                title="Judge pass rate",
                metric="judge_pass_rate",
                groupby_aggfunc="mean",
            ),
            wr.LinePlot(
                title="Latency mean by run",
                y=["latency_seconds_mean", "latency_seconds_p50"],
            ),
        ],
    )
)

# --- Mitigation ladder ---
blocks.append(wr.HorizontalRule())
blocks.append(wr.H1(text="Mitigation Ladder — post-PR175"))
blocks.append(
    wr.MarkdownBlock(
        text=(
            "4-tier ladder (BASELINE → GUARD → REPAIR → ADJ) on YS (PE+Self-Ask) "
            "and ZS (Verified PE+Self-Ask) cells. "
            "Run family: `mitigation15x5_4tier_post175`. Tag: `mitigation-ladder`."
        )
    )
)
blocks.append(
    wr.PanelGrid(
        runsets=[runset("Mitigation ladder", "mitigation-ladder")],
        panels=[
            wr.ScalarChart(
                title="Judge score mean",
                metric="score_6d_mean",
                groupby_aggfunc="mean",
            ),
            wr.ScalarChart(
                title="Judge pass rate",
                metric="judge_pass_rate",
                groupby_aggfunc="mean",
            ),
            wr.LinePlot(
                title="Score by mitigation tier",
                y=["score_6d_mean", "judge_pass_rate"],
            ),
        ],
    )
)

# --- Profiling spot-check ---
blocks.append(wr.HorizontalRule())
blocks.append(wr.H1(text="Profiling Spot-Check"))
blocks.append(
    wr.MarkdownBlock(
        text=(
            "4 runs (v\\_s\\_m, at\\_m, pe\\_s\\_m, at\\_t) with W&B system metrics, "
            "nvidia-smi, and torch-trace profiling enabled. "
            "Run family: `profile_spotcheck_20260507T0604Z`. Tag: `profiling-spotcheck`.\n\n"
            "⚠️ **Caveat:** these rows are observability evidence — not judged task-quality results."
        )
    )
)
blocks.append(
    wr.PanelGrid(
        runsets=[runset("Profiling spot-check", "profiling-spotcheck")],
        panels=[
            wr.ScalarChart(
                title="GPU utilization (%)",
                metric="system.gpu.0.gpu",
                groupby_aggfunc="mean",
            ),
            wr.ScalarChart(
                title="GPU memory allocated (%)",
                metric="system.gpu.0.memoryAllocated",
                groupby_aggfunc="mean",
            ),
            wr.ScalarChart(
                title="Mean latency (s)",
                metric="latency_seconds_mean",
                groupby_aggfunc="mean",
            ),
        ],
    )
)

# --- Reproducibility ---
blocks.append(wr.HorizontalRule())
blocks.append(wr.H1(text="Reproducibility"))
blocks.append(
    wr.MarkdownBlock(
        text=(
            "- **GitHub repo:** https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp\n"
            "- **Run inventory:** `results/metrics/profiling_inventory.csv`\n"
            "- **Scenario corpus:** `data/scenarios/` "
            "(36 canonical scenarios + 5 negative fixtures; result tables use 31-scenario floor)\n"
            "- **Data generation:** `data/generate_synthetic.py` "
            "(no proprietary CSVs shipped; public-safe synthetic outputs only)\n"
            "- **Judge model:** Llama-4 Maverick 17B via WatsonX (separate family from task model)\n"
            "- **Task model:** Llama-3.1-8B-Instruct via vLLM"
        )
    )
)

report.blocks = blocks
report.save()

print(f"\nReport URL: {report.url}")
print("Done.")
