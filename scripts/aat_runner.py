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
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Ensure repo root is on sys.path so `from scripts.*` imports resolve when
# this file is invoked as `python scripts/aat_runner.py` (which puts
# scripts/, not the repo root, on sys.path by default).
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_LOG = logging.getLogger("aat_runner")

# Importable without the SDK installed, so unit tests can patch before import.
# Real imports happen lazily inside _main().


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="aat_runner",
        description="Team-local Agent-as-Tool runner for Cells A + B of Experiment 1.",
    )
    p.add_argument(
        "--prompt",
        required=True,
        help="Scenario text (AAT_RUNNER_TEMPLATE passes $PROMPT here)",
    )
    p.add_argument(
        "--output",
        required=True,
        help="Trial JSON output path (passed as $OUTPUT_PATH)",
    )
    p.add_argument(
        "--model-id",
        required=True,
        help="LiteLLM-style model string, e.g. watsonx/meta-llama/llama-3-3-70b-instruct",
    )
    p.add_argument(
        "--mcp-mode",
        required=True,
        choices=("direct", "baseline"),
        help="direct = Cell A in-process callables; baseline = Cell B MCP stdio",
    )
    p.add_argument(
        "--max-turns",
        type=int,
        default=30,
        help="Agent turn budget (default 30 matches upstream openai-agent)",
    )
    p.add_argument(
        "--parallel-tool-calls",
        type=_parse_parallel_tool_calls,
        # argparse captures env defaults when the parser is constructed; tests
        # that exercise env-driven defaults must set AAT_PARALLEL_TOOL_CALLS
        # before calling build_parser().
        default=_parse_parallel_tool_calls(os.environ.get("AAT_PARALLEL_TOOL_CALLS")),
        help=(
            "Whether the model may emit multiple tool calls in one turn. "
            "Use false for local vLLM Llama 3 tool-calling compatibility "
            "(default: false; set AAT_PARALLEL_TOOL_CALLS=auto for SDK default)."
        ),
    )
    p.add_argument("--verbose", action="store_true")
    return p


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _parse_parallel_tool_calls(value: str | None) -> bool | None:
    """Parse CLI/env tri-state for Agents SDK parallel tool calls."""
    raw = (value if value is not None else "false").strip().lower()
    if raw in {"", "false", "0", "no", "off"}:
        return False
    if raw in {"true", "1", "yes", "on"}:
        return True
    if raw in {"auto", "default", "none"}:
        return None
    raise argparse.ArgumentTypeError(
        "parallel tool calls must be true, false, or auto; " f"got {value!r}"
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

    # Flushing semantics match AOB's _build_trajectory
    # (../AssetOpsBench/src/agent/openai_agent/runner.py:121). A "turn" is
    # terminated by the next message_output_item; any tool calls that
    # appeared before that message are attributed to the turn being CLOSED,
    # not to the new message's turn.
    current_text_parts: list[str] = []

    def _close_turn() -> None:
        """If there's pending text or tool calls, emit a turn record for them.

        Empty-content turns with non-empty tool_calls are valid tool-execution
        turns, not parser anomalies. Some SDK item orderings surface a tool
        call before the assistant text that explains it.
        """
        nonlocal turn
        if not current_text_parts and not pending_tool_calls:
            return
        turn += 1
        history.append(
            {
                "turn": turn,
                "role": "assistant",
                "content": "".join(current_text_parts),
                "tool_calls": list(pending_tool_calls),
            }
        )
        current_text_parts.clear()
        pending_tool_calls.clear()

    for item in items:
        item_type = getattr(item, "type", "")
        if item_type == "message_output_item":
            # New assistant message arrived — close out the previous turn.
            _close_turn()
            raw = getattr(item, "raw_item", None)
            if raw is not None:
                for part in getattr(raw, "content", []) or []:
                    t = getattr(part, "text", None)
                    if t:
                        current_text_parts.append(t)
        elif item_type == "tool_call_item":
            raw = getattr(item, "raw_item", None)
            if raw is None:
                continue
            name = getattr(raw, "name", "") or ""
            call_id = getattr(raw, "call_id", "") or getattr(raw, "id", "") or ""
            args_raw = getattr(raw, "arguments", "{}") or "{}"
            try:
                arguments = (
                    json.loads(args_raw) if isinstance(args_raw, str) else args_raw
                )
            except (json.JSONDecodeError, TypeError):
                arguments = {"raw": args_raw}
            pending_tool_calls.append(
                {
                    "name": name,
                    "arguments": arguments,
                    "call_id": call_id,
                }
            )
            tool_call_count += 1
        elif item_type == "tool_call_output_item":
            output = getattr(item, "output", "")
            # Attach to the most recent pending call that has no output yet.
            attached = False
            for call in reversed(pending_tool_calls):
                if "output" not in call:
                    call["output"] = output
                    attached = True
                    break
            if not attached:
                _LOG.warning(
                    "dropping tool_call_output_item without a pending tool call"
                )
            # Defensive: the real Agents SDK today surfaces tool errors as
            # stringified output content, not a separate .error attribute.
            # Kept as a forward-compat hook for future SDK versions that may.
            err = getattr(item, "error", None)
            if err:
                last_name = pending_tool_calls[-1]["name"] if pending_tool_calls else ""
                failed_tools.append({"tool": last_name, "error": str(err)})

    # Close the final turn (text or tool calls still buffered).
    _close_turn()

    final_output = getattr(result, "final_output", None)
    if final_output:
        answer = final_output
    else:
        # Find the last turn with non-empty assistant content.
        answer = ""
        for entry in reversed(history):
            if entry.get("role") == "assistant" and entry.get("content"):
                answer = entry["content"]
                break

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
            "parallel_tool_calls": args.parallel_tool_calls,
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
    litellm_base_url: str | None = None
    litellm_api_key: str | None = None
    parallel_tool_calls: bool | None = False

    async def run(self, prompt: str):
        from agents import Agent, ModelSettings, Runner
        from agents.extensions.models.litellm_model import LitellmModel
        from scripts.aat_system_prompt import AOB_SYSTEM_PROMPT

        base_url = self.litellm_base_url or os.environ.get("LITELLM_BASE_URL")
        api_key = self.litellm_api_key or os.environ.get("LITELLM_API_KEY")
        agent = Agent(
            name="smartgrid_aat",
            instructions=AOB_SYSTEM_PROMPT,
            tools=self.tools,
            mcp_servers=self.mcp_servers,
            model=LitellmModel(
                model=self.model_id,
                base_url=base_url,
                api_key=api_key,
            ),
            model_settings=ModelSettings(
                parallel_tool_calls=self.parallel_tool_calls,
            ),
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
        parallel_tool_calls=args.parallel_tool_calls,
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
                "parallel_tool_calls": args.parallel_tool_calls,
                "sdk_version": "unknown",
                "duration_seconds": time.time() - start,
            },
        }
    finally:
        for srv in mcp_servers:
            try:
                await srv.cleanup()
            except (asyncio.CancelledError, Exception) as cleanup_exc:
                # CancelledError is a BaseException in Py3.8+, and the
                # openai-agents MCP stdio teardown can surface it from anyio
                # subprocess waits. Cleanup failures should not mask the
                # original runner error.
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
