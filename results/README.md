# results/

*Last updated: 2026-04-30*

Curated, reproducible metrics and figures emitted by notebooks. Most content
here is expected to come from `benchmarks/` once the experiment lanes are
running, but exploratory notebook outputs that help validate the dataset or
analysis pipeline can live here too.

## Structure

```
results/
├── metrics/               # cleaned CSVs/JSONL that figures and tables are computed from
│   ├── baseline_latency.csv        # one row per (scenario, model, trial)
│   ├── optimized_latency.csv
│   ├── orchestration_accuracy.csv  # per scenario × orchestration condition
│   └── scenario_scores.jsonl       # LLM-as-Judge scoring outputs
├── figures/               # publication-ready PDFs/PNGs
│   ├── fig1_pipeline_overview.pdf
│   ├── fig2_latency_breakdown.pdf
│   └── fig3_orchestration_accuracy.pdf
└── wandb_exports/         # periodic snapshots of WandB runs for long-term reproducibility
    └── 2026-04-20_week3_exports.json
```

## Conventions

- Every figure in `figures/` must trace back to a CSV in `metrics/`, which traces back to a run dir in `benchmarks/`. Keep that chain intact — reviewers need it.
- The canonical WandB field definitions live in [../docs/wandb_schema.md](../docs/wandb_schema.md).
- **Don't edit files in this dir by hand** — regenerate from notebooks. If you catch yourself tweaking a PDF directly, that's a smell.
- WandB exports are snapshots in time. If a WandB run is deleted or the project is wiped, the exports here are the only remaining record.
- `scenario_scores.jsonl` should retain the run-level join keys needed to line up with WandB and benchmark artifacts, especially `run_name`, `wandb_run_url`, `scenario_id`, `trial_index`, `experiment_cell`, `orchestration_mode`, `mcp_mode`, and `judge_model`.
- Per-trial judge audit logs live under `judge_logs/<run_name>/<scenario_id>_runNN_judge_log.json`.
- Filenames should be **stable** (so the paper can reference them by path) — avoid renames once a figure is committed to a report draft.

## Status (Apr 30, 2026)

Partially populated:

- Notebook 01 now writes a reproducible dataset-exploration figure and summary
  CSVs here
- benchmark-derived judge metrics now include the first Experiment 1 / 2
  capture rows for A/B/C/D/Y/Z and Self-Ask variants; Notebook-cleaned
  aggregate CSVs/figures are still in progress

What changed since the original scaffold:

- Notebook 01 exploratory outputs now exist:
  - `results/metrics/notebook01_asset_tier_summary.csv`
  - `results/metrics/notebook01_fault_counts_by_tier.csv`
  - `results/figures/notebook01_dataset_overview.png`
  - `results/figures/notebook01_dataset_overview.pdf`
- raw benchmark proof artifacts now exist under `benchmarks/cell_*` for the
  first Insomnia capture sets, including Cell C job `9071639` and exploratory
  Cell D job `9073472`
- `results/metrics/scenario_scores.jsonl` is the canonical LLM-as-judge table;
  new judging runs also write per-trial audit logs under
  `results/judge_logs/<run_name>/`
- shared WandB runs are linked from the benchmark `summary.json` / `meta.json`
  files and mirrored into judge rows where available

What still needs to happen before this directory should fill up:

- final paper-depth Experiment 1 captures (`#25`)
- Notebook 02 transition from parser/preflight scaffold into real Experiment 1
  cleaned metrics / figures once Cells A / B / C exist (`#26` Cell A/B analysis,
  `#86` Cell C analysis)
- Notebook 03 transition from preliminary judge metrics into final
  orchestration-comparison figures once the canonical reruns are frozen
