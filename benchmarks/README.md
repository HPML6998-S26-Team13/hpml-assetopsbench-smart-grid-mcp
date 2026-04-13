# benchmarks/

Raw latency and throughput measurements from end-to-end experiment runs. Each subdirectory holds a distinct experimental condition. The raw outputs here are **not** transformed — use notebooks in `notebooks/` to derive curated metrics and write them to `results/`.

## Structure

```
benchmarks/
├── cell_A_direct/         # direct-tool baseline, no MCP
│   ├── config.json        # includes WandB linkage fields from docs/wandb_schema.md
│   ├── raw/
│   │   └── <run-id>/      # run-scoped raw outputs and logs
│   │       ├── *.json     # one file per scenario-trial
│   │       ├── latencies.jsonl
│   │       ├── harness.log
│   │       └── meta.json
│   └── summary.json       # mean, p50, p95, throughput (derived for latest run)
├── cell_B_mcp_baseline/   # shared cell between Experiment 1 and Experiment 2
├── cell_C_mcp_optimized/  # optimized MCP path for Experiment 1
├── cell_Y_plan_execute/   # Plan-Execute on MCP baseline
└── cell_Z_hybrid/         # Hybrid on MCP baseline, if mentor-cleared
    # each cell dir keeps the same config.json / raw/ / summary.json shape
```

## Conventions

- **Raw run layout:** each benchmark run gets its own `raw/<run-id>/` directory so the cell-level `config.json` and `summary.json` can represent the latest reproducible run without clobbering older raw artifacts
- **Canonical WandB schema:** see `docs/wandb_schema.md`
- **Config files** must include the required reproducibility fields from `docs/wandb_schema.md`; do not treat the examples in this README as a complete schema
- **Cell-to-directory mapping:** use the `cell_<ID>_*` top-level directory that matches `experiment_cell`; Cell B is intentionally shared across both experiment families
- **Summary files** are regenerated from `raw/` via a notebook in `notebooks/` — never edit by hand
- **Before committing a benchmark run**, make sure the corresponding config + summary are also committed so the run is reproducible
- **What goes here vs. `results/`:** `benchmarks/` holds the *raw, untransformed* outputs of measurement runs. `results/` holds *curated, publication-ready* metrics derived from those benchmarks. The bridge is notebooks.

## Status (Apr 7, 2026)

Scaffolding only. First baseline runs scheduled for W2 (Apr 7-13) after Akshat's eval harness lands and Aaron's Insomnia/vLLM environment comes up.
