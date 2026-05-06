# AaT Runner (Cells A + B) Implementation Plan

*Archived: 2026-05-05 — plan complete. `scripts/aat_runner.py` shipped and is the canonical AAT runner; #104 closed. Plan content preserved as historical record of the AAT runner build.*

> Step-by-step build plan for issue #104. Each task has tests, code, and a single commit. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `scripts/aat_runner.py` — a thin wrapper over the OpenAI Agents SDK with AOB's system prompt verbatim — wired to Cells A + B of Experiment 1 via two configs, proven by WatsonX 70B smoke runs on SGT-009.

**Architecture:** Constructor-injected tool list feeds `agents.Runner.run()`. Two sibling modules build tool lists for Cell A (in-process callables via `mcp_servers/direct_adapter.py`) and Cell B (MCP stdio via `agents.mcp.MCPServerStdio`). Invocation plugs into `scripts/run_experiment.sh`'s existing `AAT_RUNNER_TEMPLATE` hook. No shell changes.

**Tech Stack:** Python 3.11, `openai-agents` SDK (+ LiteLLM backend), existing `mcp_servers/direct_adapter.py`, pytest.

**Spec:** [`../specs/2026-04-24-aat-runner-design.md`](../specs/2026-04-24-aat-runner-design.md)

---

## Pre-flight: environment + openai-agents version lookup

### Task 0: Pick the openai-agents pin

**Files:**
- Modify later: `requirements.txt`, `requirements-insomnia.txt`

- [ ] **Step 0.1: Identify the latest stable `openai-agents` release with `MCPServerStdio` + `LitellmModel` support**

Run: `pip index versions openai-agents` (or check https://pypi.org/project/openai-agents/)

Expected: a version like `0.x.y`. Record it as `OPENAI_AGENTS_VERSION` in your shell for use in later tasks. The SDK exposes `agents.mcp.MCPServerStdio` and `agents.extensions.models.litellm_model.LitellmModel`; confirm both imports work by running:

```bash
uv run --with openai-agents=="$OPENAI_AGENTS_VERSION" python -c "
from agents import Agent, Runner, function_tool
from agents.mcp import MCPServerStdio
from agents.extensions.models.litellm_model import LitellmModel
print('OK', LitellmModel)
"
```

Expected: prints `OK <class 'LitellmModel'>` with no ImportError.

- [ ] **Step 0.2: No commit yet — this is research**

The version string gets written into `requirements*.txt` in a later task.

---

## Task 1: Vendor AOB's system prompt

**Files:**
- Create: `scripts/aat_system_prompt.py`
- Test: `tests/test_aat_system_prompt.py`

- [ ] **Step 1.1: Locate the AOB prompt and commit SHA**

Run in the sibling AOB checkout:

```bash
cd ../AssetOpsBench   # or /insomnia001/depts/edu/users/team13/AssetOpsBench
git log -1 --format='%H' -- src/agent/openai_agent/   # record 7-char prefix
cat src/agent/openai_agent/prompt.py                   # find the prompt constant
```

If the AOB AaT prompt lives somewhere other than `src/agent/openai_agent/prompt.py`, record the actual path (common alternatives: `.../runner.py`, `.../system.py`). Note the 7-char SHA prefix and the full file path — both go into the docstring of `aat_system_prompt.py`.

- [ ] **Step 1.2: Write the failing test**

Create `tests/test_aat_system_prompt.py`:

```python
"""Sanity checks on the vendored AOB system prompt.

Catches silent edits: if anyone modifies AOB_SYSTEM_PROMPT without
bumping AOB_PROMPT_SHA (and re-vendoring from a new AOB commit), this
test fails.
"""

from __future__ import annotations

import hashlib


def test_aob_prompt_sha_matches_constant() -> None:
    from scripts.aat_system_prompt import AOB_PROMPT_SHA, AOB_SYSTEM_PROMPT

    actual = hashlib.sha1(AOB_SYSTEM_PROMPT.encode("utf-8")).hexdigest()[:7]
    assert actual == AOB_PROMPT_SHA, (
        f"AOB_SYSTEM_PROMPT has been edited without updating AOB_PROMPT_SHA. "
        f"If intentional, resync from a new AOB commit and set AOB_PROMPT_SHA "
        f"to {actual!r}."
    )


def test_aob_prompt_nonempty() -> None:
    from scripts.aat_system_prompt import AOB_SYSTEM_PROMPT

    assert len(AOB_SYSTEM_PROMPT) > 100, "AOB system prompt unexpectedly short; re-vendor"
```

- [ ] **Step 1.3: Run test, verify failure**

Run: `uv run pytest tests/test_aat_system_prompt.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.aat_system_prompt'` (or similar).

- [ ] **Step 1.4: Create the vendored prompt module**

Create `scripts/aat_system_prompt.py`:

```python
"""Vendored AOB Agent-as-Tool system prompt.

The string in AOB_SYSTEM_PROMPT is copied VERBATIM from IBM/AssetOpsBench
at commit `<PASTE_7CHAR_SHA>`, source file `<PASTE_RELATIVE_PATH>`.

DO NOT MODIFY the prompt text in isolation. To resync:
  1. Update AOB_SOURCE_SHA to the new AOB commit SHA (7 chars).
  2. Paste the new prompt text into AOB_SYSTEM_PROMPT.
  3. Update AOB_PROMPT_SHA to sha1(AOB_SYSTEM_PROMPT.encode())[:7]. Compute
     with: `python -c "from scripts.aat_system_prompt import _compute_prompt_sha; print(_compute_prompt_sha())"`
     (first 7 hex chars of sha1 over the prompt string only, NOT the whole file).
  4. Commit with a message that names the AOB commit you pulled from.

The test_aob_prompt_sha_matches_constant unit test enforces this by
failing CI if the prompt and SHA drift apart.
"""

from __future__ import annotations


AOB_SOURCE_SHA = "<PASTE_7CHAR_SHA>"
AOB_SOURCE_PATH = "<PASTE_RELATIVE_PATH>"

AOB_SYSTEM_PROMPT = """<PASTE_PROMPT_VERBATIM>"""


def _compute_prompt_sha() -> str:
    """Utility for resync; not used by the runner."""
    import hashlib

    return hashlib.sha1(AOB_SYSTEM_PROMPT.encode("utf-8")).hexdigest()[:7]


# Computed sha1(AOB_SYSTEM_PROMPT.encode())[:7]. Keep in sync with the prompt.
AOB_PROMPT_SHA = "<PASTE_COMPUTED_SHA>"
```

- [ ] **Step 1.5: Substitute the placeholders**

Replace `<PASTE_7CHAR_SHA>`, `<PASTE_RELATIVE_PATH>`, and `<PASTE_PROMPT_VERBATIM>` with the values from Step 1.1. Then compute the prompt hash and fill in `<PASTE_COMPUTED_SHA>`:

```bash
python -c "
import hashlib, pathlib, re
src = pathlib.Path('scripts/aat_system_prompt.py').read_text()
prompt = re.search(r'AOB_SYSTEM_PROMPT = \"\"\"(.*?)\"\"\"', src, re.DOTALL).group(1)
print(hashlib.sha1(prompt.encode()).hexdigest()[:7])
"
```

Paste the printed 7-char hex into the `AOB_PROMPT_SHA = "..."` line.

- [ ] **Step 1.6: Run tests, verify pass**

Run: `uv run pytest tests/test_aat_system_prompt.py -v`
Expected: 2 passed.

- [ ] **Step 1.7: Commit**

```bash
git add scripts/aat_system_prompt.py tests/test_aat_system_prompt.py
git commit -m "Vendor AOB AaT system prompt + sha-pin test"
```

---

## Task 2: Cell A tool builder (in-process callables)

**Files:**
- Create: `scripts/aat_tools_direct.py`
- Test: `tests/test_aat_tools_direct.py`

- [ ] **Step 2.1: Write failing test**

Create `tests/test_aat_tools_direct.py`:

```python
"""Tests for the Cell A tool builder.

The builder wraps every entry in mcp_servers.direct_adapter as an
agents SDK function_tool, preserving name and description.
"""

from __future__ import annotations


def test_build_direct_tools_returns_one_per_registry_entry() -> None:
    from mcp_servers import direct_adapter
    from scripts.aat_tools_direct import build_direct_tools

    tools = build_direct_tools()
    registry = direct_adapter.get_tools()

    assert len(tools) == len(registry), (
        f"Expected {len(registry)} tools wrapped, got {len(tools)}"
    )


def test_build_direct_tools_preserves_names() -> None:
    from mcp_servers import direct_adapter
    from scripts.aat_tools_direct import build_direct_tools

    tools = build_direct_tools()
    registry_names = {spec.name for spec in direct_adapter.get_tools()}
    wrapped_names = {getattr(tool, "name", None) for tool in tools}

    assert wrapped_names == registry_names, (
        f"Missing or renamed tools.\n"
        f"Only in registry: {registry_names - wrapped_names}\n"
        f"Only in wrapped:  {wrapped_names - registry_names}"
    )
```

- [ ] **Step 2.2: Run test, verify failure**

Run: `uv run pytest tests/test_aat_tools_direct.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.aat_tools_direct'`.

- [ ] **Step 2.3: Implement the builder**

Create `scripts/aat_tools_direct.py`:

```python
"""Cell A tool builder: in-process Python callables from
mcp_servers.direct_adapter, wrapped as OpenAI Agents SDK function_tools.

Cell B uses MCPServerStdio for the same underlying functions; see
aat_tools_mcp.py. Keeping the name/description set identical between
this module and the MCP stdio path is the fairness contract for
Experiment 1 (issue #25) — (Cell B latency) - (Cell A latency) is
pure MCP transport overhead only if the tool surface matches.
"""

from __future__ import annotations

from typing import Any, Callable, List

from agents import function_tool
from mcp_servers import direct_adapter


def build_direct_tools() -> List[Any]:
    """Return a list of function_tool objects, one per entry in the
    direct_adapter registry.
    """
    wrapped: List[Any] = []
    for spec in direct_adapter.get_tools():
        callable_fn: Callable[..., Any] = spec.fn
        wrapped.append(
            function_tool(
                callable_fn,
                name_override=spec.name,
                description_override=spec.doc or f"Direct call to {spec.name}",
            )
        )
    return wrapped
```

- [ ] **Step 2.4: Run test, verify pass**

Run: `uv run pytest tests/test_aat_tools_direct.py -v`
Expected: 2 passed.

- [ ] **Step 2.5: Commit**

```bash
git add scripts/aat_tools_direct.py tests/test_aat_tools_direct.py
git commit -m "Add Cell A direct-callable tool builder"
```

---

## Task 3: Cell B tool builder (MCP stdio)

**Files:**
- Create: `scripts/aat_tools_mcp.py`

No unit test at this stage — the schema-parity test in Task 5 is the meaningful integration check, and it needs both builders available. This task is a straight module-write with a manual smoke.

- [ ] **Step 3.1: Implement the builder**

Create `scripts/aat_tools_mcp.py`:

```python
"""Cell B tool builder: MCP stdio connections to the team's hardened
Smart Grid MCP servers.

Returns connected MCPServerStdio objects. The AaT runner passes them
to Agent(mcp_servers=...) and calls .cleanup() on each in a finally
block — dangling stdio subprocesses after a Slurm trial would leak.

Cell A uses in-process callables for the same tool set; see
aat_tools_direct.py. The test_direct_and_mcp_tool_schemas_match test
(Task 5) asserts the two paths expose identical tool surfaces.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from agents.mcp import MCPServerStdio


SERVER_MODULES: list[tuple[str, str]] = [
    ("iot", "mcp_servers/iot_server/server.py"),
    ("fmsr", "mcp_servers/fmsr_server/server.py"),
    ("tsfm", "mcp_servers/tsfm_server/server.py"),
    ("wo", "mcp_servers/wo_server/server.py"),
]


async def build_mcp_servers(repo_root: Path) -> List[MCPServerStdio]:
    """Return a list of connected MCPServerStdio objects.

    On failure mid-way through, cleans up already-connected servers
    before re-raising, so callers don't have to handle partial state.
    """
    connected: List[MCPServerStdio] = []
    try:
        for name, rel in SERVER_MODULES:
            abs_path = repo_root / rel
            if not abs_path.exists():
                raise FileNotFoundError(
                    f"MCP server module missing: {abs_path} "
                    f"(expected under the shared team checkout)"
                )
            # Match AOB's pattern (../AssetOpsBench/src/agent/openai_agent/runner.py:96):
            # use `uv run <path>` so the server subprocess inherits uv's venv.
            # cache_tools_list=True avoids a list_tools round-trip per turn.
            srv = MCPServerStdio(
                name=name,
                params={"command": "uv", "args": ["run", str(abs_path)]},
                cache_tools_list=True,
            )
            await srv.connect()
            connected.append(srv)
        return connected
    except Exception:
        for srv in connected:
            try:
                await srv.cleanup()
            except Exception:
                pass
        raise
```

- [ ] **Step 3.2: Quick import smoke**

Run:

```bash
uv run python -c "
import asyncio, pathlib
from scripts.aat_tools_mcp import build_mcp_servers

async def main():
    servers = await build_mcp_servers(pathlib.Path.cwd())
    print(f'Connected {len(servers)} servers')
    for s in servers:
        await s.cleanup()

asyncio.run(main())
"
```

Expected: `Connected 4 servers` with no traceback. If any server fails to start, fix that first — likely a missing dependency in the venv (e.g. `fastmcp`).

- [ ] **Step 3.3: Commit**

```bash
git add scripts/aat_tools_mcp.py
git commit -m "Add Cell B MCP-stdio tool builder"
```

---

## Task 4: Main runner + CLI

**Files:**
- Create: `scripts/aat_runner.py`
- Test: `tests/test_aat_runner.py`

### Subtask 4a: Output serialization

**Real Agents SDK shape (verified from `../AssetOpsBench/src/agent/openai_agent/runner.py:121-186`):**

- `result.new_items` — list of typed items, discriminated by `item_type`:
  - `"message_output_item"` — assistant text. `item.raw_item.content[i].text` has the text.
  - `"tool_call_item"` — agent decides to call a tool. `item.raw_item.name`, `item.raw_item.arguments` (JSON string), `item.raw_item.call_id` (or `.id`).
  - `"tool_call_output_item"` — tool response. `item.output` has the result.
- `result.final_output` — final answer string (may be `None`).
- `result.raw_responses` — per-turn model responses. Each has `.usage` with `.input_tokens`, `.output_tokens`.

A "turn" in AOB's trajectory model is bounded by `message_output_item` — when one appears, flush any accumulated tool calls from the previous turn. Track turn index as a counter. Our serializer mirrors this so PE and AaT turn counts mean the same thing downstream.

- [ ] **Step 4a.1: Write failing test for `_serialize_run_result`**

Create `tests/test_aat_runner.py` with:

```python
"""Unit tests for scripts/aat_runner.py.

These tests use stubbed RunResult objects and mocked Runner.run() so
they don't require network, MCP subprocesses, or WatsonX.
"""

from __future__ import annotations

import argparse
import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest


def _stub_args(**overrides):
    defaults = dict(
        prompt="test prompt",
        output="/tmp/out.json",
        model_id="watsonx/meta-llama/llama-3-3-70b-instruct",
        mcp_mode="direct",
        max_turns=30,
        verbose=False,
    )
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def _msg_item(text: str):
    """Build a stub message_output_item matching AOB's parser."""
    return SimpleNamespace(
        type="message_output_item",
        raw_item=SimpleNamespace(content=[SimpleNamespace(text=text)]),
    )


def _tool_call_item(name: str, args: dict, call_id: str = "c1"):
    """Build a stub tool_call_item."""
    import json as _json
    return SimpleNamespace(
        type="tool_call_item",
        raw_item=SimpleNamespace(
            name=name,
            arguments=_json.dumps(args),
            call_id=call_id,
            id=call_id,
        ),
    )


def _tool_output_item(output: str):
    return SimpleNamespace(type="tool_call_output_item", output=output)


def _stub_run_result(items=None, final_output="final answer text", max_turns_reached=False):
    """Build a minimal RunResult-shaped object for serializer tests.

    Matches the shape AOB's _build_trajectory in
    ../AssetOpsBench/src/agent/openai_agent/runner.py:121 walks.
    """
    return SimpleNamespace(
        new_items=items or [],
        final_output=final_output,
        max_turns_reached=max_turns_reached,
        raw_responses=[],
    )


def test_serialize_run_result_happy_path():
    from scripts.aat_runner import _serialize_run_result

    args = _stub_args()
    result = _stub_run_result(items=[
        _tool_call_item("iot.list_sensors", {"asset_id": "T-1"}, "c1"),
        _tool_output_item("[]"),
        _msg_item("final answer text"),
    ])

    out = _serialize_run_result(args, "test prompt", result, duration_seconds=12.5)

    assert out["question"] == "test prompt"
    assert out["answer"] == "final answer text"
    assert out["success"] is True
    assert out["max_turns_exhausted"] is False
    assert out["turn_count"] >= 1
    assert out["tool_call_count"] == 1
    assert out["runner_meta"]["model_id"] == args.model_id
    assert out["runner_meta"]["mcp_mode"] == "direct"
    assert out["runner_meta"]["max_turns"] == 30
    assert out["runner_meta"]["duration_seconds"] == 12.5
    assert "aob_prompt_sha" in out["runner_meta"]


def test_serialize_run_result_max_turns_exhausted():
    from scripts.aat_runner import _serialize_run_result

    args = _stub_args()
    result = _stub_run_result(
        items=[_msg_item("still thinking")],
        final_output=None,
        max_turns_reached=True,
    )

    out = _serialize_run_result(args, "test prompt", result, duration_seconds=99.0)

    assert out["success"] is False
    assert out["max_turns_exhausted"] is True


def test_cli_parses_required_args():
    from scripts.aat_runner import build_parser

    parser = build_parser()
    args = parser.parse_args([
        "--prompt", "p",
        "--output", "/tmp/o.json",
        "--model-id", "watsonx/x",
        "--mcp-mode", "direct",
    ])
    assert args.prompt == "p"
    assert args.mcp_mode == "direct"
    assert args.max_turns == 30  # default


def test_cli_missing_args_errors():
    from scripts.aat_runner import build_parser

    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--prompt", "p"])  # missing everything else


def test_cli_invalid_mcp_mode_errors():
    from scripts.aat_runner import build_parser

    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([
            "--prompt", "p",
            "--output", "/tmp/o.json",
            "--model-id", "x",
            "--mcp-mode", "nonsense",
        ])
```

- [ ] **Step 4a.2: Run tests, verify all fail on import**

Run: `uv run pytest tests/test_aat_runner.py -v`
Expected: 5 errors, all `ModuleNotFoundError: No module named 'scripts.aat_runner'`.

### Subtask 4b: Implement the runner module

- [ ] **Step 4b.1: Create `scripts/aat_runner.py` skeleton**

Create `scripts/aat_runner.py`:

```python
"""Team-local Agent-as-Tool runner for Experiment 1 Cells A + B.

A thin wrapper over the OpenAI Agents SDK's Runner.run() using AOB's
system prompt verbatim. Cell A feeds it direct Python callables from
mcp_servers/direct_adapter; Cell B feeds it MCPServerStdio connections
to the team's hardened Smart Grid MCP servers. The runner code itself
is identical across cells — only the tool surface differs. That's the
fairness contract for (Cell B latency) - (Cell A latency) to measure
pure MCP transport overhead.

Invocation: expected to be driven by scripts/run_experiment.sh via
AAT_RUNNER_TEMPLATE in configs/aat_{direct,mcp_baseline}.env.

Spec: docs/specs/2026-04-24-aat-runner-design.md
Issue: #104 (narrowed 2026-04-24) → unblocks #25 (Experiment 1).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_LOG = logging.getLogger("aat_runner")

# Importable without the SDK installed, so unit tests can patch before import.
# Real imports happen lazily inside _main().


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="aat_runner",
        description="Team-local Agent-as-Tool runner for Cells A + B of Experiment 1.",
    )
    p.add_argument("--prompt", required=True,
                   help="Scenario text (AAT_RUNNER_TEMPLATE passes $PROMPT here)")
    p.add_argument("--output", required=True,
                   help="Trial JSON output path (passed as $OUTPUT_PATH)")
    p.add_argument("--model-id", required=True,
                   help="LiteLLM-style model string, e.g. watsonx/meta-llama/llama-3-3-70b-instruct")
    p.add_argument("--mcp-mode", required=True, choices=("direct", "baseline"),
                   help="direct = Cell A in-process callables; baseline = Cell B MCP stdio")
    p.add_argument("--max-turns", type=int, default=30,
                   help="Agent turn budget (default 30 matches upstream openai-agent)")
    p.add_argument("--verbose", action="store_true")
    return p


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _serialize_run_result(
    args: argparse.Namespace,
    prompt: str,
    result: Any,
    duration_seconds: float,
) -> dict[str, Any]:
    """Translate an Agents SDK RunResult into our output JSON schema.

    Walks ``result.new_items`` with ``item_type`` discrimination, matching
    AOB's _build_trajectory in
    ../AssetOpsBench/src/agent/openai_agent/runner.py:121. A turn boundary
    is each ``message_output_item``; tool calls and their outputs that
    precede the next message belong to the current turn.
    """
    from scripts.aat_system_prompt import AOB_PROMPT_SHA

    items = list(getattr(result, "new_items", []) or [])
    history: list[dict[str, Any]] = []
    tool_call_count = 0
    turn = 0
    pending_tool_calls: list[dict[str, Any]] = []
    failed_tools: list[dict[str, str]] = []

    def _flush_pending_into_turn(turn_idx: int) -> None:
        """Attach any pending tool calls to the current turn's history entry."""
        if pending_tool_calls and history and history[-1]["turn"] == turn_idx:
            history[-1]["tool_calls"] = list(pending_tool_calls)
        pending_tool_calls.clear()

    for item in items:
        item_type = getattr(item, "type", "")
        if item_type == "message_output_item":
            _flush_pending_into_turn(turn)
            raw = getattr(item, "raw_item", None)
            text_parts: list[str] = []
            if raw is not None:
                for part in getattr(raw, "content", []) or []:
                    t = getattr(part, "text", None)
                    if t:
                        text_parts.append(t)
            turn += 1
            history.append({
                "turn": turn,
                "role": "assistant",
                "content": "".join(text_parts),
                "tool_calls": [],
            })
        elif item_type == "tool_call_item":
            raw = getattr(item, "raw_item", None)
            if raw is None:
                continue
            name = getattr(raw, "name", "") or ""
            call_id = getattr(raw, "call_id", "") or getattr(raw, "id", "") or ""
            args_raw = getattr(raw, "arguments", "{}") or "{}"
            try:
                arguments = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
            except (json.JSONDecodeError, TypeError):
                arguments = {"raw": args_raw}
            pending_tool_calls.append({
                "name": name,
                "arguments": arguments,
                "call_id": call_id,
            })
            tool_call_count += 1
        elif item_type == "tool_call_output_item":
            output = getattr(item, "output", "")
            # Attach to the most recent pending call that has no output yet.
            for call in reversed(pending_tool_calls):
                if "output" not in call:
                    call["output"] = output
                    break
            # An error flag on the item, if the SDK surfaces one, marks a failed tool.
            err = getattr(item, "error", None)
            if err:
                last_name = pending_tool_calls[-1]["name"] if pending_tool_calls else ""
                failed_tools.append({"tool": last_name, "error": str(err)})

    # Flush any trailing tool calls that didn't precede a final message.
    if pending_tool_calls:
        turn += 1
        history.append({
            "turn": turn,
            "role": "assistant",
            "content": "",
            "tool_calls": list(pending_tool_calls),
        })
        pending_tool_calls.clear()

    final_output = getattr(result, "final_output", None)
    answer = final_output if final_output else (history[-1]["content"] if history else "")

    max_turns_reached = bool(getattr(result, "max_turns_reached", False))
    success = (not max_turns_reached) and bool(answer)

    try:
        import agents as _agents
        sdk_version = getattr(_agents, "__version__", "unknown")
    except Exception:
        sdk_version = "unknown"

    return {
        "question": prompt,
        "answer": answer,
        "success": success,
        "failed_tools": failed_tools,
        "max_turns_exhausted": max_turns_reached,
        "turn_count": turn,
        "tool_call_count": tool_call_count,
        "history": history,
        "runner_meta": {
            "model_id": args.model_id,
            "mcp_mode": args.mcp_mode,
            "aob_prompt_sha": AOB_PROMPT_SHA,
            "max_turns": args.max_turns,
            "sdk_version": f"openai-agents=={sdk_version}",
            "duration_seconds": duration_seconds,
        },
    }


def _write_output(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


@dataclass
class AaTRunner:
    """Minimal wrapper around Agents SDK. Constructor-injected tool surface."""

    model_id: str
    mcp_mode: str
    max_turns: int = 30
    tools: list = field(default_factory=list)
    mcp_servers: list = field(default_factory=list)

    async def run(self, prompt: str):
        from agents import Agent, Runner
        from agents.extensions.models.litellm_model import LitellmModel
        from scripts.aat_system_prompt import AOB_SYSTEM_PROMPT

        agent = Agent(
            name="smartgrid_aat",
            instructions=AOB_SYSTEM_PROMPT,
            tools=self.tools,
            mcp_servers=self.mcp_servers,
            model=LitellmModel(model=self.model_id),
        )
        return await Runner.run(agent, prompt, max_turns=self.max_turns)


async def _main(args: argparse.Namespace) -> int:
    repo_root = Path(__file__).resolve().parent.parent

    tools: list = []
    mcp_servers: list = []

    if args.mcp_mode == "direct":
        from scripts.aat_tools_direct import build_direct_tools
        tools = build_direct_tools()
    elif args.mcp_mode == "baseline":
        from scripts.aat_tools_mcp import build_mcp_servers
        mcp_servers = await build_mcp_servers(repo_root)
    else:
        _LOG.error("unknown --mcp-mode %r", args.mcp_mode)
        return 2

    runner = AaTRunner(
        model_id=args.model_id,
        mcp_mode=args.mcp_mode,
        max_turns=args.max_turns,
        tools=tools,
        mcp_servers=mcp_servers,
    )

    start = time.time()
    error_payload: dict[str, Any] | None = None
    try:
        result = await runner.run(args.prompt)
    except Exception as exc:
        _LOG.exception("runner failed: %s", exc)
        from scripts.aat_system_prompt import AOB_PROMPT_SHA
        error_payload = {
            "question": args.prompt,
            "answer": "",
            "success": False,
            "error": f"{type(exc).__name__}: {exc}",
            "failed_tools": [],
            "max_turns_exhausted": False,
            "turn_count": 0,
            "tool_call_count": 0,
            "history": [],
            "runner_meta": {
                "model_id": args.model_id,
                "mcp_mode": args.mcp_mode,
                "aob_prompt_sha": AOB_PROMPT_SHA,
                "max_turns": args.max_turns,
                "sdk_version": "unknown",
                "duration_seconds": time.time() - start,
            },
        }
    finally:
        for srv in mcp_servers:
            try:
                await srv.cleanup()
            except Exception as cleanup_exc:
                _LOG.warning("cleanup failed for %s: %s", srv, cleanup_exc)

    if error_payload is not None:
        _write_output(Path(args.output), error_payload)
        return 1

    duration = time.time() - start
    output = _serialize_run_result(args, args.prompt, result, duration)
    _write_output(Path(args.output), output)

    if output["max_turns_exhausted"]:
        _LOG.warning(
            "max_turns=%d exhausted without a final answer; trial marked unsuccessful",
            args.max_turns,
        )

    return 0 if output["success"] else 1


def main() -> None:
    args = build_parser().parse_args()
    _setup_logging(args.verbose)
    rc = asyncio.run(_main(args))
    sys.exit(rc)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4b.2: Install openai-agents in the test venv**

Run: `uv pip install "openai-agents==$OPENAI_AGENTS_VERSION"` (from Task 0).

- [ ] **Step 4b.3: Run tests, verify pass**

Run: `uv run pytest tests/test_aat_runner.py tests/test_aat_system_prompt.py tests/test_aat_tools_direct.py -v`
Expected: all pass (7 total: 2 prompt + 2 direct + 3+ runner).

If `test_serialize_run_result_happy_path` fails because the Agents SDK's actual message shape differs from the stubs, inspect the real `RunResult` structure (run the smoke in Task 7 once, print `result.new_messages` and `result.final_output`, then adjust both `_serialize_run_result` and the test stubs to match. Real-SDK shape is the source of truth; tests follow it.

- [ ] **Step 4b.4: Commit**

```bash
git add scripts/aat_runner.py tests/test_aat_runner.py
git commit -m "Add AaT runner + output serializer + CLI"
```

---

## Task 5: Schema-parity test between Cell A and Cell B tool surfaces

**Files:**
- Modify: `tests/test_aat_tools_direct.py` (append parity test)

This is the fairness-contract enforcer. Marked slow so CI can skip it; run manually before every PR.

- [ ] **Step 5.1: Append parity test**

Add to `tests/test_aat_tools_direct.py`:

```python
import asyncio
import pathlib

import pytest


@pytest.mark.slow
def test_direct_and_mcp_tool_schemas_match():
    """Fairness-contract enforcer for Experiment 1.

    The Cell A tool surface (in-process callables) and the Cell B tool
    surface (MCP stdio) must expose the same tool names. If this test
    fails, (Cell B - Cell A) is no longer a clean measurement of MCP
    transport overhead — there's an additional tool-surface delta.

    Marked @pytest.mark.slow because it launches 4 MCP stdio subprocesses.
    """
    from mcp_servers import direct_adapter
    from scripts.aat_tools_mcp import build_mcp_servers

    direct_names = {spec.name for spec in direct_adapter.get_tools()}

    async def collect_mcp_names() -> set[str]:
        servers = await build_mcp_servers(pathlib.Path.cwd())
        try:
            names: set[str] = set()
            for srv in servers:
                tools_result = await srv.list_tools()
                # list_tools() returns a list of Tool objects with a .name field;
                # MCP names come back unqualified (e.g. "get_sensor_readings"),
                # so we qualify with the server's name to compare against
                # direct_adapter's "domain.bare" format.
                for t in tools_result:
                    names.add(f"{srv.name}.{t.name}")
            return names
        finally:
            for srv in servers:
                await srv.cleanup()

    mcp_names = asyncio.run(collect_mcp_names())

    assert direct_names == mcp_names, (
        f"Cell A and Cell B tool surfaces diverge.\n"
        f"Only in direct_adapter: {direct_names - mcp_names}\n"
        f"Only in MCP stdio:      {mcp_names - direct_names}\n"
        f"If tanisha's MCP server hardening renamed or added tools, "
        f"resync mcp_servers/direct_adapter.py."
    )
```

- [ ] **Step 5.2: Run the slow test**

Run: `uv run pytest tests/test_aat_tools_direct.py::test_direct_and_mcp_tool_schemas_match -v --no-header`
Expected: PASS. If FAIL, the assertion message will name the tool-surface gap; fix `mcp_servers/direct_adapter.py` to resync, then rerun.

- [ ] **Step 5.3: Commit**

```bash
git add tests/test_aat_tools_direct.py
git commit -m "Add schema-parity test between Cell A/B tool surfaces"
```

---

## Task 6: Requirements edits

**Files:**
- Modify: `requirements.txt`
- Modify: `requirements-insomnia.txt`

- [ ] **Step 6.1: Read current pins**

Run: `grep -n openai requirements.txt requirements-insomnia.txt`
Take note of current ordering + style.

- [ ] **Step 6.2: Add `openai-agents==<VERSION>` to both files**

Use the version pinned in Task 0. Append a line to each file (keep alphabetical order if the file is sorted; otherwise just add at the end):

```
openai-agents==<OPENAI_AGENTS_VERSION>
```

- [ ] **Step 6.3: Sanity-check the Insomnia venv install**

On the team-shared Insomnia venv (or locally if implementing off-cluster):

```bash
uv pip install -r requirements-insomnia.txt
python -c "from agents.mcp import MCPServerStdio; from agents.extensions.models.litellm_model import LitellmModel; print('OK')"
```

Expected: `OK`. If the install fails due to a transitive conflict, record the conflicting package in the PR description and either pin it or pick a different `openai-agents` version.

- [ ] **Step 6.4: Commit**

```bash
git add requirements.txt requirements-insomnia.txt
git commit -m "Pin openai-agents for AaT runner"
```

---

## Task 7: Wire Cell A and Cell B configs

**Files:**
- Modify: `configs/aat_direct.env`
- Modify: `configs/aat_mcp_baseline.env`

- [ ] **Step 7.1: Edit `configs/aat_direct.env`**

Find the block near end of file:

```bash
# AAT_RUNNER_TEMPLATE must be set before this config is runnable.
# ...
AAT_RUNNER_TEMPLATE=""
```

Replace with:

```bash
# AaT runner wired 2026-04-24 (#104).
# Variables available in the template shell (see scripts/run_experiment.sh
# run_external_orchestration_trial): PROMPT, OUTPUT_PATH, REPO_ROOT, MODEL_ID.
AAT_RUNNER_TEMPLATE='cd "$REPO_ROOT" && uv run python scripts/aat_runner.py \
    --prompt "$PROMPT" \
    --output "$OUTPUT_PATH" \
    --model-id "$MODEL_ID" \
    --mcp-mode direct'
```

- [ ] **Step 7.2: Edit `configs/aat_mcp_baseline.env`**

Same edit, but `--mcp-mode baseline` in the template command.

- [ ] **Step 7.3: Dry-run the configs**

Run:

```bash
DRY_RUN=1 bash scripts/run_experiment.sh configs/aat_direct.env
DRY_RUN=1 bash scripts/run_experiment.sh configs/aat_mcp_baseline.env
```

Expected for each: scenario validation passes, `Dry run enabled. ...` message printed, exit 0. No `ERROR:` lines.

- [ ] **Step 7.4: Commit**

```bash
git add configs/aat_direct.env configs/aat_mcp_baseline.env
git commit -m "Wire AaT runner into Cell A + Cell B configs"
```

---

## Task 8: Smoke run — Cell A on WatsonX 70B

**Files:** committed output under `benchmarks/cell_A_direct/raw/<run-id>/`

- [ ] **Step 8.1: Pick scenario and smoke config**

The team-canonical smoke scenario is SGT-009 (from the Apr 13 PE baseline). The file is `data/scenarios/multi_01_end_to_end_fault_response.json` — confirm by checking `id == "SGT-009"`:

```bash
python -c "import json; print(json.load(open('data/scenarios/multi_01_end_to_end_fault_response.json'))['id'])"
```

Expected: `SGT-009`. If the ID doesn't match, pick whichever file has `id == "SGT-009"` (all 11 scenarios are IDs `SGT-00N`).

- [ ] **Step 8.2: Create a one-off smoke config**

Create `configs/aat_direct_smoke.env` as a throwaway that overrides the cell config for a 1-scenario 1-trial run:

```bash
# One-off smoke config for the AaT runner validation of #104.
# Do not commit benchmark runs driven by this — only the proof artifact
# goes into benchmarks/. This file is reference material.

EXPERIMENT_NAME="aat_direct_smoke_104"
EXPERIMENT_CELL="A"
EXPERIMENT_FAMILY="smoke"
SCENARIO_SET_NAME="smartgrid_sgt009_smoke"
SCENARIOS_GLOB="data/scenarios/multi_01_end_to_end_fault_response.json"

# WatsonX 70B — bypasses Insomnia queue; LAUNCH_VLLM=0 so we don't need a GPU.
MODEL_ID="watsonx/meta-llama/llama-3-3-70b-instruct"

ORCHESTRATION="agent_as_tool"
MCP_MODE="direct"
TRIALS=1
ENABLE_SMARTGRID_SERVERS=0
CONTRIBUTING_EXPERIMENTS=""
SCENARIO_DOMAIN_SCOPE="multi_domain"

MODEL_PROVIDER="watsonx"
SERVING_STACK="watsonx_hosted"
QUANTIZATION_MODE="fp8"
MAX_MODEL_LEN=8192
TEMPERATURE=0.0
MAX_TOKENS=0

LAUNCH_VLLM=0

ENABLE_WANDB=0

AAT_RUNNER_TEMPLATE='cd "$REPO_ROOT" && uv run python scripts/aat_runner.py \
    --prompt "$PROMPT" \
    --output "$OUTPUT_PATH" \
    --model-id "$MODEL_ID" \
    --mcp-mode direct'
```

- [ ] **Step 8.3: Run the smoke**

From a shell with WatsonX env vars loaded (`.env` at repo root):

```bash
set -a; source .env; set +a
bash scripts/run_experiment.sh configs/aat_direct_smoke.env
```

Expected:
- `Resolved orchestration: agent_as_tool` in the intro
- harness.log shows the scenario prompt being fed to the runner
- ~30-90 seconds elapsed (WatsonX round-trip time)
- Exit 0 if `success: true`, else exit 1 with the trial JSON still written

- [ ] **Step 8.4: Inspect the artifact**

Find the run dir: `ls -1 benchmarks/cell_A_direct/raw/ | tail -1`

Run:

```bash
RUN_DIR="benchmarks/cell_A_direct/raw/$(ls -1t benchmarks/cell_A_direct/raw/ | head -1)"
jq . "$RUN_DIR"/*.json
```

Expected: the per-trial JSON has `success: true`, `runner_meta.mcp_mode: "direct"`, `tool_call_count > 0`, and a non-empty `answer`. If `success: false`, look at `history[-1]` and `failed_tools` in the JSON, plus `harness.log` in the same dir, to diagnose.

- [ ] **Step 8.5: Commit artifacts**

```bash
git add benchmarks/cell_A_direct/raw/<run-id>/ benchmarks/cell_A_direct/config.json benchmarks/cell_A_direct/summary.json
git commit -m "Cell A smoke artifacts for #104 (WatsonX 70B, SGT-009)"
```

---

## Task 9: Smoke run — Cell B on WatsonX 70B

**Files:** committed output under `benchmarks/cell_B_mcp_baseline/raw/<run-id>/`

- [ ] **Step 9.1: Create the Cell B smoke config**

Create `configs/aat_mcp_baseline_smoke.env`: copy `configs/aat_direct_smoke.env` and change these lines:

```diff
-EXPERIMENT_NAME="aat_direct_smoke_104"
+EXPERIMENT_NAME="aat_mcp_baseline_smoke_104"
-EXPERIMENT_CELL="A"
+EXPERIMENT_CELL="B"
-MCP_MODE="direct"
+MCP_MODE="baseline"
-ENABLE_SMARTGRID_SERVERS=0
+ENABLE_SMARTGRID_SERVERS=1
-    --mcp-mode direct'
+    --mcp-mode baseline'
```

- [ ] **Step 9.2: Run the smoke**

```bash
set -a; source .env; set +a
bash scripts/run_experiment.sh configs/aat_mcp_baseline_smoke.env
```

Expected: same shape as Task 8, but the run takes longer (4 MCP stdio subprocesses come up at the start of each trial). `harness.log` will show MCP server connect/disconnect lines.

- [ ] **Step 9.3: Inspect the artifact**

```bash
RUN_DIR="benchmarks/cell_B_mcp_baseline/raw/$(ls -1t benchmarks/cell_B_mcp_baseline/raw/ | head -1)"
jq '{success, turn_count, tool_call_count, runner_meta}' "$RUN_DIR"/*.json
```

Expected: `success: true`, `runner_meta.mcp_mode: "baseline"`, `tool_call_count > 0`. `history` should show tool calls routed through MCP (the `name` on tool messages is `<domain>.<tool>` matching the direct adapter names).

If `success: false` with a cleanup-related error, the MCP servers may have exited before the agent finished — check `harness.log` for stderr from the server subprocesses. Most likely fix: ensure `fastmcp` is installed in the venv.

- [ ] **Step 9.4: Commit artifacts**

```bash
git add benchmarks/cell_B_mcp_baseline/raw/<run-id>/ benchmarks/cell_B_mcp_baseline/config.json benchmarks/cell_B_mcp_baseline/summary.json
git commit -m "Cell B smoke artifacts for #104 (WatsonX 70B, SGT-009)"
```

---

## Task 10: Push + task bookkeeping

- [ ] **Step 10.1: Push the branch**

```bash
git push origin main
```

Resolve any merge conflict via `git pull --rebase origin main` first; these changes should not touch files Alex or Tanisha are editing concurrently (confirm via `git status` after rebase).

- [ ] **Step 10.2: Comment on #104**

```bash
gh issue comment 104 --repo HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp --body "$(cat <<'EOF'
Landed the narrow-scope AaT runner (#104 revised 2026-04-24).

**What shipped:**
- `scripts/aat_runner.py` — thin wrapper over OpenAI Agents SDK's `Runner.run()` with AOB's system prompt vendored verbatim (SHA `<PASTE_SHA>`).
- `scripts/aat_tools_direct.py` — Cell A in-process callables from `mcp_servers/direct_adapter.py`.
- `scripts/aat_tools_mcp.py` — Cell B MCP stdio via `agents.mcp.MCPServerStdio`.
- `scripts/aat_system_prompt.py` — vendored AOB prompt + SHA-match test.
- `configs/aat_direct.env` + `configs/aat_mcp_baseline.env` — AAT_RUNNER_TEMPLATE wired.
- `tests/test_aat_*.py` — unit tests + schema-parity enforcer.

**Proof runs (WatsonX Llama-3.3-70B / SGT-009):**
- Cell A: `benchmarks/cell_A_direct/raw/<RUN_ID_A>/` — `success: true`, `tool_call_count: <N_A>`.
- Cell B: `benchmarks/cell_B_mcp_baseline/raw/<RUN_ID_B>/` — `success: true`, `tool_call_count: <N_B>`.

**Follow-ups (not in this PR):**
- Cell C (batched/optimized) — gated on #31.
- Parity smoke vs upstream `openai-agent` CLI — nice-to-have for paper defense.
- Insomnia Llama-3.1-8B canonical #25 captures — use same runner, different config.
- `docs/orchestration_wiring.md` §76-87 rewrite + `docs/validation_log.md` entry — follow-up doc-only PR.

Unblocks #25 Cells A/B, #32 AaT arm.

@eggrollofchaos
EOF
)"
```

Replace `<PASTE_SHA>`, `<RUN_ID_A>`, `<RUN_ID_B>`, `<N_A>`, `<N_B>` with actual values from the smokes.

- [ ] **Step 10.3: Spot-check `git log --oneline -10`**

Verify no AI attribution in any commit (no `Co-Authored-By: Claude`, no "generated with" lines). If any slipped in, amend before pushing follow-ups.

---

## Out of scope (explicit non-goals)

See `docs/specs/2026-04-24-aat-runner-design.md` §"Non-goals" for the full list. The biggest ones:

- Cell C (batched / optimized MCP) — follow-up PR once Akshat's #31 lands
- Parity smoke vs upstream `openai-agent` CLI
- Doc updates to `orchestration_wiring.md` §76-87, `validation_log.md`, `experiment1_capture_plan.md`
- Insomnia Llama-3.1-8B canonical captures (that's the body of #25; this PR only unblocks it)
- `BENCHMARK_RUN_DIR` WandB-attach verification (#27 follow-up)
- Promoting AaT to a first-class `run_agent_as_tool_trial()` default in `run_experiment.sh`

If any of those creeps in during implementation, stop and ask.
