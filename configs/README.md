# configs/

Experiment configs consumed by [`scripts/run_experiment.sh`](../scripts/run_experiment.sh).
Each file describes one benchmark cell (or one smoke run that maps to a benchmark
cell) and is sourced as bash, so the schema is just env vars.

The currently verified benchmark-facing execution path is:

- `ORCHESTRATION=plan_execute`
- `ENABLE_SMARTGRID_SERVERS=1`
- Smart Grid MCP servers passed into AssetOpsBench `plan-execute` via repeated
  `--server name=path` overrides

Repo-local follow-on paths now also exist for:

- `ENABLE_SELF_ASK=1` on the Plan-Execute lane via
  `scripts/plan_execute_self_ask_runner.py`
- `ORCHESTRATION=verified_pe` on the third-method slot via
  `scripts/verified_pe_runner.py`

Agent-as-Tool still needs an explicit external runner command until the
canonical upstream exposes a stable CLI for that orchestration mode. See
[`../docs/orchestration_wiring.md`](../docs/orchestration_wiring.md).

## Naming

Use the cell name from [`../docs/execution_plan.md`](../docs/execution_plan.md)
- the four-cell core plus the optional third-method slot:

| Cell | Orchestration | MCP mode | Suggested config name |
|---|---|---|---|
| A | Agent-as-Tool | direct | `aat_direct.env` |
| B | Agent-as-Tool | baseline | `aat_mcp_baseline.env` |
| C | Agent-as-Tool | optimized | `aat_mcp_optimized.env` |
| Y | Plan-Execute | baseline | `example_baseline.env`, `example_pe_self_ask.env` |
| Z | Verified PE (optional follow-on) | baseline | `example_verified_pe.env` |

## Required keys

- `EXPERIMENT_NAME` — short label; becomes part of the run ID
- `EXPERIMENT_CELL` — one of `A`, `B`, `C`, `Y`, `Z`
- `EXPERIMENT_FAMILY` — e.g. `exp1_mcp_overhead`, `exp2_orchestration`, `smoke`
- `SCENARIOS_GLOB` — scenario files relative to repo root
- `SCENARIO_SET_NAME` — stable label for the scenario pack
- `MODEL_ID` — model string passed to AssetOpsBench `plan-execute`

## Important optional keys

- `ORCHESTRATION` — `plan_execute`, `agent_as_tool`, `hybrid`, or `verified_pe`
- `MCP_MODE` — `direct`, `baseline`, or `optimized`
- `ENABLE_SMARTGRID_SERVERS` — when `1`, pass this repo's four Smart Grid MCP
  servers into `plan-execute`
- `ENABLE_SELF_ASK` — when `1` on the PE lane, use the repo-local
  `scripts/plan_execute_self_ask_runner.py` wrapper instead of the upstream PE
  CLI directly; repo-local follow-on runners such as Verified PE may also
  respect it when their template forwards the toggle
- `ENABLE_WANDB` — when `1`, write the canonical config + summary fields to a
  WandB run after the benchmark finishes
- `LAUNCH_VLLM` — when `1`, launch the local vLLM server first and point
  AssetOpsBench's LiteLLM client at `http://127.0.0.1:<port>/v1`
- `VLLM_SERVED_MODEL_NAME` — explicit OpenAI-compatible model ID that the
  local vLLM server should advertise; for `MODEL_ID=openai/...` runs this
  should match the provider-stripped model name exactly
- `AOB_PATH` — path to the sibling AssetOpsBench checkout; defaults to
  `../AssetOpsBench` relative to the shared project root, so it also works from
  a git worktree
- `AOB_PYTHON` — optional override for the Python interpreter used by the
  repo-local orchestration wrappers; defaults to `AOB_PATH/.venv/bin/python`

For the repo-local PE follow-on runners, the active interpreter also needs the
portable AssetOpsBench client deps from `requirements.txt` (`litellm` and
`mcp[cli]`). The shared Insomnia path gets these by installing
`requirements-insomnia.txt`, which layers the serving stack on top of that same
portable base.

### Orchestration-specific adapter hooks

- `AAT_RUNNER_TEMPLATE` — required when `ORCHESTRATION=agent_as_tool`
- `HYBRID_RUNNER_TEMPLATE` — required when `ORCHESTRATION=hybrid`
- `VERIFIED_PE_RUNNER_TEMPLATE` — optional explicit override when
  `ORCHESTRATION=verified_pe`; the benchmark runner has a built-in default
  command for this mode, so most runs should not need to set it

These are intentionally explicit. We do not want hidden shell glue for AaT or
the optional Hybrid template slot until the invocation contract is stable enough
to benchmark. Verified PE is the one optional follow-on mode that now has a
repo-local default runner path.

## Running

Dry-run the wiring first:

```bash
DRY_RUN=1 bash scripts/run_experiment.sh configs/example_baseline.env
DRY_RUN=1 bash scripts/run_experiment.sh configs/example_pe_self_ask.env
DRY_RUN=1 bash scripts/run_experiment.sh configs/example_verified_pe.env
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

As of Apr 20, 2026:

- Plan-Execute wiring is implemented through AssetOpsBench's canonical
  `plan-execute` CLI with explicit Smart Grid server overrides.
- Repo-local follow-on runners now exist for a PE + Self-Ask variant and a
  Verified PE / `Plan-Execute-Verify-Replan` prototype.
- The current Verified PE example keeps Self-Ask enabled by default, but its
  template can also pass `--disable-self-ask` for cleaner verifier-only ablations.
- WandB config + summary emission is wired in the benchmark runner.
- Agent-as-Tool still uses the explicit external-template path until a stable
  upstream invocation entry point exists.
