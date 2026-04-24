# Orchestration Wiring

*Last updated: 2026-04-21*

Current state of the repo-side orchestration wiring for issues `#22` and `#62`.
This note is intentionally concrete about what is runnable now versus what is
only adapter-ready.

## Working path now: Plan-Execute on Smart Grid MCP servers

The benchmark-facing path that is wired and reproducible in-repo is:

1. [scripts/run_experiment.sh](../scripts/run_experiment.sh) prepares the
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
[scripts/run_experiment.sh](../scripts/run_experiment.sh):

- set `ORCHESTRATION=agent_as_tool`
- provide `AAT_RUNNER_TEMPLATE` for a custom command, or rely on the
  repo-local wrapper default once `#104` lands

Example custom-template shape:

```bash
AAT_RUNNER_TEMPLATE='cd "$AOB_PATH" && uv run python path/to/aat_runner.py "$PROMPT" >"$OUTPUT_PATH"'
```

### Upstream AaT surface (as of 2026-04-21)

Upstream AssetOpsBench exposes two first-class Agent-as-Tool CLIs alongside
`plan-execute`, both registered under `[project.scripts]` in
`pyproject.toml`:

- `claude-agent` — `agent.claude_agent.cli:main`, backed by `claude-agent-sdk`
- `openai-agent` — `agent.openai_agent.cli:main`, backed by `openai-agents`

Both runners connect to registered MCP servers via stdio and route through
LiteLLM for model dispatch, so they share `DEFAULT_SERVER_PATHS` with
`plan-execute` and can in principle point at any LiteLLM-supported backend.

The Python runner classes (`OpenAIAgentRunner`, `ClaudeAgentRunner`) both
accept a `server_paths` argument in their constructors, matching
`PlanExecuteRunner`. The CLIs, however, do **not** expose a
`--server NAME=PATH` override flag like `plan-execute` does, so they cannot
be pointed at this repo's Smart Grid MCP servers without either (a) an
upstream CLI change or (b) a thin team-repo wrapper that uses the Python
API directly. This is the actual plumbing gap — not the absence of an AaT
runner upstream, which an earlier version of this doc had claimed.

### Path to end-to-end proof (`#104`)

Issue `#104` tracks the concrete wiring work:

- add `scripts/aat_runner.py` mirroring the `plan_execute_self_ask_runner.py`
  pattern — bootstrap the AOB path, import `OpenAIAgentRunner`, construct
  with team `server_paths` overrides
- wire it as the default runner when `ORCHESTRATION=agent_as_tool`, keeping
  `AAT_RUNNER_TEMPLATE` as an override escape hatch
- first smoke: SGT-009 / T-015 on WatsonX Llama-3.3-70B (matches the Apr 13
  PE smoke baseline), then on Insomnia Llama-3.1-8B
- artifacts under `benchmarks/cell_B_mcp_baseline/raw/<run-id>/` following
  the canonical layout

`openai-agent` is the recommended upstream runner because it is
provider-generic via LiteLLM, which lets Experiment 2's AaT arm share the
same Llama-3.1-8B model family as the PE arm. `claude-agent` remains
available for a separate Claude-family smoke if symmetry is wanted later.

### What is done on our side

- common benchmark/logging/config plumbing exists
- Smart Grid MCP server discovery contract is defined
- benchmark invocation contract is documented
- `ORCHESTRATION=agent_as_tool` dispatch and `AAT_RUNNER_TEMPLATE` override
  path are live in the harness

### What remains

- repo-local `scripts/aat_runner.py` wrapper (tracked in `#104`)
- default `run_experiment.sh` dispatch for `agent_as_tool` that uses the
  wrapper without requiring `AAT_RUNNER_TEMPLATE` (tracked in `#104`)
- one successful end-to-end AaT run committed under
  `benchmarks/cell_B_mcp_baseline/raw/` with a `docs/validation_log.md`
  entry (tracked in `#104`)

So `#22` is adapter-ready on our side. The remaining "prove AaT end-to-end"
work is scoped and tracked under `#104`, and is not blocked on upstream.

### Teammate note: AOB dependency

If you are trying to run PE-family or AaT benchmark lanes, assume a sibling
AssetOpsBench checkout is required.

- `AOB_PATH` defaults to `../AssetOpsBench` relative to the shared project root.
- On Insomnia, the shared `team13` area already has that sibling clone, and it
  should stay in sync with the runtime slice we are using here.
- Repo-local PE runners do **not** vendor AOB. They import a small
  plan-execute runtime slice from that checkout.
- The upcoming vanilla AaT runner in `#104` will use the same pattern through
  AOB's `OpenAIAgentRunner`, not a standalone team-repo implementation.
- Do not assume the upstream AaT CLIs are enough by themselves: the real gap is
  that neither upstream AaT CLI supports `--server NAME=PATH`, so the Smart
  Grid MCP servers still need the team wrapper layer.

Practical implication: if a teammate sees "AssetOpsBench not found" or the
runner cannot reach the Smart Grid servers, check `AOB_PATH` and the wrapper
path first before debugging the model or MCP servers.

## Self-Ask PE status

The repo now has a local Self-Ask variant for the PE lane:

- keep `ORCHESTRATION=plan_execute`
- set `ENABLE_SELF_ASK=1`
- the benchmark runner swaps in `scripts/plan_execute_self_ask_runner.py`
  instead of calling the upstream PE CLI directly

This is the current implementation path for `#24` on the runnable PE baseline.
The hook stays lightweight on purpose:

- one internal clarification decision before planning
- no human-facing clarification loop
- no open-ended back-and-forth that would make the benchmark path unstable

Current trigger rule:

- the runner asks the LLM whether the question needs an internal clarification
  pass before tool planning
- if the answer is "no", the PE path behaves like vanilla planning
- if the answer is "yes", the runner appends up to two clarification questions
  plus short temporary assumptions to the planning question and then proceeds
  with normal PE execution

## Verified PE status

The optional third-method slot is now implemented locally as a verifier-gated
Plan-Execute design:

- set `ORCHESTRATION=verified_pe`
- the benchmark runner now has a built-in default command for this mode
- provide `VERIFIED_PE_RUNNER_TEMPLATE` only if you need an explicit override
- the repo-local entry point is `scripts/verified_pe_runner.py`

This replaces the older vague `Hybrid` framing for `#23`. The benchmark runner
still preserves the same artifact path and external-runner pattern, but the
control loop is now explicit:

- planner + executor reuse from the existing PE path
- one verifier pass after each successful step
- bounded repair policy: `continue`, `retry`, or `replan_suffix`
- explicit retry / replan budgets so the method stays benchmarkable

Current control rules:

- the runner can perform the same pre-plan Self-Ask clarification pass used by
  the PE + Self-Ask variant; the current example config keeps it enabled, but
  the runner also supports disabling it for cleaner ablations
- after each successful step, a verifier decides whether to `continue`,
  `retry`, or `replan_suffix`
- `retry` is bounded per step and feeds the prior attempt plus verifier reason
  back into the next execution prompt rather than replaying an identical call
- `replan_suffix` is bounded globally per run and only replans the unfinished
  suffix rather than the whole trajectory

The current scope rule still holds: the core experiment story remains vanilla
AaT vs vanilla PE. Verified PE is an active optional follow-on, not permission
to quietly rewrite Experiment 2 around a third method.

## Why this split is intentional

The repo now distinguishes between:

- **benchmark plumbing we own here**: configs, artifacts, WandB linkage, MCP
  server overrides, Insomnia/vLLM launch
- **orchestration entry points we may or may not own upstream**: concrete AaT
  runners, plus the repo-local PE mitigation variants we now own directly

That keeps the benchmark/logging layer moving without smuggling in unstable
orchestration assumptions.
