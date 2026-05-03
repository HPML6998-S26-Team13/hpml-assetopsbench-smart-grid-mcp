#!/usr/bin/env bash
set -euo pipefail
cd /home/wax/hpml-final-grid-git
source .venv-insomnia/bin/activate
export PATH="$HOME/.local/bin:$(dirname "$(g++ -print-prog-name=cc1plus)"):$PATH"
export SMARTGRID_COMPUTE_PROVIDER=gcp
export SMARTGRID_COMPUTE_ZONE=us-central1-a
export SMARTGRID_COMPUTE_INSTANCE=smartgrid-a100-spot-20260503-0217
export GPU_TYPE="NVIDIA A100-SXM4-40GB"
export SMARTGRID_BATCH_ID=final5x6_a100_20260503T090200Z
export SMARTGRID_RESUME=1
export SMARTGRID_FORCE_RERUN=1
export SMARTGRID_RESUME_REQUIRE_LATENCY=1
export PLAN_EXECUTE_REPO_LOCAL=1
export AOB_PYTHON=/home/wax/AssetOpsBench/.venv/bin/python
python3 - <<PY
from pathlib import Path
bad = {
    "final5x6_a100_20260503T090200Z_Y_final5x6_exp2_cell_Y_pe_mcp_baseline",
    "final5x6_a100_20260503T090200Z_YS_final5x6_exp2_cell_Y_pe_self_ask_mcp_baseline",
    "final5x6_a100_20260503T090200Z_Z_final5x6_exp2_cell_Z_verified_pe_mcp_baseline",
    "final5x6_a100_20260503T090200Z_ZS_final5x6_exp2_cell_Z_verified_pe_self_ask_mcp_baseline",
}
path = Path("results/metrics/scenario_scores.jsonl")
if path.exists():
    lines = path.read_text().splitlines()
    kept = [line for line in lines if not any(run in line for run in bad)]
    path.write_text("\n".join(kept) + ("\n" if kept else ""))
    print(f"Filtered scenario_scores.jsonl: removed {len(lines)-len(kept)} stale PE-family rows")
PY
run_row() {
  local label="$1" config="$2" run_id="$3" run_dir="$4"
  export SMARTGRID_RUN_ID="$run_id"
  echo "=== rerun $label $run_id ==="
  bash scripts/run_experiment.sh "$config"
  echo "=== judge $label $run_id ==="
  python3 scripts/judge_trajectory.py \
    --run-dir "$run_dir" \
    --scenario-dir data/scenarios \
    --out results/metrics/scenario_scores.jsonl \
    --log-dir results/judge_logs
}
run_row Y configs/final_matrix_5x6/Y_pe_mcp_baseline.env final5x6_a100_20260503T090200Z_Y_final5x6_exp2_cell_Y_pe_mcp_baseline benchmarks/cell_Y_plan_execute/raw/final5x6_a100_20260503T090200Z_Y_final5x6_exp2_cell_Y_pe_mcp_baseline
run_row YS configs/final_matrix_5x6/YS_pe_self_ask_mcp_baseline.env final5x6_a100_20260503T090200Z_YS_final5x6_exp2_cell_Y_pe_self_ask_mcp_baseline benchmarks/cell_Y_plan_execute/raw/final5x6_a100_20260503T090200Z_YS_final5x6_exp2_cell_Y_pe_self_ask_mcp_baseline
run_row Z configs/final_matrix_5x6/Z_verified_pe_mcp_baseline.env final5x6_a100_20260503T090200Z_Z_final5x6_exp2_cell_Z_verified_pe_mcp_baseline benchmarks/cell_Z_hybrid/raw/final5x6_a100_20260503T090200Z_Z_final5x6_exp2_cell_Z_verified_pe_mcp_baseline
run_row ZS configs/final_matrix_5x6/ZS_verified_pe_self_ask_mcp_baseline.env final5x6_a100_20260503T090200Z_ZS_final5x6_exp2_cell_Z_verified_pe_self_ask_mcp_baseline benchmarks/cell_Z_hybrid/raw/final5x6_a100_20260503T090200Z_ZS_final5x6_exp2_cell_Z_verified_pe_self_ask_mcp_baseline
