#!/bin/bash
#SBATCH --job-name=smartgrid-exp
#SBATCH --account=edu
#SBATCH --partition=short
#SBATCH --qos=short
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --cpus-per-task=4
#SBATCH --time=02:00:00
#SBATCH --output=logs/exp_%j.out
#
# Generic Slurm experiment template for SmartGridBench benchmark cells.
# Brings up vLLM + (eventually) MCP servers + the AssetOpsBench harness inside
# a single Slurm job, runs every scenario in the config, and writes per-scenario
# trajectories to logs/.
#
# Usage (with BEGIN/END/FAIL email notifications):
#   sbatch --mail-type=BEGIN,END,FAIL --mail-user=<UNI>@columbia.edu \
#       scripts/run_experiment.sh configs/example_baseline.env
#
# Or without notifications:
#   sbatch scripts/run_experiment.sh configs/example_baseline.env
#
# Tip: export MAIL_USER=<UNI>@columbia.edu in your shell profile and run:
#   sbatch --mail-type=BEGIN,END,FAIL --mail-user="$MAIL_USER" \
#       scripts/run_experiment.sh configs/example_baseline.env
#
# The config is a sourceable bash env file. See configs/example_baseline.env
# for the schema and defaults.
#
# Status: SKELETON. The vLLM bring-up + scenario loop work end-to-end against
# the WatsonX path today. Wiring for local-vLLM model IDs, MCP mode switching,
# multi-trial loops, and WandB logging is marked TODO and depends on
# Akshat/Tanisha/Alex finalizing their interfaces.

set -euo pipefail

CONFIG_PATH="${1:?Usage: sbatch $0 <config.env>}"

if [ ! -f "$CONFIG_PATH" ]; then
    echo "ERROR: config not found: $CONFIG_PATH" >&2
    exit 1
fi

# --- Repo root: works for both sbatch and bare bash invocation ---
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# --- Load config (sourced as bash) ---
# shellcheck disable=SC1090
source "$CONFIG_PATH"

# Required config keys (fail loudly if missing)
: "${EXPERIMENT_NAME:?config must set EXPERIMENT_NAME}"
: "${SCENARIOS_GLOB:?config must set SCENARIOS_GLOB (e.g. data/scenarios/iot_*.json)}"
: "${MODEL_ID:?config must set MODEL_ID (e.g. watsonx/meta-llama/llama-3-3-70b-instruct)}"

# Optional config keys with defaults
ORCHESTRATION="${ORCHESTRATION:-plan_execute}"
MCP_MODE="${MCP_MODE:-baseline}"
TRIALS="${TRIALS:-1}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-8192}"
VLLM_PORT="${VLLM_PORT:-8000}"
VLLM_MODEL_PATH="${VLLM_MODEL_PATH:-models/Llama-3.1-8B-Instruct}"
LAUNCH_VLLM="${LAUNCH_VLLM:-1}"
AOB_PATH="${AOB_PATH:-$REPO_ROOT/../AssetOpsBench}"

# --- Run identifiers + paths ---
RUN_ID="${SLURM_JOB_ID:-local-$(date +%Y%m%d-%H%M%S)}_${EXPERIMENT_NAME}"
RUN_DIR="logs/exp_${RUN_ID}"
mkdir -p "$RUN_DIR"

VLLM_LOG="$RUN_DIR/vllm.log"
HARNESS_LOG="$RUN_DIR/harness.log"
META_FILE="$RUN_DIR/meta.json"

echo "=== SmartGridBench Experiment ==="
echo "Run ID:        $RUN_ID"
echo "Config:        $CONFIG_PATH"
echo "Experiment:    $EXPERIMENT_NAME"
echo "Orchestration: $ORCHESTRATION"
echo "MCP mode:      $MCP_MODE"
echo "Model:         $MODEL_ID"
echo "Scenarios:     $SCENARIOS_GLOB"
echo "Trials:        $TRIALS"
echo "Node:          $(hostname)"
echo "Job ID:        ${SLURM_JOB_ID:-N/A}"
echo "Start:         $(date)"
echo "Output dir:    $RUN_DIR"
echo ""

# Write run metadata for downstream analysis (notebooks, WandB import, etc.)
python3 -c "
import json, os, datetime
meta = {
    'run_id': '$RUN_ID',
    'experiment_name': '$EXPERIMENT_NAME',
    'orchestration': '$ORCHESTRATION',
    'mcp_mode': '$MCP_MODE',
    'model_id': '$MODEL_ID',
    'scenarios_glob': '$SCENARIOS_GLOB',
    'trials': $TRIALS,
    'vllm_model_path': '$VLLM_MODEL_PATH',
    'launch_vllm': bool($LAUNCH_VLLM),
    'aob_path': '$AOB_PATH',
    'node': os.uname().nodename,
    'slurm_job_id': os.environ.get('SLURM_JOB_ID'),
    'started_at': datetime.datetime.utcnow().isoformat() + 'Z',
}
with open('$META_FILE', 'w') as f:
    json.dump(meta, f, indent=2)
print(json.dumps(meta, indent=2))
"

# --- CUDA setup (don't use module load cuda, it's broken on Insomnia) ---
export PATH=/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:${LD_LIBRARY_PATH:-}

# --- Activate the team's Insomnia venv ---
# shellcheck disable=SC1091
source .venv-insomnia/bin/activate

# cuDNN from pip install (no system cuDNN on Insomnia)
CUDNN_LIB="$(python -c 'import nvidia.cudnn, os; print(os.path.join(os.path.dirname(nvidia.cudnn.__file__), "lib"))' 2>/dev/null || true)"
if [ -n "$CUDNN_LIB" ]; then
    export LD_LIBRARY_PATH="$CUDNN_LIB:$LD_LIBRARY_PATH"
fi

# --- vLLM bring-up (skip if config sets LAUNCH_VLLM=0, e.g. for WatsonX-only runs) ---
VLLM_PID=""
cleanup() {
    local rc=$?
    if [ -n "$VLLM_PID" ] && kill -0 "$VLLM_PID" 2>/dev/null; then
        echo ""
        echo "=== Cleanup: stopping vLLM (pid $VLLM_PID) ==="
        kill "$VLLM_PID" 2>/dev/null || true
        wait "$VLLM_PID" 2>/dev/null || true
    fi
    # TODO: stop MCP servers here once they're launched as subprocesses
    echo "Run finished at $(date) with exit code $rc"
}
trap cleanup EXIT

if [ "$LAUNCH_VLLM" = "1" ]; then
    echo ""
    echo "=== Launching vLLM ==="
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

    python -u -m vllm.entrypoints.openai.api_server \
        --model "$VLLM_MODEL_PATH" \
        --port "$VLLM_PORT" \
        --max-model-len "$MAX_MODEL_LEN" \
        --dtype float16 \
        > "$VLLM_LOG" 2>&1 &
    VLLM_PID=$!

    echo "vLLM PID: $VLLM_PID"
    echo "Waiting for /health (up to 600s)..."
    for i in $(seq 1 600); do
        if curl -s "http://localhost:$VLLM_PORT/health" > /dev/null 2>&1; then
            echo "  Server ready after ${i}s"
            break
        fi
        if ! kill -0 "$VLLM_PID" 2>/dev/null; then
            echo "ERROR: vLLM process died during startup. Last log lines:" >&2
            tail -50 "$VLLM_LOG" >&2
            exit 1
        fi
        sleep 1
    done

    if ! curl -s "http://localhost:$VLLM_PORT/health" > /dev/null 2>&1; then
        echo "ERROR: vLLM did not become ready within 600s" >&2
        tail -50 "$VLLM_LOG" >&2
        exit 1
    fi

    # Point OpenAI-compatible clients (incl. plan-execute via litellm) at our local vLLM.
    # TODO: confirm with Akshat that the harness's openai/<model> path honors these env vars.
    export OPENAI_API_BASE="http://localhost:$VLLM_PORT/v1"
    export OPENAI_API_KEY="dummy-vllm-not-checked"
fi

# --- TODO: Launch MCP servers based on $MCP_MODE ---
# baseline:  start each MCP server as a long-lived subprocess (Tanisha's hardened servers)
# direct:    skip MCP entirely; harness uses in-process tool calls (existing AssetOpsBench path)
# optimized: same as baseline but with batched/connection-reused config flags
# Depends on Tanisha finalizing the server-launch contract.
case "$MCP_MODE" in
    baseline|optimized)
        echo "TODO: launch MCP servers for mode=$MCP_MODE (waiting on Tanisha's hardened launch contract)"
        ;;
    direct)
        echo "MCP mode=direct: skipping MCP server launch"
        ;;
    *)
        echo "ERROR: unknown MCP_MODE=$MCP_MODE (expected baseline|optimized|direct)" >&2
        exit 1
        ;;
esac

# --- Validate scenarios before running ---
echo ""
echo "=== Validating scenarios ==="
python data/scenarios/validate_scenarios.py || {
    echo "ERROR: scenario validation failed; aborting before harness invocation" >&2
    exit 1
}

# --- Resolve the AssetOpsBench harness ---
if [ ! -f "$AOB_PATH/pyproject.toml" ]; then
    echo "ERROR: AssetOpsBench not found at $AOB_PATH" >&2
    echo "       Set AOB_PATH in the config or clone AssetOpsBench as a sibling of this repo." >&2
    exit 1
fi

# --- Scenario loop ---
echo ""
echo "=== Running scenarios ==="
SCENARIOS=($SCENARIOS_GLOB)
echo "Found ${#SCENARIOS[@]} scenario(s) matching $SCENARIOS_GLOB"

PASS=0
FAIL=0
SCENARIO_INDEX=0

for SCENARIO_FILE in "${SCENARIOS[@]}"; do
    SCENARIO_INDEX=$((SCENARIO_INDEX + 1))
    SCENARIO_BASENAME=$(basename "$SCENARIO_FILE" .json)

    for TRIAL in $(seq 1 "$TRIALS"); do
        TRIAL_ID="${SCENARIO_BASENAME}_t${TRIAL}"
        TRIAL_OUT="$RUN_DIR/${TRIAL_ID}.json"

        echo ""
        echo "[$SCENARIO_INDEX/${#SCENARIOS[@]}] $SCENARIO_BASENAME (trial $TRIAL/$TRIALS)"

        # Extract the prompt text from the scenario JSON
        PROMPT=$(python3 -c "import json,sys; print(json.load(open('$SCENARIO_FILE'))['text'])")

        # Invoke the harness via uv run inside the AssetOpsBench checkout.
        # TODO: --orchestration flag once Alex's AaT/PE/Hybrid wiring lands.
        if (cd "$AOB_PATH" && \
            uv run plan-execute \
                --json \
                --model-id "$MODEL_ID" \
                "$PROMPT" \
                > "$TRIAL_OUT" 2>> "$HARNESS_LOG"); then
            PASS=$((PASS + 1))
            echo "  OK -> $TRIAL_OUT"
        else
            FAIL=$((FAIL + 1))
            echo "  FAIL (see $HARNESS_LOG)"
        fi

        # TODO: log per-trial metrics to WandB (Alex's schema)
    done
done

# --- Summary ---
TOTAL=$((PASS + FAIL))
echo ""
echo "=== Run Summary ==="
echo "Run ID:    $RUN_ID"
echo "Scenarios: ${#SCENARIOS[@]}, Trials: $TRIALS, Total runs: $TOTAL"
echo "Pass:      $PASS"
echo "Fail:      $FAIL"
echo "Outputs:   $RUN_DIR"

# Append final status to meta
python3 -c "
import json
meta = json.load(open('$META_FILE'))
meta['finished_at'] = __import__('datetime').datetime.utcnow().isoformat() + 'Z'
meta['scenario_count'] = ${#SCENARIOS[@]}
meta['trials'] = $TRIALS
meta['total_runs'] = $TOTAL
meta['pass'] = $PASS
meta['fail'] = $FAIL
json.dump(meta, open('$META_FILE', 'w'), indent=2)
"

# Non-zero exit if anything failed, so Slurm marks the job FAILED
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
