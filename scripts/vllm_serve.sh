#!/bin/bash
#SBATCH --job-name=vllm-llama8b
#SBATCH --account=edu
#SBATCH --partition=short
#SBATCH --qos=short
#SBATCH --gres=gpu:A6000:1
#SBATCH --mem=64G
#SBATCH --cpus-per-task=4
#SBATCH --time=02:00:00
#SBATCH --output=logs/vllm_%j.out
#
# Launches vLLM serving Llama-3.1-8B-Instruct on a single A6000.
# After the server starts, runs a test prompt and keeps serving until the time limit.
#
# MUST be submitted from the repo root — `#SBATCH --output=logs/...` is
# resolved relative to $SLURM_SUBMIT_DIR, so running `sbatch` from elsewhere
# either writes logs to a surprising location or fails with "no such file".
# If you need to submit from a different directory, add
# `--chdir=/path/to/repo` to the sbatch invocation.
#
# Usage (with BEGIN/END/FAIL email notifications):
#   cd /insomnia001/depts/edu/users/team13/hpml-assetopsbench-smart-grid-mcp
#   sbatch --mail-type=BEGIN,END,FAIL --mail-user=<UNI>@columbia.edu scripts/vllm_serve.sh
#
# Or without notifications:
#   sbatch scripts/vllm_serve.sh
#
# Tip: export MAIL_USER=<UNI>@columbia.edu in your shell profile and run:
#   sbatch --mail-type=BEGIN,END,FAIL --mail-user="$MAIL_USER" scripts/vllm_serve.sh
#
# --- Connecting to the running server ---
#
# vLLM binds to 127.0.0.1 on the compute node (not the compute node's external
# interface), so SSH-tunneling from the login node does NOT work. The tested
# path is to attach to the Slurm job from another shell via --overlap:
#
#   srun --jobid=<JOB_ID> --overlap --pty bash
#
# Inside that shell, hit the server via localhost:
#
#   bash scripts/test_inference.sh localhost 8000 models/Llama-3.1-8B-Instruct
#   # or raw curl:
#   curl -s http://127.0.0.1:8000/v1/completions \
#       -H "Content-Type: application/json" \
#       -d '{"model":"models/Llama-3.1-8B-Instruct","prompt":"hello","max_tokens":16}'

set -euo pipefail

REPO_ROOT="${SLURM_SUBMIT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$REPO_ROOT"

# Shared checkout on Insomnia: keep new logs group-writable for teammates.
umask 0002
mkdir -p logs
chmod 2775 logs 2>/dev/null || true
if command -v setfacl >/dev/null 2>&1; then
    setfacl -m g::rwx logs 2>/dev/null || true
    setfacl -d -m g::rwx logs 2>/dev/null || true
fi

if [ ! -f ".venv-insomnia/bin/activate" ]; then
    echo "ERROR: missing .venv-insomnia. Run bash scripts/setup_insomnia.sh first." >&2
    exit 1
fi

STARTUP_TIMEOUT="${STARTUP_TIMEOUT:-900}"
MODEL_PATH="${MODEL_PATH:-models/Llama-3.1-8B-Instruct}"
PORT="${PORT:-8000}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-32768}"

if [ ! -d "$MODEL_PATH" ]; then
    echo "ERROR: missing model directory at $MODEL_PATH" >&2
    echo "Run bash scripts/setup_insomnia.sh first, or set MODEL_PATH to the downloaded checkpoint." >&2
    exit 1
fi

for cmd in curl nvidia-smi python3; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "ERROR: required command not found: $cmd" >&2
        exit 1
    fi
done

VLLM_PID=""
trap 'if [ -n "$VLLM_PID" ]; then kill "$VLLM_PID" 2>/dev/null || true; wait "$VLLM_PID" 2>/dev/null || true; fi' EXIT INT TERM

# --- CUDA setup (don't use module load cuda, it's broken) ---
export PATH=/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:${LD_LIBRARY_PATH:-}

# Cluster-specific env (NCCL overrides for Insomnia Slingshot fabric, etc.)
# shellcheck source=scripts/insomnia_env.sh
source "$(dirname "${BASH_SOURCE[0]}")/insomnia_env.sh"

# --- Activate venv ---
source .venv-insomnia/bin/activate

# cuDNN from pip install
CUDNN_LIB="$(python3 -c 'import nvidia.cudnn; import os; print(os.path.join(os.path.dirname(nvidia.cudnn.__file__), "lib"))' 2>/dev/null || true)"
if [ -n "$CUDNN_LIB" ]; then
    export LD_LIBRARY_PATH="$CUDNN_LIB:$LD_LIBRARY_PATH"
fi

echo "=== vLLM Serving Job ==="
echo "Node:      $(hostname)"
echo "GPU:       $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader)"
echo "Model:     $MODEL_PATH"
echo "Port:      $PORT"
echo "Job ID:    ${SLURM_JOB_ID:-N/A}"
echo "Start:     $(date)"
echo ""

# --- Record baseline GPU state ---
nvidia-smi

# Add vLLM logging
VLLM_STARTUP_LOG="logs/vllm_startup_${SLURM_JOB_ID:-local}.log"

# --- Launch vLLM server in background ---
python3 -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_PATH" \
    --served-model-name "$(basename "${MODEL_PATH%/}")" \
    --host 127.0.0.1 \
    --port "$PORT" \
    --max-model-len "$MAX_MODEL_LEN" \
    --dtype float16 \
    >"$VLLM_STARTUP_LOG" 2>&1 &

VLLM_PID=$!

# --- Wait for server to be ready ---
echo ""
echo "Waiting for vLLM server to start..."
for i in $(seq 1 "$STARTUP_TIMEOUT"); do
    if curl -s http://127.0.0.1:$PORT/health > /dev/null 2>&1; then
        echo "Server ready after ${i}s"
        break
    fi
    if ! kill -0 "$VLLM_PID" 2>/dev/null; then
        echo "ERROR: vLLM process died during startup"
	tail -100 "$VLLM_STARTUP_LOG" || true
        exit 1
    fi
    sleep 1
done

if ! curl -s http://127.0.0.1:$PORT/health > /dev/null 2>&1; then
    echo "ERROR: Server did not start within ${STARTUP_TIMEOUT}s"
    echo "=== Process state ==="
    ps -fp "$VLLM_PID" || true
    echo "=== Port state ==="
    ss -ltnp | grep ":$PORT" || true
    echo "=== Recent vLLM startup log ==="
    tail -100 "$VLLM_STARTUP_LOG" || true
    kill "$VLLM_PID" 2>/dev/null || true
    exit 1
fi

# --- Run test inference ---
echo ""
echo "=== Test Inference ==="
TEST_RESPONSE="$(curl -s http://127.0.0.1:$PORT/v1/completions \
    -H "Content-Type: application/json" \
    -d "{
        \"model\": \"$MODEL_PATH\",
        \"prompt\": \"A power transformer's dissolved gas analysis shows elevated hydrogen and acetylene levels. This pattern indicates\",
        \"max_tokens\": 100,
        \"temperature\": 0.7
    }")"

echo "$TEST_RESPONSE" | python3 -c '
import json
import sys

raw = sys.stdin.read()
if not raw.strip():
    raise SystemExit("ERROR: inference returned an empty response.")

try:
    payload = json.loads(raw)
except json.JSONDecodeError:
    raise SystemExit(f"ERROR: inference returned non-JSON output: {raw[:500]}")

error = payload.get("error")
if error is not None:
    raise SystemExit(f"ERROR: inference returned error payload: {error}")

choices = payload.get("choices") or []
if not choices:
    raise SystemExit("ERROR: inference response had no choices.")

text = (choices[0].get("text") or "").strip()
if not text:
    raise SystemExit("ERROR: inference response had an empty completion.")

print(json.dumps(payload, indent=2))
'

# --- Record GPU utilization after model load ---
echo ""
echo "=== GPU State After Model Load ==="
nvidia-smi

echo ""
echo "=== Server Running ==="
echo "vLLM is serving on localhost:$PORT on compute node $(hostname)"
echo "To run the standalone inference smoke test from another shell, attach to this allocation:"
echo "  srun --jobid ${SLURM_JOB_ID:-<job-id>} --overlap --pty bash"
echo ""
echo "Then, inside that shell, run:"
echo "  bash scripts/test_inference.sh localhost $PORT $MODEL_PATH"
echo ""
echo "Server will run until the SLURM time limit is hit (script default is 2 hours unless overridden at submission). Ctrl+C or scancel ${SLURM_JOB_ID:-<job-id>} to stop."

# --- Keep alive until time limit ---
wait $VLLM_PID
