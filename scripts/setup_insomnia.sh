#!/bin/bash
# One-time setup for vLLM + Llama-3.1-8B-Instruct on Insomnia.
#
# The team operates out of a single shared checkout in edu scratch:
#     /insomnia001/depts/edu/users/team13/hpml-assetopsbench-smart-grid-mcp
# Only (re)run this script after coordinating with the team — the venv it
# creates is shared across everyone, and wiping it mid-job breaks in-flight
# work.
#
# --- FIRST-TIME CHECKLIST (do these in order; only the last step is this script) ---
#
#   1. Browser-approve access to the gated Llama 3.1 model:
#          https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct
#      Meta's auto-approval is typically instant. Check status at
#      https://huggingface.co/settings/gated-repos . Until approved, every
#      `hf download` will fail with a 401.
#
#   2. Create a HF access token (Read scope only) at
#          https://huggingface.co/settings/tokens
#      and export it in your shell:
#          export HF_TOKEN=hf_yourtokenhere
#
#   3. SSH into Insomnia and cd to the shared team checkout:
#          cd /insomnia001/depts/edu/users/team13/hpml-assetopsbench-smart-grid-mcp
#
#   4. Run this script.
#
# --- SETUP_MODE env var ---
#
#   SETUP_MODE=all     (default) venv + model
#   SETUP_MODE=venv    venv only; skip model download (use if the shared venv
#                      is broken but the model is already on disk)
#   SETUP_MODE=model   model only; skip venv (use if the model dir was wiped
#                      or you want a specific revision without touching the venv)
#
# --- MODEL_REVISION env var ---
#
#   Leave unset to pull `main` (the current default HF tag). For
#   reproducibility in benchmark runs, pin to the resolved commit SHA, e.g.:
#       export MODEL_REVISION=0e9e39f249a16976918f6564b8830bc894c89659
#   The script prints the resolved SHA after the download completes so you
#   can capture it for the next invocation. See
#   docs/governance/model_registry.yaml for the current repo-level model
#   contract around this pin.
#
# Usage:
#   cd /insomnia001/depts/edu/users/team13/hpml-assetopsbench-smart-grid-mcp
#   export HF_TOKEN=hf_...
#   bash scripts/setup_insomnia.sh
#
# See also: docs/insomnia_runbook.md (cluster gotchas), docs/runbook.md
# (reproducibility), docs/governance/model_registry.yaml (current model/runtime
# contract), and issue #111 (why this script is shaped like this).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$REPO_ROOT/.venv-insomnia"
MODEL_DIR="$REPO_ROOT/models"
MODEL_NAME="meta-llama/Llama-3.1-8B-Instruct"
MODEL_REVISION="${MODEL_REVISION:-main}"
SETUP_MODE="${SETUP_MODE:-all}"

case "$SETUP_MODE" in
    all|venv|model) ;;
    *)
        echo "ERROR: SETUP_MODE=$SETUP_MODE (expected all|venv|model)" >&2
        exit 1
        ;;
esac

do_venv=0
do_model=0
case "$SETUP_MODE" in
    all)   do_venv=1; do_model=1 ;;
    venv)  do_venv=1 ;;
    model) do_model=1 ;;
esac

echo "=== Insomnia Environment Setup ==="
echo "Repo root:  $REPO_ROOT"
echo "Mode:       $SETUP_MODE"
echo "Model:      $MODEL_NAME @ $MODEL_REVISION"

for cmd in python3 uv; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "ERROR: required command not found: $cmd" >&2
        exit 1
    fi
done

if [ "$do_model" = "1" ] && [ -z "${HF_TOKEN:-}" ]; then
    echo "ERROR: HF_TOKEN must be exported for model download." >&2
    echo "Accept the Llama license at https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct" >&2
    echo "and create a Read-scope token at https://huggingface.co/settings/tokens" >&2
    exit 1
fi

# --- Step 1: Create Python venv -----------------------------------------
if [ "$do_venv" = "1" ]; then
    if [ ! -d "$VENV_DIR" ]; then
        echo ""
        echo "[1] Creating Python 3.11 virtual environment with uv..."
        uv venv "$VENV_DIR" --python 3.11
    else
        echo "[1] Virtual environment already exists at $VENV_DIR"
    fi

    # --- Step 2: Install dependencies ---
    echo ""
    echo "[2] Installing pinned dependencies from requirements-insomnia.txt..."
    uv pip install --python "$VENV_DIR/bin/python" -r "$REPO_ROOT/requirements-insomnia.txt"

    # Metadata-only version check (does NOT import torch / vllm — those imports
    # are heavy enough to draw a warning email from RCS about login-node abuse;
    # see docs/insomnia_runbook.md §"Login node etiquette").
    echo ""
    echo "Installed versions (from package metadata; no heavy imports):"
    "$VENV_DIR/bin/python3" - <<'PY'
from importlib.metadata import PackageNotFoundError, version

for pkg in ("torch", "vllm", "transformers", "huggingface-hub", "nvidia-cudnn-cu12"):
    try:
        print(f"  {pkg:20s}  {version(pkg)}")
    except PackageNotFoundError:
        print(f"  {pkg:20s}  NOT INSTALLED")
PY
else
    echo "[1/2] Skipped venv creation (SETUP_MODE=$SETUP_MODE)."
fi

# --- Step 3: HuggingFace login + download -------------------------------
if [ "$do_model" = "1" ]; then
    # Prefer venv python if available so we pick up the pinned hf CLI,
    # otherwise fall back to the system python3 + user-site install.
    if [ -x "$VENV_DIR/bin/python3" ]; then
        PYTHON_BIN="$VENV_DIR/bin/python3"
    else
        PYTHON_BIN="python3"
    fi

    echo ""
    echo "[3] HuggingFace auth (needed for the gated Llama model)..."
    # `hf auth login` is the canonical command in huggingface-hub 0.30+;
    # `huggingface-cli login` is a thin backward-compat shim that still works
    # but emits a deprecation warning.
    "$PYTHON_BIN" -m huggingface_hub.commands.huggingface_cli auth login \
        --token "$HF_TOKEN"

    echo ""
    echo "[4] Downloading $MODEL_NAME @ $MODEL_REVISION (~16 GB)..."
    echo "    This may take 10-30 minutes on the first run."
    mkdir -p "$MODEL_DIR"
    "$PYTHON_BIN" -m huggingface_hub.commands.huggingface_cli download \
        "$MODEL_NAME" \
        --revision "$MODEL_REVISION" \
        --local-dir "$MODEL_DIR/Llama-3.1-8B-Instruct"

    # Report the resolved commit SHA so reproducibility captures can pin it.
    echo ""
    echo "Resolved revision for reproducibility:"
    "$PYTHON_BIN" - "$MODEL_NAME" "$MODEL_REVISION" <<'PY'
import sys
from huggingface_hub import HfApi

repo_id, revision = sys.argv[1], sys.argv[2]
info = HfApi().model_info(repo_id, revision=revision)
print(f"  repo:     {repo_id}")
print(f"  revision: {info.sha}  (requested: {revision})")
print(f"  pin with: export MODEL_REVISION={info.sha}")
PY
else
    echo "[3/4] Skipped model download (SETUP_MODE=$SETUP_MODE)."
fi

echo ""
echo "=== Setup Complete ==="
echo "Venv:        $VENV_DIR"
echo "Model dir:   $MODEL_DIR/Llama-3.1-8B-Instruct"
echo "Pinned deps: requirements-insomnia.txt"
echo ""
echo "Next steps:"
echo "  - Submit the vLLM serving job from this directory:"
echo "      sbatch --mail-type=BEGIN,END,FAIL --mail-user=\$MAIL_USER scripts/vllm_serve.sh"
echo "  - Or run a benchmark cell:"
echo "      sbatch scripts/run_experiment.sh configs/example_baseline.env"
