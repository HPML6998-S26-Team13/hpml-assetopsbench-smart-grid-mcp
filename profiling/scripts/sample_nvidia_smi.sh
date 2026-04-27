#!/bin/bash
# Lightweight GPU utilization sampler. Polls nvidia-smi once per second and
# writes one CSV row per sample to the output file. Runs in the foreground;
# backgroun it with `&` and kill it when the workload finishes.
#
# Usage:
#   # Foreground, manual stop:
#   bash profiling/scripts/sample_nvidia_smi.sh profiling/traces/my_run_nvidia_smi.csv
#
#   # Background around a benchmark run:
#   OUT=profiling/traces/$(date +%Y%m%d-%H%M%S)_nvidia_smi.csv
#   bash profiling/scripts/sample_nvidia_smi.sh "$OUT" &
#   SAMPLER_PID=$!
#   sbatch --wait scripts/run_experiment.sh configs/example_baseline.env
#   kill "$SAMPLER_PID"
#
# Queryable fields: timestamp, GPU index + name, GPU/memory utilization, memory
# usage, temperature, power draw. Appended in CSV format suitable for pandas:
#   pd.read_csv(path)
#
# Environment overrides:
#   SAMPLE_INTERVAL (seconds between samples, default 1)

set -euo pipefail

OUTPUT="${1:?Usage: $0 <output.csv> [interval_seconds]}"
INTERVAL="${2:-${SAMPLE_INTERVAL:-1}}"

if ! command -v nvidia-smi >/dev/null 2>&1; then
    echo "ERROR: nvidia-smi not found. Run this on a compute node, not the login node." >&2
    exit 1
fi

mkdir -p "$(dirname "$OUTPUT")"

# nvidia-smi --format=csv emits a header on every invocation; we want the
# header once, then only rows. Query once with --format=csv for the header,
# then loop with --format=csv,noheader,nounits.
FIELDS="timestamp,index,name,utilization.gpu,utilization.memory,memory.used,memory.total,temperature.gpu,power.draw"

# Sidecar log for sampler-internal errors (nvidia-smi transient failures,
# permission glitches, etc.). Lives next to the CSV so reviewers can see why
# a row is missing without digging through the slurm .out.
ERR_LOG="${OUTPUT%.csv}.stderr.log"
: >"$ERR_LOG"

echo "sample_nvidia_smi: writing to $OUTPUT (interval=${INTERVAL}s, pid=$$)" >&2
echo "sample_nvidia_smi: stderr -> $ERR_LOG" >&2

# Write header. Header write IS allowed to fail-fast under set -e: if we
# can't even produce the header we want to know immediately.
nvidia-smi --query-gpu="$FIELDS" --format=csv | head -1 > "$OUTPUT"

# Append rows until signalled. Drop `set -e` for the loop so a transient
# nvidia-smi exit (DCGM contention, brief driver reset, momentary CUDA OOM
# during workload startup) does NOT terminate the sampler — we just log the
# failure and try again next tick. Without this, prior runs ended up with
# header-only CSVs because the very first nvidia-smi call after the workload
# started returned non-zero and `set -euo pipefail` killed the loop.
trap 'echo "sample_nvidia_smi: stopping (pid=$$)" >&2; exit 0' INT TERM

set +e
while true; do
    nvidia-smi --query-gpu="$FIELDS" --format=csv,noheader \
        >> "$OUTPUT" 2>>"$ERR_LOG" \
        || echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) WARN: nvidia-smi exit $?" >>"$ERR_LOG"
    sleep "$INTERVAL"
done
