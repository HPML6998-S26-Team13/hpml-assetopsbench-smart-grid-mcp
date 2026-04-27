#!/bin/bash
#SBATCH --job-name=lane2-kv-smoke
#SBATCH --account=edu
#SBATCH --partition=short
#SBATCH --qos=short
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --cpus-per-task=8
#SBATCH --time=01:00:00
#SBATCH --output=logs/lane2_kv_smoke_%j.out
#
# Lane 2 / #30 KV-cache mini-comparison.
# Compares three KV-cache configurations against the FP16 baseline using the
# canonical SGT-009 multi-domain scenario through the AaT direct path:
#   1. baseline                                             (no KV optimization)
#   2. --enable-prefix-caching                              (chosen for Cell C)
#   3. --enable-prefix-caching --kv-cache-dtype fp8         (originally planned;
#                                                           known to fail under
#                                                           FP16 weights in
#                                                           vLLM 0.19.0 FA3 —
#                                                           see status doc)
# One run per variant; all variants use the same model, scenario, and prompt
# template so latency deltas attribute to KV-cache. The fp8 variant is
# expected to fail at vLLM startup; the summary step degrades gracefully.
#
# Wall-clock ~10-20 min once allocated (3 vLLM startups + 1 trial each).
#
# Usage:
#   sbatch --mail-type=BEGIN,END,FAIL --mail-user=$USER@columbia.edu \
#       scripts/test_kv_cache_smoke.sh
#
# Outputs:
#   benchmarks/cell_A_direct/raw/<JOB>_lane2_kv_<variant>/  (per-variant trial JSON)
#   docs/lane2_int8_kv_status.md  (manual update with the result table after the run)
#
# After completion, summarize with:
#   bash scripts/test_kv_cache_smoke.sh --summarize <JOB>

set -euo pipefail

# Self-summarize mode: bash scripts/test_kv_cache_smoke.sh --summarize <JOB>
if [ "${1:-}" = "--summarize" ]; then
    JOB="${2:?Usage: $0 --summarize <SLURM_JOB_ID>}"
    echo "=== Lane 2 KV-cache mini-comparison summary (job $JOB) ==="
    for variant in baseline prefix prefix_fp8; do
        run_dir="benchmarks/cell_A_direct/raw/${JOB}_lane2_kv_${variant}"
        if [ ! -d "$run_dir" ]; then
            echo "  $variant: NO RUN DIR"
            continue
        fi
        meta="$run_dir/meta.json"
        trials=("$run_dir"/2026-*.json)
        if [ ! -f "${trials[0]:-}" ]; then
            echo "  $variant: no per-trial JSON"
            continue
        fi
        # Wrap the per-variant load/print in try/except so one malformed
        # meta.json or trial JSON (e.g. vLLM startup timeout that produced
        # only a partial run dir) doesn't abort the whole table.
        python3 -c "
import json, sys
variant = '$variant'
try:
    m = json.load(open('$meta'))
    trial = json.load(open('${trials[0]}'))
    print(f'  {variant:12s}  success={trial.get(\"success\")}  '
          f'turns={trial.get(\"turn_count\")}  tools={trial.get(\"tool_call_count\")}  '
          f'duration={trial.get(\"runner_meta\",{}).get(\"duration_seconds\",0):.2f}s')
except (FileNotFoundError, json.JSONDecodeError, KeyError) as exc:
    print(f'  {variant:12s}  meta.json or trial JSON missing/malformed: {exc}')
"
    done
    exit 0
fi

REPO_ROOT="${SLURM_SUBMIT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$REPO_ROOT"
umask 0002
mkdir -p logs

JOB="${SLURM_JOB_ID:?expected to be running inside a Slurm job}"

echo "=== Lane 2 / #30 KV-Cache Mini-Comparison ==="
echo "Node:        $(hostname)"
echo "Slurm job:   $JOB"
echo "Repo root:   $REPO_ROOT"
echo "Started:     $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# Three variants. EXTRA_VLLM_ARGS is the env hook (added in this branch) the
# runner appends to the vLLM CLI.
declare -A VARIANTS=(
    [baseline]=""
    [prefix]="--enable-prefix-caching"
    [prefix_fp8]="--enable-prefix-caching --kv-cache-dtype fp8"
)

# Run order: baseline first (slowest), then prefix, then prefix+fp8.
for variant in baseline prefix prefix_fp8; do
    extra="${VARIANTS[$variant]}"
    echo ""
    echo "--- Variant: $variant ---"
    echo "    EXTRA_VLLM_ARGS=\"$extra\""

    # Wrap the run: a one-off config with a unique EXPERIMENT_NAME so each
    # variant lands in its own run dir under cell_A_direct/raw/.
    EXTRA_VLLM_ARGS="$extra" \
    EXPERIMENT_NAME="lane2_kv_${variant}" \
    SCENARIO_SET_NAME="lane2_kv_smoke" \
    EXPERIMENT_FAMILY="lane2_smoke" \
        bash scripts/run_experiment.sh configs/aat_direct_smoke.env \
            || echo "WARN: variant $variant exited non-zero (continuing)"

    # Brief pause to let vLLM port settle between variants
    sleep 5
done

echo ""
echo "=== All variants attempted ==="
echo "Summarize with:"
echo "  bash scripts/test_kv_cache_smoke.sh --summarize $JOB"
echo "Finished: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
