#!/usr/bin/env bash
# Stage-friendly SmartGridBench demo runner.
#
# Runs one scenario through the 8B ZS cell shape, then judges the generated
# trajectory. Use one invocation per scenario so terminal recordings stay easy
# to edit.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

export PATH="$HOME/.local/bin:$PATH"

ENV_SOURCE="none"
if [ -f "$REPO_ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$REPO_ROOT/.env"
  set +a
  ENV_SOURCE="$REPO_ROOT/.env"
fi

PYTHON_BIN="${PYTHON_BIN:-}"
if [ -z "$PYTHON_BIN" ]; then
  if [ -x "$REPO_ROOT/.venv-insomnia/bin/python" ]; then
    PYTHON_BIN="$REPO_ROOT/.venv-insomnia/bin/python"
  else
    PYTHON_BIN="python3"
  fi
fi

SCENARIO_PATH="${1:-data/scenarios/multi_02_dga_to_workorder_pipeline.json}"
CONFIG_SOURCE="${CONFIG_SOURCE:-configs/final_matrix_5x6/ZS_verified_pe_self_ask_mcp_baseline.env}"
TRIALS="${TRIALS:-1}"
DEMO_MAX_MODEL_LEN="${DEMO_MAX_MODEL_LEN:-8192}"
DEMO_ENABLE_WANDB="${DEMO_ENABLE_WANDB:-0}"
JUDGE_OUT="${JUDGE_OUT:-results/metrics/demo_recording_scores.jsonl}"
RUN_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"

if [ ! -f "$SCENARIO_PATH" ]; then
  echo "ERROR: scenario not found: $SCENARIO_PATH" >&2
  exit 1
fi
if [ ! -f "$CONFIG_SOURCE" ]; then
  echo "ERROR: config source not found: $CONFIG_SOURCE" >&2
  exit 1
fi

SCENARIO_ID="$("$PYTHON_BIN" - "$SCENARIO_PATH" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(payload.get("id", Path(sys.argv[1]).stem))
PY
)"
SCENARIO_STEM="$(basename "$SCENARIO_PATH" .json)"
RUN_ID="demo_${RUN_STAMP}_ZS_${SCENARIO_ID}_${SCENARIO_STEM}"
CONFIG_PATH="$(mktemp "${TMPDIR:-/tmp}/smartgrid_demo_config.XXXXXX.env")"
START_EPOCH="$(date +%s)"

elapsed() {
  local now delta h m s
  now="$(date +%s)"
  delta=$((now - START_EPOCH))
  h=$((delta / 3600))
  m=$(((delta % 3600) / 60))
  s=$((delta % 60))
  printf "%02d:%02d:%02d" "$h" "$m" "$s"
}

log() {
  printf '[T+%s] %s\n' "$(elapsed)" "$*"
}

run_with_timer() {
  set +e
  "$@" 2>&1 | while IFS= read -r line; do
    printf '[T+%s] %s\n' "$(elapsed)" "$line"
  done
  local rc=${PIPESTATUS[0]}
  set -e
  return "$rc"
}

cat >"$CONFIG_PATH" <<EOF
source "$CONFIG_SOURCE"

EXPERIMENT_NAME="demo_recording_ZS"
SCENARIO_SET_NAME="demo_recording_single_${SCENARIO_ID}"
SCENARIOS_GLOB="$SCENARIO_PATH"
TRIALS=$TRIALS
SCENARIO_DOMAIN_SCOPE="demo_single"
SMARTGRID_RUN_ID="$RUN_ID"
SMARTGRID_RESUME=0
SMARTGRID_FORCE_RERUN=1
SMARTGRID_RESUME_REQUIRE_LATENCY=0
MAX_MODEL_LEN=$DEMO_MAX_MODEL_LEN
TORCH_PROFILE=0
ENABLE_WANDB=$DEMO_ENABLE_WANDB
WANDB_MODE=disabled
HARNESS_VERBOSE=1
EOF

cleanup() {
  rm -f "$CONFIG_PATH"
}
trap cleanup EXIT

log "SmartGridBench demo recording run"
log "Repo: $REPO_ROOT"
log "Git SHA: $(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
log "Scenario: $SCENARIO_PATH"
log "Cell shape: ZS = verified Plan-Execute + Self-Ask + MCP baseline"
log "Model: Llama-3.1-8B-Instruct via local vLLM"
log "Demo max model length: $DEMO_MAX_MODEL_LEN"
log "Env source: $ENV_SOURCE"
log "Env keys: HF_TOKEN=$([ -n "${HF_TOKEN:-}" ] && echo present || echo missing), WATSONX_APIKEY=$([ -n "${WATSONX_APIKEY:-}" ] && echo present || echo missing)"
log "Run ID: $RUN_ID"

"$PYTHON_BIN" - "$SCENARIO_PATH" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
payload = json.loads(path.read_text(encoding="utf-8"))
print("\n--- Scenario card ---")
print(f"id: {payload.get('id')}")
print(f"type: {payload.get('type')}")
print(f"domains: {', '.join(payload.get('domain_tags', []))}")
print(f"expected tools: {', '.join(payload.get('expected_tools', []))}")
print(f"task: {payload.get('text')}")
print(f"expected behavior: {payload.get('characteristic_form')}")
print("--- End scenario card ---\n")
PY

"$PYTHON_BIN" - "$SCENARIO_ID" <<'PY'
import json
import statistics
import sys
from pathlib import Path

scenario_id = sys.argv[1]
score_path = Path("results/metrics/scenario_scores.jsonl")
rows = []
if score_path.exists():
    for line in score_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        run_name = str(row.get("run_name", ""))
        model_id = str(row.get("model_id", "")).lower()
        cell = str(row.get("experiment_cell", ""))
        is_zs = cell == "ZS" or "_ZS_" in run_name or "cell_ZS_" in run_name
        if row.get("scenario_id") == scenario_id and is_zs and "70b" not in model_id:
            rows.append(row)

if rows:
    scores = [float(r["score_6d"]) for r in rows]
    passes = sum(score >= 0.6 for score in scores)
    print("--- Historical ZS evidence for this scenario ---")
    print(f"rows: {len(rows)}")
    print(f"pass rate: {passes}/{len(rows)}")
    print(f"mean score_6d: {statistics.mean(scores):.3f}")
    print("This is prior evidence only; the next block is a fresh live trial.")
    print("--- End historical evidence ---\n")
PY

log "Trial timer starts now."
log "Running live trajectory capture..."
run_with_timer bash scripts/run_experiment.sh "$CONFIG_PATH"

RUN_DIR="benchmarks/cell_Z_hybrid/raw/$RUN_ID"
if [ ! -d "$RUN_DIR" ]; then
  echo "ERROR: expected run dir missing: $RUN_DIR" >&2
  exit 1
fi

log "Trajectory capture complete: $RUN_DIR"
"$PYTHON_BIN" - "$RUN_DIR" <<'PY'
import json
import sys
from pathlib import Path

run_dir = Path(sys.argv[1])
trajectories = sorted(
    p for p in run_dir.glob("*.json")
    if p.name not in {"meta.json", "resume_manifest.jsonl"} and p.is_file()
)
print("\n--- Live trajectory summary ---")
print(f"run_dir: {run_dir}")
if not trajectories:
    print("no trajectory JSON found")
else:
    path = trajectories[0]
    payload = json.loads(path.read_text(encoding="utf-8"))
    print(f"trajectory: {path.name}")
    print(f"success: {payload.get('success')}")
    print(f"turn_count: {payload.get('turn_count')}")
    print(f"tool_call_count: {payload.get('tool_call_count')}")
    history = payload.get("history") or []
    tools = []
    for item in history:
        if isinstance(item, dict):
            name = item.get("tool") or item.get("tool_name") or item.get("function")
            server = item.get("server")
            if name:
                tools.append(f"{server + '.' if server else ''}{name}")
    if tools:
        print("tool sequence:")
        for i, tool in enumerate(tools, 1):
            print(f"  {i}. {tool}")
    answer = payload.get("answer") or payload.get("final_answer") or ""
    if answer:
        print("final answer:")
        print(answer)
print("--- End live trajectory summary ---\n")
PY

log "Judging trajectory with AssetOpsBench 6D rubric..."
mkdir -p "$(dirname "$JUDGE_OUT")"
if run_with_timer "$PYTHON_BIN" scripts/judge_trajectory.py \
  --run-dir "$RUN_DIR" \
  --scenario-dir data/scenarios \
  --out "$JUDGE_OUT" \
  --force; then
  log "Judge complete: $JUDGE_OUT"
  "$PYTHON_BIN" - "$JUDGE_OUT" "$RUN_ID" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
run_id = sys.argv[2]
rows = []
for line in path.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    row = json.loads(line)
    if run_id in str(row.get("run_name", "")) or run_id in str(row.get("trajectory_file", "")):
        rows.append(row)
if rows:
    row = rows[-1]
    print("\n--- Judge result ---")
    print(f"score_6d: {row.get('score_6d')}")
    print(f"pass: {row.get('pass')}")
    for key in (
        "dim_task_completion",
        "dim_data_retrieval_accuracy",
        "dim_generalized_result_verification",
        "dim_agent_sequence_correct",
        "dim_clarity_and_justification",
        "dim_hallucinations",
    ):
        print(f"{key}: {row.get(key)}")
    if row.get("suggestions"):
        print(f"suggestions: {row['suggestions']}")
    print("--- End judge result ---\n")
PY
else
  log "Live judge failed. Check WatsonX credentials in .env / environment."
  log "Trajectory capture still succeeded; judge can be rerun later with:"
  echo "  $PYTHON_BIN scripts/judge_trajectory.py --run-dir '$RUN_DIR' --scenario-dir data/scenarios --out '$JUDGE_OUT' --force"
  exit 2
fi

log "Demo run complete."
