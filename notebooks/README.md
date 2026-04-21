# notebooks/

Jupyter notebooks for exploratory analysis and figure generation. Notebooks are the **bridge** between raw measurements in `benchmarks/` and curated results in `results/`: they read from `benchmarks/`, transform, and write to `results/metrics/` and `results/figures/`.

## Planned notebooks

```
notebooks/
├── 01_data_exploration.ipynb         # EDA on processed Kaggle CSVs (data/processed/)
├── 02_latency_analysis.ipynb         # Experiment 1: Cell A vs B vs C latency / MCP-overhead analysis
├── 03_orchestration_comparison.ipynb # Experiment 2: AaT vs PE (optional Hybrid only if it becomes real)
└── 04_figure_generation.ipynb        # produces publication-ready PDFs in results/figures/
```

## Conventions

- **Number notebooks** by analysis order — `01_` comes before `02_` etc. so the pipeline reads top-down.
- **Install the right notebook deps** — `requirements.txt` now carries the portable execution stack (`nbconvert`, `nbclient`, `ipykernel`); add `requirements-notebooks.txt` if you want the interactive JupyterLab UI locally.
- **Don't commit rendered cell outputs.** `.ipynb_checkpoints/` is gitignored, but cell outputs still land in the notebook JSON. Run `jupyter nbconvert --clear-output --inplace <notebook>.ipynb` before `git add`.
- **Pin versions** — record the Python + package versions used in a markdown cell at the top of each notebook. Future you will thank present you.
- **Every figure generated here must write to `results/figures/`** — don't leave figures living inside the notebook only.
- **Reference files by relative path from repo root** (e.g. `data/processed/sensor_readings.csv`), not by absolute path — keeps the notebook portable across machines.

## Status (Apr 20, 2026)

Notebook 01 (data exploration):

- reproducible replacement for the older static `docs/dataset_visualization.png` smoke test
- reads tracked processed CSVs under `data/processed/`
- writes exploratory outputs under `results/metrics/` and `results/figures/`

Notebook 02 (Experiment 1 — MCP overhead):

- preflight checks Cells A / B / C under `benchmarks/cell_<X>_*/`
- reads the full `summary.json` schema (latency p50/p95, tool error count, MCP latency, tool call counts) plus `meta.json` profiling linkage fields (`profiling_dir`, `profiling_artifact`, `profiling_summary`) added by `#27`
- computes MCP overhead decomposition (B−A, B−C, C−A) at both p50 and p95
- exports `notebook02_cell_availability.csv`, `notebook02_latency_summary.csv`, `notebook02_mcp_overhead.csv`, and `notebook02_latency_comparison.png`
- graceful degradation: skips aggregation / plots when any cell is missing captures, but always writes the availability CSV

Notebook 03 (Experiment 2 — orchestration comparison):

- preflight checks Cells B / Y / Z under `benchmarks/cell_<X>_*/`
- reads per-scenario JSONs for the `success` / `failed_steps` / `history` / `answer` shape that `scripts/run_experiment.sh` + the AOB PE client and the repo-local PE-Self-Ask / Verified-PE runners produce
- catches JSON error-payload masking by scanning `history[*].response.error` in addition to `step.success=False` (per Codex's 2026-04-20 finding)
- computes success rate, mean failed steps, mean history length, mean tool-error count, recovery rate, and (when `results/metrics/scenario_scores.jsonl` is populated per `#17`) judge pass rate per orchestration
- exports `notebook03_cell_availability.csv`, `notebook03_orchestration_comparison.csv`, `notebook03_failure_breakdown.csv`, and `notebook03_orchestration_comparison.png`

Notebook 04 is still pending — it will consume `results/figures/` outputs from 02 and 03 to produce paper-ready PDFs.

## Known cleanup

- Two parallel config sets exist in `configs/` after the Apr 20 rebase:
  - `configs/aat_{direct,mcp_baseline,mcp_optimized}.env` (from Aaron's `#25` scaffold on `91cb21e`)
  - `configs/experiment1/exp1_cell_{A,B,C}_*.env` + `configs/experiment2/exp2_cell_{B,Y,Z}_*.env` (from Alex's `8fce22a` pre-rebase scaffold)

  They target the same benchmark directories (`cell_A_direct`, `cell_B_mcp_baseline`, ...), so the notebooks key off those dirs and are agnostic to which config was used. But the duplication should be reconciled — likely by dropping one set — before the first live Cell A/B/C runs to avoid teammate confusion about which config to `sbatch`.
