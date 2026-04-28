#!/bin/bash
#SBATCH --job-name=lane2-int8-smoke
#SBATCH --account=edu
#SBATCH --partition=short
#SBATCH --qos=short
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --cpus-per-task=8
#SBATCH --time=01:00:00
#SBATCH --output=logs/lane2_int8_smoke_%j.out
#
# Lane 2 / #29 INT8 quantization startup + reachability smoke.
# Validates that vLLM 0.19.0 can serve a CompressedTensors INT8 (W8A8) variant
# of Llama-3.1-8B-Instruct and that the served model is reachable + responds
# to a one-shot completion. NOT a full benchmark — just startup + /v1/models
# + one /v1/completions round-trip.
#
# Status: deferred per docs/lane2_int8_kv_status.md. Run this only after team
# decision to revive INT8 for Cell C v2 / a model-scaling cell.
#
# Prerequisites (one-time):
#   1. HuggingFace gating approval for the INT8 checkpoint (typically
#      RedHatAI/Meta-Llama-3.1-8B-Instruct-quantized.w8a8 or equivalent).
#   2. HF_TOKEN exported in the team .env (or in this shell).
#   3. ~16 GB free in models/ for the INT8 checkpoint (separate from the
#      existing FP16 checkpoint).
#
# Usage:
#   sbatch --mail-type=BEGIN,END,FAIL --mail-user=$USER@columbia.edu \
#       scripts/test_int8_smoke.sh
#
# Override the model + revision via env if you want to try a different INT8 build:
#   INT8_MODEL_REPO=other/llama-int8-repo \
#   INT8_MODEL_REVISION=<sha> \
#       sbatch ... scripts/test_int8_smoke.sh

set -euo pipefail

REPO_ROOT="${SLURM_SUBMIT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$REPO_ROOT"
umask 0002
mkdir -p logs

JOB="${SLURM_JOB_ID:?expected to be running inside a Slurm job}"

INT8_MODEL_REPO="${INT8_MODEL_REPO:-RedHatAI/Meta-Llama-3.1-8B-Instruct-quantized.w8a8}"
INT8_MODEL_REVISION="${INT8_MODEL_REVISION:-main}"
INT8_LOCAL_DIR="${INT8_LOCAL_DIR:-models/Llama-3.1-8B-Instruct-int8}"
PORT="${PORT:-8001}"  # Different from default 8000 so doesn't collide with a live vLLM

OUT_DIR="benchmarks/lane2/int8_smoke/${JOB}"
mkdir -p "$OUT_DIR"

echo "=== Lane 2 / #29 INT8 Startup + Reachability Smoke ==="
echo "Node:        $(hostname)"
echo "Slurm job:   $JOB"
echo "INT8 model:  $INT8_MODEL_REPO @ $INT8_MODEL_REVISION"
echo "Local dir:   $INT8_LOCAL_DIR"
echo "Port:        $PORT"
echo "Out dir:     $OUT_DIR"
echo "Started:     $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# CUDA setup (don't use module load cuda, broken on Insomnia)
export PATH=/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:${LD_LIBRARY_PATH:-}

# Activate the team-shared venv
source .venv-insomnia/bin/activate

# Source the repo-root .env (if present) so HF_TOKEN / WANDB_API_KEY land in
# the environment without the caller having to remember to export them. The
# main runner (scripts/run_experiment.sh) does this; this standalone smoke
# previously didn't, which made the "HF_TOKEN can live in the team .env"
# usage doc misleading.
if [ -f "$REPO_ROOT/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$REPO_ROOT/.env"
    set +a
fi

# Step 1: download INT8 checkpoint if not already present
if [ ! -d "$INT8_LOCAL_DIR" ] || [ -z "$(ls -A "$INT8_LOCAL_DIR" 2>/dev/null)" ]; then
    echo "--- Downloading $INT8_MODEL_REPO @ $INT8_MODEL_REVISION ---"
    if [ -z "${HF_TOKEN:-}" ]; then
        echo "ERROR: HF_TOKEN not set. Either add HF_TOKEN=... to the repo-root .env or export it before sbatch." >&2
        exit 1
    fi
    mkdir -p "$INT8_LOCAL_DIR"
    .venv-insomnia/bin/python -m huggingface_hub.commands.huggingface_cli \
        download "$INT8_MODEL_REPO" \
        --revision "$INT8_MODEL_REVISION" \
        --local-dir "$INT8_LOCAL_DIR" \
        --token "$HF_TOKEN"
else
    echo "--- INT8 checkpoint already present at $INT8_LOCAL_DIR ---"
fi

# Step 2: launch vLLM with --quantization compressed-tensors
echo ""
echo "--- Starting vLLM with --quantization compressed-tensors ---"
VLLM_LOG="$OUT_DIR/vllm.log"

setsid python3 -u -m vllm.entrypoints.openai.api_server \
    --model "$INT8_LOCAL_DIR" \
    --served-model-name "Llama-3.1-8B-Instruct-int8" \
    --host 127.0.0.1 \
    --port "$PORT" \
    --max-model-len 8192 \
    --quantization compressed-tensors \
    >"$VLLM_LOG" 2>&1 &
VLLM_PID=$!
# `setsid` puts the leader and all its children in a new process group whose
# pgid equals the leader's PID. Killing the pgid (-PID) reaps vLLM's worker
# processes too; killing only the leader leaves workers pinned to the GPU
# until Slurm hard-kills the job at the --time= boundary. Mirrors the cleanup
# pattern in scripts/run_experiment.sh:698-710.
VLLM_PGID="$VLLM_PID"
cleanup_vllm() {
    if [ -n "${VLLM_PGID:-}" ] && kill -0 -- "-$VLLM_PGID" 2>/dev/null; then
        kill -TERM -- "-$VLLM_PGID" 2>/dev/null || true
        sleep 2
        kill -KILL -- "-$VLLM_PGID" 2>/dev/null || true
        wait "$VLLM_PID" 2>/dev/null || true
    fi
}
trap cleanup_vllm EXIT

# Step 3: wait for /health
echo "--- Waiting for /health ---"
for i in $(seq 1 600); do
    if curl -s "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then
        echo "    ready after ${i}s"
        break
    fi
    if ! kill -0 "$VLLM_PID" 2>/dev/null; then
        echo "ERROR: vLLM died during startup. Last 50 lines of vllm.log:" >&2
        tail -50 "$VLLM_LOG" >&2
        exit 1
    fi
    sleep 1
done

if ! curl -s "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then
    echo "ERROR: vLLM did not become ready within 600s" >&2
    tail -50 "$VLLM_LOG" >&2
    exit 1
fi

# Step 4: verify /v1/models lists the INT8 served name. Fail closed: use
# `--fail-with-body` so curl exits non-zero on HTTP 4xx/5xx instead of
# silently writing the OpenAI error payload to disk and continuing to
# "smoke complete". (curl rejects `-f` and `--fail-with-body` together
# as mutually exclusive; we want the body-preserving form.) Then assert
# that the served name is actually present in the response — vLLM
# happily lists the path basename if the --served-model-name flag is
# misread.
echo ""
echo "--- /v1/models ---"
if ! curl -sS --fail-with-body "http://127.0.0.1:$PORT/v1/models" \
        -o "$OUT_DIR/models.json"; then
    echo "ERROR: /v1/models returned non-200" >&2
    cat "$OUT_DIR/models.json" >&2 || true
    exit 1
fi
cat "$OUT_DIR/models.json"
echo ""
python3 - "$OUT_DIR/models.json" <<'PY' || exit 1
import json, sys
data = json.loads(open(sys.argv[1]).read())
ids = [m.get("id") for m in data.get("data", [])]
expected = "Llama-3.1-8B-Instruct-int8"
if expected not in ids:
    print(f"ERROR: served-model-name '{expected}' not in /v1/models list: {ids}", file=sys.stderr)
    sys.exit(1)
print(f"OK: /v1/models contains '{expected}'")
PY

# Step 5: one-shot completion smoke. Same fail-closed treatment: curl errors
# out on HTTP 4xx, then we assert no top-level `error` and a non-empty
# `choices[0].text`. Without these checks an OpenAI-compatible error
# (model-name typo, context-window exceeded, etc.) would still end with
# `=== INT8 smoke complete ===` and a meta.json claiming success.
echo ""
echo "--- Test completion ---"
TEST_PROMPT="A power transformer with elevated H2 and C2H2 in DGA indicates"
if ! curl -sS --fail-with-body "http://127.0.0.1:$PORT/v1/completions" \
        -H "Content-Type: application/json" \
        -d "{\"model\":\"Llama-3.1-8B-Instruct-int8\",\"prompt\":\"$TEST_PROMPT\",\"max_tokens\":80,\"temperature\":0.1}" \
        -o "$OUT_DIR/completion.json"; then
    echo "ERROR: /v1/completions returned non-200" >&2
    cat "$OUT_DIR/completion.json" >&2 || true
    exit 1
fi
cat "$OUT_DIR/completion.json"
echo ""
python3 - "$OUT_DIR/completion.json" <<'PY' || exit 1
import json, sys
data = json.loads(open(sys.argv[1]).read())
if "error" in data:
    print(f"ERROR: completion returned error payload: {data['error']}", file=sys.stderr)
    sys.exit(1)
choices = data.get("choices", [])
if not choices:
    print(f"ERROR: completion returned empty choices array", file=sys.stderr)
    sys.exit(1)
text = choices[0].get("text", "")
if not text.strip():
    print(f"ERROR: completion choices[0].text is empty / whitespace", file=sys.stderr)
    sys.exit(1)
print(f"OK: completion returned {len(text)} chars of non-empty text")
PY

# Step 6: GPU memory snapshot (proves INT8 actually reduced memory vs FP16)
echo ""
echo "--- nvidia-smi snapshot ---"
# Filter to the GPU Slurm allocated. nvidia-smi does NOT honor CUDA_VISIBLE_DEVICES
# on its own, so on multi-GPU nodes a bare query returns all GPUs and the
# memory line for the wrong device.
nvidia-smi --id="${CUDA_VISIBLE_DEVICES:-0}" \
    --query-gpu=name,memory.used,memory.free,memory.total --format=csv \
    | tee "$OUT_DIR/nvidia_smi.csv"

# Step 7: write meta summary
echo ""
python3 -c "
import json, pathlib, datetime
meta = {
    'slurm_job_id': '$JOB',
    'int8_model_repo': '$INT8_MODEL_REPO',
    'int8_model_revision': '$INT8_MODEL_REVISION',
    'int8_local_dir': '$INT8_LOCAL_DIR',
    'vllm_port': $PORT,
    'started_at': datetime.datetime.utcnow().isoformat() + 'Z',
    'served_model_name': 'Llama-3.1-8B-Instruct-int8',
    'quantization_flag': 'compressed-tensors',
    'vllm_log': '$VLLM_LOG',
    'completion_path': '$OUT_DIR/completion.json',
    'nvidia_smi_path': '$OUT_DIR/nvidia_smi.csv',
}
pathlib.Path('$OUT_DIR/meta.json').write_text(json.dumps(meta, indent=2) + '\n')
print('meta.json written to $OUT_DIR')
"

echo ""
echo "=== INT8 smoke complete ==="
echo "Outputs in $OUT_DIR/"
echo "Update docs/lane2_int8_kv_status.md with the result."
echo "Finished: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# vLLM auto-stops on exit via the trap
