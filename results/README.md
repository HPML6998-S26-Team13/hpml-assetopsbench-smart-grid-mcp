# results/

*Last updated: 2026-05-01*

Curated, reproducible metrics and figures emitted by notebooks. Most content
here is expected to come from `benchmarks/` once the experiment lanes are
running, but exploratory notebook outputs that help validate the dataset or
analysis pipeline can live here too.

## Structure

```
results/
├── metrics/               # cleaned CSVs/JSONL that figures and tables are computed from
│   ├── experiment_matrix_summary.csv  # compact row-per-condition result table
│   ├── optimized_serving_ablation.csv  # Cell D / ZSD focused follow-on deltas
│   ├── baseline_latency.csv        # one row per (scenario, model, trial)
│   ├── optimized_latency.csv
│   ├── orchestration_accuracy.csv  # per scenario × orchestration condition
│   ├── scenario_scores.jsonl       # LLM-as-Judge scoring outputs
│   ├── failure_evidence_table.csv  # classified judge-failed rows for #35/#64/#36
│   ├── failure_taxonomy_counts.csv # derived taxonomy-count source table
│   ├── failure_stage_cell_counts.csv
│   ├── mitigation_run_inventory.csv
│   └── mitigation_before_after.csv # header-only until matched reruns land
├── figures/               # publication-ready PDFs/PNGs
│   ├── fig1_pipeline_overview.pdf
│   ├── fig2_latency_breakdown.pdf
│   ├── fig3_orchestration_accuracy.pdf
│   ├── failure_taxonomy_counts.svg
│   ├── failure_stage_cell_heatmap.svg
│   └── mitigation_priority_table.svg
└── wandb_exports/         # periodic snapshots of WandB runs for long-term reproducibility
    └── 2026-04-20_week3_exports.json
```

## Conventions

- Every figure in `figures/` must trace back to a CSV in `metrics/`, which traces back to a run dir in `benchmarks/`. Keep that chain intact — reviewers need it.
- The canonical WandB field definitions live in [../docs/wandb_schema.md](../docs/wandb_schema.md).
- **Don't edit files in this dir by hand** — regenerate from notebooks. If you catch yourself tweaking a PDF directly, that's a smell.
- WandB exports are snapshots in time. If a WandB run is deleted or the project is wiped, the exports here are the only remaining record.
- `scenario_scores.jsonl` should retain the run-level join keys needed to line up with WandB and benchmark artifacts, especially `run_name`, `wandb_run_url`, `scenario_id`, `trial_index`, `experiment_cell`, `orchestration_mode`, `mcp_mode`, and `judge_model`.
- `failure_evidence_table.csv` classifies judge-failed rows from `scenario_scores.jsonl` into the failure taxonomy used by `docs/failure_taxonomy_evidence.md`.
- `scripts/render_failure_taxonomy_figures.py` regenerates the taxonomy
  summary CSVs, mitigation inventory, and SVG figures from
  `failure_evidence_table.csv`.
- `mitigation_before_after.csv` is the #66 comparison export contract. It is
  header-only until a guarded rerun lands; do not treat its presence as an
  after-run result.
- Per-trial judge audit logs live under `judge_logs/<run_name>/<scenario_id>_runNN_judge_log.json`.
- `experiment_matrix_summary.csv` is the compact "what ran?" table. It keeps
  legacy cell names, display-code names, run names, latency, judge-score, and
  raw-directory links together. The human-facing copy lives in
  [../docs/experiment_matrix.md](../docs/experiment_matrix.md).
- `optimized_serving_ablation.csv` keeps the focused D/ZSD follow-on deltas
  separate from the core notebook tables, so exploratory serving-stack results
  do not blur the main Experiment 1 / Experiment 2 claims.
- Filenames should be **stable** (so the paper can reference them by path) — avoid renames once a figure is committed to a report draft.

## Status (Apr 30, 2026)

First-capture populated:

- Notebook 01 now writes a reproducible dataset-exploration figure and summary
  CSVs here
- benchmark-derived judge metrics now include the first Experiment 1 / 2
  capture rows for A/B/C/D/Y/Z and Self-Ask variants
- Notebook 02 now exports full first-capture A/B/C MCP-overhead metrics and
  figure outputs
- Notebook 03 now exports first-capture B/Y/Z orchestration comparison,
  PE-family follow-on, Self-Ask ablation, and failure-breakdown metrics/figures
- the focused optimized-serving follow-on table is exported as
  `results/metrics/optimized_serving_ablation.csv`

What changed since the original scaffold:

- Notebook 01 exploratory outputs now exist:
  - `results/metrics/notebook01_asset_tier_summary.csv`
  - `results/metrics/notebook01_fault_counts_by_tier.csv`
  - `results/figures/notebook01_dataset_overview.png`
  - `results/figures/notebook01_dataset_overview.pdf`
- raw benchmark proof artifacts now exist under `benchmarks/cell_*` for the
  first Insomnia capture sets, including Cell C job `9071639` and exploratory
  Cell D job `9073472`
- `results/metrics/experiment_matrix_summary.csv` is the compact entry point
  for run lookup across A/B/C/D/Y/YS/Z/ZS/ZSD
- `results/metrics/optimized_serving_ablation.csv` captures the two current
  D/ZSD deltas: Cell D versus Cell C, and ZSD versus Z + Self-Ask baseline
- `results/metrics/scenario_scores.jsonl` is the canonical LLM-as-judge table;
  new judging runs also write per-trial audit logs under
  `results/judge_logs/<run_name>/`
- `results/metrics/failure_evidence_table.csv` now provides the first
  CSV-backed failure-taxonomy pass for the 35 judge-failed rows in the current
  scoring set
- failure-analysis figure sources now exist:
  - `results/metrics/failure_taxonomy_counts.csv`
  - `results/metrics/failure_symptom_counts.csv`
  - `results/metrics/failure_stage_cell_counts.csv`
  - `results/metrics/mitigation_run_inventory.csv`
  - `results/metrics/mitigation_before_after.csv` (schema only; no after-run rows yet)
  - `results/figures/failure_taxonomy_counts.svg`
  - `results/figures/failure_stage_cell_heatmap.svg`
  - `results/figures/mitigation_priority_table.svg`
- shared WandB runs are linked from the benchmark `summary.json` / `meta.json`
  files and mirrored into judge rows where available

What still needs to happen before this directory should be paper-final:

- final paper-depth captures at the agreed 5-trial / broader-scenario grid
- replacement of first-capture CSVs/figures with the frozen final run set
- optional 70B spot-check rows once the hosted WatsonX configs are run and judged
