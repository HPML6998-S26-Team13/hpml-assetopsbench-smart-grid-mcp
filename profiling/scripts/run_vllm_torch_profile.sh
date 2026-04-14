#!/bin/bash
# PyTorch Profiler wrapper for vLLM-backed benchmark runs.
#
# vLLM ships with built-in torch.profiler support that activates when the env
# var VLLM_TORCH_PROFILER_DIR points at a writable directory. When set, vLLM
# exposes /start_profile and /stop_profile HTTP endpoints on the serve process
# and writes Chrome-trace-compatible JSON files into the dir.
#
# This script:
#   1. Prepares the profiler output dir
#   2. Launches vLLM with the env var set (reuses scripts/vllm_serve.sh logic
#      via re-export — the serve script itself already inherits the environment)
#   3. Waits for the server to become ready
#   4. Hits /start_profile, runs the target command, hits /stop_profile
#   5. Returns the exit code of the target command
#
# Usage:
#   bash profiling/scripts/run_vllm_torch_profile.sh <output_dir> \
#       -- <target command that drives inference>
#
# Example: profile the smoke chat prompt end-to-end:
#   bash profiling/scripts/run_vllm_torch_profile.sh profiling/traces/smoke \
#       -- curl -s http://127.0.0.1:8000/v1/chat/completions \
#            -H 'Content-Type: application/json' \
#            -d @/tmp/chat.json
#
# IMPORTANT — ordering:
#
#   This wrapper assumes a vLLM server is ALREADY running in a separate
#   Slurm allocation (or srun --pty shell) with VLLM_TORCH_PROFILER_DIR
#   exported when the server was started. If vLLM wasn't started with the
#   env var set, /start_profile returns an error and this script aborts.
#
#   To start vLLM with profiling enabled:
#     export VLLM_TORCH_PROFILER_DIR=/path/to/profiling/traces/<runid>
#     sbatch --export=ALL scripts/vllm_serve.sh
#
# Output:
#   $OUTPUT_DIR/pt.trace.json (Chrome trace, viewable in chrome://tracing
#                              or https://ui.perfetto.dev)
#   $OUTPUT_DIR/profile_meta.json (runid, timestamps, target command)

set -euo pipefail

OUTPUT_DIR="${1:?Usage: $0 <output_dir> -- <command> [args...]}"
shift

if [ "${1:-}" != "--" ]; then
    echo "ERROR: expected -- between output dir and command." >&2
    echo "Usage: $0 <output_dir> -- <command> [args...]" >&2
    exit 1
fi
shift

if [ "$#" -lt 1 ]; then
    echo "ERROR: no command given after --." >&2
    exit 1
fi

VLLM_HOST="${VLLM_HOST:-127.0.0.1}"
VLLM_PORT="${VLLM_PORT:-8000}"
BASE_URL="http://$VLLM_HOST:$VLLM_PORT"

mkdir -p "$OUTPUT_DIR"

# Confirm vLLM is reachable and has profiling endpoints
if ! curl -s "$BASE_URL/health" > /dev/null 2>&1; then
    echo "ERROR: vLLM not reachable at $BASE_URL/health" >&2
    echo "       Start vLLM with VLLM_TORCH_PROFILER_DIR set before running this wrapper." >&2
    exit 1
fi

echo "run_vllm_torch_profile: starting profiler via $BASE_URL/start_profile" >&2
START_RESP="$(curl -s -o /tmp/start_profile.out -w '%{http_code}' -X POST "$BASE_URL/start_profile" || true)"
if [ "$START_RESP" != "200" ]; then
    echo "ERROR: /start_profile returned HTTP $START_RESP" >&2
    echo "Response body:" >&2
    cat /tmp/start_profile.out >&2 || true
    echo "" >&2
    echo "Most common cause: vLLM was not started with VLLM_TORCH_PROFILER_DIR set." >&2
    exit 1
fi

START_TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "run_vllm_torch_profile: running target command" >&2
echo "  cmd: $*" >&2

set +e
"$@"
CMD_RC=$?
set -e

STOP_TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo "run_vllm_torch_profile: stopping profiler" >&2
STOP_RESP="$(curl -s -o /tmp/stop_profile.out -w '%{http_code}' -X POST "$BASE_URL/stop_profile" || true)"
if [ "$STOP_RESP" != "200" ]; then
    echo "WARNING: /stop_profile returned HTTP $STOP_RESP (target rc=$CMD_RC)" >&2
    cat /tmp/stop_profile.out >&2 || true
fi

# Write meta alongside the trace so downstream analysis has context
META_FILE="$OUTPUT_DIR/profile_meta.json"
python3 - "$META_FILE" "$START_TS" "$STOP_TS" "$CMD_RC" "$@" <<'PY'
import json
import sys

meta_path = sys.argv[1]
start_ts = sys.argv[2]
stop_ts = sys.argv[3]
cmd_rc = int(sys.argv[4])
cmd = sys.argv[5:]

meta = {
    "start_ts": start_ts,
    "stop_ts": stop_ts,
    "target_command": cmd,
    "target_exit_code": cmd_rc,
    "notes": "Chrome trace written by vLLM into the directory pointed at by "
             "VLLM_TORCH_PROFILER_DIR. Open with chrome://tracing or "
             "https://ui.perfetto.dev.",
}
with open(meta_path, "w") as f:
    json.dump(meta, f, indent=2)
PY

echo "run_vllm_torch_profile: done. Target rc=$CMD_RC. Meta: $META_FILE" >&2
exit "$CMD_RC"
