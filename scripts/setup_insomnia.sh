#!/bin/bash
# One-time setup for vLLM + Llama-3.1-8B-Instruct on Insomnia
# Run this from the repo root on the Insomnia LOGIN NODE.
#
# Prerequisites:
#   - SSH access to insomnia.rcs.columbia.edu working
#   - Repo cloned to ~/hpml-assetopsbench-smart-grid-mcp
#   - HuggingFace token with Llama access (https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct)
#
# Usage:
#   cd ~/hpml-assetopsbench-smart-grid-mcp
#   bash scripts/setup_insomnia.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$REPO_ROOT/.venv-insomnia"
MODEL_DIR="$REPO_ROOT/models"
MODEL_NAME="meta-llama/Llama-3.1-8B-Instruct"

echo "=== Insomnia Environment Setup ==="
echo "Repo root: $REPO_ROOT"

# --- Step 1: Create Python venv ---
if [ ! -d "$VENV_DIR" ]; then
    echo ""
    echo "[1/4] Creating Python virtual environment..."
    python3 -m venv "$VENV_DIR"
else
    echo "[1/4] Virtual environment already exists at $VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

# --- Step 2: Install dependencies ---
echo ""
echo "[2/4] Installing vLLM, torch, transformers..."
pip install --upgrade pip
pip install vllm torch transformers huggingface-hub

# cuDNN for PyTorch (no system cuDNN on Insomnia)
pip install nvidia-cudnn-cu12

echo ""
echo "Installed versions:"
python -c "import torch; print(f'  torch: {torch.__version__}')"
python -c "import vllm; print(f'  vllm:  {vllm.__version__}')"
python -c "import transformers; print(f'  transformers: {transformers.__version__}')"

# --- Step 3: HuggingFace login ---
echo ""
echo "[3/4] HuggingFace login (needed for gated Llama model)..."
if [ -z "${HF_TOKEN:-}" ]; then
    echo "  Set HF_TOKEN env var or run: huggingface-cli login"
    echo "  You must have accepted the Llama 3.1 license at:"
    echo "  https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct"
    huggingface-cli login
else
    huggingface-cli login --token "$HF_TOKEN"
fi

# --- Step 4: Download model ---
echo ""
echo "[4/4] Downloading $MODEL_NAME (~16 GB)..."
echo "  This may take a while on the first run."
mkdir -p "$MODEL_DIR"
huggingface-cli download "$MODEL_NAME" --local-dir "$MODEL_DIR/Llama-3.1-8B-Instruct"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Model downloaded to: $MODEL_DIR/Llama-3.1-8B-Instruct"
echo "Virtual env at:      $VENV_DIR"
echo ""
echo "Next step: submit the vLLM serving job:"
echo "  sbatch scripts/vllm_serve.sh"
