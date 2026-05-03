# benchmarks/

Raw latency and throughput measurements from end-to-end experiment runs. Each subdirectory holds a distinct experimental condition. The raw outputs here are **not** transformed — use notebooks in `notebooks/` to derive curated metrics and write them to `results/`.

## Structure

```
benchmarks/
├── cell_A_direct/         # direct-tool baseline for Experiment 1
│   ├── config.json        # includes WandB linkage fields from docs/wandb_schema.md
│   ├── raw/
│   │   └── <run-id>/      # run-scoped raw outputs and logs
│   │       ├── *.json     # one file per scenario-trial
│   │       ├── latencies.jsonl
│   │       ├── harness.log
│   │       └── meta.json
│   └── summary.json       # mean, p50, p95, throughput (derived for latest run)
├── cell_B_mcp_baseline/   # shared AaT baseline cell for Experiment 1 and 2
├── cell_C_mcp_optimized/  # optimized MCP path for Experiment 1
├── cell_Y_plan_execute/   # Plan-Execute on MCP baseline (Experiment 2 core)
├── cell_Z_hybrid/         # Cell Z / Verified PE follow-on (legacy dir name kept for compatibility)
    # each cell dir keeps the same config.json / raw/ / summary.json shape
└── gcp_a100_final_20260503/
    ├── logs/              # cohort-level GCP driver logs, manifests, runtime patch, nvidia-smi
    └── summary/           # compact pulled-back A100 matrix and mitigation views
```

## Conventions

- **Raw run layout:** each benchmark run gets its own `raw/<run-id>/` directory so the cell-level `config.json` and `summary.json` can represent the latest reproducible run without clobbering older raw artifacts
- **Canonical WandB schema:** see `docs/wandb_schema.md`
- **Config files** must include the required reproducibility fields from `docs/wandb_schema.md`; do not treat the examples in this README as a complete schema
- **Cell-to-directory mapping:** use the `cell_<ID>_*` top-level directory that matches `experiment_cell`; Cell B is intentionally shared across both experiment families
- **Summary files** are regenerated from `raw/` via a notebook in `notebooks/` — never edit by hand
- **Before committing a benchmark run**, make sure the corresponding config + summary are also committed so the run is reproducible
- **What goes here vs. `results/`:** `benchmarks/` holds the *raw, untransformed* outputs of measurement runs. `results/` holds *curated, publication-ready* metrics derived from those benchmarks. The bridge is notebooks.
- **Cohort-level provenance:** when a cloud batch spans multiple cell
  directories, keep the run directories under their normal cells and preserve
  cohort manifests, driver logs, runtime diffs, and hardware snapshots under a
  cohort directory such as `benchmarks/gcp_a100_final_20260503/`.
- **Raw logs are intentionally unsanitized.** Files such as `harness.log` and
  `vllm.log` preserve the runner's original stdout/stderr, including ANSI
  escape sequences, debug output, and trailing whitespace. Do not use
  repository-wide whitespace checks over committed `benchmarks/*/raw/`
  directories as a merge gate; scope those checks to code/docs, or sanitize a
  separate derived artifact under `results/` when a publication-clean log is
  needed.

## Status (Apr 20, 2026)

The directory is no longer scaffolding-only:

- the first kept proof run now lives under `cell_Y_plan_execute/`, specifically as a WatsonX-hosted 70B / Mac 1-scenario smoke run
- `config.json`, `summary.json`, `meta.json`, `harness.log`, and raw per-run
  JSON outputs are committed for that run
- the committed artifacts back-reference the first real shared WandB run
- the canonical scenario corpus currently contains 10 committed JSON scenarios under `data/scenarios/`
- the committed benchmark layout now includes explicit top-level cell
  directories for Experiment 1 (A / B / C), the existing Plan-Execute proof
  cell (Y), and the optional Cell Z / Verified PE follow-on slot (Z)

What is still missing:

- Experiment 1 raw captures for Cells A / B / C
- profiling-linked artifacts from `#25` / `#27`
- curated derived metrics in `results/`
