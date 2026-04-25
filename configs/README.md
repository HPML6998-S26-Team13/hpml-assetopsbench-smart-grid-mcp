# configs/

Experiment configs consumed by [scripts/run_experiment.sh](../scripts/run_experiment.sh).
Each file describes one benchmark cell (or one smoke run that maps to a benchmark
cell) and is sourced as bash, so the schema is just env vars.

The currently verified benchmark-facing execution path is:

- `ORCHESTRATION=plan_execute`
- `ENABLE_SMARTGRID_SERVERS=1`
- Smart Grid MCP servers passed into AssetOpsBench `plan-execute` via repeated
  `--server name=path` overrides

Agent-as-Tool still needs an explicit external runner command. Repo-local
Verified PE runner code exists, but the canonical Experiment 2 Cell Z config is
still pending promotion from the legacy placeholder. See
[../docs/orchestration_wiring.md](../docs/orchestration_wiring.md).

## Naming

Use the cell name from [../docs/execution_plan.md](../docs/execution_plan.md).
The execution-facing config convention is:

- `configs/aat_{direct,mcp_baseline,mcp_optimized}.env` for the canonical
  Experiment 1 Cell A / B / C runs
- `configs/experiment2/` for the extra Experiment 2 templates that do not
  already exist on `main` (currently the Plan-Execute / Cell Y lane and the
  optional Cell Z follow-on)

The active cell mapping is:

| Cell | Orchestration | MCP mode | Suggested config name |
|---|---|---|---|
| A | Agent-as-Tool | direct | `aat_direct.env` |
| B | Agent-as-Tool | baseline | `aat_mcp_baseline.env` |
| C | Agent-as-Tool | optimized | `aat_mcp_optimized.env` |
| Y | Plan-Execute | baseline | `experiment2/exp2_cell_Y_pe_mcp_baseline.env` |
| Z | Verified PE follow-on | baseline | pending canonical promotion; the current `experiment2/exp2_cell_Z_hybrid_mcp_baseline.env` is still a legacy placeholder |

## Required keys

- `EXPERIMENT_NAME` — short label; becomes part of the run ID
- `EXPERIMENT_CELL` — one of `A`, `B`, `C`, `Y`, `Z`
- `EXPERIMENT_FAMILY` — e.g. `exp1_mcp_overhead`, `exp2_orchestration`, `smoke`
- `SCENARIOS_GLOB` — scenario files relative to repo root
- `SCENARIO_SET_NAME` — stable label for the scenario pack
- `MODEL_ID` — model string passed to AssetOpsBench `plan-execute`

## Important optional keys

- `ORCHESTRATION` — `plan_execute`, `agent_as_tool`, or `hybrid`
- `MCP_MODE` — `direct`, `baseline`, or `optimized`
- `ENABLE_SMARTGRID_SERVERS` — when `1`, pass this repo's four Smart Grid MCP
  servers into `plan-execute`
- `ENABLE_WANDB` — when `1`, write the canonical config + summary fields to a
  WandB run after the benchmark finishes
- `LAUNCH_VLLM` — when `1`, launch the local vLLM server first and point
  AssetOpsBench's LiteLLM client at `http://127.0.0.1:<port>/v1`
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

As of Apr 20, 2026:

- Plan-Execute wiring is implemented through AssetOpsBench's canonical
  `plan-execute` CLI with explicit Smart Grid server overrides.
- WandB config + summary emission is wired in the benchmark runner.
- Experiment 1 analysis still maps to Cells A / B / C, but the execution
  configs for those lanes stay on the canonical `configs/aat_*.env` names that
  `main` already documents.
- AaT still needs an explicit external runner template until a stable upstream
  invocation path exists.
- Verified PE has a repo-local runner and smoke proofs, but the canonical
  Experiment 2 Z config and raw run set still need to be promoted before Z is a
  notebook-ready follow-on lane.
