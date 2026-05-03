# Experiment 2 Capture Plan

*Last updated: 2026-05-03*
*Owner: Wei Alexander Xin (wax1)*

Plan for producing the raw benchmark + profiling artifacts for Experiment 2
(orchestration comparison), issue `#32`. Notebook 03 (`#34`) consumes those
artifacts to compare AaT vs Plan-Execute vs Verified PE on the shared
MCP-baseline transport.

See `docs/experiment1_capture_plan.md` for the sibling exp1 plan; the runner,
profiling pipeline, and WandB conventions are identical.

## Experimental cells

| Cell | Method | Config | Benchmark dir |
|---|---|---|---|
| **B** | Agent-as-Tool (ReAct) | `configs/aat_mcp_baseline.env` | `benchmarks/cell_B_mcp_baseline/` |
| **Y** | Plan-Execute | `configs/experiment2/exp2_cell_Y_pe_mcp_baseline.env` | `benchmarks/cell_Y_plan_execute/` |
| **Z** | Verified PE | `configs/experiment2/exp2_cell_Z_verified_pe_mcp_baseline.env` | `benchmarks/cell_Z_hybrid/` *(legacy dir name)* |

Self-Ask ablation variants (run separately, paired with their baselines via
the run-inventory selector in Notebook 03):

| Cell | Method | Config |
|---|---|---|
| Y + Self-Ask | Plan-Execute + Self-Ask | `configs/experiment2/exp2_cell_Y_pe_self_ask_mcp_baseline.env` |
| Z + Self-Ask | Verified PE + Self-Ask | `configs/experiment2/exp2_cell_Z_verified_pe_self_ask_mcp_baseline.env` |

**Fairness contract.** All cells use the same MCP transport (baseline), the
same scenario slice (`data/scenarios/multi_*.json`), the same model
(`Llama-3.1-8B-Instruct` on Insomnia vLLM), and the same decoding parameters.
The only variable is the orchestration method.

**Runner Python version caveat.** Cell Y (vanilla Plan-Execute) runs upstream
AssetOpsBench's `plan-execute` CLI under its pinned Python 3.12 environment
via `uv run plan-execute` from `$AOB_PATH`. The remaining PE-family cells
(Y + Self-Ask, Z, Z + Self-Ask) use repo-local runners
(`scripts/plan_execute_self_ask_runner.py`, `scripts/verified_pe_runner.py`)
under Python 3.11 from `.venv-insomnia`. Cell B uses `scripts/aat_runner.py`,
also under Python 3.11. The model server, MCP servers, scenario set, and
decoding parameters are identical across all cells — only the orchestration
client's interpreter differs. We keep Cell Y on AOB's pinned 3.12 toolchain
deliberately so it remains "vanilla AOB plan-execute as published," rather
than monkey-patching it to match. Methods section should document this
delta when reporting Cell Y comparisons.

**Shared Cell B.** Cell B is the AaT condition for Experiment 2 *and* the MCP
baseline for Experiment 1. The same `8979314_aat_mcp_baseline` capture is the
canonical anchor for both experiments — do not re-run B for Experiment 2.

**Z directory naming.** The runner case statement in `scripts/run_experiment.sh`
maps `EXPERIMENT_CELL=Z` → `benchmarks/cell_Z_hybrid/` for historical reasons
(the original Z method was "hybrid"). The current Z method is **Verified PE**;
the dir name stays as a legacy alias and Notebook 03 reads it under the
Verified PE label. Renaming would invalidate prior smoke captures and the
validation log entries.

## Current status

First canonical capture set landed via PR `#144` on 2026-04-27. All four
PE-family cells captured at TRIALS=3 × 2 multi-domain scenarios on
Insomnia / `Llama-3.1-8B-Instruct`:

"Completion" = runner-level `success` field per trial (harness loop closed without
error). "Judge-pass" = per-trial `score_6d ≥ 0.6` (the 6-dim Maverick rubric
threshold). Both are independent: a trial can complete the loop and still fail
the judge, or vice-versa.

| Cell | Method | Run ID | Completion | Judge-pass (≥0.6) | Mean `score_6d` |
|---|---|---|---:|---:|---:|
| A | AaT direct (shared) | `8979314_aat_direct` (PR `#130`) | 6/6 | 1/6 | 0.167 |
| B | AaT MCP baseline (shared) | `8979314_aat_mcp_baseline` (PR `#130`) | 6/6 | 2/6 | 0.278 |
| Y | Plan-Execute | `8998340_exp2_cell_Y_pe_mcp_baseline` | 3/6 | 0/6 | 0.111 |
| Y + Self-Ask | Plan-Execute + Self-Ask | `8998341_exp2_cell_Y_pe_self_ask_mcp_baseline` | 6/6 | 3/6 | 0.444 |
| Z | Verified PE | `8998342_exp2_cell_Z_verified_pe_mcp_baseline` | 6/6 | 4/6 | 0.639 |
| Z + Self-Ask | Verified PE + Self-Ask | `8998343_exp2_cell_Z_verified_pe_self_ask_mcp_baseline` | 6/6 | **5/6** | **0.833** |

Hardware caveat: this first PE-family capture was not a single-hardware
cohort. Y/YS/Z landed on Insomnia A6000 nodes, while Z + Self-Ask landed on an
H100 NVL node because the Slurm wrapper then requested generic `--gres=gpu:1`.
Keep that in mind when interpreting the standout ZS 5/6 result; see
`docs/compute_environment_discrepancies.md`.

Pre-canonical smokes still on disk (kept as historical reference, not
analysis sources):

- Cell Y: `benchmarks/cell_Y_plan_execute/raw/local-20260413-003914_*` (Watsonx).
- Cell Z: `benchmarks/cell_Z_hybrid/raw/8857843_verified_pe_mcp_baseline_smoke`.
- Cell Y + Self-Ask: `benchmarks/cell_Y_plan_execute/raw/8857842_pe_self_ask_mcp_baseline_smoke`.

Quality ranking inverts the speed/completion ranking: Z + Self-Ask leads
(5/6 judge-pass, 0.833 mean), B is 4–7× faster end-to-end but only 2/6
scenarios pass the judge. See `results/metrics/scenario_scores.jsonl` and
per-trial logs at `results/judge_logs/<run>/<scenario_id>_judge_log.json`.

What remains for `#32` is the eventual 5×6 final canonical re-run across
all cells once the team agrees on the final scenario set (likely 2 multi
+ 4 single-domain reps, single-domain canonicalization pending). Pinned
in `pm/backlog.md`.

## Runner dispatch

`scripts/run_experiment.sh` reads the config, launches vLLM if requested, and
dispatches by `ORCHESTRATION`:

- `agent_as_tool` → `scripts/aat_runner.py` (no template needed)
- `plan_execute` → upstream AssetOpsBench Plan-Execute path
  (`PLAN_EXECUTE_RUNNER_TEMPLATE` overridable; default is the in-repo path)
- `plan_execute` + `ENABLE_SELF_ASK=1` → `scripts/plan_execute_self_ask_runner.py`
- `verified_pe` → `scripts/verified_pe_runner.py`
- `verified_pe` + `ENABLE_SELF_ASK=1` → same runner with the Self-Ask flag

Profiling is driven by `TORCH_PROFILE=1` (now set in all four exp2 configs)
and `profiling/scripts/capture_around.sh` for the nvidia-smi + Nsight pass.

## Recommended run sequence on Insomnia

Run from the repo root inside the shared `.venv-insomnia` environment.

```bash
# 1. Y baseline (5 trials × 2 multi-domain scenarios per the config; ~15-20 min including vLLM warmup)
sbatch --wait --mail-type=BEGIN,END,FAIL --mail-user=$MAIL_USER \
    scripts/run_experiment.sh configs/experiment2/exp2_cell_Y_pe_mcp_baseline.env

# 2. Y + Self-Ask (paired with #1 for the ablation row in Notebook 03)
sbatch --wait \
    scripts/run_experiment.sh configs/experiment2/exp2_cell_Y_pe_self_ask_mcp_baseline.env

# 3. Z baseline
sbatch --wait \
    scripts/run_experiment.sh configs/experiment2/exp2_cell_Z_verified_pe_mcp_baseline.env

# 4. Z + Self-Ask
sbatch --wait \
    scripts/run_experiment.sh configs/experiment2/exp2_cell_Z_verified_pe_self_ask_mcp_baseline.env
```

After each run completes, the run dir lands under
`benchmarks/cell_<Y|Z>_*/raw/<slurm_job_id>_<EXPERIMENT_NAME>/`. The next
notebook execution picks them up automatically (latest-run selection by
`meta.json.started_at`).

## Notebook 03 expectations

Notebook 03 (`#34`) is staged so that it produces real outputs as soon as any
of the four runs above commits artifacts:

- the orchestration comparison plot draws Cell B alongside whichever PE-family
  cells have data, with hatched placeholders for the missing ones
- the Self-Ask ablation table emits a row for each (baseline, self-ask) pair
  where both runs are committed
- the run-inventory preflight CSV always emits so reviewers can see what's
  classified as baseline vs Self-Ask before any plot is generated

## Open decisions

1. **Trial count.** Configs default to 5 trials × 2 multi-domain scenarios.
   Increase to 5 × 6 once the single-domain scenarios are part of the
   canonical exp2 slice.
2. **Scenario slice expansion.** Same as exp1 question — keep
   `multi_*.json` only, or include `iot_*`, `fmsr_*`, `tsfm_*`, `wo_*`.
3. **Judge scoring.** Currently `JUDGE_MODEL=""` in all four configs.
   Notebook 03 falls back to success-rate / failure-breakdown when judge
   scores are absent. Add a judge if the paper needs scored quality, not just
   latency + success.

## What the merge unlocks

Once these four runs land:

- Notebook 03's headline orchestration comparison (B vs Y vs Z) becomes real
- Notebook 03's Self-Ask ablation rows emit non-empty deltas
- The PE-family follow-on figure populates
- Issue `#32` closes; issue `#34` advances from "scaffolded" to "publishing"
