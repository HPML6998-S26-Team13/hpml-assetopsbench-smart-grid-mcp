#!/bin/bash
# Replay scenario prompts from a completed benchmark run against the current
# vLLM endpoint. Used for Phase 2 of the Experiment 1 profiling capture:
# runs one pass of each unique scenario so the vLLM torch profiler captures
# representative model-forward cost without the full 3-trial benchmark overhead.
#
# IMPORTANT: vLLM must already be running (LITELLM_BASE_URL set or default
# http://127.0.0.1:8000/v1 reachable). This script does not start or stop vLLM.
# In normal use it is called from run_experiment.sh after TORCH_PROFILE=1 runs,
# while vLLM is still alive. See scripts/run_experiment.sh for integration and
# profiling/scripts/run_vllm_torch_profile.sh for the wrapper that brackets the
# torch profiler start/stop around this script.
#
# Usage:
#   bash scripts/replay_scenarios.sh <bench_run_dir> [mcp_mode]
#
# Arguments:
#   bench_run_dir   Path to benchmarks/cell_X/raw/<run-id>/
#                   Must contain latencies.jsonl (written by run_experiment.sh).
#   mcp_mode        direct | baseline  (default: direct)
#                   Passed to aat_runner.py --mcp-mode.
#
# Environment (all optional — inherit from the parent run_experiment.sh env):
#   LITELLM_BASE_URL                 vLLM endpoint base URL (default http://127.0.0.1:8000/v1)
#   LITELLM_API_KEY                  dummy key for local vLLM (default "dummy-vllm-not-checked")
#   MODEL_ID                         e.g. openai/Llama-3.1-8B-Instruct
#   AAT_OPENAI_AGENTS_VERSION        pinned version (default 0.14.5)
#   AAT_MCP_VERSION                  pinned version (default 1.27.0)
#   AAT_LITELLM_VERSION              pinned version (default 1.81.13)
#   AAT_PARALLEL_TOOL_CALLS          false (default)
#   AAT_MCP_SERVER_PYTHON            path to Python for MCP servers (baseline mode)
#   AAT_MCP_SERVER_LAUNCH_MODE       uv | python (default: uv)
#   HARNESS_VERBOSE                  1 to enable aat_runner verbose output (default 0)
#   SERVER_IOT_PATH / SERVER_FMSR_PATH / SERVER_TSFM_PATH / SERVER_WO_PATH
#                                    MCP server paths (baseline mode only)
#
# Output:
#   <bench_run_dir>/replay/<scenario_basename>_replay.json  per-scenario output
#   <bench_run_dir>/replay/replay_meta.json                 replay run metadata

set -euo pipefail

BENCH_DIR="${1:?Usage: $0 <bench_run_dir> [mcp_mode]}"
MCP_MODE="${2:-direct}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

MODEL_ID="${MODEL_ID:-openai/Llama-3.1-8B-Instruct}"
AAT_OPENAI_AGENTS_VERSION="${AAT_OPENAI_AGENTS_VERSION:-0.14.5}"
AAT_MCP_VERSION="${AAT_MCP_VERSION:-1.27.0}"
AAT_LITELLM_VERSION="${AAT_LITELLM_VERSION:-1.81.13}"
AAT_PARALLEL_TOOL_CALLS="${AAT_PARALLEL_TOOL_CALLS:-false}"
HARNESS_VERBOSE="${HARNESS_VERBOSE:-0}"

LITELLM_BASE_URL="${LITELLM_BASE_URL:-http://127.0.0.1:8000/v1}"
export LITELLM_BASE_URL
export LITELLM_API_KEY="${LITELLM_API_KEY:-dummy-vllm-not-checked}"

REPLAY_DIR="$BENCH_DIR/replay"
mkdir -p "$REPLAY_DIR"

LATENCY_FILE="$BENCH_DIR/latencies.jsonl"
if [ ! -f "$LATENCY_FILE" ]; then
    echo "replay_scenarios: ERROR — latencies.jsonl not found in $BENCH_DIR" >&2
    exit 1
fi

# Extract unique scenario file paths in the order they first appeared
SCENARIO_FILES="$(python3 - "$LATENCY_FILE" <<'PY'
import json, sys
seen, out = set(), []
for line in open(sys.argv[1], encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    sf = json.loads(line).get("scenario_file", "")
    if sf and sf not in seen:
        seen.add(sf)
        out.append(sf)
for sf in out:
    print(sf)
PY
)"

if [ -z "$SCENARIO_FILES" ]; then
    echo "replay_scenarios: ERROR — no scenario_file entries in $LATENCY_FILE" >&2
    exit 1
fi

SCENARIO_COUNT="$(echo "$SCENARIO_FILES" | wc -l | tr -d ' ')"
echo "replay_scenarios: replaying $SCENARIO_COUNT unique scenario(s) from $BENCH_DIR"
echo "replay_scenarios: mcp_mode=$MCP_MODE  model=$MODEL_ID"
echo "replay_scenarios: output=$REPLAY_DIR"

# Confirm vLLM is up before starting any trial
VLLM_HOST_PORT="${LITELLM_BASE_URL%/v1}"
if ! curl -sf "${VLLM_HOST_PORT}/health" >/dev/null 2>&1; then
    echo "replay_scenarios: ERROR — vLLM not reachable at ${VLLM_HOST_PORT}/health" >&2
    echo "  Start vLLM before calling replay_scenarios.sh." >&2
    exit 1
fi

START_TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
PASS=0
FAIL=0

while IFS= read -r SCENARIO_FILE; do
    [ -z "$SCENARIO_FILE" ] && continue
    SCENARIO_BASENAME="$(basename "$SCENARIO_FILE" .json)"
    PROMPT="$(python3 - "$REPO_ROOT/$SCENARIO_FILE" <<'PY'
import json, sys
p = json.load(open(sys.argv[1], encoding="utf-8"))
print(p["text"])
PY
)"
    OUT="$REPLAY_DIR/${SCENARIO_BASENAME}_replay.json"

    CMD=(
        uv run
        --with "openai-agents==$AAT_OPENAI_AGENTS_VERSION"
        --with "mcp[cli]==$AAT_MCP_VERSION"
        --with "litellm==$AAT_LITELLM_VERSION"
        python scripts/aat_runner.py
        --prompt "$PROMPT"
        --output "$OUT"
        --model-id "$MODEL_ID"
        --mcp-mode "$MCP_MODE"
        --parallel-tool-calls "$AAT_PARALLEL_TOOL_CALLS"
    )
    [ "$HARNESS_VERBOSE" = "1" ] && CMD+=(--verbose)

    echo "replay_scenarios: running $SCENARIO_BASENAME ..."
    if (cd "$REPO_ROOT" && "${CMD[@]}" 2>&1); then
        PASS=$((PASS + 1))
        echo "replay_scenarios:   ok  $SCENARIO_BASENAME"
    else
        FAIL=$((FAIL + 1))
        echo "replay_scenarios:   FAIL $SCENARIO_BASENAME (non-fatal; continuing)"
    fi
done <<< "$SCENARIO_FILES"

STOP_TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

python3 - "$REPLAY_DIR/replay_meta.json" \
    "$BENCH_DIR" "$MCP_MODE" "$MODEL_ID" \
    "$START_TS" "$STOP_TS" \
    "$PASS" "$FAIL" "$SCENARIO_COUNT" <<'PY'
import json, os, socket, sys
from pathlib import Path

(
    meta_path,
    bench_dir,
    mcp_mode,
    model_id,
    start_ts,
    stop_ts,
    passed,
    failed,
    total,
) = sys.argv[1:]

meta = {
    "bench_run_dir": bench_dir,
    "mcp_mode": mcp_mode,
    "model_id": model_id,
    "host": socket.gethostname(),
    "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
    "start_ts": start_ts,
    "stop_ts": stop_ts,
    "scenarios_replayed": int(total),
    "scenarios_passed": int(passed),
    "scenarios_failed": int(failed),
}
Path(meta_path).write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
PY

echo "replay_scenarios: done. pass=$PASS fail=$FAIL  meta=$REPLAY_DIR/replay_meta.json"
