# profiling/

PyTorch Profiler and NVIDIA Nsight traces, plus the wrapper scripts that produce them. Traces are large binary files and are **gitignored** by default (see `.gitignore` — `profiling/traces/` is excluded). Only the scripts and configs are tracked here.

## Structure

```
profiling/
├── traces/                  # GITIGNORED — actual .pt.trace.json / nsight reports
│   └── (not in git)
├── scripts/                 # wrapper scripts for running profiling sessions
│   └── run_profile.sh
└── README.md
```

## Conventions

- **Traces are not committed.** They're hundreds of MB each and regenerable from the scripts. Share via team WandB run attachments or upload to a shared drive when needed.
- **Scripts must be reproducible** — they should take a config file (or CLI args) pointing to a specific benchmark run in `benchmarks/`, not hardcode paths.
- **Each profiling run should also log a summary to `benchmarks/`** — the profiling trace answers "where did time go?", the benchmark summary answers "how fast was it overall?". Both are needed for the paper.
- **Profiling runs belong on Insomnia** — A6000 nodes are fine for most runs; H100 only for final comparisons due to the 2-hour session cap on H100 nodes.

## Status (Apr 7, 2026)

Scaffolding only. First profiling scripts will land in W3 (Apr 14-20) once Aaron's Insomnia/vLLM environment is up and the first baseline trajectory has run through MCP successfully.
