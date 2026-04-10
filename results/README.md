# results/

Curated, publication-ready metrics and figures. Content here is derived from `benchmarks/` via notebooks in `notebooks/` — treat this as the authoritative "these are the numbers in the paper" directory.

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
- The canonical WandB field definitions live in `docs/wandb_schema.md`.
- **Don't edit files in this dir by hand** — regenerate from notebooks. If you catch yourself tweaking a PDF directly, that's a smell.
- WandB exports are snapshots in time. If a WandB run is deleted or the project is wiped, the exports here are the only remaining record.
- `scenario_scores.jsonl` should retain the run-level join keys needed to line up with WandB and benchmark artifacts, especially `run_name`, `wandb_run_url`, `scenario_id`, `trial_index`, `experiment_cell`, `orchestration_mode`, `mcp_mode`, and `judge_model`.
- Filenames should be **stable** (so the paper can reference them by path) — avoid renames once a figure is committed to a report draft.

## Status (Apr 7, 2026)

Scaffolding only. First metrics will land in W3 (Apr 14-20) once baseline profiling runs produce raw data in `benchmarks/`.
