#!/bin/bash
#SBATCH --job-name=sgexp1-ab
#SBATCH --account=edu
#SBATCH --partition=short
#SBATCH --qos=short
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --cpus-per-task=8
#SBATCH --time=04:00:00
#SBATCH --output=logs/exp1_ab_%j.out
#
# Experiment 1 Cell A + B full capture — benchmark + nvidia-smi GPU profiling.
# Runs Cell A (direct tools) and Cell B (MCP baseline) sequentially in one
# Slurm allocation so both cells share the same node environment and GPU type.
#
# Phase 1 for each cell: run_experiment.sh handles vLLM lifecycle, the 3-trial
# multi-domain scenario loop, WandB upload, and (when TORCH_PROFILE=1) the
# vLLM torch-profiler replay pass while vLLM is still alive.
#
# Phase 2 for each cell: capture_around.sh wraps the Phase 1 command and
# records a background nvidia-smi CSV timeline, then calls
# log_profiling_to_wandb.py to attach gpu-util / memory stats to the
# benchmark's WandB run.
#
# Usage:
#   sbatch --mail-type=BEGIN,END,FAIL --mail-user=$USER \
#       scripts/run_exp1_ab_capture.sh
#
# After the job completes, find artifacts at:
#   benchmarks/cell_A_direct/raw/<SLURM_JOB_ID>_aat_direct/
#   benchmarks/cell_B_mcp_baseline/raw/<SLURM_JOB_ID>_aat_mcp_baseline/
#   profiling/traces/<SLURM_JOB_ID>_cell_a/        (nvidia_smi.csv, capture_meta.json)
#   profiling/traces/<SLURM_JOB_ID>_cell_b/
#   profiling/traces/<SLURM_JOB_ID>_aat_direct_torch/     (*.pt.trace.json.gz, if profiler ran)
#   profiling/traces/<SLURM_JOB_ID>_aat_mcp_baseline_torch/
#
# To disable the torch-profiler replay for a faster run:
#   TORCH_PROFILE=0 sbatch scripts/run_exp1_ab_capture.sh

set -euo pipefail

REPO_ROOT="${SLURM_SUBMIT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$REPO_ROOT"
umask 0002

mkdir -p logs
chmod 2775 logs 2>/dev/null || true

echo "=== Experiment 1 Cell A + B Capture ==="
echo "Node:        $(hostname)"
echo "Slurm job:   ${SLURM_JOB_ID:-N/A}"
echo "Repo root:   $REPO_ROOT"
echo "Started:     $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# Pre-compute run dirs so we can set BENCHMARK_RUN_DIR before the run starts.
# run_experiment.sh constructs: ${SLURM_JOB_ID:-local-<timestamp>}_<EXPERIMENT_NAME>
# Since we are inside the Slurm job, SLURM_JOB_ID is set.
JOB="${SLURM_JOB_ID:?expected to be running inside a Slurm job}"

CELL_A_RUN_ID="${JOB}_aat_direct"
CELL_B_RUN_ID="${JOB}_aat_mcp_baseline"

CELL_A_BENCH="benchmarks/cell_A_direct/raw/${CELL_A_RUN_ID}"
CELL_B_BENCH="benchmarks/cell_B_mcp_baseline/raw/${CELL_B_RUN_ID}"

CELL_A_PROF="profiling/traces/${JOB}_cell_a"
CELL_B_PROF="profiling/traces/${JOB}_cell_b"

mkdir -p "$CELL_A_PROF" "$CELL_B_PROF"

# ── Cell A ────────────────────────────────────────────────────────────────────

echo "--- Cell A: direct tools (configs/aat_direct.env) ---"
echo "  Benchmark run dir: $CELL_A_BENCH"
echo "  Profiling dir:     $CELL_A_PROF"
echo ""

BENCHMARK_RUN_DIR="$CELL_A_BENCH" \
    bash profiling/scripts/capture_around.sh "$CELL_A_PROF" \
        -- bash scripts/run_experiment.sh configs/aat_direct.env

echo ""
echo "Cell A complete."
echo "  nvidia-smi:  $CELL_A_PROF/nvidia_smi.csv"
echo "  capture meta: $CELL_A_PROF/capture_meta.json"
[ -f "$CELL_A_BENCH/summary.json" ] && \
    python3 -c "import json; s=json.load(open('$CELL_A_BENCH/summary.json')); print(f'  summary: {s[\"scenarios_completed\"]}/{s[\"scenarios_attempted\"]} passed  mean={s[\"latency_seconds_mean\"]:.1f}s')" || true
echo ""

# ── Cell B ────────────────────────────────────────────────────────────────────

echo "--- Cell B: MCP baseline (configs/aat_mcp_baseline.env) ---"
echo "  Benchmark run dir: $CELL_B_BENCH"
echo "  Profiling dir:     $CELL_B_PROF"
echo ""

BENCHMARK_RUN_DIR="$CELL_B_BENCH" \
    bash profiling/scripts/capture_around.sh "$CELL_B_PROF" \
        -- bash scripts/run_experiment.sh configs/aat_mcp_baseline.env

echo ""
echo "Cell B complete."
echo "  nvidia-smi:  $CELL_B_PROF/nvidia_smi.csv"
echo "  capture meta: $CELL_B_PROF/capture_meta.json"
[ -f "$CELL_B_BENCH/summary.json" ] && \
    python3 -c "import json; s=json.load(open('$CELL_B_BENCH/summary.json')); print(f'  summary: {s[\"scenarios_completed\"]}/{s[\"scenarios_attempted\"]} passed  mean={s[\"latency_seconds_mean\"]:.1f}s')" || true
echo ""

# ── Summary ───────────────────────────────────────────────────────────────────

echo "=== Capture complete ==="
echo "Cell A bench: $CELL_A_BENCH"
echo "Cell B bench: $CELL_B_BENCH"
echo "Cell A prof:  $CELL_A_PROF"
echo "Cell B prof:  $CELL_B_PROF"
echo ""
echo "Next steps:"
echo "  1. Check both summary.json files above for pass/fail counts."
echo "  2. Verify WandB runs at https://wandb.ai/assetopsbench-smartgrid/assetopsbench-smartgrid"
echo "  3. Add a docs/validation_log.md entry referencing these run dirs and the WandB run URLs."
echo "  4. Run Notebook 02 parser checks against the latencies.jsonl files:"
echo "       $CELL_A_BENCH/latencies.jsonl"
echo "       $CELL_B_BENCH/latencies.jsonl"
echo "  5. Check torch profiler traces (if TORCH_PROFILE=1 was set in the configs):"
echo "       profiling/traces/${JOB}_aat_direct_torch/"
echo "       profiling/traces/${JOB}_aat_mcp_baseline_torch/"
echo "     vLLM 0.19 emits *.pt.trace.json.gz; open via https://ui.perfetto.dev (handles .gz)"
echo "     or 'gunzip -k <file>.pt.trace.json.gz' first then chrome://tracing"
echo "Finished: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
