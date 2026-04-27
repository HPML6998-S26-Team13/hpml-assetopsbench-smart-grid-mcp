# notebooks/

Jupyter notebooks for exploratory analysis and figure generation. Notebooks are the **bridge** between raw measurements in `benchmarks/` and curated results in `results/`: they read from `benchmarks/`, transform, and write to `results/metrics/` and `results/figures/`.

## Planned notebooks

```
notebooks/
├── 01_data_exploration.ipynb         # EDA on processed Kaggle CSVs (data/processed/)
├── 02_latency_analysis.ipynb         # Experiment 1: Cell A vs B vs C latency / MCP-overhead analysis
├── 03_orchestration_comparison.ipynb # Experiment 2: AaT vs PE (optional Verified PE follow-on)
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
- exports `notebook02_cell_availability.preflight.csv`, `notebook02_cell_b_contract.preflight.csv`, `notebook02_latency_summary.csv`, `notebook02_mcp_overhead.csv`, and `notebook02_latency_comparison.png`
- graceful degradation: degraded / zero-cell reruns deterministically replace
  every output (rather than leaving stale prior-run artifacts) — schema-only
  CSVs carry an explicit `note` column and the figure renders a "zero-cell
  preview" placeholder, so downstream readers can never see a fresh availability
  CSV alongside a stale overhead figure
- as soon as Cell B exists, it also validates the **shared Cell B
  contract** for `#104` / Experiment 2:
  - scenario IDs + trial indices match the downstream join keys
  - latency rows exist in the canonical shape
  - Cell B still advertises `CONTRIBUTING_EXPERIMENTS="exp1_mcp_overhead,exp2_orchestration"`
- partial-readiness mode: when only some of A / B / C are present, the
  notebook still computes pairwise overhead deltas and renders the latency
  figure with hatched placeholder bars for missing cells. With Cells A and B
  today the headline `MCP transport overhead (B − A)` row populates while the
  Cell C overlay waits for `#31`.
- intended usage is phased: preflight as soon as any A / B / C artifacts exist,
  early best-effort analysis on the first complete A / B / C set, and final
  publishable figures after the chosen Cell C optimization stack plus the
  larger scenario corpus are rerun

Notebook 03 (Experiment 2 — orchestration comparison):

- preflight checks Cells B / Y / Z under `benchmarks/cell_<X>_*/`
- reads per-scenario JSONs for the `success` / `failed_steps` / `history` / `answer` shape that `scripts/run_experiment.sh` + the AOB PE client and the repo-local PE-Self-Ask / Verified-PE runners produce
- catches JSON error-payload masking by scanning `history[*].response.error` in addition to `step.success=False` (per Codex's 2026-04-20 finding)
- computes success rate, mean failed steps, mean history length, mean tool-error count, recovery rate, and (when `results/metrics/scenario_scores.jsonl` is populated per `#17`) judge pass rate per orchestration
- exports `notebook03_cell_availability.preflight.csv`, `notebook03_self_ask_run_inventory.preflight.csv`, `notebook03_orchestration_comparison.csv`, `notebook03_failure_breakdown.csv`, and `notebook03_orchestration_comparison.png`
- staged usage:
  - Y / Z can already support a PE-family follow-on comparison and ablation pass
  - the minimum real Experiment 2 comparison is still Cell B vs Y
  - Cell Z is runnable and supported, but remains an optional third-method lane
    rather than the minimum evidence needed to make the AaT vs PE comparison real
- preliminary mode in the orchestration comparison aggregator: when no
  canonical scenario.id propagation exists yet (current AaT runner gap), the
  comparison aggregates on `scenario_file` instead and tags the output with
  `mode=preliminary` so reviewers can spot the difference
- should now also export a PE-family follow-on artifact when Y and Z are both
  present:
  - `notebook03_pe_family_follow_on.csv`
  - `notebook03_pe_family_follow_on.png`
- should now also export a run-centric Self-Ask ablation inventory and, when a
  ready baseline/self-ask pair exists for Y and/or Z, the ablation outputs:
  - `notebook03_self_ask_run_inventory.preflight.csv`
  - `notebook03_self_ask_ablation.csv`
  - `notebook03_self_ask_ablation.png`

Notebook 04 is still pending — it will consume `results/figures/` outputs from 02 and 03 to produce paper-ready PDFs.

## Config note

- Notebook 02 still analyzes the Experiment 1 Cell A / B / C lanes, but the
  canonical execution configs for those live at `configs/aat_*.env` on `main`.
- Notebook 03 uses the extra Experiment 2 templates under `configs/experiment2/`
  for the Y / Z follow-on lanes, including the baseline Self-Ask ablations:
  - `exp2_cell_Y_pe_mcp_baseline.env`
  - `exp2_cell_Y_pe_self_ask_mcp_baseline.env`
  - `exp2_cell_Z_verified_pe_mcp_baseline.env`
  - `exp2_cell_Z_verified_pe_self_ask_mcp_baseline.env`
- Z / Self-Ask follow-ons remain runnable but still need raw artifacts before
  the notebook can produce real comparison plots for those lanes.
