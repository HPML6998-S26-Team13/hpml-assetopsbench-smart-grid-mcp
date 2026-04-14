# Orchestration Wiring

*Last updated: 2026-04-14*

Current state of the repo-side orchestration wiring for issues `#22` and `#62`.
This note is intentionally concrete about what is runnable now versus what is
only adapter-ready.

## Working path now: Plan-Execute on Smart Grid MCP servers

The benchmark-facing path that is wired and reproducible in-repo is:

1. [`scripts/run_experiment.sh`](../scripts/run_experiment.sh) prepares the
   benchmark config and raw-output directory under `benchmarks/`
2. it launches local vLLM first when `LAUNCH_VLLM=1`, or uses WatsonX / another
   preconfigured backend when `LAUNCH_VLLM=0`
3. it calls AssetOpsBench's canonical `plan-execute` CLI
4. it overrides the default MCP server set by passing this repo's Smart Grid
   servers explicitly:
   - `iot=$REPO_ROOT/mcp_servers/iot_server/server.py`
   - `fmsr=$REPO_ROOT/mcp_servers/fmsr_server/server.py`
   - `tsfm=$REPO_ROOT/mcp_servers/tsfm_server/server.py`
   - `wo=$REPO_ROOT/mcp_servers/wo_server/server.py`
5. it writes benchmark artifacts plus WandB linkage fields back into
   `benchmarks/cell_<...>/config.json` and `summary.json`

This is the repo-side implementation for issue `#62`.

### Reproducible dry run

```bash
DRY_RUN=1 bash scripts/run_experiment.sh configs/example_baseline.env
```

### Reproducible batch submission

```bash
sbatch scripts/run_experiment.sh configs/example_baseline.env
```

## Shared plumbing for all orchestration modes

The generic runner already provides the common pieces we want for all
orchestration conditions:

- benchmark directory layout under `benchmarks/`
- run-scoped raw outputs under `benchmarks/<cell>/raw/<run-id>/`
- canonical config and summary files aligned to `docs/wandb_schema.md`
- optional local vLLM launch on Insomnia
- Smart Grid MCP server path overrides
- WandB run creation and back-reference patching

This means `#61`, `#22`, and `#62` should share the same artifact and logging
surface rather than each inventing their own.

For `#61`, this first pass wires benchmark-level and agent-pipeline-level
metadata into WandB through the generic runner. It does **not** yet claim full
per-server latency instrumentation inside each MCP server process; that remains
separate follow-on work once the server-side timing contract is settled.

## Agent-as-Tool status

Repo-side support for issue `#22` exists as an explicit adapter surface in
[`scripts/run_experiment.sh`](../scripts/run_experiment.sh):

- set `ORCHESTRATION=agent_as_tool`
- provide `AAT_RUNNER_TEMPLATE`

Example shape:

```bash
AAT_RUNNER_TEMPLATE='cd "$AOB_PATH" && uv run python path/to/aat_runner.py "$PROMPT" >"$OUTPUT_PATH"'
```

This is intentionally explicit because the current canonical AssetOpsBench repo
does not expose a stable top-level AaT CLI comparable to `plan-execute`.

### What is done on our side

- common benchmark/logging/config plumbing exists
- Smart Grid MCP server discovery contract is defined
- benchmark invocation contract is documented

### What is still upstream or unresolved

- stable AaT CLI / runner entry point in AssetOpsBench, or
- a thin local wrapper script in this repo once the invocation contract is clear

So `#22` is adapter-ready on our side, but not yet proven end-to-end the same
way Plan-Execute is.

## Hybrid status

Hybrid uses the same pattern:

- set `ORCHESTRATION=hybrid`
- provide `HYBRID_RUNNER_TEMPLATE`

That keeps the benchmark artifact path ready without pretending we already have
a canonical runnable hybrid implementation.

The current default scope decision is: proceed with **vanilla Agent-as-Tool vs
vanilla Plan-Execute** unless Dhaval later reopens Hybrid. That means the
absence of a default hybrid runner should not block this week's experiment
progress. If Hybrid stays in scope, it needs both:

- a real runnable entry point, and
- a written checkpoint design note that makes the reflection behavior explicit

## Why this split is intentional

The repo now distinguishes between:

- **benchmark plumbing we own here**: configs, artifacts, WandB linkage, MCP
  server overrides, Insomnia/vLLM launch
- **orchestration entry points we may or may not own upstream**: concrete AaT /
  Hybrid runners

That keeps the benchmark/logging layer moving without smuggling in unstable
orchestration assumptions.
