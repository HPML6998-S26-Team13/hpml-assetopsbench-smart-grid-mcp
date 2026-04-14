# results/

Curated, reproducible metrics and figures emitted by notebooks. Most content
here is expected to come from `benchmarks/` once the experiment lanes are
running, but exploratory notebook outputs that help validate the dataset or
analysis pipeline can live here too.

## Structure

```
results/
├── metrics/               # cleaned CSVs/JSONL that figures and tables are computed from
│   ├── baseline_latency.csv        # one row per (scenario, model, trial) [placeholder]
│   ├── optimized_latency.csv       # [placeholder]
│   ├── orchestration_accuracy.csv  # per scenario × orchestration condition [placeholder]
│   └── scenario_scores.jsonl       # LLM-as-Judge scoring outputs (2 entries live)
├── judge_logs/            # full judge audit trail: prompt sent + raw model response + dims
│   └── <run_name>/
│       └── <SCENARIO_ID>_judge_log.json
├── figures/               # publication-ready PDFs/PNGs [placeholder]
└── wandb_exports/         # periodic snapshots of WandB runs for long-term reproducibility
```

## Conventions

- Every figure in `figures/` must trace back to a CSV in `metrics/`, which traces back to a run dir in `benchmarks/`. Keep that chain intact — reviewers need it.
- The canonical WandB field definitions live in `docs/wandb_schema.md`.
- **Don't edit `scenario_scores.jsonl` by hand** — regenerate from `scripts/judge_trajectory.py`. If you need to re-score, re-run the script; do not patch values manually.
- WandB exports are snapshots in time. If a WandB run is deleted or the project is wiped, the exports here are the only remaining record.
- `scenario_scores.jsonl` retains the run-level join keys needed to line up with WandB and benchmark artifacts: `run_name`, `wandb_run_url`, `scenario_id`, `trial_index`, `experiment_cell`, `orchestration_mode`, `mcp_mode`, `judge_model`.
- `judge_logs/<run_name>/<SCENARIO_ID>_judge_log.json` contains the verbatim prompt sent to Maverick and its raw response. Use these for audit, debugging, and prompt-engineering iteration. Generated automatically when `--log-dir` is passed to `judge_trajectory.py`.
- Filenames should be **stable** (so the paper can reference them by path) — avoid renames once a figure is committed to a report draft.

## Status (Apr 20, 2026)

Partially populated:

- Notebook 01 now writes a reproducible dataset-exploration figure and summary
  CSVs here
- benchmark-derived Experiment 1 / Experiment 2 metrics are still pending

What changed since the original scaffold:

- Notebook 01 exploratory outputs now exist:
  - `results/metrics/notebook01_asset_tier_summary.csv`
  - `results/metrics/notebook01_fault_counts_by_tier.csv`
  - `results/figures/notebook01_dataset_overview.png`
  - `results/figures/notebook01_dataset_overview.pdf`
- raw benchmark proof artifacts now exist under `benchmarks/cell_Y_plan_execute/` as a WatsonX-hosted 70B / Mac 1-scenario smoke run; the primary-lane Insomnia 8B proof is still PR-only
- the first shared WandB run is real and linked back into those raw artifacts

What still needs to happen before this directory should fill up:

- Experiment 1 profiling captures (`#25`)
- profiling / benchmark linkage into WandB (`#27`)
- Notebook 02 analysis and export of cleaned metrics / figures (`#26`)

**Live W3 judge artifacts:**

| File | Contents | Source |
|------|----------|--------|
| `metrics/scenario_scores.jsonl` | 2 scored entries (AOB-FMSR-001 @ 1.0, SGT-003 @ 0.5) | `scripts/judge_trajectory.py` + Maverick-17B |
| `judge_logs/issue18-smartgrid-smoke/SGT-003_judge_log.json` | Full audit trail for the committed SGT-003 Maverick judge call | issue `#20` |
