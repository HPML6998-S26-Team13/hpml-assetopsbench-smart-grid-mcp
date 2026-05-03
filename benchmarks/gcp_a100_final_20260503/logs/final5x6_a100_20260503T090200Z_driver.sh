#!/usr/bin/env bash
set -euo pipefail
cd /home/wax/hpml-final-grid-git
source .venv-insomnia/bin/activate
export PATH="$HOME/.local/bin:$(dirname "$(g++ -print-prog-name=cc1plus)"):$PATH"
export SMARTGRID_COMPUTE_PROVIDER=gcp
export SMARTGRID_COMPUTE_ZONE=us-central1-a
export SMARTGRID_COMPUTE_INSTANCE=smartgrid-a100-spot-20260503-0217
export GPU_TYPE="NVIDIA A100-SXM4-40GB"
export COHORT_TSV=configs/final_matrix_5x6/cohort.tsv
export SMARTGRID_BATCH_ID=final5x6_a100_20260503T090200Z
export PYTHON_BIN=python3
bash scripts/run_gcp_context_batch.sh --resume-batch final5x6_a100_20260503T090200Z
