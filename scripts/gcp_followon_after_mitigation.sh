#!/usr/bin/env bash
# Wait for the final-six mitigation cohort, validate it, then run PE-family
# optimized-transport follow-ons on the same GCP VM.
set -euo pipefail

MITIGATION_BATCH_ID="${MITIGATION_BATCH_ID:-mitigation_final6_4tier_a100_20260503T121709Z}"
WAIT_TMUX="${WAIT_TMUX:-continue_final5x6_then_mitigation}"
FOLLOWON_COHORT_TSV="${FOLLOWON_COHORT_TSV:-configs/final_matrix_5x6/followon_transport.tsv}"
FOLLOWON_BATCH_ID="${FOLLOWON_BATCH_ID:-final5x6_followon_transport_a100_$(date -u +%Y%m%dT%H%M%SZ)}"
POLL_SECONDS="${POLL_SECONDS:-120}"

log() {
  printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"
}

setup_env() {
  # shellcheck disable=SC1091
  source .venv-insomnia/bin/activate
  export PATH="$HOME/.local/bin:$(dirname "$(g++ -print-prog-name=cc1plus)"):$PATH"
  export SMARTGRID_COMPUTE_PROVIDER="${SMARTGRID_COMPUTE_PROVIDER:-gcp}"
  export SMARTGRID_COMPUTE_ZONE="${SMARTGRID_COMPUTE_ZONE:-us-central1-a}"
  export SMARTGRID_COMPUTE_INSTANCE="${SMARTGRID_COMPUTE_INSTANCE:-smartgrid-a100-spot-20260503-0217}"
  export GPU_TYPE="${GPU_TYPE:-NVIDIA A100-SXM4-40GB}"
  export PLAN_EXECUTE_REPO_LOCAL="${PLAN_EXECUTE_REPO_LOCAL:-1}"
  export AOB_PYTHON="${AOB_PYTHON:-/home/wax/AssetOpsBench/.venv/bin/python}"
  export SMARTGRID_RESUME=1
  export PYTHON_BIN="${PYTHON_BIN:-python}"
  unset SMARTGRID_FORCE_RERUN
}

state_run_id() {
  local label="$1"
  awk -F '\t' -v label="$label" '$1 == label { run_id = $3 } END { print run_id }' \
    "logs/gcp_${MITIGATION_BATCH_ID}_state.tsv"
}

run_dir_for_label() {
  local label="$1" run_id="$2"
  case "$label" in
    YS*) printf 'benchmarks/cell_Y_plan_execute/raw/%s\n' "$run_id" ;;
    ZS*) printf 'benchmarks/cell_Z_hybrid/raw/%s\n' "$run_id" ;;
    *) return 1 ;;
  esac
}

count_json() {
  find "$1" -maxdepth 1 -name '*_run[0-9][0-9].json' 2>/dev/null | wc -l | tr -d ' '
}

count_latencies() {
  wc -l "$1/latencies.jsonl" 2>/dev/null | awk '{ print $1 + 0 }'
}

count_scores() {
  grep -c "$1" results/metrics/scenario_scores.jsonl 2>/dev/null | awk '{ print $1 + 0 }'
}

validate_mitigation() {
  local ok=0
  local labels=(
    YS_BASELINE
    ZS_BASELINE
    YS_GUARD
    ZS_GUARD
    YS_REPAIR
    ZS_REPAIR
    YS_ADJ
    ZS_ADJ
  )
  for label in "${labels[@]}"; do
    local run_id run_dir json_count latency_count score_count
    run_id="$(state_run_id "$label")"
    run_dir="$(run_dir_for_label "$label" "$run_id")"
    json_count="$(count_json "$run_dir")"
    latency_count="$(count_latencies "$run_dir")"
    score_count="$(count_scores "$run_id")"
    log "validate $label run_id=$run_id json=$json_count lat=$latency_count scores=$score_count"
    if [ -z "$run_id" ] || [ "$json_count" -lt 30 ] || [ "$latency_count" -lt 30 ] || [ "$score_count" -lt 30 ]; then
      ok=1
    fi
  done
  return "$ok"
}

main() {
  setup_env
  log "waiting for tmux session $WAIT_TMUX"
  while tmux has-session -t "$WAIT_TMUX" 2>/dev/null; do
    sleep "$POLL_SECONDS"
  done
  log "tmux session $WAIT_TMUX ended; validating mitigation batch $MITIGATION_BATCH_ID"
  validate_mitigation
  log "starting follow-on transport batch $FOLLOWON_BATCH_ID"
  export SMARTGRID_BATCH_ID="$FOLLOWON_BATCH_ID"
  export COHORT_TSV="$FOLLOWON_COHORT_TSV"
  bash scripts/run_gcp_context_batch.sh --resume-batch "$FOLLOWON_BATCH_ID"
  log "follow-on transport batch complete: $FOLLOWON_BATCH_ID"
}

main "$@"
