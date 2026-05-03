#!/usr/bin/env bash
# Canonical GCP context-window closeout launcher.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

COHORT_TSV="${COHORT_TSV:-configs/gcp_context_closeout.tsv}"
BATCH_ID="${SMARTGRID_BATCH_ID:-gcp_context_$(date -u +%Y%m%dT%H%M%SZ)}"
STATE_FILE="${STATE_FILE:-}"
MANIFEST_TSV="${MANIFEST_TSV:-}"
MANIFEST_JSONL="${MANIFEST_JSONL:-}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
DRY_RUN="${DRY_RUN:-0}"
RUN_JUDGE=1
ROWS_FILTER=""

usage() {
  cat <<'EOF'
Usage: scripts/run_gcp_context_batch.sh [--batch-id ID|--resume-batch ID] [--rows A,B] [--dry-run] [--no-judge]

Runs the canonical seven-row GCP context closeout cohort with stable run IDs,
SMARTGRID_RESUME=1, per-row manifest/state files, and idempotent judge scoring.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --batch-id)
      BATCH_ID="$2"; shift 2 ;;
    --resume-batch)
      BATCH_ID="$2"; shift 2 ;;
    --rows)
      ROWS_FILTER=",$2,"; shift 2 ;;
    --dry-run)
      DRY_RUN=1; shift ;;
    --no-judge)
      RUN_JUDGE=0; shift ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 2 ;;
  esac
done

[ -n "$STATE_FILE" ] || STATE_FILE="logs/gcp_${BATCH_ID}_state.tsv"
[ -n "$MANIFEST_TSV" ] || MANIFEST_TSV="logs/gcp_${BATCH_ID}_manifest.tsv"
[ -n "$MANIFEST_JSONL" ] || MANIFEST_JSONL="logs/gcp_${BATCH_ID}_manifest.jsonl"
mkdir -p logs results/metrics results/judge_logs

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

state_value() {
  local label="$1" field="$2"
  [ -f "$STATE_FILE" ] || return 0
  awk -F'\t' -v label="$label" -v field="$field" '
    NR == 1 {
      for (i = 1; i <= NF; i++) idx[$i] = i
      next
    }
    $1 == label && idx[field] { value = $idx[field] }
    END {
      if (value != "") print value
    }
  ' "$STATE_FILE"
}

append_state() {
  if [ ! -f "$STATE_FILE" ]; then
    printf 'label\tconfig\trun_id\tstatus\tstarted_at\tfinished_at\n' >"$STATE_FILE"
  fi
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" "$5" "$6" >>"$STATE_FILE"
}

append_manifest() {
  local label="$1" config="$2" run_id="$3" run_dir="$4" run_rc="$5" judge_rc="$6" status="$7" started="$8" finished="$9"
  if [ ! -f "$MANIFEST_TSV" ]; then
    printf 'label\tconfig\trun_id\trun_dir\trun_rc\tjudge_rc\tstatus\tstarted_at\tfinished_at\tprovider\tzone\tinstance\tgpu_type\n' >"$MANIFEST_TSV"
  fi
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$label" "$config" "$run_id" "$run_dir" "$run_rc" "$judge_rc" "$status" "$started" "$finished" \
    "${SMARTGRID_COMPUTE_PROVIDER:-gcp}" "${SMARTGRID_COMPUTE_ZONE:-}" "${SMARTGRID_COMPUTE_INSTANCE:-$(hostname)}" "${GPU_TYPE:-}" \
    >>"$MANIFEST_TSV"
  "$PYTHON_BIN" - "$MANIFEST_JSONL" "$label" "$config" "$run_id" "$run_dir" "$run_rc" "$judge_rc" "$status" "$started" "$finished" <<'PY'
import json
import os
import pathlib
import sys

path, label, config, run_id, run_dir, run_rc, judge_rc, status, started, finished = sys.argv[1:]
payload = {
    "schema_version": 1,
    "label": label,
    "config": config,
    "run_id": run_id,
    "run_dir": run_dir,
    "run_rc": None if run_rc == "" else int(run_rc),
    "judge_rc": None if judge_rc == "" else int(judge_rc),
    "status": status,
    "started_at": started,
    "finished_at": finished,
    "compute_provider": os.environ.get("SMARTGRID_COMPUTE_PROVIDER", "gcp"),
    "compute_zone": os.environ.get("SMARTGRID_COMPUTE_ZONE"),
    "compute_instance": os.environ.get("SMARTGRID_COMPUTE_INSTANCE") or os.uname().nodename,
    "gpu_type": os.environ.get("GPU_TYPE"),
}
pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
with pathlib.Path(path).open("a", encoding="utf-8") as fh:
    fh.write(json.dumps(payload, sort_keys=True) + "\n")
PY
}

preflight_runtime() {
  [ "$DRY_RUN" = "1" ] && return 0
  command -v "$PYTHON_BIN" >/dev/null
  command -v g++ >/dev/null
  command -v cc1plus >/dev/null
  if command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi -L >/dev/null
  fi
  "$PYTHON_BIN" - <<'PY'
import importlib.util
import sys

if sys.version_info < (3, 11):
    raise SystemExit("Python >=3.11 required")
for module in ("torch", "vllm"):
    if importlib.util.find_spec(module) is None:
        raise SystemExit(f"{module} is not importable")
PY
}

preflight_boot_disk_autodelete() {
  [ "$DRY_RUN" = "1" ] && return 0
  [ -n "${SMARTGRID_COMPUTE_INSTANCE:-}" ] || return 0
  [ -n "${SMARTGRID_COMPUTE_ZONE:-}" ] || return 0
  command -v gcloud >/dev/null 2>&1 || return 0
  local autodelete
  autodelete="$(
    gcloud compute instances describe "$SMARTGRID_COMPUTE_INSTANCE" \
      --zone "$SMARTGRID_COMPUTE_ZONE" \
      --format='value(disks[0].autoDelete)' 2>/dev/null || true
  )"
  if [ "$autodelete" = "True" ] || [ "$autodelete" = "true" ]; then
    echo "ERROR: boot disk autoDelete=true for $SMARTGRID_COMPUTE_INSTANCE; set autoDelete=false before capture." >&2
    return 1
  fi
}

preflight_runtime
preflight_boot_disk_autodelete

tail -n +2 "$COHORT_TSV" | while IFS=$'\t' read -r label config; do
  [ -n "$label" ] || continue
  if [ -n "$ROWS_FILTER" ] && [[ "$ROWS_FILTER" != *",$label,"* ]]; then
    continue
  fi
  if [ ! -f "$config" ]; then
    echo "ERROR: config missing for $label: $config" >&2
    exit 1
  fi
  existing_run_id="$(state_value "$label" run_id || true)"
  existing_status="$(state_value "$label" status || true)"
  # shellcheck disable=SC1090
  source "$config"
  run_id="${existing_run_id:-${BATCH_ID}_${label}_${EXPERIMENT_NAME}}"
  run_dir="benchmarks/$(cell_dir_name "$EXPERIMENT_CELL")/raw/$run_id"
  started="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

  if [ "$existing_status" = "complete" ]; then
    echo "Skipping $label: already complete in $STATE_FILE"
    append_manifest "$label" "$config" "$run_id" "$run_dir" "" "" "skipped_complete" "$started" "$started"
    continue
  fi

  append_state "$label" "$config" "$run_id" "started" "$started" ""

  if [ "$DRY_RUN" = "1" ]; then
    echo "DRY_RUN $label: SMARTGRID_RUN_ID=$run_id bash scripts/run_experiment.sh $config"
    append_state "$label" "$config" "$run_id" "dry_run" "$started" "$started"
    append_manifest "$label" "$config" "$run_id" "$run_dir" "" "" "dry_run" "$started" "$started"
    continue
  fi

  run_rc=0
  SMARTGRID_BATCH_ID="$BATCH_ID" \
  SMARTGRID_RUN_ID="$run_id" \
  SMARTGRID_RESUME=1 \
  SMARTGRID_COMPUTE_PROVIDER="${SMARTGRID_COMPUTE_PROVIDER:-gcp}" \
  SMARTGRID_COMPUTE_INSTANCE="${SMARTGRID_COMPUTE_INSTANCE:-$(hostname)}" \
    bash scripts/run_experiment.sh "$config" || run_rc=$?

  judge_rc=0
  if [ "$RUN_JUDGE" = "1" ]; then
    "$PYTHON_BIN" scripts/judge_trajectory.py \
      --run-dir "$run_dir" \
      --scenario-dir data/scenarios \
      --out results/metrics/scenario_scores.jsonl \
      --log-dir results/judge_logs || judge_rc=$?
  fi
  finished="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  status="complete"
  [ "$run_rc" -ne 0 ] && status="run_failed"
  [ "$judge_rc" -ne 0 ] && status="judge_failed"
  append_state "$label" "$config" "$run_id" "$status" "$started" "$finished"
  append_manifest "$label" "$config" "$run_id" "$run_dir" "$run_rc" "$judge_rc" "$status" "$started" "$finished"
done
