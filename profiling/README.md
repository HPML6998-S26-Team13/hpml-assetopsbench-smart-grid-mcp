# profiling/

PyTorch Profiler / NVIDIA Nsight / `nvidia-smi` wrappers and captured traces. Traces are large binary files and are **gitignored by default** (`profiling/traces/` and `*.pt.trace.json` are excluded via `.gitignore`). Only the wrapper scripts and this README are tracked here.

## Structure

```
profiling/
├── traces/                  # GITIGNORED — actual .pt.trace.json / nsys reports / nvidia_smi.csv
├── scripts/                 # wrapper scripts experimenters invoke
│   ├── sample_nvidia_smi.sh        # background GPU utilization sampler (CSV)
│   ├── run_nsight.sh               # `nsys profile` wrapper with stats post-proc
│   ├── run_vllm_torch_profile.sh   # PyTorch Profiler via vLLM's built-in endpoints
│   ├── capture_around.sh           # convenience wrapper: nvidia-smi + optional nsys around any command
│   └── log_profiling_to_wandb.py   # link profiling outputs to the benchmark's WandB run
└── README.md
```

## Conventions

- **Traces are not committed.** They're hundreds of MB each and regenerable from the scripts. Share via team WandB run attachments or upload to a shared drive when needed.
- **Scripts must be reproducible** — they take explicit output paths, not hardcoded filenames, so the same wrapper can be driven from different run contexts (Slurm, interactive, CI).
- **Each profiling run should also log a summary** — the profiling trace answers "where did time go?", the benchmark summary answers "how fast was it overall?". Both are needed for the paper. For benchmark runs this pairs with the canonical `benchmarks/cell_<X>/raw/<run-id>/meta.json` + `latencies.jsonl` emitted by `scripts/run_experiment.sh`.
- **Profiling runs belong on a compute node.** `nvidia-smi` and `nsys` are only available on compute nodes. Never run these from the login node (see `docs/insomnia_runbook.md`).
- **A6000 for development, H100 only for final scaling comparisons.** See `docs/compute_plan.md`.

## Pick the right tool

| Tool | Use when you want | Overhead |
|---|---|---|
| `sample_nvidia_smi.sh` | Coarse GPU util / memory / power over the whole run, plottable timeline | ~0% |
| `run_vllm_torch_profile.sh` | Per-kernel, per-op inside vLLM — where time goes in model forward | ~2-5x slowdown during capture window |
| `run_nsight.sh` | System-level trace: CUDA kernels, CPU threads, cuDNN, NVTX ranges | ~5-10x slowdown |
| `capture_around.sh` | Quick bundle: always captures nvidia-smi, optionally wraps in nsys | Same as underlying tools |

**Rule of thumb:**
- For every benchmark run, set `capture_around.sh` to bundle `nvidia-smi` — near-free insurance.
- For Experiment 1 profiling cells specifically, add `run_vllm_torch_profile.sh` (pinpoints MCP-serialization vs model-forward breakdown).
- Reserve `nsys` for one or two deep-dive runs where you suspect a specific CUDA/cuDNN issue. The trace files are huge and the overhead is non-trivial.

## Usage

### Lightweight: nvidia-smi around a benchmark run

```bash
# Kick off a benchmark in the background
sbatch scripts/run_experiment.sh configs/pe_mcp_baseline.env

# In the same srun allocation OR from a sidecar srun --overlap on the same job,
# background the sampler and stop it when the benchmark finishes
OUT=profiling/traces/$(date +%Y%m%d-%H%M%S)_pe_baseline
mkdir -p "$OUT"
bash profiling/scripts/sample_nvidia_smi.sh "$OUT/nvidia_smi.csv" &
SAMPLER=$!
# ...wait for the benchmark to finish...
kill "$SAMPLER"
```

### Convenience: capture_around.sh

Wraps any command with nvidia-smi capture (and optionally nsys). Output lands
under one directory with a `capture_meta.json` that records host, start/stop
timestamps, the wrapped command, and its exit code.

```bash
# nvidia-smi only
bash profiling/scripts/capture_around.sh profiling/traces/pe_baseline_$(date +%s) \
    -- sbatch --wait scripts/run_experiment.sh configs/pe_mcp_baseline.env

# nvidia-smi + nsys (heavier)
CAPTURE_NSYS=1 bash profiling/scripts/capture_around.sh profiling/traces/pe_baseline_nsys \
    -- sbatch --wait scripts/run_experiment.sh configs/pe_mcp_baseline.env
```

### PyTorch Profiler via vLLM's built-in endpoints

vLLM exposes `/start_profile` and `/stop_profile` HTTP routes that internally
drive `torch.profiler`. They're only available if vLLM was launched with
`VLLM_TORCH_PROFILER_DIR` pointing at a writable directory.

Start vLLM with profiling enabled:

```bash
export VLLM_TORCH_PROFILER_DIR=$PWD/profiling/traces/pt_$(date +%s)
mkdir -p "$VLLM_TORCH_PROFILER_DIR"
# --export=ALL ensures Slurm forwards the env var to the job
sbatch --export=ALL scripts/vllm_serve.sh
```

Then, from the same compute node (via `srun --jobid=<id> --overlap --pty bash`)
or over an SSH tunnel:

```bash
bash profiling/scripts/run_vllm_torch_profile.sh "$VLLM_TORCH_PROFILER_DIR" \
    -- bash scripts/run_experiment.sh configs/pe_mcp_baseline.env
```

The wrapper hits `/start_profile` before the command and `/stop_profile` after.
Open the emitted `pt.trace.json` in `chrome://tracing` or
<https://ui.perfetto.dev>.

### Nsight Systems

```bash
bash profiling/scripts/run_nsight.sh profiling/traces/pe_baseline_nsys \
    -- bash scripts/run_experiment.sh configs/pe_mcp_baseline.env
```

Emits `pe_baseline_nsys.nsys-rep` (binary, open in Nsight Systems GUI locally)
and `pe_baseline_nsys_stats.txt` (plain-text summary from `nsys stats`).

Useful `NSYS_*` overrides:
- `NSYS_TRACE=cuda,nvtx,osrt,cudnn` (default) — trim to just `cuda,nvtx` to reduce file size
- `NSYS_DELAY=30` — skip the first 30 seconds so import-time noise doesn't dominate the trace
- `NSYS_SAMPLE=none` — disable CPU sampling entirely if overhead matters

## Integration with `scripts/run_experiment.sh`

These wrappers are deliberately standalone — they do not modify the benchmark
runner. To produce matched profiling + benchmark artifacts, invoke the runner
under `capture_around.sh` and keep the per-run directory name aligned with
the runner's `RUN_ID`:

```bash
RUN_ID="pe_mcp_baseline_$(date +%s)"
OUT=profiling/traces/$RUN_ID
mkdir -p "$OUT"

# Benchmark writes to benchmarks/cell_Y_plan_execute/raw/<RUN_ID>/
# Profiling writes to profiling/traces/$RUN_ID/
bash profiling/scripts/capture_around.sh "$OUT" \
    -- sbatch --wait scripts/run_experiment.sh configs/pe_mcp_baseline.env
```

The W4 optimization experiments (`docs/execution_plan.md`) will consume these
artifacts via notebooks in `notebooks/` to produce the before/after latency
and utilization comparisons in the paper.

## WandB linkage

The benchmark runner (`scripts/run_experiment.sh`) already writes
`wandb_run_url` into `benchmarks/cell_<X>/raw/<RUN_ID>/{meta,summary,config}.json`
when `ENABLE_WANDB=1`. To link the profiling outputs to the same WandB run,
set `BENCHMARK_RUN_DIR` when invoking `capture_around.sh`:

```bash
RUN_ID="pe_mcp_baseline_$(date +%s)"
BENCH=benchmarks/cell_Y_plan_execute/raw/$RUN_ID
OUT=profiling/traces/$RUN_ID

# Phase 1 — run the benchmark and populate BENCH/{meta,config,summary}.json
sbatch --wait scripts/run_experiment.sh configs/pe_mcp_baseline.env

# Phase 2 — profile a follow-up inference pass and link it to the existing WandB run
BENCHMARK_RUN_DIR=$BENCH bash profiling/scripts/capture_around.sh "$OUT" \
    -- bash scripts/test_inference.sh localhost 8000
```

When `BENCHMARK_RUN_DIR` is set, `capture_around.sh` calls
`profiling/scripts/log_profiling_to_wandb.py` after the command finishes. That
helper:

1. Parses the WandB run id from `wandb_run_url` and resumes the run via
   `wandb.init(id=..., resume="allow")`.
2. Uploads every file under `$OUT_DIR` as a WandB `Artifact` of type
   `profiling` named `profiling-<RUN_ID>`.
3. Parses `nvidia_smi.csv` and writes summary stats onto the same run:
   `profiling/gpu_util_{mean,max}`, `profiling/mem_util_mean`,
   `profiling/gpu_mem_used_mib_{mean,max}`, `profiling/power_draw_w_{mean,max}`,
   `profiling/nvidia_smi_samples`.
4. Stamps `profiling_dir`, `profiling_artifact`, and a `profiling_summary`
   block back into the benchmark `meta.json` so the filesystem record matches
   WandB.

The link step is **non-fatal** — if `wandb` isn't installed, if
`wandb_run_url` is missing (e.g. `ENABLE_WANDB=0`), or if WandB is unreachable,
the profiling artifacts still land on disk and the wrapper returns the target
command's exit code normally.

If you want to skip the WandB step for a local run:

```bash
# Either don't set BENCHMARK_RUN_DIR, or force offline mode
WANDB_MODE=offline BENCHMARK_RUN_DIR=$BENCH \
    bash profiling/scripts/capture_around.sh "$OUT" -- <cmd>
```

## Status (Apr 14, 2026)

- `sample_nvidia_smi.sh`, `run_nsight.sh`, `run_vllm_torch_profile.sh`, `capture_around.sh` landed Apr 14.
- First profiling runs against the Plan-Execute smoke (`benchmarks/cell_Y_plan_execute/raw/...`) scheduled for W3 once the shared vLLM endpoint stabilizes on Insomnia.
- Analysis notebooks (`notebooks/02_mcp_latency.ipynb`, etc.) owned by Alex; will consume `benchmarks/cell_<X>/raw/<run-id>/latencies.jsonl` + `profiling/traces/<run-id>/nvidia_smi.csv`.
