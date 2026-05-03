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
export SMARTGRID_RUN_ID=final5x6_a100_20260503T090200Z_Y_final5x6_exp2_cell_Y_pe_mcp_baseline
export SMARTGRID_RESUME=1
export SMARTGRID_FORCE_RERUN=1
export SMARTGRID_RESUME_REQUIRE_LATENCY=1
export PLAN_EXECUTE_REPO_LOCAL=1
bash scripts/run_experiment.sh configs/final_matrix_5x6/Y_pe_mcp_baseline.env
python3 scripts/judge_trajectory.py \
  --run-dir benchmarks/cell_Y_plan_execute/raw/final5x6_a100_20260503T090200Z_Y_final5x6_exp2_cell_Y_pe_mcp_baseline \
  --scenario-dir data/scenarios \
  --out results/metrics/scenario_scores.jsonl \
  --log-dir results/judge_logs
