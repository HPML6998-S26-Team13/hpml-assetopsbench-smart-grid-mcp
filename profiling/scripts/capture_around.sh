#!/bin/bash
# Wrap any command with GPU + optional Nsight profiling capture. The scripts/
# peers do the actual work; this is the convenience wrapper experimenters
# invoke from run_experiment.sh configs, sbatch scripts, or ad-hoc sessions.
#
# Always: nvidia-smi background sampler writes a CSV alongside the traces.
# Optional: if CAPTURE_NSYS=1, the whole command is run under `nsys profile`.
#
# Usage:
#   bash profiling/scripts/capture_around.sh <out_dir> -- <command> [args...]
#
# Example:
#   bash profiling/scripts/capture_around.sh profiling/traces/pe_baseline_$(date +%s) \
#       -- sbatch --wait scripts/run_experiment.sh configs/pe_mcp_baseline.env
#
# Environment overrides:
#   CAPTURE_NSYS         (1 to also run under nsys profile, default 0)
#   CAPTURE_INTERVAL     (nvidia-smi poll interval seconds, default 1)
#   BENCHMARK_RUN_DIR    (path to benchmarks/cell_X/raw/<run-id>/; when set
#                         and the run has ENABLE_WANDB=1, upload the profiling
#                         outputs to the benchmark's WandB run as an Artifact
#                         and write gpu-util / memory summary stats to the
#                         run.summary. Non-fatal if WandB isn't available.)
#   WANDB_MODE           (online|offline|disabled; default online)
#
# Output:
#   $OUT_DIR/nvidia_smi.csv
#   $OUT_DIR/nsys.nsys-rep, $OUT_DIR/nsys_stats.txt  (if CAPTURE_NSYS=1)
#   $OUT_DIR/capture_meta.json  (command, host, start/stop timestamps)

set -euo pipefail

OUT_DIR="${1:?Usage: $0 <out_dir> -- <command> [args...]}"
shift

if [ "${1:-}" != "--" ]; then
    echo "ERROR: expected -- between out_dir and command." >&2
    echo "Usage: $0 <out_dir> -- <command> [args...]" >&2
    exit 1
fi
shift

if [ "$#" -lt 1 ]; then
    echo "ERROR: no command given after --." >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$OUT_DIR"

CAPTURE_NSYS="${CAPTURE_NSYS:-0}"
CAPTURE_INTERVAL="${CAPTURE_INTERVAL:-1}"

START_TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# --- Start nvidia-smi background sampler ---
SMI_CSV="$OUT_DIR/nvidia_smi.csv"
bash "$SCRIPT_DIR/sample_nvidia_smi.sh" "$SMI_CSV" "$CAPTURE_INTERVAL" &
SMI_PID=$!
echo "capture_around: nvidia-smi sampler pid=$SMI_PID writing $SMI_CSV" >&2

stop_sampler() {
    if [ -n "${SMI_PID:-}" ] && kill -0 "$SMI_PID" 2>/dev/null; then
        kill "$SMI_PID" 2>/dev/null || true
        wait "$SMI_PID" 2>/dev/null || true
    fi
}
trap stop_sampler EXIT INT TERM

# Tiny delay so the sampler captures pre-run idle state
sleep 1

# --- Run the target (optionally under nsys) ---
set +e
if [ "$CAPTURE_NSYS" = "1" ]; then
    bash "$SCRIPT_DIR/run_nsight.sh" "$OUT_DIR/nsys" -- "$@"
    CMD_RC=$?
else
    "$@"
    CMD_RC=$?
fi
set -e

STOP_TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

stop_sampler
trap - EXIT INT TERM

# --- Write capture meta ---
META_FILE="$OUT_DIR/capture_meta.json"
python3 - "$META_FILE" "$START_TS" "$STOP_TS" "$CMD_RC" "$CAPTURE_NSYS" "$CAPTURE_INTERVAL" "$@" <<'PY'
import json
import os
import socket
import sys

(
    meta_path,
    start_ts,
    stop_ts,
    cmd_rc_s,
    capture_nsys_s,
    capture_interval_s,
    *cmd,
) = sys.argv[1:]

meta = {
    "host": socket.gethostname(),
    "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
    "start_ts": start_ts,
    "stop_ts": stop_ts,
    "target_command": cmd,
    "target_exit_code": int(cmd_rc_s),
    "captures": {
        "nvidia_smi": True,
        "nvidia_smi_interval_seconds": float(capture_interval_s),
        "nsys": capture_nsys_s == "1",
    },
}

with open(meta_path, "w") as f:
    json.dump(meta, f, indent=2)
PY

# --- Optionally link profiling output to the benchmark's WandB run ---
if [ -n "${BENCHMARK_RUN_DIR:-}" ]; then
    if [ ! -d "$BENCHMARK_RUN_DIR" ]; then
        echo "capture_around: BENCHMARK_RUN_DIR=$BENCHMARK_RUN_DIR does not exist; skipping WandB link." >&2
    else
        WANDB_MODE="${WANDB_MODE:-online}"
        echo "capture_around: linking profiling to WandB run in $BENCHMARK_RUN_DIR (mode=$WANDB_MODE)" >&2
        if ! python3 "$SCRIPT_DIR/log_profiling_to_wandb.py" \
                --benchmark-run-dir "$BENCHMARK_RUN_DIR" \
                --profiling-dir "$OUT_DIR" \
                --mode "$WANDB_MODE"; then
            echo "capture_around: WandB link failed (non-fatal; artifacts remain on disk)" >&2
        fi
    fi
fi

echo "capture_around: done. rc=$CMD_RC, out=$OUT_DIR" >&2
exit "$CMD_RC"
