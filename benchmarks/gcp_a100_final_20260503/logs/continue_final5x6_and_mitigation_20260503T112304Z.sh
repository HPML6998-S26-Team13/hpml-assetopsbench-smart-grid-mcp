#!/usr/bin/env bash
set -uo pipefail
cd /home/wax/hpml-final-grid-git

log() { printf "[%s] %s\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }

setup_env() {
  # shellcheck disable=SC1091
  source .venv-insomnia/bin/activate
  export PATH="$HOME/.local/bin:$(dirname "$(g++ -print-prog-name=cc1plus)"):$PATH"
  export SMARTGRID_COMPUTE_PROVIDER=gcp
  export SMARTGRID_COMPUTE_ZONE=us-central1-a
  export SMARTGRID_COMPUTE_INSTANCE=smartgrid-a100-spot-20260503-0217
  export GPU_TYPE="NVIDIA A100-SXM4-40GB"
  export PLAN_EXECUTE_REPO_LOCAL=1
  export AOB_PYTHON=/home/wax/AssetOpsBench/.venv/bin/python
  export SMARTGRID_RESUME=1
  export PYTHON_BIN=python
  unset SMARTGRID_FORCE_RERUN
}

count_json() { find "$1" -maxdepth 1 -name "*_run[0-9][0-9].json" 2>/dev/null | wc -l | tr -d " "; }
count_lat() { wc -l "$1/latencies.jsonl" 2>/dev/null | awk "{print \$1+0}"; }
count_scores() { grep -c "$2" results/metrics/scenario_scores.jsonl 2>/dev/null | awk "{print \$1+0}"; }

validate_run() {
  local label="$1" run_dir="$2" run_id="$3"
  local json_count lat_count score_count
  json_count=$(count_json "$run_dir")
  lat_count=$(count_lat "$run_dir")
  score_count=$(count_scores "$run_dir" "$run_id")
  log "validate $label json=$json_count lat=$lat_count scores=$score_count run_id=$run_id"
  if [ "$json_count" -lt 30 ] || [ "$lat_count" -lt 30 ] || [ "$score_count" -lt 30 ]; then
    log "ERROR: $label incomplete after repair; stopping continuation before extra/mitigation batches."
    return 1
  fi
  return 0
}

validate_core() {
  local ok=0
  validate_run A benchmarks/cell_A_direct/raw/final5x6_a100_20260503T090200Z_A_final5x6_aat_direct final5x6_a100_20260503T090200Z_A_final5x6_aat_direct || ok=1
  validate_run B benchmarks/cell_B_mcp_baseline/raw/final5x6_a100_20260503T090200Z_B_final5x6_aat_mcp_baseline final5x6_a100_20260503T090200Z_B_final5x6_aat_mcp_baseline || ok=1
  validate_run C benchmarks/cell_C_mcp_optimized/raw/final5x6_a100_20260503T090200Z_C_final5x6_aat_mcp_optimized final5x6_a100_20260503T090200Z_C_final5x6_aat_mcp_optimized || ok=1
  validate_run Y benchmarks/cell_Y_plan_execute/raw/final5x6_a100_20260503T090200Z_Y_final5x6_exp2_cell_Y_pe_mcp_baseline final5x6_a100_20260503T090200Z_Y_final5x6_exp2_cell_Y_pe_mcp_baseline || ok=1
  validate_run YS benchmarks/cell_Y_plan_execute/raw/final5x6_a100_20260503T090200Z_YS_final5x6_exp2_cell_Y_pe_self_ask_mcp_baseline final5x6_a100_20260503T090200Z_YS_final5x6_exp2_cell_Y_pe_self_ask_mcp_baseline || ok=1
  validate_run Z benchmarks/cell_Z_hybrid/raw/final5x6_a100_20260503T090200Z_Z_final5x6_exp2_cell_Z_verified_pe_mcp_baseline final5x6_a100_20260503T090200Z_Z_final5x6_exp2_cell_Z_verified_pe_mcp_baseline || ok=1
  validate_run ZS benchmarks/cell_Z_hybrid/raw/final5x6_a100_20260503T090200Z_ZS_final5x6_exp2_cell_Z_verified_pe_self_ask_mcp_baseline final5x6_a100_20260503T090200Z_ZS_final5x6_exp2_cell_Z_verified_pe_self_ask_mcp_baseline || ok=1
  return "$ok"
}

run_batch() {
  local batch_id="$1" cohort="$2" label="$3"
  log "starting $label batch_id=$batch_id cohort=$cohort"
  if [ ! -f "$cohort" ]; then
    log "ERROR: cohort missing: $cohort"
    return 1
  fi
  export SMARTGRID_BATCH_ID="$batch_id"
  export COHORT_TSV="$cohort"
  bash scripts/run_gcp_context_batch.sh --resume-batch "$batch_id"
  local rc=$?
  log "finished $label rc=$rc batch_id=$batch_id"
  return "$rc"
}

setup_env
log "continuation driver started"
while tmux has-session -t repair_final5x6_pe 2>/dev/null; do
  log "waiting for repair_final5x6_pe to finish"
  sleep 120
done
log "repair session no longer present; validating core rows"
if ! validate_core; then
  exit 2
fi

extra_batch="final5x6_extra_a100_$(date -u +%Y%m%dT%H%M%SZ)"
run_batch "$extra_batch" configs/final_matrix_5x6/extra_variants.tsv "D/ZSD extra variants"
extra_rc=$?

mit_batch="mitigation_final6_4tier_a100_$(date -u +%Y%m%dT%H%M%SZ)"
run_batch "$mit_batch" configs/mitigation_final6_5x6/cohort_4tier.tsv "4-tier mitigation"
mit_rc=$?

log "continuation complete extra_rc=$extra_rc mit_rc=$mit_rc extra_batch=$extra_batch mit_batch=$mit_batch"
exit $(( extra_rc != 0 || mit_rc != 0 ))
