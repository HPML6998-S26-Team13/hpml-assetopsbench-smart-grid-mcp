#!/bin/bash
#SBATCH --job-name=vllm-llama8b
#SBATCH --account=edu
#SBATCH --partition=burst
#SBATCH --qos=burst
#SBATCH --gres=gpu:A6000:1
#SBATCH --mem=64G
#SBATCH --cpus-per-task=4
#SBATCH --time=02:00:00
#SBATCH --output=logs/vllm_%j.out
#
# Launches vLLM serving Llama-3.1-8B-Instruct on a single A6000.
# After the server starts, runs a test prompt and keeps serving until the time limit.
#
# Usage:
#   sbatch scripts/vllm_serve.sh
#
# To connect from the login node (after job starts):
#   See the job output for the node hostname, then:
#   curl http://<node>:8000/v1/completions \
#     -H "Content-Type: application/json" \
#     -d '{"model":"models/Llama-3.1-8B-Instruct","prompt":"Hello","max_tokens":50}'

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# --- CUDA setup (don't use module load cuda, it's broken) ---
export PATH=/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:${LD_LIBRARY_PATH:-}

# --- Activate venv ---
source .venv-insomnia/bin/activate

# cuDNN from pip install
CUDNN_LIB="$(python -c 'import nvidia.cudnn; import os; print(os.path.join(os.path.dirname(nvidia.cudnn.__file__), "lib"))' 2>/dev/null || true)"
if [ -n "$CUDNN_LIB" ]; then
    export LD_LIBRARY_PATH="$CUDNN_LIB:$LD_LIBRARY_PATH"
fi

MODEL_PATH="models/Llama-3.1-8B-Instruct"
PORT=8000

echo "=== vLLM Serving Job ==="
echo "Node:      $(hostname)"
echo "GPU:       $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader)"
echo "Model:     $MODEL_PATH"
echo "Port:      $PORT"
echo "Job ID:    $SLURM_JOB_ID"
echo "Start:     $(date)"
echo ""

# --- Record baseline GPU state ---
nvidia-smi

# --- Launch vLLM server in background ---
python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_PATH" \
    --port "$PORT" \
    --max-model-len 8192 \
    --dtype float16 &

VLLM_PID=$!

# --- Wait for server to be ready ---
echo ""
echo "Waiting for vLLM server to start..."
for i in $(seq 1 120); do
    if curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
        echo "Server ready after ${i}s"
        break
    fi
    if ! kill -0 $VLLM_PID 2>/dev/null; then
        echo "ERROR: vLLM process died during startup"
        exit 1
    fi
    sleep 1
done

if ! curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
    echo "ERROR: Server did not start within 120s"
    kill $VLLM_PID 2>/dev/null
    exit 1
fi

# --- Run test inference ---
echo ""
echo "=== Test Inference ==="
curl -s http://localhost:$PORT/v1/completions \
    -H "Content-Type: application/json" \
    -d "{
        \"model\": \"$MODEL_PATH\",
        \"prompt\": \"A power transformer's dissolved gas analysis shows elevated hydrogen and acetylene levels. This pattern indicates\",
        \"max_tokens\": 100,
        \"temperature\": 0.7
    }" | python -m json.tool

# --- Record GPU utilization after model load ---
echo ""
echo "=== GPU State After Model Load ==="
nvidia-smi

echo ""
echo "=== Server Running ==="
echo "vLLM is serving on $(hostname):$PORT"
echo "From the login node, run:"
echo "  curl http://$(hostname):$PORT/v1/completions -H 'Content-Type: application/json' -d '{\"model\":\"$MODEL_PATH\",\"prompt\":\"test\",\"max_tokens\":50}'"
echo ""
echo "Or run the test script:"
echo "  bash scripts/test_inference.sh $(hostname) $PORT"
echo ""
echo "Server will run until SLURM time limit (2 hours). Ctrl+C or scancel $SLURM_JOB_ID to stop."

# --- Keep alive until time limit ---
wait $VLLM_PID
