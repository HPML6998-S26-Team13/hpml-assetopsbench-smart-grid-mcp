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

echo "sample_nvidia_smi: writing to $OUTPUT (interval=${INTERVAL}s, pid=$$)" >&2

# Write header
nvidia-smi --query-gpu="$FIELDS" --format=csv | head -1 > "$OUTPUT"

# Append rows until signalled
trap 'echo "sample_nvidia_smi: stopping (pid=$$)" >&2; exit 0' INT TERM

while true; do
    nvidia-smi --query-gpu="$FIELDS" --format=csv,noheader >> "$OUTPUT"
    sleep "$INTERVAL"
done
