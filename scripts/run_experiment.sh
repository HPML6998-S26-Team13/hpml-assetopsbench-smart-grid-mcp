#!/bin/bash
#SBATCH --job-name=smartgrid-exp
#SBATCH --account=edu
#SBATCH --partition=short
#SBATCH --qos=short
#SBATCH --gres=gpu:A6000:1
#SBATCH --mem=64G
#SBATCH --cpus-per-task=4
#SBATCH --time=02:00:00
#SBATCH --output=logs/exp_%j.out
#
# Generic Slurm experiment runner for SmartGridBench benchmark cells.
# The canonical benchmark-facing orchestration paths are Plan-Execute against
# the team's Smart Grid MCP servers, Agent-as-Tool Cells A/B, and repo-local
# follow-on runners for Self-Ask PE and Verified PE. Runner templates remain
# available as explicit escape hatches for parity or variant smoke checks.
#
# MUST be submitted from the intended repo root or worktree. This script uses
# $SLURM_SUBMIT_DIR as REPO_ROOT; `sbatch --chdir=/path/to/repo` changes the
# job's cwd but does not change $SLURM_SUBMIT_DIR on Insomnia, so it is not a
# safe substitute for `cd /path/to/repo && sbatch ...`.
#
# Usage:
#   sbatch scripts/run_experiment.sh configs/example_baseline.env

set -euo pipefail
shopt -s nullglob

CONFIG_PATH="${1:?Usage: sbatch $0 <config.env>}"
REPO_ROOT="${SLURM_SUBMIT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PROJECT_ROOT="$(cd "$(dirname "$(git -C "$REPO_ROOT" rev-parse --git-common-dir)")" && pwd)"
cd "$REPO_ROOT"

# Shared checkout on Insomnia: keep new logs group-writable for teammates.
umask 0002

if [ ! -f "$CONFIG_PATH" ]; then
  echo "ERROR: config not found: $CONFIG_PATH" >&2
  exit 1
fi

mkdir -p logs
chmod 2775 logs 2>/dev/null || true
if command -v setfacl >/dev/null 2>&1; then
  setfacl -m g::rwx logs 2>/dev/null || true
  setfacl -d -m g::rwx logs 2>/dev/null || true
fi

# Load the repo-root .env when present so local WatsonX/WandB runs can reuse
# the team's canonical ignored credential file without shell-specific export
# setup.
if [ -f "$PROJECT_ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1090
  source "$PROJECT_ROOT/.env"
  set +a
fi

# shellcheck disable=SC1090
source "$CONFIG_PATH"

: "${EXPERIMENT_NAME:?config must set EXPERIMENT_NAME}"
: "${EXPERIMENT_CELL:?config must set EXPERIMENT_CELL}"
: "${EXPERIMENT_FAMILY:?config must set EXPERIMENT_FAMILY}"
: "${SCENARIOS_GLOB:?config must set SCENARIOS_GLOB}"
: "${SCENARIO_SET_NAME:?config must set SCENARIO_SET_NAME}"
: "${MODEL_ID:?config must set MODEL_ID}"

ORCHESTRATION="${ORCHESTRATION:-plan_execute}"
case "$ORCHESTRATION" in
  aat) ORCHESTRATION="agent_as_tool" ;;
  plan-execute) ORCHESTRATION="plan_execute" ;;
  agent-as-tool) ORCHESTRATION="agent_as_tool" ;;
  verified-pe) ORCHESTRATION="verified_pe" ;;
  *) ;;
esac

MCP_MODE="${MCP_MODE:-baseline}"
TRIALS="${TRIALS:-1}"
DRY_RUN="${DRY_RUN:-0}"
HARNESS_VERBOSE="${HARNESS_VERBOSE:-1}"
ENABLE_SMARTGRID_SERVERS="${ENABLE_SMARTGRID_SERVERS:-1}"
ENABLE_WANDB="${ENABLE_WANDB:-0}"
WANDB_PROJECT="${WANDB_PROJECT:-assetopsbench-smartgrid}"
WANDB_ENTITY="${WANDB_ENTITY:-assetopsbench-smartgrid}"
WANDB_MODE="${WANDB_MODE:-online}"
SMARTGRID_RUN_ID="${SMARTGRID_RUN_ID:-}"
SMARTGRID_RESUME="${SMARTGRID_RESUME:-0}"
SMARTGRID_FORCE_RERUN="${SMARTGRID_FORCE_RERUN:-0}"
SMARTGRID_RESUME_REQUIRE_LATENCY="${SMARTGRID_RESUME_REQUIRE_LATENCY:-1}"
SMARTGRID_BATCH_ID="${SMARTGRID_BATCH_ID:-}"
export SMARTGRID_RUN_ID SMARTGRID_RESUME SMARTGRID_FORCE_RERUN
export SMARTGRID_RESUME_REQUIRE_LATENCY SMARTGRID_BATCH_ID
MAX_MODEL_LEN="${MAX_MODEL_LEN:-32768}"
VLLM_PORT="${VLLM_PORT:-8000}"
VLLM_MODEL_PATH="${VLLM_MODEL_PATH:-models/Llama-3.1-8B-Instruct}"
VLLM_SERVED_MODEL_NAME="${VLLM_SERVED_MODEL_NAME:-$(basename "$VLLM_MODEL_PATH")}"
VLLM_DTYPE="${VLLM_DTYPE:-float16}"
EXTRA_VLLM_ARGS="${EXTRA_VLLM_ARGS:-}"
VLLM_GENERATION_CONFIG="${VLLM_GENERATION_CONFIG:-vllm}"
export VLLM_DTYPE EXTRA_VLLM_ARGS VLLM_GENERATION_CONFIG
VLLM_ENABLE_AUTO_TOOL_CHOICE="${VLLM_ENABLE_AUTO_TOOL_CHOICE:-1}"
# Default tool-call parser is model-family-aware. Llama-3.x → llama3_json
# (the team's pinned `Llama-3.1-8B-Instruct`). Other families
# (qwen, mistral, hermes) use distinct parsers; configs targeting those
# models must override `VLLM_TOOL_CALL_PARSER` explicitly. The current
# parser landscape changes with vLLM releases, so we don't try to
# enumerate every family here — just pick a safe default for the model
# the team actually runs and let other configs opt in.
case "${MODEL_ID:-}" in
  *llama-3*|*Llama-3*|*llama3*|*Llama3*) _DEFAULT_TOOL_CALL_PARSER=llama3_json ;;
  *qwen*|*Qwen*) _DEFAULT_TOOL_CALL_PARSER=hermes ;;
  *mistral*|*Mistral*) _DEFAULT_TOOL_CALL_PARSER=mistral ;;
  *) _DEFAULT_TOOL_CALL_PARSER=llama3_json ;;  # safest single fallback for our pinned stack
esac
VLLM_TOOL_CALL_PARSER="${VLLM_TOOL_CALL_PARSER:-$_DEFAULT_TOOL_CALL_PARSER}"
VLLM_STARTUP_TIMEOUT="${VLLM_STARTUP_TIMEOUT:-}"
LAUNCH_VLLM="${LAUNCH_VLLM:-0}"
AOB_PATH="${AOB_PATH:-$PROJECT_ROOT/../AssetOpsBench}"
CONTRIBUTING_EXPERIMENTS="${CONTRIBUTING_EXPERIMENTS:-}"
SCENARIO_DOMAIN_SCOPE="${SCENARIO_DOMAIN_SCOPE:-unknown}"
QUANTIZATION_MODE="${QUANTIZATION_MODE:-none}"
MODEL_PROVIDER="${MODEL_PROVIDER:-unknown}"
SERVING_STACK="${SERVING_STACK:-unknown}"
TEMPERATURE="${TEMPERATURE:-0.0}"
MAX_TOKENS="${MAX_TOKENS:-0}"
export MAX_TOKENS
JUDGE_MODEL="${JUDGE_MODEL:-}"
AAT_RUNNER_TEMPLATE="${AAT_RUNNER_TEMPLATE:-}"
AAT_OPENAI_AGENTS_VERSION="${AAT_OPENAI_AGENTS_VERSION:-0.14.5}"
AAT_MCP_VERSION="${AAT_MCP_VERSION:-1.27.0}"
AAT_LITELLM_VERSION="${AAT_LITELLM_VERSION:-1.81.13}"
AAT_MCP_SERVER_PYTHON="${AAT_MCP_SERVER_PYTHON:-}"
AAT_MCP_SERVER_LAUNCH_MODE="${AAT_MCP_SERVER_LAUNCH_MODE:-python}"
AAT_MCP_CLIENT_TIMEOUT_SECONDS="${AAT_MCP_CLIENT_TIMEOUT_SECONDS:-30}"
AAT_PARALLEL_TOOL_CALLS="${AAT_PARALLEL_TOOL_CALLS:-false}"
TORCH_PROFILE="${TORCH_PROFILE:-0}"
TORCH_PROFILE_DIR="${TORCH_PROFILE_DIR:-}"
HYBRID_RUNNER_TEMPLATE="${HYBRID_RUNNER_TEMPLATE:-}"
VERIFIED_PE_RUNNER_TEMPLATE="${VERIFIED_PE_RUNNER_TEMPLATE:-}"
ENABLE_SELF_ASK="${ENABLE_SELF_ASK:-0}"
PLAN_EXECUTE_REPO_LOCAL="${PLAN_EXECUTE_REPO_LOCAL:-}"
if [ -z "$PLAN_EXECUTE_REPO_LOCAL" ]; then
  if [ "$ORCHESTRATION" = "plan_execute" ] && [ "$ENABLE_SMARTGRID_SERVERS" = "1" ]; then
    PLAN_EXECUTE_REPO_LOCAL=1
  else
    PLAN_EXECUTE_REPO_LOCAL=0
  fi
fi
ENABLE_MISSING_EVIDENCE_GUARD="${ENABLE_MISSING_EVIDENCE_GUARD:-0}"
ENABLE_MISSING_EVIDENCE_REPAIR="${ENABLE_MISSING_EVIDENCE_REPAIR:-0}"
MISSING_EVIDENCE_REPAIR_MAX_ATTEMPTS="${MISSING_EVIDENCE_REPAIR_MAX_ATTEMPTS:-2}"
MISSING_EVIDENCE_REPAIR_MAX_ATTEMPTS_PER_TARGET="${MISSING_EVIDENCE_REPAIR_MAX_ATTEMPTS_PER_TARGET:-1}"
ENABLE_EXPLICIT_FAULT_RISK_ADJUDICATION="${ENABLE_EXPLICIT_FAULT_RISK_ADJUDICATION:-0}"
export ENABLE_MISSING_EVIDENCE_GUARD ENABLE_MISSING_EVIDENCE_REPAIR ENABLE_EXPLICIT_FAULT_RISK_ADJUDICATION
export MISSING_EVIDENCE_REPAIR_MAX_ATTEMPTS MISSING_EVIDENCE_REPAIR_MAX_ATTEMPTS_PER_TARGET

SERVER_IOT_PATH="${SERVER_IOT_PATH:-$REPO_ROOT/mcp_servers/iot_server/server.py}"
SERVER_FMSR_PATH="${SERVER_FMSR_PATH:-$REPO_ROOT/mcp_servers/fmsr_server/server.py}"
SERVER_TSFM_PATH="${SERVER_TSFM_PATH:-$REPO_ROOT/mcp_servers/tsfm_server/server.py}"
SERVER_WO_PATH="${SERVER_WO_PATH:-$REPO_ROOT/mcp_servers/wo_server/server.py}"

SCENARIO_FILES=($SCENARIOS_GLOB)
if [ "${#SCENARIO_FILES[@]}" -eq 0 ]; then
  echo "ERROR: no scenarios matched $SCENARIOS_GLOB" >&2
  exit 1
fi

cell_dir_name() {
  case "$1" in
    A) echo "cell_A_direct" ;;
    B) echo "cell_B_mcp_baseline" ;;
    C) echo "cell_C_mcp_optimized" ;;
    Y) echo "cell_Y_plan_execute" ;;
    Z) echo "cell_Z_hybrid" ;;
    *) echo "cell_${1}" ;;
  esac
}

model_short_name() {
  python3 - "$1" <<'PY'
import re
import sys

model = sys.argv[1]
short = model.split("/")[-1].lower()
short = re.sub(r"[^a-z0-9]+", "-", short).strip("-")
print(short[:40] or "model")
PY
}

SCENARIO_SET_HASH="$(
  python3 - "${SCENARIO_FILES[@]}" <<'PY'
import hashlib
import json
import pathlib
import sys

entries = []
for raw_path in sys.argv[1:]:
    path = pathlib.Path(raw_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    entries.append(f"{path.as_posix()}:{hashlib.sha256(canonical).hexdigest()}")

blob = "\n".join(sorted(entries)).encode("utf-8")
print(hashlib.sha256(blob).hexdigest())
PY
)"

DATE_TAG="$(date +%Y-%m-%d)"
MODEL_SHORT="$(model_short_name "$MODEL_ID")"
RUN_BASENAME="${DATE_TAG}_${EXPERIMENT_CELL}_${MODEL_SHORT}_${ORCHESTRATION}_${MCP_MODE}"
RUN_ID="${SMARTGRID_RUN_ID:-${SLURM_JOB_ID:-local-$(date +%Y%m%d-%H%M%S)}_${EXPERIMENT_NAME}}"
CELL_DIR="benchmarks/$(cell_dir_name "$EXPERIMENT_CELL")"
RAW_DIR="$CELL_DIR/raw"
RUN_DIR="$RAW_DIR/$RUN_ID"
mkdir -p "$RUN_DIR"

CONFIG_FILE="$CELL_DIR/config.json"
SUMMARY_FILE="$CELL_DIR/summary.json"
META_FILE="$RUN_DIR/meta.json"
VLLM_LOG="$RUN_DIR/vllm.log"
HARNESS_LOG="$RUN_DIR/harness.log"
LATENCY_FILE="$RUN_DIR/latencies.jsonl"
RESUME_MANIFEST_FILE="$RUN_DIR/resume_manifest.jsonl"
: >"$HARNESS_LOG"
VLLM_PGID=""

echo "=== SmartGridBench Experiment ==="
echo "Run ID:        $RUN_ID"
echo "Config:        $CONFIG_PATH"
echo "Cell:          $EXPERIMENT_CELL"
echo "Experiment:    $EXPERIMENT_NAME"
echo "Family:        $EXPERIMENT_FAMILY"
echo "Orchestration: $ORCHESTRATION"
echo "MCP mode:      $MCP_MODE"
echo "Model:         $MODEL_ID"
echo "Scenarios:     ${#SCENARIO_FILES[@]} file(s)"
echo "Node:          $(hostname)"
echo "Job ID:        ${SLURM_JOB_ID:-N/A}"
echo "Cell dir:      $CELL_DIR"
echo "Run dir:       $RUN_DIR"
echo "Resume:        $SMARTGRID_RESUME"
echo "Force rerun:   $SMARTGRID_FORCE_RERUN"
echo ""

PYTHON_BIN="python3"
if [ "$LAUNCH_VLLM" != "1" ] && [ -x "$PROJECT_ROOT/.venv/bin/python" ]; then
  PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
fi
AOB_PYTHON="${AOB_PYTHON:-$AOB_PATH/.venv/bin/python}"
if [ ! -x "$AOB_PYTHON" ]; then
  AOB_PYTHON="$PYTHON_BIN"
fi

for cmd in python3 curl uv; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "ERROR: required command not found: $cmd" >&2
    exit 1
  fi
done

# Resolve the GPU model name once at job start so config.json / summary.json
# stamp the actual hardware (e.g. "NVIDIA RTX A6000", "NVIDIA L40S") instead
# of "unknown". nvidia-smi does NOT honor CUDA_VISIBLE_DEVICES on its own, so
# we filter explicitly. Falls back to "unknown" if nvidia-smi is missing
# (login-node / non-GPU runs, dry runs) or the query fails. Caller-provided
# GPU_TYPE wins so smoke / replay paths can override. (#132)
#
# Quirk: nvidia-smi prints diagnostic messages like "No devices were found"
# to STDOUT and exits non-zero, so we must check the exit code rather than
# only redirecting stderr — otherwise an error message lands as the GPU
# name in the JSON.
if [ -z "${GPU_TYPE:-}" ]; then
  if command -v nvidia-smi >/dev/null 2>&1; then
    if _gpu_name="$(nvidia-smi --id="${CUDA_VISIBLE_DEVICES:-0}" \
        --query-gpu=name --format=csv,noheader 2>/dev/null)"; then
      GPU_TYPE="$(printf '%s\n' "$_gpu_name" \
          | head -1 \
          | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    fi
    unset _gpu_name
  fi
  GPU_TYPE="${GPU_TYPE:-unknown}"
fi
export GPU_TYPE
echo "GPU type: $GPU_TYPE"

# Support both WatsonX env spellings across repos/tooling.
if [ -n "${WATSONX_API_KEY:-}" ] && [ -z "${WATSONX_APIKEY:-}" ]; then
  export WATSONX_APIKEY="$WATSONX_API_KEY"
fi
if [ -n "${WATSONX_APIKEY:-}" ] && [ -z "${WATSONX_API_KEY:-}" ]; then
  export WATSONX_API_KEY="$WATSONX_APIKEY"
fi
# Bridge documented WATSONX_* env vars to the WX_* names litellm's newer
# WatsonX provider expects (litellm 1.81.x rejects with
# "Watsonx project_id and space_id not set" otherwise). Subprocess Python
# entry points (generator, AaT runner, judge_trajectory.py) call the same
# alias via scripts/watsonx_env.py; doing it here too keeps inherited
# env consistent for any sub-shell or PE/Verified PE runner that bypasses
# the Python helper. (#177)
if [ -n "${WATSONX_API_KEY:-}" ] && [ -z "${WX_API_KEY:-}" ]; then
  export WX_API_KEY="$WATSONX_API_KEY"
fi
if [ -n "${WATSONX_PROJECT_ID:-}" ] && [ -z "${WX_PROJECT_ID:-}" ]; then
  export WX_PROJECT_ID="$WATSONX_PROJECT_ID"
fi
if [ -n "${WATSONX_URL:-}" ] && [ -z "${WX_URL:-}" ]; then
  export WX_URL="$WATSONX_URL"
fi

if [ ! -f "$AOB_PATH/pyproject.toml" ]; then
  echo "ERROR: AssetOpsBench not found at $AOB_PATH" >&2
  exit 1
fi

"$PYTHON_BIN" data/scenarios/validate_scenarios.py >/dev/null

SERVER_ARGS=()
if [ "$ENABLE_SMARTGRID_SERVERS" = "1" ]; then
  SERVER_ARGS+=(--server "iot=$SERVER_IOT_PATH")
  SERVER_ARGS+=(--server "fmsr=$SERVER_FMSR_PATH")
  SERVER_ARGS+=(--server "tsfm=$SERVER_TSFM_PATH")
  SERVER_ARGS+=(--server "wo=$SERVER_WO_PATH")
fi

if [ "$DRY_RUN" = "1" ]; then
  echo "Dry run enabled. Scenario validation, config writing, and command wiring completed."
  echo "Resolved orchestration: $ORCHESTRATION"
  echo "AssetOpsBench path:     $AOB_PATH"
  printf 'Server args: %s\n' "${SERVER_ARGS[*]}"
  exit 0
fi

"$PYTHON_BIN" - "$CONFIG_FILE" "$SUMMARY_FILE" "$META_FILE" "$CONFIG_PATH" "$RUN_ID" "$WANDB_ENTITY" "$WANDB_PROJECT" "$EXPERIMENT_FAMILY" "$EXPERIMENT_CELL" "$ORCHESTRATION" "$MCP_MODE" "$TRIALS" "${#SCENARIO_FILES[@]}" "$SCENARIO_SET_NAME" "$SCENARIO_SET_HASH" "$SCENARIO_DOMAIN_SCOPE" "$MODEL_ID" "$MODEL_PROVIDER" "$SERVING_STACK" "$QUANTIZATION_MODE" "$MAX_MODEL_LEN" "$TEMPERATURE" "$MAX_TOKENS" "$JUDGE_MODEL" <<'PY'
import importlib.metadata
import json
import os
import pathlib
import re
import subprocess
import sys
from datetime import datetime, timezone

(
    config_path,
    summary_path,
    meta_path,
    benchmark_config_path,
    run_name,
    wandb_entity,
    project_name,
    experiment_family,
    experiment_cell,
    orchestration_mode,
    mcp_mode,
    trial_count,
    scenario_count,
    scenario_set_name,
    scenario_set_hash,
    scenario_domain_scope,
    model_id,
    model_provider,
    serving_stack,
    quantization_mode,
    context_window,
    temperature,
    max_tokens,
    judge_model,
) = sys.argv[1:]

def git_value(args, default="unknown"):
    try:
        return subprocess.check_output(args, text=True).strip() or default
    except Exception:
        return default

def git_dirty():
    try:
        subprocess.check_call(
            ["git", "diff-index", "--quiet", "HEAD", "--"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return True
    except Exception:
        return None
    return False

def package_version(name):
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None

def command_output(args):
    try:
        return subprocess.check_output(
            args,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=10,
        ).strip()
    except Exception:
        return None

def runtime_versions():
    cuda_visible = os.environ.get("CUDA_VISIBLE_DEVICES")
    gpu_id = (cuda_visible or "0").split(",")[0].strip() or "0"
    versions = {
        "vllm_version": package_version("vllm"),
        "torch_version": package_version("torch"),
        "cuda_visible_devices": cuda_visible,
        "nvidia_driver_version": None,
        "cuda_version": None,
        "nvidia_smi_query": None,
    }
    raw = command_output(
        [
            "nvidia-smi",
            f"--id={gpu_id}",
            "--query-gpu=driver_version,cuda_version",
            "--format=csv,noheader",
        ]
    )
    if raw:
        versions["nvidia_smi_query"] = raw
        first_row = raw.splitlines()[0]
        parts = [part.strip() for part in first_row.split(",")]
        if parts:
            versions["nvidia_driver_version"] = parts[0] or None
        if len(parts) > 1:
            versions["cuda_version"] = parts[1] or None
    if versions["nvidia_driver_version"] is None:
        driver = command_output(
            [
                "nvidia-smi",
                f"--id={gpu_id}",
                "--query-gpu=driver_version",
                "--format=csv,noheader",
            ]
        )
        if driver:
            versions["nvidia_driver_version"] = driver.splitlines()[0].strip() or None
    if versions["cuda_version"] is None:
        smi = command_output(["nvidia-smi"])
        if smi:
            match = re.search(r"CUDA Version:\s*([0-9.]+)", smi)
            if match:
                versions["cuda_version"] = match.group(1)
    return versions

payload = {
    "schema_version": "v1",
    "wandb_entity": wandb_entity,
    "project_name": project_name,
    "run_name": run_name,
    "git_sha": git_value(["git", "rev-parse", "HEAD"]),
    "git_branch": git_value(["git", "branch", "--show-current"]),
    "git_dirty": git_dirty(),
    "run_timestamp": datetime.now(timezone.utc).isoformat(),
    "benchmark_config_path": pathlib.Path(benchmark_config_path).as_posix(),
    "benchmark_summary_path": pathlib.Path(summary_path).as_posix(),
    "wandb_run_url": None,
    "experiment_family": experiment_family,
    "contributing_experiments": [],
    "experiment_cell": experiment_cell,
    "orchestration_mode": orchestration_mode,
    "mcp_mode": mcp_mode,
    "trial_count": int(trial_count),
    "scenario_count": int(scenario_count),
    "scenario_set_name": scenario_set_name,
    "scenario_set_hash": scenario_set_hash,
    "scenario_domain_scope": scenario_domain_scope,
    "judge_model": judge_model or None,
    "judge_pass_threshold": None,
    "model_id": model_id,
    "model_provider": model_provider,
    "serving_stack": serving_stack,
    "quantization_mode": quantization_mode,
    "context_window": int(context_window),
    "temperature": float(temperature),
    "max_tokens": int(max_tokens),
    "host_name": os.uname().nodename,
    "compute_env": "insomnia" if "SLURM_JOB_ID" in os.environ else "local",
    "gpu_type": os.environ.get("GPU_TYPE", "unknown"),
    "gpu_count": int(os.environ.get("SLURM_GPUS_ON_NODE", "1") or "1"),
    "runtime_owner": os.environ.get("USER"),
    "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
    "smartgrid_batch_id": os.environ.get("SMARTGRID_BATCH_ID"),
    "smartgrid_resume": os.environ.get("SMARTGRID_RESUME", "0") == "1",
    "smartgrid_force_rerun": os.environ.get("SMARTGRID_FORCE_RERUN", "0") == "1",
    "smartgrid_resume_require_latency": os.environ.get(
        "SMARTGRID_RESUME_REQUIRE_LATENCY",
        "1",
    )
    == "1",
}

if os.environ.get("CONTRIBUTING_EXPERIMENTS"):
    payload["contributing_experiments"] = [
        part.strip() for part in os.environ["CONTRIBUTING_EXPERIMENTS"].split(",") if part.strip()
    ]

if orchestration_mode == "agent_as_tool":
    payload["aat_parallel_tool_calls"] = os.environ.get("AAT_PARALLEL_TOOL_CALLS", "false")
payload["missing_evidence_guard"] = (
    os.environ.get("ENABLE_MISSING_EVIDENCE_GUARD", "0").strip().lower()
    in {"1", "true", "yes", "on"}
)
payload["missing_evidence_repair"] = (
    os.environ.get("ENABLE_MISSING_EVIDENCE_REPAIR", "0").strip().lower()
    in {"1", "true", "yes", "on"}
)
payload["explicit_fault_risk_adjudication"] = (
    os.environ.get("ENABLE_EXPLICIT_FAULT_RISK_ADJUDICATION", "0").strip().lower()
    in {"1", "true", "yes", "on"}
)
payload["missing_evidence_repair_max_attempts"] = int(
    os.environ.get("MISSING_EVIDENCE_REPAIR_MAX_ATTEMPTS", "2")
)
payload["missing_evidence_repair_max_attempts_per_target"] = int(
    os.environ.get("MISSING_EVIDENCE_REPAIR_MAX_ATTEMPTS_PER_TARGET", "1")
)

# Persist EXTRA_VLLM_ARGS into the benchmark config + meta so artifact
# consumers (notebooks, WandB, paper tables) can recover the exact vLLM
# optimization knobs that produced a run without re-reading harness.log.
# Lane 2 / #30 specifically needs this for the prefix-cache / kv-dtype
# distinction in Cell C.
extra_vllm_args = os.environ.get("EXTRA_VLLM_ARGS", "").strip()
payload["vllm_dtype"] = os.environ.get("VLLM_DTYPE", "float16")
payload["vllm_generation_config"] = os.environ.get("VLLM_GENERATION_CONFIG", "vllm")
payload["vllm_extra_args"] = extra_vllm_args
payload["vllm_extra_args_list"] = extra_vllm_args.split() if extra_vllm_args else []
payload["runtime_versions"] = runtime_versions()

pathlib.Path(config_path).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
pathlib.Path(meta_path).write_text(
    json.dumps(
        {
            "started_at": payload["run_timestamp"],
            "run_name": run_name,
            "benchmark_config_path": payload["benchmark_config_path"],
            "benchmark_summary_path": payload["benchmark_summary_path"],
            # Classifier fields. Per-run meta needs these so downstream
            # scoring (`scripts/judge_trajectory.py`) can label each
            # trajectory by cell / orchestration / model without
            # re-reading the cell-level config.json (which the next run
            # overwrites). Mirror the values from the cell config payload
            # written above. (PR #144)
            "experiment_cell": payload["experiment_cell"],
            "orchestration_mode": payload["orchestration_mode"],
            "mcp_mode": payload["mcp_mode"],
            "model_id": payload["model_id"],
            "experiment_family": payload["experiment_family"],
            "missing_evidence_guard": payload["missing_evidence_guard"],
            "missing_evidence_repair": payload["missing_evidence_repair"],
            "explicit_fault_risk_adjudication": payload[
                "explicit_fault_risk_adjudication"
            ],
            "missing_evidence_repair_max_attempts": payload[
                "missing_evidence_repair_max_attempts"
            ],
            "missing_evidence_repair_max_attempts_per_target": payload[
                "missing_evidence_repair_max_attempts_per_target"
            ],
            # vLLM extra args. Per-run meta records the exact optimization
            # knobs that produced a run so notebooks / paper tables can
            # recover the prefix-cache / kv-dtype / etc. choice without
            # re-reading harness.log. (PR #129 / Lane 2)
            "vllm_dtype": payload["vllm_dtype"],
            "vllm_extra_args": payload["vllm_extra_args"],
            "vllm_extra_args_list": payload["vllm_extra_args_list"],
            "runtime_versions": payload["runtime_versions"],
            "git_sha": payload["git_sha"],
            "git_branch": payload["git_branch"],
            "git_dirty": payload["git_dirty"],
            "smartgrid_batch_id": payload["smartgrid_batch_id"],
            "smartgrid_resume": payload["smartgrid_resume"],
            "smartgrid_force_rerun": payload["smartgrid_force_rerun"],
            "smartgrid_resume_require_latency": payload[
                "smartgrid_resume_require_latency"
            ],
        },
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
PY

if [ "$LAUNCH_VLLM" = "1" ]; then
  export PATH=/usr/local/cuda/bin:$PATH
  export LD_LIBRARY_PATH=/usr/local/cuda/lib64:${LD_LIBRARY_PATH:-}
  # Cluster-specific env (NCCL overrides for Insomnia Slingshot fabric, etc.)
  # shellcheck source=scripts/insomnia_env.sh
  source "$REPO_ROOT/scripts/insomnia_env.sh"
  # shellcheck disable=SC1091
  source .venv-insomnia/bin/activate
  if [ "$AAT_MCP_SERVER_LAUNCH_MODE" != "uv" ] && [ -z "$AAT_MCP_SERVER_PYTHON" ] && [ -x "$REPO_ROOT/.venv-insomnia/bin/python" ]; then
    export AAT_MCP_SERVER_PYTHON="$REPO_ROOT/.venv-insomnia/bin/python"
  fi
  CUDNN_LIB="$("$PYTHON_BIN" -c 'import nvidia.cudnn, os; print(os.path.join(os.path.dirname(nvidia.cudnn.__file__), "lib"))' 2>/dev/null || true)"
  if [ -n "$CUDNN_LIB" ]; then
    export LD_LIBRARY_PATH="$CUDNN_LIB:$LD_LIBRARY_PATH"
  fi
fi

preflight_vllm_gpu_runtime() {
  if [ "$LAUNCH_VLLM" != "1" ]; then
    return 0
  fi

  {
    echo "=== vLLM GPU preflight ==="
    echo "Node: $(hostname)"
    echo "SLURM_JOB_ID=${SLURM_JOB_ID:-N/A}"
    echo "SLURM_JOB_GPUS=${SLURM_JOB_GPUS:-<unset>}"
    echo "SLURM_GPUS_ON_NODE=${SLURM_GPUS_ON_NODE:-<unset>}"
    echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-<unset>}"
  } >>"$HARNESS_LOG"

  if ! command -v nvidia-smi >/dev/null 2>&1; then
    echo "ERROR: nvidia-smi not found after CUDA path setup; cannot launch vLLM." >&2
    return 1
  fi

  if ! nvidia-smi -L >>"$HARNESS_LOG" 2>&1; then
    echo "ERROR: Slurm allocated node $(hostname), but nvidia-smi cannot see a GPU." >&2
    echo "This is a cluster/GPU allocation problem, not an AaT runner failure." >&2
    echo "Try resubmitting, or exclude this node if it repeats: sbatch --exclude=$(hostname) ..." >&2
    return 1
  fi

  if ! "$PYTHON_BIN" >>"$HARNESS_LOG" 2>&1 <<'PY'
import sys

import torch

print(f"torch={torch.__version__}")
print(f"cuda_available={torch.cuda.is_available()}")
print(f"cuda_device_count={torch.cuda.device_count()}")
if not torch.cuda.is_available() or torch.cuda.device_count() < 1:
    raise SystemExit("torch cannot see an allocated CUDA device")
torch.cuda.init()
print(f"cuda_device_0={torch.cuda.get_device_name(0)}")
PY
  then
    echo "ERROR: PyTorch CUDA preflight failed before vLLM launch. See $HARNESS_LOG." >&2
    echo "This usually means the Slurm node/GPU allocation is unhealthy; try a fresh node." >&2
    return 1
  fi
}

run_plan_execute_trial() {
  local prompt="$1"
  local out_path="$2"
  if [ "$ENABLE_SELF_ASK" = "1" ] || [ "${PLAN_EXECUTE_REPO_LOCAL:-0}" = "1" ]; then
    local -a wrapper_cmd=(
      "$AOB_PYTHON"
      "$REPO_ROOT/scripts/plan_execute_self_ask_runner.py"
      --json
      --model-id "$MODEL_ID"
      --aob-path "$AOB_PATH"
      --mcp-mode "$MCP_MODE"
    )
    if [ "$ENABLE_SELF_ASK" != "1" ]; then
      wrapper_cmd+=(--disable-self-ask)
    fi
    if [ "$HARNESS_VERBOSE" = "1" ]; then
      wrapper_cmd+=(--verbose --show-plan --show-trajectory)
    fi
    wrapper_cmd+=("${SERVER_ARGS[@]}")
    wrapper_cmd+=("$prompt")
    run_json_stdout_trial "$out_path" "$REPO_ROOT" "${wrapper_cmd[@]}"
    return
  fi
  local -a cmd=(uv run plan-execute --json --model-id "$MODEL_ID")
  if [ "$HARNESS_VERBOSE" = "1" ]; then
    cmd+=(--verbose --show-plan --show-trajectory)
  fi
  cmd+=("$prompt")
  (cd "$AOB_PATH" && "${cmd[@]}") >"$out_path" 2>>"$HARNESS_LOG"
}

run_json_stdout_trial() {
  local out_path="$1"
  local cwd="$2"
  shift 2

  local raw_path="${out_path}.stdout.tmp"
  local rc=0
  (cd "$cwd" && "$@") >"$raw_path" 2>>"$HARNESS_LOG" || rc=$?
  if "$PYTHON_BIN" - "$raw_path" "$out_path" >>"$HARNESS_LOG" 2>&1 <<'PY'
import json
import pathlib
import sys

raw_path = pathlib.Path(sys.argv[1])
out_path = pathlib.Path(sys.argv[2])
raw = raw_path.read_text(encoding="utf-8", errors="replace")
decoder = json.JSONDecoder()

for index, char in enumerate(raw):
    if char != "{":
        continue
    try:
        payload, end = decoder.raw_decode(raw[index:])
    except json.JSONDecodeError:
        continue
    trailing = raw[index + end :].strip()
    if trailing:
        continue
    if index:
        print(
            f"Sanitized {raw_path.name}: removed {index} leading non-JSON characters before runner JSON.",
            file=sys.stderr,
        )
    out_path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    raw_path.unlink(missing_ok=True)
    raise SystemExit(0)

print(
    f"ERROR: could not extract a complete JSON object from runner stdout {raw_path}",
    file=sys.stderr,
)
excerpt = raw.strip()
if len(excerpt) > 4000:
    excerpt = excerpt[:4000] + "...[truncated]"
out_path.write_text(
    json.dumps(
        {
            "success": False,
            "failed_steps": [],
            "history": [],
            "answer": "",
            "error": (
                "Runner produced no complete JSON object on stdout; "
                "see harness.log for stderr and traceback details."
            ),
            "raw_stdout_excerpt": excerpt,
        },
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
raw_path.unlink(missing_ok=True)
raise SystemExit(1)
PY
  then
    return "$rc"
  fi

  return 1
}

preflight_repo_local_orchestration_runtime() {
  case "$ORCHESTRATION" in
    verified_pe) ;;
    plan_execute)
      if [ "$ENABLE_SELF_ASK" != "1" ]; then
        return 0
      fi
      ;;
    *)
      return 0
      ;;
  esac

  if ! (
    cd "$REPO_ROOT"
    "$AOB_PYTHON" - "$REPO_ROOT" "$AOB_PATH" >>"$HARNESS_LOG" 2>&1 <<'PY'
from pathlib import Path
import sys

repo_root = Path(sys.argv[1])
aob_path = Path(sys.argv[2])

sys.path.insert(0, str(repo_root / "scripts"))

from orchestration_utils import (  # noqa: E402
    bootstrap_aob,
    preflight_aob_runtime_dependencies,
)

bootstrap_aob(aob_path)
preflight_aob_runtime_dependencies()
print("Repo-local orchestration runtime preflight passed.")
PY
  ); then
    echo "ERROR: repo-local orchestration runtime preflight failed. See $HARNESS_LOG for details." >&2
    return 1
  fi
}

preflight_aat_runtime_dependencies() {
  if [ "$ORCHESTRATION" != "agent_as_tool" ]; then
    return 0
  fi

  if ! (
    cd "$REPO_ROOT"
    uv run \
      --with "openai-agents==$AAT_OPENAI_AGENTS_VERSION" \
      --with "mcp[cli]==$AAT_MCP_VERSION" \
      --with "litellm==$AAT_LITELLM_VERSION" \
      python - >>"$HARNESS_LOG" 2>&1 <<'PY'
from importlib.metadata import version

from agents import Agent, Runner, function_tool
from agents.extensions.models.litellm_model import LitellmModel
from agents.mcp import MCPServerStdio

import litellm
import mcp

print("AaT runtime dependency preflight passed.")
print(f"openai-agents=={version('openai-agents')}")
print(f"mcp=={version('mcp')}")
print(f"litellm=={version('litellm')}")
PY
  ); then
    echo "ERROR: AaT runtime dependency preflight failed before vLLM launch. See $HARNESS_LOG." >&2
    echo "Check AAT_OPENAI_AGENTS_VERSION, AAT_MCP_VERSION, and AAT_LITELLM_VERSION." >&2
    return 1
  fi

  echo "AaT parallel tool calls: $AAT_PARALLEL_TOOL_CALLS" >>"$HARNESS_LOG"

  if [ "$MCP_MODE" != "direct" ]; then
    echo "AaT MCP server launch mode: $AAT_MCP_SERVER_LAUNCH_MODE" >>"$HARNESS_LOG"
    if [ "$AAT_MCP_SERVER_LAUNCH_MODE" = "uv" ]; then
      if ! (
        cd "$REPO_ROOT"
        uv run \
          --with "mcp[cli]==$AAT_MCP_VERSION" \
          --with pandas \
          --with numpy \
          python - >>"$HARNESS_LOG" 2>&1 <<'PY'
from importlib.metadata import version

import mcp
import numpy
import pandas

print("AaT MCP server dependency preflight passed.")
print("server_launch_mode=uv")
print(f"mcp=={version('mcp')}")
print(f"numpy=={version('numpy')}")
print(f"pandas=={version('pandas')}")
PY
      ); then
        echo "ERROR: AaT MCP server dependency preflight failed before vLLM launch. See $HARNESS_LOG." >&2
        return 1
      fi
    elif [ -n "$AAT_MCP_SERVER_PYTHON" ]; then
      if ! "$AAT_MCP_SERVER_PYTHON" >>"$HARNESS_LOG" 2>&1 <<'PY'
from importlib.metadata import version

import mcp
import numpy
import pandas

print("AaT MCP server dependency preflight passed.")
print(f"server_python={__import__('sys').executable}")
print(f"mcp=={version('mcp')}")
print(f"numpy=={version('numpy')}")
print(f"pandas=={version('pandas')}")
PY
      then
        echo "ERROR: AaT MCP server dependency preflight failed before vLLM launch. See $HARNESS_LOG." >&2
        return 1
      fi
    elif [ "$AAT_MCP_SERVER_LAUNCH_MODE" = "python" ]; then
      echo "ERROR: AAT_MCP_SERVER_LAUNCH_MODE=python requires AAT_MCP_SERVER_PYTHON." >&2
      echo "For local uv-managed launches, set AAT_MCP_SERVER_LAUNCH_MODE=uv." >&2
      return 1
    elif ! (
      cd "$REPO_ROOT"
      uv run \
        --with "mcp[cli]==$AAT_MCP_VERSION" \
        --with pandas \
        --with numpy \
        python - >>"$HARNESS_LOG" 2>&1 <<'PY'
from importlib.metadata import version

import mcp
import numpy
import pandas

print("AaT MCP server dependency preflight passed.")
print(f"mcp=={version('mcp')}")
print(f"numpy=={version('numpy')}")
print(f"pandas=={version('pandas')}")
PY
    ); then
      echo "ERROR: AaT MCP server dependency preflight failed before vLLM launch. See $HARNESS_LOG." >&2
      return 1
    fi
  fi
}

run_external_orchestration_trial() {
  local prompt="$1"
  local out_path="$2"
  local template_var="$3"
  local template="${!template_var:-}"
  if [ -z "$template" ]; then
    echo "ERROR: $template_var must be set for ORCHESTRATION=$ORCHESTRATION" >&2
    return 1
  fi
  PROMPT="$prompt" \
    OUTPUT_PATH="$out_path" \
    REPO_ROOT="$REPO_ROOT" \
    AOB_PATH="$AOB_PATH" \
    AOB_PYTHON="$AOB_PYTHON" \
    MODEL_ID="$MODEL_ID" \
    AAT_OPENAI_AGENTS_VERSION="$AAT_OPENAI_AGENTS_VERSION" \
    AAT_MCP_VERSION="$AAT_MCP_VERSION" \
    AAT_LITELLM_VERSION="$AAT_LITELLM_VERSION" \
    AAT_MCP_SERVER_PYTHON="$AAT_MCP_SERVER_PYTHON" \
    AAT_MCP_SERVER_LAUNCH_MODE="$AAT_MCP_SERVER_LAUNCH_MODE" \
    AAT_MCP_CLIENT_TIMEOUT_SECONDS="$AAT_MCP_CLIENT_TIMEOUT_SECONDS" \
    AAT_PARALLEL_TOOL_CALLS="$AAT_PARALLEL_TOOL_CALLS" \
    ENABLE_SELF_ASK="$ENABLE_SELF_ASK" \
    ENABLE_MISSING_EVIDENCE_GUARD="$ENABLE_MISSING_EVIDENCE_GUARD" \
    ENABLE_MISSING_EVIDENCE_REPAIR="$ENABLE_MISSING_EVIDENCE_REPAIR" \
    ENABLE_EXPLICIT_FAULT_RISK_ADJUDICATION="$ENABLE_EXPLICIT_FAULT_RISK_ADJUDICATION" \
    MISSING_EVIDENCE_REPAIR_MAX_ATTEMPTS="$MISSING_EVIDENCE_REPAIR_MAX_ATTEMPTS" \
    MISSING_EVIDENCE_REPAIR_MAX_ATTEMPTS_PER_TARGET="$MISSING_EVIDENCE_REPAIR_MAX_ATTEMPTS_PER_TARGET" \
    HARNESS_VERBOSE="$HARNESS_VERBOSE" \
    SERVER_IOT_PATH="$SERVER_IOT_PATH" \
    SERVER_FMSR_PATH="$SERVER_FMSR_PATH" \
    SERVER_TSFM_PATH="$SERVER_TSFM_PATH" \
    SERVER_WO_PATH="$SERVER_WO_PATH" \
    bash -lc "$template" >>"$HARNESS_LOG" 2>&1
}

run_agent_as_tool_trial() {
  local prompt="$1"
  local out_path="$2"

  export AAT_MCP_SERVER_PYTHON AAT_MCP_SERVER_LAUNCH_MODE AAT_MCP_CLIENT_TIMEOUT_SECONDS

  if [ -n "$AAT_RUNNER_TEMPLATE" ]; then
    run_external_orchestration_trial "$prompt" "$out_path" "AAT_RUNNER_TEMPLATE"
    return
  fi

  local -a cmd=(
    uv run
    --with "openai-agents==$AAT_OPENAI_AGENTS_VERSION"
    --with "mcp[cli]==$AAT_MCP_VERSION"
    --with "litellm==$AAT_LITELLM_VERSION"
    python scripts/aat_runner.py
    --prompt "$prompt"
    --output "$out_path"
    --model-id "$MODEL_ID"
    --mcp-mode "$MCP_MODE"
    --parallel-tool-calls "$AAT_PARALLEL_TOOL_CALLS"
  )
  if [ "$HARNESS_VERBOSE" = "1" ]; then
    cmd+=(--verbose)
  fi
  (cd "$REPO_ROOT" && "${cmd[@]}") >>"$HARNESS_LOG" 2>&1
}

run_agent_as_tool_batch() {
  local out_dir="$1"

  export AAT_MCP_SERVER_PYTHON AAT_MCP_SERVER_LAUNCH_MODE AAT_MCP_CLIENT_TIMEOUT_SECONDS

  local -a cmd=(
    uv run
    --with "openai-agents==$AAT_OPENAI_AGENTS_VERSION"
    --with "mcp[cli]==$AAT_MCP_VERSION"
    --with "litellm==$AAT_LITELLM_VERSION"
    python scripts/aat_runner.py
    --scenarios-glob "$SCENARIOS_GLOB"
    --trials "$TRIALS"
    --output-dir "$out_dir"
    --run-basename "$RUN_BASENAME"
    --model-id "$MODEL_ID"
    --mcp-mode "$MCP_MODE"
    --parallel-tool-calls "$AAT_PARALLEL_TOOL_CALLS"
  )
  if [ "$HARNESS_VERBOSE" = "1" ]; then
    cmd+=(--verbose)
  fi
  (cd "$REPO_ROOT" && "${cmd[@]}") >>"$HARNESS_LOG" 2>&1
}

run_verified_pe_trial() {
  local prompt="$1"
  local out_path="$2"
  if [ -n "$VERIFIED_PE_RUNNER_TEMPLATE" ]; then
    run_external_orchestration_trial "$prompt" "$out_path" "VERIFIED_PE_RUNNER_TEMPLATE"
    return
  fi

  local -a cmd=(
    "$AOB_PYTHON"
    "$REPO_ROOT/scripts/verified_pe_runner.py"
    --json
    --model-id "$MODEL_ID"
    --aob-path "$AOB_PATH"
    --mcp-mode "$MCP_MODE"
  )
  if [ "$ENABLE_SELF_ASK" != "1" ]; then
    cmd+=(--disable-self-ask)
  fi
  if [ "$HARNESS_VERBOSE" = "1" ]; then
    cmd+=(--verbose --show-plan --show-trajectory)
  fi
  cmd+=("$prompt")
  run_json_stdout_trial "$out_path" "$REPO_ROOT" "${cmd[@]}"
}

trial_succeeded() {
  local out_path="$1"
  if [ ! -s "$out_path" ]; then
    return 1
  fi
  "$PYTHON_BIN" - "$out_path" <<'PY'
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
try:
    payload = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    raise SystemExit(1)

success = payload.get("success")
if isinstance(success, bool):
    raise SystemExit(0 if success else 1)

raise SystemExit(0)
PY
}

VLLM_PID=""
cleanup() {
  if [ -n "$VLLM_PGID" ] && kill -0 -- "-$VLLM_PGID" 2>/dev/null; then
    kill -TERM -- "-$VLLM_PGID" 2>/dev/null || true
    sleep 2
    kill -KILL -- "-$VLLM_PGID" 2>/dev/null || true
    wait "$VLLM_PID" 2>/dev/null || true
  elif [ -n "$VLLM_PID" ] && kill -0 "$VLLM_PID" 2>/dev/null; then
    kill -TERM "$VLLM_PID" 2>/dev/null || true
    wait "$VLLM_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

preflight_repo_local_orchestration_runtime
preflight_aat_runtime_dependencies
preflight_vllm_gpu_runtime

if [ "$LAUNCH_VLLM" = "1" ]; then
  if [ -z "$VLLM_STARTUP_TIMEOUT" ]; then
    if [ "$MAX_MODEL_LEN" -ge 32768 ]; then
      VLLM_STARTUP_TIMEOUT=1800
    elif [ "$MAX_MODEL_LEN" -ge 16384 ]; then
      VLLM_STARTUP_TIMEOUT=1500
    else
      VLLM_STARTUP_TIMEOUT=1200
    fi
  fi
  if [[ "$MODEL_ID" == openai/* ]]; then
    REQUEST_MODEL_NAME="${MODEL_ID#openai/}"
    if [ "$REQUEST_MODEL_NAME" != "$VLLM_SERVED_MODEL_NAME" ]; then
      echo "ERROR: MODEL_ID=$MODEL_ID implies requested local vLLM model '$REQUEST_MODEL_NAME'," >&2
      echo "but VLLM_SERVED_MODEL_NAME is '$VLLM_SERVED_MODEL_NAME'." >&2
      exit 1
    fi
  fi
  echo "vLLM startup timeout: ${VLLM_STARTUP_TIMEOUT}s"
  VLLM_SERVER_ARGS=(
    -u
    -m vllm.entrypoints.openai.api_server
    --model "$VLLM_MODEL_PATH"
    --served-model-name "$VLLM_SERVED_MODEL_NAME"
    --host 127.0.0.1
    --port "$VLLM_PORT"
    --max-model-len "$MAX_MODEL_LEN"
    --dtype "$VLLM_DTYPE"
    --generation-config "$VLLM_GENERATION_CONFIG"
  )
  if [ "$VLLM_ENABLE_AUTO_TOOL_CHOICE" = "1" ]; then
    if [ -z "$VLLM_TOOL_CALL_PARSER" ]; then
      echo "ERROR: VLLM_TOOL_CALL_PARSER must be set when VLLM_ENABLE_AUTO_TOOL_CHOICE=1." >&2
      exit 1
    fi
    echo "vLLM auto tool choice: enabled with parser '$VLLM_TOOL_CALL_PARSER'"
    VLLM_SERVER_ARGS+=(--enable-auto-tool-choice --tool-call-parser "$VLLM_TOOL_CALL_PARSER")
  fi
  if [ "$TORCH_PROFILE" = "1" ]; then
    [ -z "$TORCH_PROFILE_DIR" ] && TORCH_PROFILE_DIR="profiling/traces/${RUN_ID}_torch"
    mkdir -p "$TORCH_PROFILE_DIR"
    # vLLM 0.19.0 dropped the VLLM_TORCH_PROFILER_DIR env var; profiling is
    # now enabled via --profiler-config CLI flag (see vllm/config/profiler.py
    # and vllm/entrypoints/serve/profile/api_router.py). The path must be absolute.
    TORCH_PROFILE_DIR_ABS="$(cd "$TORCH_PROFILE_DIR" && pwd)"
    VLLM_SERVER_ARGS+=(--profiler-config "{\"profiler\":\"torch\",\"torch_profiler_dir\":\"$TORCH_PROFILE_DIR_ABS\"}")
    echo "Torch profiler enabled: --profiler-config torch torch_profiler_dir=$TORCH_PROFILE_DIR_ABS" | tee -a "$HARNESS_LOG"
  fi
  # EXTRA_VLLM_ARGS: optional whitespace-separated extra CLI flags for the
  # vLLM server. Used by Cell C and the #29/#30 smoke configs to pass
  # --quantization, --kv-cache-dtype, --enable-prefix-caching, etc., without
  # editing this script per experiment.
  #
  # Quoting contract: values go through POSIX word-splitting on whitespace
  # only — there is NO shell-metacharacter re-evaluation, so values like
  # `--foo $HOME` or `--foo $(date)` will be passed literally and NOT
  # expanded. If you need a value with embedded whitespace, you can't pass it
  # via EXTRA_VLLM_ARGS today; promote it to its own config var instead.
  # When passing via `sbatch --export=EXTRA_VLLM_ARGS="--foo bar"`, sbatch's
  # own shell handles the outer quoting; this script then word-splits the
  # received value once.
  if [ -n "${EXTRA_VLLM_ARGS:-}" ]; then
    # shellcheck disable=SC2206  # intentional word-splitting
    EXTRA_VLLM_ARGS_ARR=($EXTRA_VLLM_ARGS)
    VLLM_SERVER_ARGS+=("${EXTRA_VLLM_ARGS_ARR[@]}")
    echo "vLLM extra args: $EXTRA_VLLM_ARGS" | tee -a "$HARNESS_LOG"
  fi
  if command -v setsid >/dev/null 2>&1; then
    setsid "$PYTHON_BIN" "${VLLM_SERVER_ARGS[@]}" >"$VLLM_LOG" 2>&1 &
    VLLM_PGID=$!
  else
    "$PYTHON_BIN" "${VLLM_SERVER_ARGS[@]}" >"$VLLM_LOG" 2>&1 &
  fi
  VLLM_PID=$!
  for i in $(seq 1 "$VLLM_STARTUP_TIMEOUT"); do
    if curl -s "http://127.0.0.1:$VLLM_PORT/health" >/dev/null 2>&1; then
      break
    fi
    if ! kill -0 "$VLLM_PID" 2>/dev/null; then
      tail -50 "$VLLM_LOG" >&2 || true
      exit 1
    fi
    sleep 1
  done
  if ! curl -s "http://127.0.0.1:$VLLM_PORT/health" >/dev/null 2>&1; then
    echo "ERROR: vLLM did not become ready within ${VLLM_STARTUP_TIMEOUT}s" >&2
    echo "MAX_MODEL_LEN=$MAX_MODEL_LEN can stretch startup on A6000 nodes well past simple weight-load time." >&2
    echo "Set VLLM_STARTUP_TIMEOUT in the config if this run intentionally uses a slower startup profile." >&2
    tail -50 "$VLLM_LOG" >&2 || true
    exit 1
  fi
  MODELS_JSON="$(curl -s "http://127.0.0.1:$VLLM_PORT/v1/models")"
  if ! MODELS_JSON_PAYLOAD="$MODELS_JSON" "$PYTHON_BIN" -c '
import json
import os
import sys

expected = sys.argv[1]
payload = json.loads(os.environ["MODELS_JSON_PAYLOAD"])
model_ids = [item.get("id") for item in payload.get("data", []) if item.get("id")]
if expected not in model_ids:
    raise SystemExit(
        f"expected served model {expected!r} not present in /v1/models: {model_ids}"
    )
' "$VLLM_SERVED_MODEL_NAME"
  then
    echo "ERROR: vLLM registry did not expose expected served model '$VLLM_SERVED_MODEL_NAME'." >&2
    echo "$MODELS_JSON" >&2
    exit 1
  fi
  export LITELLM_BASE_URL="http://127.0.0.1:$VLLM_PORT/v1"
  export LITELLM_API_KEY="dummy-vllm-not-checked"
fi

PASS=0
FAIL=0
TOTAL=0
RESUME_SKIPPED=0
RESUME_RERUN=0
INFRA_FAIL=0
if [ "$SMARTGRID_RESUME" = "1" ] && [ "$SMARTGRID_FORCE_RERUN" != "1" ]; then
  touch "$LATENCY_FILE"
else
  : >"$LATENCY_FILE"
  : >"$RESUME_MANIFEST_FILE"
fi

# Cell C optimized: run all scenarios in a single aat_runner.py call so MCP
# subprocesses are reused across trials (reuse_mcp_connections).
if [ "$ORCHESTRATION" = "agent_as_tool" ] && [ "$MCP_MODE" = "optimized" ] && [ "$SMARTGRID_RESUME" != "1" ]; then
  if [ -n "${AAT_RUNNER_TEMPLATE:-}" ]; then
    echo "ERROR: AAT_RUNNER_TEMPLATE is not supported with MCP_MODE=optimized batch mode." >&2
    exit 1
  fi
  EXPECTED_TOTAL=$(( ${#SCENARIO_FILES[@]} * TRIALS ))
  BATCH_RC=0
  run_agent_as_tool_batch "$RUN_DIR" || BATCH_RC=$?
  if [ "$BATCH_RC" -gt 1 ]; then
    echo "ERROR: agent-as-tool batch runner failed with exit code $BATCH_RC" >&2
    INFRA_FAIL=1
  fi
  # Merge per-trial latency records into the canonical latencies.jsonl.
  if [ -f "$RUN_DIR/_batch_latencies.jsonl" ]; then
    cat "$RUN_DIR/_batch_latencies.jsonl" >>"$LATENCY_FILE"
  fi
  # Count pass/fail — RUN_BASENAME prefix safely excludes meta.json etc.
  for trial_json in "$RUN_DIR/${RUN_BASENAME}"_*.json; do
    [ -f "$trial_json" ] || continue
    TOTAL=$((TOTAL + 1))
    if trial_succeeded "$trial_json"; then
      PASS=$((PASS + 1))
    else
      FAIL=$((FAIL + 1))
    fi
  done
  # Account for trials that never wrote output (e.g. MCP crash before any JSON).
  MISSING=$(( EXPECTED_TOTAL - TOTAL ))
  if [ "$MISSING" -gt 0 ]; then
    echo "WARNING: $MISSING trial(s) missing from batch output — counting as failures" >&2
    FAIL=$(( FAIL + MISSING ))
    TOTAL=$(( TOTAL + MISSING ))
    INFRA_FAIL=1
  fi
else

for SCENARIO_FILE in "${SCENARIO_FILES[@]}"; do
  SCENARIO_BASENAME="$(basename "$SCENARIO_FILE" .json)"
  PROMPT="$("$PYTHON_BIN" - "$SCENARIO_FILE" <<'PY'
import json
import sys

payload = json.load(open(sys.argv[1], encoding="utf-8"))
print(payload["text"])
PY
)"

  for TRIAL in $(seq 1 "$TRIALS"); do
    TOTAL=$((TOTAL + 1))
    TRIAL_ID="${SCENARIO_BASENAME}_run$(printf '%02d' "$TRIAL")"
    TRIAL_OUT="$RUN_DIR/${RUN_BASENAME}_${TRIAL_ID}.json"
    TRIAL_TMP="${TRIAL_OUT}.tmp"
    RESUME_REASON="fresh_run"

    if [ "$SMARTGRID_RESUME" = "1" ] && [ "$SMARTGRID_FORCE_RERUN" != "1" ]; then
      REQUIRE_LATENCY_ARGS=()
      if [ "$SMARTGRID_RESUME_REQUIRE_LATENCY" = "1" ]; then
        REQUIRE_LATENCY_ARGS+=(--require-latency)
      fi
      eval "$("$PYTHON_BIN" scripts/gcp_resume_state.py trial-status-shell \
        --run-dir "$RUN_DIR" \
        --scenario-file "$SCENARIO_FILE" \
        --trial-index "$TRIAL" \
        --output-path "$TRIAL_OUT" \
        --latency-file "$LATENCY_FILE" \
        "${REQUIRE_LATENCY_ARGS[@]}")"
      TRIAL_OUT="$RESUME_OUTPUT_PATH"
      TRIAL_TMP="${TRIAL_OUT}.tmp"
      if [ "$RESUME_COMPLETE" = "1" ]; then
        RESUME_SKIPPED=$((RESUME_SKIPPED + 1))
        if [ "$RESUME_SUCCESS" = "1" ]; then
          PASS=$((PASS + 1))
        else
          FAIL=$((FAIL + 1))
        fi
        "$PYTHON_BIN" scripts/gcp_resume_state.py manifest-event \
          --manifest-file "$RESUME_MANIFEST_FILE" \
          --state "$RESUME_STATE" \
          --scenario-file "$SCENARIO_FILE" \
          --trial-index "$TRIAL" \
          --output-path "$TRIAL_OUT" \
          --run-name "$RUN_ID" \
          --reason "resume_skip:$RESUME_REASON" \
          --batch-id "$SMARTGRID_BATCH_ID"
        echo "Resume skip: $TRIAL_ID ($RESUME_STATE)"
        continue
      fi
      RESUME_RERUN=$((RESUME_RERUN + 1))
    fi

    "$PYTHON_BIN" scripts/gcp_resume_state.py preserve-incomplete \
      --output-path "$TRIAL_OUT" \
      --manifest-file "$RESUME_MANIFEST_FILE" \
      --scenario-file "$SCENARIO_FILE" \
      --trial-index "$TRIAL" \
      --run-name "$RUN_ID" \
      --batch-id "$SMARTGRID_BATCH_ID" \
      --reason "pre_rerun_incomplete:$RESUME_REASON" || true
    "$PYTHON_BIN" scripts/gcp_resume_state.py preserve-incomplete \
      --output-path "$TRIAL_TMP" \
      --manifest-file "$RESUME_MANIFEST_FILE" \
      --scenario-file "$SCENARIO_FILE" \
      --trial-index "$TRIAL" \
      --run-name "$RUN_ID" \
      --batch-id "$SMARTGRID_BATCH_ID" \
      --reason "pre_rerun_tmp" || true

    START_EPOCH="$("$PYTHON_BIN" - <<'PY'
import time
print(time.time())
PY
)"
    TRIAL_RC=0

    case "$ORCHESTRATION" in
      plan_execute)
        run_plan_execute_trial "$PROMPT" "$TRIAL_TMP" || TRIAL_RC=$?
        ;;
      agent_as_tool)
        run_agent_as_tool_trial "$PROMPT" "$TRIAL_TMP" || TRIAL_RC=$?
        ;;
      hybrid)
        run_external_orchestration_trial "$PROMPT" "$TRIAL_TMP" "HYBRID_RUNNER_TEMPLATE" || TRIAL_RC=$?
        ;;
      verified_pe)
        run_verified_pe_trial "$PROMPT" "$TRIAL_TMP" || TRIAL_RC=$?
        ;;
      *)
        echo "ERROR: unknown ORCHESTRATION=$ORCHESTRATION" >&2
        exit 1
        ;;
    esac

    END_EPOCH="$("$PYTHON_BIN" - <<'PY'
import time
print(time.time())
PY
)"

    eval "$("$PYTHON_BIN" scripts/gcp_resume_state.py finalize-trial-shell \
      --scenario-file "$SCENARIO_FILE" \
      --trial-index "$TRIAL" \
      --temp-output "$TRIAL_TMP" \
      --output-path "$TRIAL_OUT" \
      --latency-file "$LATENCY_FILE" \
      --manifest-file "$RESUME_MANIFEST_FILE" \
      --run-name "$RUN_ID" \
      --batch-id "$SMARTGRID_BATCH_ID" \
      --start-epoch "$START_EPOCH" \
      --end-epoch "$END_EPOCH" \
      --return-code "$TRIAL_RC")"

    if [ "$FINAL_SUCCESS" = "1" ]; then
      PASS=$((PASS + 1))
    else
      FAIL=$((FAIL + 1))
    fi
  done
done

fi  # end of per-scenario/per-trial loop (skipped for MCP_MODE=optimized batch path)

"$PYTHON_BIN" - "$SUMMARY_FILE" "$CONFIG_FILE" "$META_FILE" "$LATENCY_FILE" "$RUN_DIR" "$PASS" "$FAIL" "$TOTAL" "$RESUME_SKIPPED" "$RESUME_RERUN" <<'PY'
import json
import pathlib
import statistics
import sys
from datetime import datetime, timezone

(
    summary_path,
    config_path,
    meta_path,
    latency_path,
    run_dir,
    passed,
    failed,
    total,
    resume_skipped,
    resume_rerun,
) = sys.argv[1:]
config = json.loads(pathlib.Path(config_path).read_text(encoding="utf-8"))
meta = json.loads(pathlib.Path(meta_path).read_text(encoding="utf-8"))
latency_records = [
    json.loads(line)
    for line in pathlib.Path(latency_path).read_text(encoding="utf-8").splitlines()
    if line.strip()
]
latencies = [
    record["latency_seconds"]
    for record in latency_records
    if isinstance(record.get("latency_seconds"), (int, float))
]
mcp_setup_values = [
    record["mcp_setup_seconds"]
    for record in latency_records
    if isinstance(record.get("mcp_setup_seconds"), (int, float))
    and record["mcp_setup_seconds"] > 0
]
mcp_setup_seconds = max(mcp_setup_values) if mcp_setup_values else None
wall_clock_seconds_total = sum(latencies) + (mcp_setup_seconds or 0)

tool_call_total = 0
tool_call_trials = 0
# Per-trial token usage, aggregated for summary.json (#133). Tokens are
# captured by aat_runner.py from the Agents SDK RunContextWrapper.usage and
# written into payload["usage"] on each trial JSON. Trials with missing /
# null usage are excluded from the totals so the summary distinguishes
# "no data" (None) from "zero tokens" (0).
input_tokens_total = 0
output_tokens_total = 0
total_tokens_total = 0
usage_trials = 0
for output_path in sorted(pathlib.Path(run_dir).glob("*_run[0-9][0-9].json")):
    try:
        payload = json.loads(output_path.read_text(encoding="utf-8"))
    except Exception:
        continue
    usage = payload.get("usage")
    if isinstance(usage, dict):
        i_t = usage.get("input_tokens")
        o_t = usage.get("output_tokens")
        t_t = usage.get("total_tokens")
        # Only count trials that report at least input + output. Treat
        # explicit None as missing (not zero).
        if (
            isinstance(i_t, int)
            and not isinstance(i_t, bool)
            and i_t >= 0
            and isinstance(o_t, int)
            and not isinstance(o_t, bool)
            and o_t >= 0
        ):
            input_tokens_total += i_t
            output_tokens_total += o_t
            if isinstance(t_t, int) and not isinstance(t_t, bool) and t_t >= 0:
                total_tokens_total += t_t
            else:
                total_tokens_total += i_t + o_t
            usage_trials += 1
    explicit_tool_calls = payload.get("tool_call_count")
    if (
        isinstance(explicit_tool_calls, int)
        and not isinstance(explicit_tool_calls, bool)
        and explicit_tool_calls >= 0
    ):
        tool_call_total += explicit_tool_calls
        tool_call_trials += 1
        continue
    history = payload.get("history")
    if not isinstance(history, list):
        continue
    tool_calls = 0
    for step in history:
        nested_calls = step.get("tool_calls")
        if isinstance(nested_calls, list):
            tool_calls += len(nested_calls)
            continue
        tool = str(step.get("tool", "")).strip().lower()
        if tool and tool not in {"none", "null"}:
            tool_calls += 1
    tool_call_total += tool_calls
    tool_call_trials += 1

def percentile(values, p):
    if not values:
        return None
    values = sorted(values)
    idx = min(len(values) - 1, round((p / 100) * (len(values) - 1)))
    return values[idx]

summary = {
    **{
        k: config[k]
        for k in (
            "schema_version",
            "wandb_entity",
            "project_name",
            "run_name",
            "git_sha",
            "benchmark_config_path",
            "benchmark_summary_path",
            "wandb_run_url",
            "experiment_family",
            "contributing_experiments",
            "experiment_cell",
            "orchestration_mode",
            "mcp_mode",
            "scenario_set_name",
            "scenario_set_hash",
            "model_id",
            "host_name",
            "gpu_type",
            "slurm_job_id",
        )
    },
    "missing_evidence_guard": bool(config.get("missing_evidence_guard", False)),
    "missing_evidence_repair": bool(config.get("missing_evidence_repair", False)),
    "explicit_fault_risk_adjudication": bool(config.get("explicit_fault_risk_adjudication", False)),
    "missing_evidence_repair_max_attempts": config.get("missing_evidence_repair_max_attempts"),
    "missing_evidence_repair_max_attempts_per_target": config.get("missing_evidence_repair_max_attempts_per_target"),
    "run_status": "success" if int(failed) == 0 else ("partial" if int(passed) > 0 else "failed"),
    "scenarios_attempted": int(total),
    "scenarios_completed": int(passed),
    "resume_skipped_count": int(resume_skipped),
    "resume_rerun_count": int(resume_rerun),
    "success_rate": (int(passed) / int(total)) if int(total) else 0.0,
    "failure_count": int(failed),
    "wall_clock_seconds_total": wall_clock_seconds_total,
    "latency_seconds_mean": statistics.mean(latencies) if latencies else None,
    "latency_seconds_p50": percentile(latencies, 50),
    "latency_seconds_p95": percentile(latencies, 95),
    "mcp_setup_seconds": mcp_setup_seconds,
    # End-to-end agent throughput. Denominator is wall_clock_seconds_total
    # which includes tool-call round-trips, MCP serialization, and
    # orchestration time — NOT just model decode. Per #133 / Alex's review:
    # label this "end-to-end agent throughput", not "model decode tok/s".
    # Null when no trial reported usage (e.g. older runs predating the
    # aat_runner.py usage capture in #131/#133 PR).
    "tokens_per_second_mean": (
        (output_tokens_total / wall_clock_seconds_total)
        if usage_trials and wall_clock_seconds_total
        else None
    ),
    "input_tokens_total": input_tokens_total if usage_trials else None,
    "output_tokens_total": output_tokens_total if usage_trials else None,
    "total_tokens_total": total_tokens_total if usage_trials else None,
    "tokens_usage_trial_count": usage_trials,
    "tool_call_count_total": tool_call_total if tool_call_trials else None,
    "tool_call_count_mean": (tool_call_total / tool_call_trials) if tool_call_trials else None,
    "mcp_latency_seconds_mean": None,
    "mcp_latency_seconds_p95": None,
    "tool_latency_seconds_mean": None,
    "tool_error_count": int(failed),
    "judge_score_mean": None,
    "judge_score_p50": None,
    "judge_score_p95": None,
    "judge_score_p5": None,
    "judge_pass_rate": None,
    "finished_at": datetime.now(timezone.utc).isoformat(),
}
pathlib.Path(summary_path).write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
meta["finished_at"] = summary["finished_at"]
meta["pass"] = int(passed)
meta["fail"] = int(failed)
meta["total_runs"] = int(total)
meta["run_status"] = summary["run_status"]
meta["mcp_setup_seconds"] = summary["mcp_setup_seconds"]
meta["resume_skipped_count"] = summary["resume_skipped_count"]
meta["resume_rerun_count"] = summary["resume_rerun_count"]
pathlib.Path(meta_path).write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
PY

if [ "${TORCH_PROFILE:-0}" = "1" ] && [ -n "${TORCH_PROFILE_DIR:-}" ] && [ "$LAUNCH_VLLM" = "1" ] && [ "$ORCHESTRATION" = "agent_as_tool" ]; then
  # Replay phase always invokes scripts/aat_runner.py, so it only makes sense
  # for AaT cells (A, B, C). For PE / Verified PE cells, an AaT replay would
  # produce a trace shaped like the AaT loop rather than the cell's actual
  # multi-step orchestration — see docs/replay_phase_analysis.md. Profile
  # coverage for non-AaT cells happens during the main benchmark loop above
  # (vLLM captures whatever requests hit it while TORCH_PROFILE=1).
  echo ""
  echo "=== Torch profiler replay pass ==="
  echo "Profiler dir: $TORCH_PROFILE_DIR"
  # Export the parent run's model + AaT runtime settings so replay uses the
  # exact same local-vLLM served model and MCP bootstrap mode as the benchmark.
  # This matters for model-variant cells such as D, where vLLM exposes only
  # `Llama-3.1-8B-Instruct-int8`.
  export VLLM_PORT MODEL_ID
  export AAT_OPENAI_AGENTS_VERSION AAT_MCP_VERSION AAT_LITELLM_VERSION
  export AAT_PARALLEL_TOOL_CALLS AAT_MCP_SERVER_PYTHON AAT_MCP_SERVER_LAUNCH_MODE
  export HARNESS_VERBOSE SERVER_IOT_PATH SERVER_FMSR_PATH SERVER_TSFM_PATH SERVER_WO_PATH
  if VLLM_PORT="$VLLM_PORT" bash profiling/scripts/run_vllm_torch_profile.sh \
      "$TORCH_PROFILE_DIR" \
      -- bash scripts/replay_scenarios.sh "$RUN_DIR" "$MCP_MODE" \
      2>>"$HARNESS_LOG"; then
    echo "Torch profiler trace written to $TORCH_PROFILE_DIR"
  else
    echo "WARNING: torch profiler replay failed (non-fatal; nvidia-smi capture unaffected)"
  fi
elif [ "${TORCH_PROFILE:-0}" = "1" ] && [ -n "${TORCH_PROFILE_DIR:-}" ] && [ "$LAUNCH_VLLM" = "1" ]; then
  echo ""
  echo "=== Torch profiler replay pass — SKIPPED ==="
  echo "Skipping replay for ORCHESTRATION=$ORCHESTRATION (replay only fires for agent_as_tool)."
  echo "Main-loop profiling covered the cell's actual workload; see docs/replay_phase_analysis.md."
fi

if [ "$ENABLE_WANDB" = "1" ]; then
  "$PYTHON_BIN" - "$CONFIG_FILE" "$SUMMARY_FILE" "$META_FILE" "$WANDB_MODE" <<'PY'
import json
import pathlib
import sys

import wandb

config_path = pathlib.Path(sys.argv[1])
summary_path = pathlib.Path(sys.argv[2])
meta_path = pathlib.Path(sys.argv[3])
wandb_mode = sys.argv[4]

config = json.loads(config_path.read_text(encoding="utf-8"))
summary = json.loads(summary_path.read_text(encoding="utf-8"))
meta = json.loads(meta_path.read_text(encoding="utf-8"))

tags = [
    f"experiment:{config['experiment_family']}",
    f"cell:{config['experiment_cell']}",
    f"orchestration:{config['orchestration_mode']}",
    f"mcp:{config['mcp_mode']}",
    f"model:{config['model_id'].split('/')[-1]}",
]

run = wandb.init(
    entity=config["wandb_entity"],
    project=config["project_name"],
    name=config["run_name"],
    config={k: v for k, v in config.items() if k != "wandb_run_url"},
    tags=tags,
    mode=wandb_mode,
)

run_url = getattr(run, "url", None)
config["wandb_run_url"] = run_url
summary["wandb_run_url"] = run_url
meta["wandb_run_url"] = run_url

run.config.update({"wandb_run_url": run_url}, allow_val_change=True)
run.summary.update(summary)
run.finish()

config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
PY
fi

# Link torch profiler trace to WandB after wandb_run_url is written into meta.json.
# This runs even when ENABLE_WANDB=0 — log_profiling_to_wandb.py is non-fatal if
# wandb_run_url is missing (it still logs a summary to stdout and exits 0).
if [ "${TORCH_PROFILE:-0}" = "1" ] && [ -n "${TORCH_PROFILE_DIR:-}" ]; then
  "$PYTHON_BIN" profiling/scripts/log_profiling_to_wandb.py \
      --benchmark-run-dir "$RUN_DIR" \
      --profiling-dir "$TORCH_PROFILE_DIR" \
      --mode "${WANDB_MODE:-online}" \
      2>>"$HARNESS_LOG" \
    || echo "WARNING: torch profiler WandB link failed (non-fatal)" | tee -a "$HARNESS_LOG"
fi

echo ""
echo "=== Experiment summary ==="
echo "Completed: $PASS / $TOTAL"
echo "Failed:    $FAIL"
echo "Config:    $CONFIG_FILE"
echo "Summary:   $SUMMARY_FILE"
echo "Raw dir:   $RUN_DIR"
if [ "$INFRA_FAIL" -ne 0 ]; then
  echo "Infrastructure failure detected; exiting nonzero."
  exit "$INFRA_FAIL"
fi
