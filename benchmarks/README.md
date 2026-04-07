# benchmarks/

Raw latency and throughput measurements from end-to-end experiment runs. Each subdirectory holds a distinct experimental condition. The raw outputs here are **not** transformed — use notebooks in `notebooks/` to derive curated metrics and write them to `results/`.

## Structure

```
benchmarks/
├── baseline/              # pre-optimization runs (direct Python, MCP baseline)
│   ├── config.json        # model, scenario set, hardware, date, git SHA
│   ├── raw/               # one file per trial (CSV or JSONL)
│   │   └── 2026-04-14_llama8b_mcp_run01.csv
│   └── summary.json       # mean, p50, p95, throughput (derived)
└── optimized/             # post-optimization runs
    ├── int8/              # INT8 quantization
    ├── kv_cache/          # KV-cache tuning
    └── batched/           # batched tool-call scheduling
    # each with the same config.json / raw/ / summary.json shape
```

## Conventions

- **File naming:** `<date>_<model>_<harness>_run<NN>.csv` (e.g. `2026-04-14_llama8b_mcp_run01.csv`)
- **Config files** must include: model ID, scenario set hash, GPU/host, git SHA of the code used to run, WandB run URL
- **Summary files** are regenerated from `raw/` via a notebook in `notebooks/` — never edit by hand
- **Before committing a benchmark run**, make sure the corresponding config + summary are also committed so the run is reproducible
- **What goes here vs. `results/`:** `benchmarks/` holds the *raw, untransformed* outputs of measurement runs. `results/` holds *curated, publication-ready* metrics derived from those benchmarks. The bridge is notebooks.

## Status (Apr 7, 2026)

Scaffolding only. First baseline runs scheduled for W2 (Apr 7-13) after Akshat's eval harness lands and Aaron's Insomnia/vLLM environment comes up.
