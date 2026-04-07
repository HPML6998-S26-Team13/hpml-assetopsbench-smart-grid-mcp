# notebooks/

Jupyter notebooks for exploratory analysis and figure generation. Notebooks are the **bridge** between raw measurements in `benchmarks/` and curated results in `results/`: they read from `benchmarks/`, transform, and write to `results/metrics/` and `results/figures/`.

## Planned notebooks

```
notebooks/
├── 01_data_exploration.ipynb         # EDA on processed Kaggle CSVs (data/processed/)
├── 02_latency_analysis.ipynb         # benchmarks/baseline vs benchmarks/optimized comparison
├── 03_orchestration_comparison.ipynb # AaT vs PE (vs Hybrid if Dhaval greenlights)
└── 04_figure_generation.ipynb        # produces publication-ready PDFs in results/figures/
```

## Conventions

- **Number notebooks** by analysis order — `01_` comes before `02_` etc. so the pipeline reads top-down.
- **Don't commit rendered cell outputs.** `.ipynb_checkpoints/` is gitignored, but cell outputs still land in the notebook JSON. Run `jupyter nbconvert --clear-output --inplace <notebook>.ipynb` before `git add`.
- **Pin versions** — record the Python + package versions used in a markdown cell at the top of each notebook. Future you will thank present you.
- **Every figure generated here must write to `results/figures/`** — don't leave figures living inside the notebook only.
- **Reference files by relative path from repo root** (e.g. `data/processed/sensor_readings.csv`), not by absolute path — keeps the notebook portable across machines.

## Status (Apr 7, 2026)

Scaffolding only. First notebook (`01_data_exploration.ipynb`) will land once someone generalizes the `docs/dataset_visualization.png` smoke test into a committed, reproducible notebook.
