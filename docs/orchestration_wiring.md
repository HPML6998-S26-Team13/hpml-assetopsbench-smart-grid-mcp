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
- rely on the repo-local `scripts/aat_runner.py` default dispatch, or provide
  `AAT_RUNNER_TEMPLATE` for a custom parity / variant command

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
be pointed at this repo's Smart Grid MCP servers without a team-repo
wrapper. This is the actual plumbing gap — not the absence of an AaT
runner upstream, which an earlier version of this doc had claimed.

### Why we wrap the Agents SDK, not AOB's runner

_Decision date: 2026-04-24._

Which API to wrap is a design choice with experimental consequences.
`OpenAIAgentRunner.run()` at `src/agent/openai_agent/runner.py:224`
hardcodes `_build_mcp_servers(server_paths)` and feeds the resulting MCP
servers to the OpenAI Agents SDK's `Runner.run()`. There is no hook to
swap in direct Python callables, which means AOB's runner cannot serve
Cell A (direct, no-MCP) without a fork.

Using AOB's runner for Cell B while forking or vendoring it for Cell A
would give us two code paths, and `(B - A)` in Experiment 1 would then
include any implementation delta between those paths on top of the MCP
transport overhead we want to measure.

So the team runner at `scripts/aat_runner.py` wraps the OpenAI Agents SDK
(`agents.Runner.run()`) directly — one layer below AOB — with AOB's
system prompt copied verbatim from a pinned AOB SHA. Tool source is
parameterized across cells:

- Cell A: direct Python callables over `mcp_servers/direct_adapter.py`
- Cell B: MCP stdio servers (our four Smart Grid servers)
- Cell C: optimized MCP stdio servers (gated on `#85`–`#88`, `#33`)

A/B/C share the exact same runner code; the only difference is the tool
source. `(B - A)` measures MCP transport overhead by construction.

### Path to end-to-end proof (`#104`)

Issue `#104` tracks the concrete wiring work:

- add `scripts/aat_runner.py` per the SDK-wrapping design above (**done**)
- wire smoke configs through first-class `ORCHESTRATION=agent_as_tool`
  dispatch, with `AAT_RUNNER_TEMPLATE` kept as an explicit variant/parity
  override (**done**)
- Cell A smoke on SGT-009 / T-015, direct callables (**done:** Slurm job
  `8962310_aat_direct_smoke_104`, `1 / 1` success)
- Cell B smoke on the same scenario, MCP stdio, matching the Apr 13 PE smoke
  baseline (**done:** Slurm job `8969519_aat_mcp_baseline_smoke_104`,
  `1 / 1` success)
- parity smoke: run Cell B once more through upstream AssetOpsBench's
  `OpenAIAgentRunner` Python API on the same scenario to quantify any
  implementation gap between our runner and AOB's (**done:** Slurm job
  `8970383_aat_mcp_baseline_upstream_smoke_104`, `1 / 1` success,
  Slurm elapsed `00:11:18`)
- artifacts under `benchmarks/cell_{A_direct,B_mcp_baseline}/raw/<run-id>/`
  following the canonical layout

`OpenAIAgentRunner` remains the reference upstream runner for the parity check
because it is provider-generic via LiteLLM. We use the Python API rather than
the `openai-agent` CLI because the CLI cannot pass Smart Grid `server_paths`;
the parity wrapper keeps AOB's agent loop but patches its MCP server factory
onto the warmed Smart Grid server launch/timeout envelope that the benchmark
Cell B smoke uses. `claude-agent` stays available for a separate Claude-family
smoke if symmetry is wanted later.

### What is done on our side

- common benchmark/logging/config plumbing exists
- Smart Grid MCP server discovery contract is defined
- benchmark invocation contract is documented
- `ORCHESTRATION=agent_as_tool` dispatch is live in the harness with
  `scripts/aat_runner.py` as the default and `AAT_RUNNER_TEMPLATE` as an
  override path
- `scripts/aat_runner.py` runs Cells A/B on one OpenAI Agents SDK loop with the
  AOB prompt pinned by SHA
- Cell A and Cell B expose the same model-visible bare tool names
- Insomnia local-vLLM smoke proofs exist for Cell A (`8962310`) and Cell B
  (`8969519`) on the shared SGT-009 / T-015 scenario
- upstream `OpenAIAgentRunner` parity smoke exists for Cell B (`8970383`) on
  the same shared scenario and Smart Grid MCP server paths

### What remains

- Cell C once the optimized MCP stack is ready
- full `#25` Experiment 1 capture set across `multi_*.json` with 3 trials

So `#22` is adapter-ready on our side. The remaining "prove AaT end-to-end"
work now has Cell A/B smoke artifacts plus upstream parity proof; the remaining
work is broader capture and Cell C optimization, not the core runner/MCP
bootstrap.

### Teammate note: AOB dependency

If you are trying to run PE-family or AaT benchmark lanes, assume a sibling
AssetOpsBench checkout is required.

- `AOB_PATH` defaults to `../AssetOpsBench` relative to the shared project root.
- On Insomnia, the shared `team13` area already has that sibling clone, and it
  should stay in sync with the runtime slice we are using here.
- Repo-local PE runners do **not** vendor AOB. They import a small
  plan-execute runtime slice from that checkout.
- The vanilla AaT parity smoke uses the same pattern through AOB's
  `OpenAIAgentRunner`; the benchmark Cell A/B runner is the team-local
  OpenAI Agents SDK wrapper described above so the direct and MCP arms share
  one agent loop.
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
