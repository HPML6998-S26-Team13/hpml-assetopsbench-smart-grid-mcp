#!/bin/bash
# One-time setup for vLLM + Llama-3.1-8B-Instruct on Insomnia.
# The team operates out of a single shared checkout in edu scratch:
#     /insomnia001/depts/edu/users/team13/hpml-assetopsbench-smart-grid-mcp
# Only (re)run this script after coordinating with the team — the venv it
# creates is shared across everyone, and wiping it mid-job breaks in-flight work.
#
# Prerequisites:
#   - SSH access to insomnia.rcs.columbia.edu working
#   - You're in the team checkout under /insomnia001/depts/edu/users/team13/...
#   - HuggingFace token with Llama access (https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct)
#
# Usage:
#   cd /insomnia001/depts/edu/users/team13/hpml-assetopsbench-smart-grid-mcp
#   bash scripts/setup_insomnia.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$REPO_ROOT/.venv-insomnia"
MODEL_DIR="$REPO_ROOT/models"
MODEL_NAME="meta-llama/Llama-3.1-8B-Instruct"
MODEL_REVISION="${MODEL_REVISION:-}"

echo "=== Insomnia Environment Setup ==="
echo "Repo root: $REPO_ROOT"
echo "Model: $MODEL_NAME @ $MODEL_REVISION"

for cmd in python3 uv; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "ERROR: required command not found: $cmd" >&2
        exit 1
    fi
done

if [ -z "${HF_TOKEN:-}" ]; then
    echo "ERROR: HF_TOKEN must be exported before running this script." >&2
    echo "Accept the Llama license at https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct and then rerun with HF_TOKEN set." >&2
    exit 1
fi

if [ -z "$MODEL_REVISION" ]; then
    echo "ERROR: MODEL_REVISION must be set to an explicit HuggingFace tag or commit SHA before setup." >&2
    echo "Example: export MODEL_REVISION=4e38f6d" >&2
    exit 1
fi

# --- Step 1: Create Python venv ---
if [ ! -d "$VENV_DIR" ]; then
    echo ""
    echo "[1/4] Creating Python virtual environment..."
    uv venv "$VENV_DIR" --python 3.11
else
    echo "[1/4] Virtual environment already exists at $VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

# --- Step 2: Install dependencies ---
echo ""
echo "[2/4] Installing pinned dependencies from requirements-insomnia.txt..."
uv pip install --python "$VENV_DIR/bin/python" -r "$REPO_ROOT/requirements-insomnia.txt"

echo ""
echo "Installed versions:"
python3 -c "import torch; print(f'  torch: {torch.__version__}')"
python3 -c "import vllm; print(f'  vllm:  {vllm.__version__}')"
python3 -c "import transformers; print(f'  transformers: {transformers.__version__}')"

# --- Step 3: HuggingFace login ---
echo ""
echo "[3/4] HuggingFace login (needed for gated Llama model)..."
huggingface-cli login --token "$HF_TOKEN"

# --- Step 4: Download model ---
echo ""
echo "[4/4] Downloading $MODEL_NAME @ $MODEL_REVISION (~16 GB)..."
echo "  This may take a while on the first run."
mkdir -p "$MODEL_DIR"
huggingface-cli download "$MODEL_NAME" \
    --revision "$MODEL_REVISION" \
    --local-dir "$MODEL_DIR/Llama-3.1-8B-Instruct"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Model downloaded to: $MODEL_DIR/Llama-3.1-8B-Instruct"
echo "Virtual env at:      $VENV_DIR"
echo "Pinned stack file:   requirements-insomnia.txt"
echo ""
echo "Next step: submit the vLLM serving job:"
echo "  sbatch scripts/vllm_serve.sh"
