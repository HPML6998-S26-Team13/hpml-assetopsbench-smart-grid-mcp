# Design — `scripts/aat_runner.py` (Cells A + B)

*Date: 2026-04-24*
*Owner: Aaron Fan (af3623)*
*Issue: [#104](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/104)*
*Unblocks: [#25](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/25), [#32](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/32)*

## Context

Issue #104 was re-scoped on 2026-04-24 (Alex's comment) away from "wrap AOB's `OpenAIAgentRunner`" toward "thin wrapper over the OpenAI Agents SDK with AOB's prompt verbatim, parameterized across Cells A/B/C of Experiment 1." Rationale: AOB's `OpenAIAgentRunner.run()` at `src/agent/openai_agent/runner.py:224` hardcodes MCP servers via `_build_mcp_servers(server_paths)` and has no clean hook for in-process callables. Forking AOB creates drift; running Cell A through a different code path than Cell B would leak code-path delta into `(B − A)`.

This spec covers the minimal PR (scope A): Cells A + B runner + one smoke proof. Cell C (batched/optimized), parity smoke vs upstream `openai-agent` CLI, broader doc updates, and Insomnia Llama-3.1-8B canonical #25 captures are explicit follow-ups.

## Goal

Land a team-local Agent-as-Tool runner that:

- Uses the OpenAI Agents SDK's `Runner.run()` driven by AOB's system prompt verbatim (SHA-pinned)
- Exposes the same 21-tool surface via two transports — in-process Python callables (Cell A) and MCP stdio (Cell B) — with zero runner-code difference between them
- Plugs into `scripts/run_experiment.sh`'s existing `AAT_RUNNER_TEMPLATE` hook with no shell changes
- Emits trial artifacts whose JSON shape is compatible with Alex's Notebook 02 parsing alongside PE outputs

## Non-goals (follow-ups, not this PR)

- Cell C (batched / optimized MCP) — gated on Akshat's #31
- Parity smoke against upstream `openai-agent` CLI on SGT-009 / T-015
- Narrative doc updates to `docs/orchestration_wiring.md` §76-87, `docs/validation_log.md`, `docs/experiment1_capture_plan.md` status rows
- The actual #25 canonical Experiment 1 captures on Insomnia Llama-3.1-8B
- `BENCHMARK_RUN_DIR` WandB artifact-attach verification on a live run (#27 follow-up)
- Default `run_agent_as_tool_trial()` function promotion inside `run_experiment.sh`
- `--server NAME=PATH` CLI flag on the runner

## Architecture

One runner, two tool-source builders, CLI-driven dispatch via `--mcp-mode`.

```
            ┌─────────────────────────────────────┐
 config ───►│ scripts/run_experiment.sh           │
 .env       │  (agent_as_tool dispatch path)      │
            │  expands AAT_RUNNER_TEMPLATE        │
            └──────────────────┬──────────────────┘
                               │ uv run python scripts/aat_runner.py \
                               │   --prompt "$PROMPT" --mcp-mode {direct|baseline} \
                               │   --model-id "$MODEL_ID" --output "$OUTPUT_PATH"
                               ▼
                ┌─────────────────────────────┐
                │ scripts/aat_runner.py       │
                │  AaTRunner (dataclass)      │
                │   ├── AOB system prompt     │  (from aat_system_prompt.py)
                │   ├── OpenAI Agents SDK     │
                │   │   Runner.run() loop     │
                │   └── serialize_run_result  │
                └────┬────────────┬───────────┘
                     │ direct     │ baseline
                     ▼            ▼
         ┌────────────────┐ ┌────────────────────────┐
         │ aat_tools_     │ │ aat_tools_mcp.py       │
         │   direct.py    │ │  MCPServerStdio x 4    │
         │                │ │  (iot/fmsr/tsfm/wo)    │
         │ function_tool  │ │  agents SDK discovers  │
         │   wrappers on  │ │  tools from servers    │
         │   direct_      │ │                        │
         │   adapter.py   │ │                        │
         │   callables    │ │                        │
         └────────────────┘ └────────────────────────┘
```

### Fairness contract

Same runner code, same agent instructions, same model, same scenario, same tool names/descriptions/schemas — **only the transport differs**. The unit test `test_direct_and_mcp_tool_schemas_match` enforces the tool-surface identity. Under this contract, `(B − A)` in Experiment 1 is pure MCP transport overhead by construction.

## File layout

```
scripts/
├── aat_runner.py              NEW — runner + CLI entrypoint
├── aat_tools_direct.py        NEW — Cell A tool builder (in-process callables)
├── aat_tools_mcp.py           NEW — Cell B tool builder (MCP stdio)
└── aat_system_prompt.py       NEW — AOB system prompt verbatim, SHA-pinned

configs/
├── aat_direct.env             EDIT — set AAT_RUNNER_TEMPLATE
└── aat_mcp_baseline.env       EDIT — set AAT_RUNNER_TEMPLATE

tests/
└── test_aat_runner.py         NEW — unit tests with stub tools + mocked SDK

requirements-insomnia.txt      EDIT — add pinned openai-agents
requirements.txt               EDIT — add pinned openai-agents (laptop parity)

benchmarks/cell_A_direct/raw/<smoke-run-id>/             NEW (committed smoke artifacts)
├── <date>_A_llama-3-3-70b_agent_as_tool_direct_SGT-009_run01.json
├── meta.json, latencies.jsonl, harness.log, config.json  (written by run_experiment.sh)

benchmarks/cell_B_mcp_baseline/raw/<smoke-run-id>/       NEW — same layout
```

Splitting the tool builders into sibling modules keeps each focused: the runner doesn't know about transport; the tool modules don't know about SDK loop control. Each unit is testable in isolation.

## Components

### `scripts/aat_system_prompt.py`

A single module exporting:

```python
AOB_PROMPT_SHA: str = "<7-char SHA>"
AOB_PROMPT_SOURCE_PATH: str = "src/agent/openai_agent/prompt.py"
AOB_SYSTEM_PROMPT: str = """..."""
```

The prompt text is copied **verbatim** from the pinned AOB commit at spec-write time. A comment block documents:

- The exact commit SHA
- The source file path in the AOB repo
- The rule: DO NOT MODIFY; any edit must be a deliberate SHA bump with the new SHA in the commit message

`test_aob_prompt_sha_matches_constant` computes `sha1(AOB_SYSTEM_PROMPT.encode())[:7]` and asserts it matches `AOB_PROMPT_SHA`, failing CI if anyone edits the prompt without updating the constant.

### `scripts/aat_tools_direct.py`

```python
from typing import Callable
from agents import function_tool
from mcp_servers import direct_adapter

def build_direct_tools() -> list:
    """Cell A: in-process callables wrapped as Agents SDK function_tools."""
    tools = []
    for spec in direct_adapter.list_tool_specs_for_llm():
        fn: Callable = direct_adapter.get_tool(spec["name"])
        tools.append(function_tool(
            fn,
            name_override=spec["name"],
            description_override=spec["description"],
        ))
    return tools
```

Synchronous, no I/O. Tool errors raise Python exceptions which the Agents SDK catches and surfaces to the agent as tool-call error observations.

### `scripts/aat_tools_mcp.py`

```python
from pathlib import Path
from agents.mcp import MCPServerStdio

SERVER_MODULES = [
    ("iot",  "mcp_servers/iot_server/server.py"),
    ("fmsr", "mcp_servers/fmsr_server/server.py"),
    ("tsfm", "mcp_servers/tsfm_server/server.py"),
    ("wo",   "mcp_servers/wo_server/server.py"),
]

async def build_mcp_servers(repo_root: Path) -> list[MCPServerStdio]:
    """Cell B: MCPServerStdio connections to the team's hardened servers."""
    servers = []
    for name, rel in SERVER_MODULES:
        srv = MCPServerStdio(
            name=name,
            params={"command": "python", "args": [str(repo_root / rel)]},
        )
        await srv.connect()
        servers.append(srv)
    return servers
```

Returns connected stdio servers. The runner passes them to `Agent(mcp_servers=...)` and calls `await srv.cleanup()` for each in a `finally` block.

**Cell B's server paths are hardcoded relative to `$REPO_ROOT`.** `ENABLE_SMARTGRID_SERVERS` and `SERVER_ARGS` from `run_experiment.sh` do not plumb through the runner in this PR. A follow-up can add `--server NAME=PATH` flags if we ever need to point at non-default servers.

### `scripts/aat_runner.py`

Single-file CLI entrypoint. Imports from the two tool modules and the prompt module. Top-level structure:

```python
import argparse, asyncio, json, logging, sys, time
from dataclasses import dataclass, field
from pathlib import Path
from agents import Agent, Runner, RunResult
from agents.extensions.models.litellm_model import LitellmModel
from aat_system_prompt import AOB_SYSTEM_PROMPT, AOB_PROMPT_SHA

@dataclass
class AaTRunner:
    model_id: str
    mcp_mode: str                          # "direct" | "baseline"
    max_turns: int = 30
    tools: list = field(default_factory=list)
    mcp_servers: list = field(default_factory=list)

    async def run(self, prompt: str) -> RunResult:
        agent = Agent(
            name="smartgrid_aat",
            instructions=AOB_SYSTEM_PROMPT,
            tools=self.tools,
            mcp_servers=self.mcp_servers,
            model=LitellmModel(model=self.model_id),
        )
        return await Runner.run(agent, prompt, max_turns=self.max_turns)

async def _main(args):
    repo_root = Path(__file__).resolve().parent.parent
    prompt = args.prompt
    tools, servers = [], []
    try:
        if args.mcp_mode == "direct":
            from aat_tools_direct import build_direct_tools
            tools = build_direct_tools()
        elif args.mcp_mode == "baseline":
            from aat_tools_mcp import build_mcp_servers
            servers = await build_mcp_servers(repo_root)
        else:
            raise SystemExit(f"unknown --mcp-mode {args.mcp_mode!r}")

        runner = AaTRunner(
            model_id=args.model_id,
            mcp_mode=args.mcp_mode,
            max_turns=args.max_turns,
            tools=tools,
            mcp_servers=servers,
        )
        start = time.time()
        result = await runner.run(prompt)
        duration = time.time() - start
    finally:
        for s in servers:
            try: await s.cleanup()
            except Exception as e: logging.warning("cleanup failed for %s: %s", s, e)

    output = _serialize_run_result(args, prompt, result, duration)
    _write_output(Path(args.output), output)
    sys.exit(0 if output["success"] else 1)
```

**Model routing.** `args.model_id` uses the LiteLLM-style prefix (`openai/...`, `watsonx/...`). When `LITELLM_BASE_URL` is set by `run_experiment.sh` (local vLLM path), `LitellmModel` honors it. When unset (WatsonX path), LiteLLM routes via WatsonX provider using existing `WATSONX_*` env vars from `.env`. No new env-var handling in the runner.

**Output translation.** `_serialize_run_result` walks `result.new_messages` (per Agents SDK) and produces the shape described in the output schema below.

**CLI.**

```
python scripts/aat_runner.py \
    --prompt <scenario text, string>        [required; passed from $PROMPT] \
    --output <trial JSON output path>       [required; passed from $OUTPUT_PATH] \
    --model-id <provider/model>             [required; passed from $MODEL_ID] \
    --mcp-mode {direct|baseline}            [required; hardcoded in each config] \
    --max-turns 30                          [optional, default 30] \
    --verbose
```

The runner does **not** take a scenario JSON path — `run_experiment.sh` extracts the scenario `text` field upstream and passes it as `$PROMPT`. The runner does not know the scenario ID or file path and doesn't need them.

The runner does **not** touch `latencies.jsonl`. `run_experiment.sh` appends one record per trial post-exit (see sh lines 644-658), based on the trial wall-clock it measures around `AAT_RUNNER_TEMPLATE` invocation. The sidecar shape the sh produces is:

```json
{"scenario_file": "data/scenarios/...", "trial_index": 1,
 "latency_seconds": 42.7, "output_path": "..."}
```

which is the same shape it writes for PE trials today. No runner changes needed; Notebook 02 parses the same jsonl format across orchestrations.

## Output JSON schema

PE-compatible where fields overlap; AaT-specific additions where they don't. Notebook 02 detects orchestration via presence of `plan` (PE) vs `runner_meta.mcp_mode` (AaT).

```jsonc
{
  "question": "<raw scenario text>",
  "answer": "<final assistant message content>",
  "success": true,
  "failed_tools": [{"tool": "iot.list_sensors", "error": "..."}],
  "max_turns_exhausted": false,
  "turn_count": 8,
  "tool_call_count": 5,
  "history": [
    {"turn": 1, "role": "assistant", "content": "...", "tool_calls": [
      {"name": "iot.get_asset_metadata", "arguments": {"asset_id": "T-011"}}
    ]},
    {"turn": 1, "role": "tool", "name": "iot.get_asset_metadata",
     "tool_call_id": "call_abc", "content": "{...}"},
    {"turn": 2, "role": "assistant", "content": "...", "tool_calls": [...]},
    // ... one entry per agent turn + one per tool result
    {"turn": 8, "role": "assistant", "content": "<final answer>"}
  ],
  "runner_meta": {
    "model_id": "watsonx/meta-llama/llama-3-3-70b-instruct",
    "mcp_mode": "direct",
    "aob_prompt_sha": "abc1234",
    "max_turns": 30,
    "sdk_version": "openai-agents==X.Y.Z",
    "duration_seconds": 42.7
  }
}
```

### Success semantics

| Outcome | `success` | Notes |
|---|---|---|
| Agent produced a final message before `max_turns` hit | `true` | default happy path |
| Agent exhausted `max_turns` with no final answer | `false` | also sets `max_turns_exhausted: true` |
| Tool call raised unexpected Python exception (not caught by SDK) | `false` | entry appended to `failed_tools` |
| Agents SDK internal error (model API failure, connection) | `false` | runner writes minimal `{"success": false, "error": "..."}` JSON and exits 1 |

Tools returning error strings (the SDK's normal error-propagation path) count as tool calls, not failures.

### Latency sidecar (`latencies.jsonl`)

**The runner does not write this file.** `run_experiment.sh` already appends one record per trial post-exit (sh lines 644-658), measuring wall-clock around the `AAT_RUNNER_TEMPLATE` invocation. The record shape is:

```json
{"scenario_file": "data/scenarios/sgt-009.json", "trial_index": 1,
 "latency_seconds": 42.7, "output_path": "..."}
```

Same shape the sh writes for PE trials today. Notebook 02 parses a single jsonl format across all orchestrations; no AaT-specific latency plumbing is required.

## Wiring

### `configs/aat_direct.env` edit

```bash
# WAS: AAT_RUNNER_TEMPLATE=""
AAT_RUNNER_TEMPLATE='cd "$REPO_ROOT" && uv run python scripts/aat_runner.py \
    --prompt "$PROMPT" \
    --output "$OUTPUT_PATH" \
    --model-id "$MODEL_ID" \
    --mcp-mode direct'
```

### `configs/aat_mcp_baseline.env` edit

Identical except `--mcp-mode baseline`.

Both templates use the env vars that `run_external_orchestration_trial` exports to the template shell: `PROMPT`, `OUTPUT_PATH`, `REPO_ROOT`, `MODEL_ID`. No shell changes required.

### `requirements-insomnia.txt` + `requirements.txt`

Add pinned `openai-agents`. Version will be picked at spec implementation time (latest stable that Agents SDK provides MCP + LitellmModel support).

### `scripts/run_experiment.sh`

No changes. Existing `agent_as_tool` dispatch path (`run_external_orchestration_trial "$PROMPT" "$TRIAL_OUT" "AAT_RUNNER_TEMPLATE"`) already does what we need.

## Error handling

| Failure | Runner behavior |
|---|---|
| Scenario JSON can't be parsed | Log error, exit 2, no output file written |
| `--mcp-mode` value invalid | argparse error, exit 2 |
| `build_mcp_servers` fails to connect to a server | Log which server, exit 1, no output file written, cleanup already-connected servers |
| `Runner.run()` raises (model API / SDK internal) | Catch; write `{"success": false, "error": "<message>", "runner_meta": {...}}` to output path; cleanup servers; exit 1 |
| Tool exception during agent run | SDK catches; surface to agent as observation; runner records `{"tool": ..., "error": ...}` in `failed_tools`; agent continues |
| `max_turns` exhausted | Runner writes output with `success: false`, `max_turns_exhausted: true`; logs WARNING; exits 1 |
| MCP server cleanup raises | Log WARNING; do not fail the run (trial already succeeded) |

## Testing strategy

`tests/test_aat_runner.py`:

| Test | Coverage |
|---|---|
| `test_aob_prompt_sha_matches_constant` | Hash of vendored prompt string equals `AOB_PROMPT_SHA`. Catches silent prompt edits. |
| `test_build_direct_tools_has_21_tools` | `build_direct_tools()` returns exactly 21 `function_tool`s with names from `direct_adapter.REGISTRY`. |
| `test_direct_and_mcp_tool_schemas_match` | Tool name/description/param schema set from Cell A and Cell B paths are identical. Marked `@pytest.mark.slow` and CI-optional since it needs MCP subprocesses. |
| `test_serialize_run_result_shape` | Stub `RunResult` → expected JSON schema. All required fields present, types correct. |
| `test_success_false_on_max_turns` | Stub `RunResult` with exhausted turns → `success: false`, `max_turns_exhausted: true`. |
| `test_cli_parses_required_args` | `--prompt`, `--output`, `--model-id`, `--mcp-mode` are required; sensible error on missing. |

All fast tests use stub tool lists + mocked `Runner.run()`. No network, no MCP subprocess, no WatsonX in the default suite.

## Smoke-run acceptance (PR evidence)

| Check | Pass condition |
|---|---|
| `scripts/aat_runner.py --help` | Imports cleanly in `.venv-insomnia`, prints argparse help |
| Cell A smoke on SGT-009 via WatsonX `llama-3-3-70b-instruct` | Non-empty trial JSON, `success: true`, `runner_meta.mcp_mode = "direct"`, `tool_call_count > 0` |
| Cell B smoke on SGT-009 via WatsonX `llama-3-3-70b-instruct` | Non-empty trial JSON, `success: true`, `runner_meta.mcp_mode = "baseline"`, `history` shows MCP tool calls |
| `latencies.jsonl` | Both smokes append records; `jq` round-trip clean |
| `DRY_RUN=1 bash scripts/run_experiment.sh configs/aat_direct.env` | Resolved template command printed, no errors |

Committed smoke artifacts land under:

- `benchmarks/cell_A_direct/raw/<smoke-run-id>/2026-04-24_A_llama-3-3-70b_agent_as_tool_direct_SGT-009_run01.json`
- `benchmarks/cell_B_mcp_baseline/raw/<smoke-run-id>/2026-04-24_B_llama-3-3-70b_agent_as_tool_baseline_SGT-009_run01.json`

Both with `meta.json`, `latencies.jsonl`, `harness.log`, patched `config.json`.

## Risks and open concerns

1. **Agents SDK MCP API stability.** `MCPServerStdio` is relatively new. Pin to a specific version and call out in the runner docstring. Mitigation: if the SDK breaks, Cell B falls back to manually instantiating an MCP stdio client in a follow-up — the runner boundary is unaffected.

2. **Model behavior on 8B.** AOB's system prompt was designed assuming 70B-class models. Our #25 canonical runs use Llama-3.1-8B. If the 8B model handles the ReAct format poorly (fails to follow the "Thought / Action / Action Input / Observation" pattern), we'll see tool_call_count=0 or high `max_turns_exhausted` rates. This is not a bug in the runner — it's an experiment result. Mitigation: the runner logs `max_turns_exhausted` prominently so we spot it fast; the eventual #25 runs on 8B can raise `--max-turns` if needed.

3. **MCP tool-surface drift.** If Tanisha's hardened servers add or rename tools post-merge, `test_direct_and_mcp_tool_schemas_match` breaks. That's the intended signal — the fairness contract is violated and both paths need resync. Mitigation: the test surfaces the drift; resync is a one-line change in `direct_adapter.py`.

4. **AOB sibling checkout SHA.** Even though we vendor the prompt, `run_experiment.sh` still expects `$AOB_PATH/pyproject.toml` to exist (line 203). For the AaT smoke we don't actually call AOB's CLI — it's our runner — but the sh check still runs. Mitigation: leave the check; document in the PR description that AOB on the team Insomnia venv must exist but no specific SHA is required for the AaT path.

## Implementation order (for the writing-plans skill)

1. `aat_system_prompt.py` — vendor the prompt + SHA constant.
2. `aat_tools_direct.py` — direct tool builder + unit test for tool count.
3. `aat_tools_mcp.py` — MCP server builder (no unit test at this stage; covered by the schema-parity test in the next step).
4. `aat_runner.py` — runner class, CLI, output serialization. Unit tests for output shape + success semantics.
5. Schema-parity test spanning both tool builders (marked slow/optional).
6. `requirements.txt` / `requirements-insomnia.txt` additions.
7. `configs/aat_direct.env` + `configs/aat_mcp_baseline.env` `AAT_RUNNER_TEMPLATE` edits.
8. Smoke runs on WatsonX 70B for Cell A and Cell B on SGT-009; commit artifacts.
9. PR description referencing this spec + #104 + #25 follow-up plan.
