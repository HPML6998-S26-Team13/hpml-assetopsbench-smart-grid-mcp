# configs/

Experiment configs consumed by [scripts/run_experiment.sh](../scripts/run_experiment.sh).
Each file describes one benchmark cell (or one smoke run that maps to a benchmark
cell) and is sourced as bash, so the schema is just env vars.

The currently verified benchmark-facing execution paths are:

- `ORCHESTRATION=plan_execute`
- `ORCHESTRATION=plan_execute` with `ENABLE_SELF_ASK=1`
- `ORCHESTRATION=verified_pe`
- `ORCHESTRATION=verified_pe` with `ENABLE_SELF_ASK=1`
- `ENABLE_SMARTGRID_SERVERS=1`
- Smart Grid MCP servers passed into AssetOpsBench `plan-execute` or the
  repo-local PE-family wrappers via the same server-path contract

Agent-as-Tool now uses the repo-local default runner at `scripts/aat_runner.py`
(no template required). Repo-local Verified PE runner code exists; this branch
promotes the canonical Experiment 2 Cell Z config out of the legacy placeholder
and adds the Y/Z + Self-Ask variants. See
[../docs/orchestration_wiring.md](../docs/orchestration_wiring.md).

## Naming

Use the cell name from [../docs/execution_plan.md](../docs/execution_plan.md).
The execution-facing config convention is:

- `configs/aat_{direct,mcp_baseline,mcp_optimized}.env` for the canonical
  Experiment 1 Cell A / B / C runs
- `configs/aat_mcp_model_optimized.env` for exploratory Cell D, which stacks
  optimized AaT MCP transport with model-side INT8/BF16/fp8-KV serving
- `configs/experiment2/` for the extra Experiment 2 templates that do not
  already exist on `main` (currently the Plan-Execute / Cell Y lane and the
  optional Cell Z follow-on plus the PE-family Self-Ask and optimized-serving
  ablations)

The active cell mapping is:

| Cell | Orchestration | MCP mode | Suggested config name |
|---|---|---|---|
| A | Agent-as-Tool | direct | `aat_direct.env` |
| B | Agent-as-Tool | baseline | `aat_mcp_baseline.env` |
| C | Agent-as-Tool | optimized | `aat_mcp_optimized.env` |
| D | Agent-as-Tool | optimized + model-side | `aat_mcp_model_optimized.env` |
| Y | Plan-Execute | baseline | `experiment2/exp2_cell_Y_pe_mcp_baseline.env` |
| Y + Self-Ask | Plan-Execute | baseline | `experiment2/exp2_cell_Y_pe_self_ask_mcp_baseline.env` |
| Z | Verified PE follow-on | baseline | `experiment2/exp2_cell_Z_verified_pe_mcp_baseline.env` |
| Z + Self-Ask | Verified PE follow-on | baseline | `experiment2/exp2_cell_Z_verified_pe_self_ask_mcp_baseline.env` |
| Z + Self-Ask + D | Verified PE + Self-Ask | optimized + model-side | `experiment2/exp2_cell_ZSD_verified_pe_self_ask_mcp_model_optimized.env` |

## Required keys

- `EXPERIMENT_NAME` — short label; becomes part of the run ID
- `EXPERIMENT_CELL` — one of `A`, `B`, `C`, `D`, `Y`, `Z`, `ZSD`
- `EXPERIMENT_FAMILY` — e.g. `exp1_mcp_overhead`, `exp2_orchestration`, `smoke`
- `SCENARIOS_GLOB` — scenario files relative to repo root
- `SCENARIO_SET_NAME` — stable label for the scenario pack
- `MODEL_ID` — model string passed to AssetOpsBench `plan-execute`

## Important optional keys

- `ORCHESTRATION` — `plan_execute`, `agent_as_tool`, or `verified_pe`
- `MCP_MODE` — `direct`, `baseline`, or `optimized`
- `ENABLE_SMARTGRID_SERVERS` — when `1`, pass this repo's four Smart Grid MCP
  servers into `plan-execute`
- `ENABLE_WANDB` — when `1`, write the canonical config + summary fields to a
  WandB run after the benchmark finishes
- `LAUNCH_VLLM` — when `1`, launch the local vLLM server first and point
  AssetOpsBench's LiteLLM client at `http://127.0.0.1:<port>/v1`
- `VLLM_DTYPE` — vLLM `--dtype`; defaults to `float16`, but Cell D uses
  `bfloat16` for the compressed-tensors INT8 / fp8-KV stack
- `AOB_PATH` — path to the sibling AssetOpsBench checkout; defaults to
  `../AssetOpsBench` relative to the shared project root, so it also works from
  a git worktree

### Orchestration-specific adapter hooks

- `AAT_RUNNER_TEMPLATE` — optional override when
  `ORCHESTRATION=agent_as_tool`; otherwise the harness runs
  `scripts/aat_runner.py`
- `AAT_PARALLEL_TOOL_CALLS` — optional AaT runner setting for the OpenAI
  Agents SDK; defaults to `false` for local vLLM Llama 3 tool-call compatibility
- `HYBRID_RUNNER_TEMPLATE` — required only for the legacy `hybrid` placeholder
  path
- `VERIFIED_PE_RUNNER_TEMPLATE` — optional override when
  `ORCHESTRATION=verified_pe`; otherwise the repo-local Verified PE runner is
  used

These are intentionally explicit. AaT now has a default benchmark dispatch
path; templates are reserved for parity smoke checks and one-off variants.

## Running

Dry-run the wiring first:

```bash
DRY_RUN=1 bash scripts/run_experiment.sh configs/example_baseline.env
# or
DRY_RUN=1 bash scripts/run_experiment.sh configs/experiment2/exp2_cell_Y_pe_mcp_baseline.env
```

Submit the real job:

```bash
sbatch scripts/run_experiment.sh configs/aat_mcp_baseline.env
```

## Output layout

Outputs follow the canonical `benchmarks/` shape:

- `benchmarks/cell_<...>/config.json` — reproducibility config, later patched
  with `wandb_run_url`
- `benchmarks/cell_<...>/summary.json` — aggregate summary for the most recent
  run of that cell
- `benchmarks/cell_<...>/raw/<run-id>/` — run-scoped raw outputs and logs
  - one JSON file per scenario-trial
  - `latencies.jsonl`
  - `harness.log`
  - `vllm.log` when local vLLM launch is enabled
  - `meta.json`

## Status

As of Apr 30, 2026:

- Plan-Execute wiring is implemented through AssetOpsBench's canonical
  `plan-execute` CLI with explicit Smart Grid server overrides.
- WandB config + summary emission is wired in the benchmark runner.
- Experiment 1 analysis still maps to Cells A / B / C, but the execution
  configs for those lanes stay on the canonical `configs/aat_*.env` names that
  `main` already documents.
- AaT now uses `scripts/aat_runner.py` by default; templates only for variants.
- Verified PE / PE + Self-Ask are already runnable on the canonical harness
  path. Cell Z raw run set still needs to be captured before Z is a
  notebook-ready follow-on lane.
- Repo-local PE-family runners can use `MCP_MODE=optimized` to reuse initialized
  MCP stdio sessions inside a scenario run. The first committed user is the
  exploratory `ZSD` config, which stacks Verified PE + Self-Ask with the Cell D
  INT8/BF16/fp8-KV serving profile. Slurm job
  `9074775_exp2_cell_ZSD_verified_pe_self_ask_mcp_model_optimized` is the first
  successful ZSD proof run (`6 / 6`, W&B `48nqpclw`, judge mean `0.611`).
