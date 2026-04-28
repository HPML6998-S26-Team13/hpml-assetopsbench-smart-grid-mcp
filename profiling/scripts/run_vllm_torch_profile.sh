#!/bin/bash
# PyTorch Profiler wrapper for vLLM-backed benchmark runs.
#
# vLLM ships with built-in torch.profiler support that activates when the
# server is launched with --profiler-config (vLLM >= 0.19.0; the older
# VLLM_TORCH_PROFILER_DIR env-var path was removed). When the flag is set,
# vLLM exposes /start_profile and /stop_profile HTTP endpoints on the serve
# process and writes Chrome-trace-compatible JSON files into the configured
# torch_profiler_dir.
#
# This wrapper:
#   1. Confirms the already-running vLLM server is reachable
#   2. Hits /start_profile, runs the target command, hits /stop_profile
#   3. Writes profile_meta.json alongside the trace
#   4. Returns the exit code of the target command
#
# It does NOT launch vLLM. The canonical capture route is the benchmark
# wrapper (TORCH_PROFILE=1 bash scripts/run_experiment.sh <config>), which
# constructs the --profiler-config flag automatically. Use this script only
# for ad-hoc / debugging captures against a manually-launched vLLM serve.
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
#   Slurm allocation (or srun --pty shell) and was launched with
#   --profiler-config pointing at a writable absolute path. If vLLM wasn't
#   started with the flag, /start_profile returns an error and this script
#   aborts.
#
#   To start vLLM with profiling enabled (manual recipe):
#     TRACE_DIR="$PWD/profiling/traces/<runid>_torch"
#     mkdir -p "$TRACE_DIR"
#     python -u -m vllm.entrypoints.openai.api_server \
#         --model models/Llama-3.1-8B-Instruct \
#         --served-model-name Llama-3.1-8B-Instruct \
#         --port 8000 --max-model-len 32768 --dtype float16 \
#         --enable-auto-tool-choice --tool-call-parser llama3_json \
#         --profiler-config "{\"profiler\":\"torch\",\"torch_profiler_dir\":\"$TRACE_DIR\"}"
#
#   Or, more typically, use the benchmark wrapper:
#     TORCH_PROFILE=1 bash scripts/run_experiment.sh <config>
#   which handles the flag construction in run_experiment.sh:783-785.
#
# Output:
#   $OUTPUT_DIR/*.pt.trace.json.gz (Chrome trace; vLLM 0.19 emits gzipped form.
#                                   Open via https://ui.perfetto.dev directly,
#                                   or `gunzip -k <file>.pt.trace.json.gz` and
#                                   load the resulting .pt.trace.json in
#                                   chrome://tracing)
#   $OUTPUT_DIR/profile_meta.json  (runid, timestamps, target command)

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
    echo "       Start vLLM with --profiler-config '{\"profiler\":\"torch\",\"torch_profiler_dir\":\"<abs-path>\"}' before running this wrapper." >&2
    exit 1
fi

echo "run_vllm_torch_profile: starting profiler via $BASE_URL/start_profile" >&2
START_RESP="$(curl -s -o /tmp/start_profile.out -w '%{http_code}' -X POST "$BASE_URL/start_profile" || true)"
if [ "$START_RESP" != "200" ]; then
    echo "ERROR: /start_profile returned HTTP $START_RESP" >&2
    echo "Response body:" >&2
    cat /tmp/start_profile.out >&2 || true
    echo "" >&2
    echo "Most common cause: vLLM was not started with --profiler-config (vLLM >= 0.19.0)." >&2
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
    "notes": "Chrome trace written by vLLM into the directory configured via "
             "--profiler-config (vLLM >= 0.19.0). Emitted as gzipped "
             "*.pt.trace.json.gz. Upload the .gz directly to "
             "https://ui.perfetto.dev (handles gzip transparently), or "
             "`gunzip -k <file>.pt.trace.json.gz` first and load the resulting "
             ".pt.trace.json in chrome://tracing.",
}
with open(meta_path, "w") as f:
    json.dump(meta, f, indent=2)
PY

echo "run_vllm_torch_profile: done. Target rc=$CMD_RC. Meta: $META_FILE" >&2
exit "$CMD_RC"
