#!/bin/bash
# NVIDIA Nsight Systems wrapper. Runs `nsys profile` around a command and
# writes a .nsys-rep report + a plain-text summary.
#
# Usage:
#   bash profiling/scripts/run_nsight.sh <output_basename> -- <command> [args...]
#
# Examples:
#
#   # Profile a one-shot vLLM completion via the OpenAI-compatible client
#   bash profiling/scripts/run_nsight.sh profiling/traces/vllm_smoke \
#       -- python3 scripts/one_shot_inference.py
#
#   # Profile the benchmark runner end-to-end (heavy, ~10x overhead)
#   bash profiling/scripts/run_nsight.sh profiling/traces/pe_mcp_baseline \
#       -- bash scripts/run_experiment.sh configs/pe_mcp_baseline.env
#
# The `.nsys-rep` report is gitignored (profiling/traces/ is excluded). Open
# it in Nsight Systems GUI locally, or post-process with:
#   nsys stats <output>.nsys-rep --output <output>.txt
#
# This script delegates to `nsys` which ships with the CUDA toolkit on
# Insomnia compute nodes (CUDA 12.9 under /usr/local/cuda). It is NOT
# available on the login node.
#
# Environment overrides:
#   NSYS_TRACE  (activities to capture; default "cuda,nvtx,osrt,cudnn")
#   NSYS_SAMPLE (CPU sampling; default "cpu")
#   NSYS_DELAY  (seconds to delay capture start; default 0 — increase to skip
#                import-time overhead and focus on steady-state)

set -euo pipefail

BASENAME="${1:?Usage: $0 <output_basename> -- <command> [args...]}"
shift

if [ "${1:-}" != "--" ]; then
    echo "ERROR: expected -- between output basename and command." >&2
    echo "Usage: $0 <output_basename> -- <command> [args...]" >&2
    exit 1
fi
shift

if [ "$#" -lt 1 ]; then
    echo "ERROR: no command given after --." >&2
    exit 1
fi

# Make sure nsys is on PATH — add CUDA bin if missing (Insomnia default).
if ! command -v nsys >/dev/null 2>&1; then
    if [ -x "/usr/local/cuda/bin/nsys" ]; then
        export PATH=/usr/local/cuda/bin:$PATH
    else
        echo "ERROR: nsys not found. Make sure you're on a compute node with CUDA on PATH." >&2
        echo "       export PATH=/usr/local/cuda/bin:\$PATH" >&2
        exit 1
    fi
fi

TRACE="${NSYS_TRACE:-cuda,nvtx,osrt,cudnn}"
SAMPLE="${NSYS_SAMPLE:-cpu}"
DELAY="${NSYS_DELAY:-0}"

OUT_DIR="$(dirname "$BASENAME")"
mkdir -p "$OUT_DIR"

REPORT="${BASENAME}.nsys-rep"
STATS="${BASENAME}_stats.txt"

echo "run_nsight: report=$REPORT trace=$TRACE sample=$SAMPLE delay=${DELAY}s" >&2
echo "run_nsight: cmd=$*" >&2

nsys profile \
    --trace="$TRACE" \
    --sample="$SAMPLE" \
    --delay="$DELAY" \
    --output="$BASENAME" \
    --force-overwrite=true \
    "$@"

# Post-process for a human-readable summary alongside the binary report.
echo "run_nsight: generating stats summary -> $STATS" >&2
nsys stats "$REPORT" > "$STATS" 2>&1 || {
    echo "run_nsight: nsys stats failed; keeping binary report only." >&2
}

echo "run_nsight: done. Report: $REPORT" >&2
