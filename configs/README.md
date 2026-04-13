# configs/

Experiment configs consumed by [`scripts/run_experiment.sh`](../scripts/run_experiment.sh).
Each file describes one benchmark cell (or one smoke run that maps to a benchmark
cell) and is sourced as bash, so the schema is just env vars.

The currently verified benchmark-facing execution path is:

- `ORCHESTRATION=plan_execute`
- `ENABLE_SMARTGRID_SERVERS=1`
- Smart Grid MCP servers passed into AssetOpsBench `plan-execute` via repeated
  `--server name=path` overrides

Agent-as-Tool and Hybrid share the same config schema here, but still need an
explicit external runner command until the canonical upstream exposes a stable
CLI for those orchestration modes. See
[`../docs/orchestration_wiring.md`](../docs/orchestration_wiring.md).

## Naming

Use the cell name from [`../docs/execution_plan.md`](../docs/execution_plan.md)
— the 5-cell experimental grid:

| Cell | Orchestration | MCP mode | Suggested config name |
|---|---|---|---|
| A | Agent-as-Tool | direct | `aat_direct.env` |
| B | Agent-as-Tool | baseline | `aat_mcp_baseline.env` |
| C | Agent-as-Tool | optimized | `aat_mcp_optimized.env` |
| Y | Plan-Execute | baseline | `pe_mcp_baseline.env` |
| Z | Hybrid | baseline | `hybrid_mcp_baseline.env` |

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

- `AAT_RUNNER_TEMPLATE` — required when `ORCHESTRATION=agent_as_tool`
- `HYBRID_RUNNER_TEMPLATE` — required when `ORCHESTRATION=hybrid`

These are intentionally explicit. We do not want hidden shell glue for AaT or
Hybrid until the invocation contract is stable enough to benchmark.

## Running

Dry-run the wiring first:

```bash
DRY_RUN=1 bash scripts/run_experiment.sh configs/example_baseline.env
```

Submit the real job:

```bash
sbatch scripts/run_experiment.sh configs/example_baseline.env
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

As of Apr 12, 2026:

- Plan-Execute wiring is implemented through AssetOpsBench's canonical
  `plan-execute` CLI with explicit Smart Grid server overrides.
- WandB config + summary emission is wired in the benchmark runner.
- AaT and Hybrid can use the same artifact/logging path, but still need an
  explicit external runner template until a stable upstream invocation path
  exists.
