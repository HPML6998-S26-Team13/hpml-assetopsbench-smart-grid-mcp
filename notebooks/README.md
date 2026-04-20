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

Notebook 01 now exists:

- `01_data_exploration.ipynb` is the reproducible replacement for the older
  static `docs/dataset_visualization.png` smoke test
- it reads the tracked processed CSVs under `data/processed/`
- it writes stable exploratory outputs under `results/metrics/` and
  `results/figures/`

Notebook 02 now exists as scaffold:

- it can discover the repo root from a worktree or the main checkout
- it can preflight the expected Cell A / B / C artifact layout under
  `benchmarks/`
- it can export a stable availability snapshot before real latency analysis is
  possible
- it intentionally stops short of claiming Experiment 1 results until those raw
  captures land

Notebook 03 and Notebook 04 are still pending the benchmark / experiment
artifacts they depend on.
