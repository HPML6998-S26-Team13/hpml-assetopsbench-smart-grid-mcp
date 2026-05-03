"""Team-local Agent-as-Tool runner for Experiment 1 Cells A, B, and C.

A thin wrapper over the OpenAI Agents SDK's Runner.run() using AOB's
system prompt verbatim. Cell A feeds it direct Python callables from
mcp_servers/direct_adapter; Cell B feeds it MCPServerStdio connections
to the team's hardened Smart Grid MCP servers; Cell C does the same as
Cell B with two optimizations enabled:

  - parallel_tool_calls=True (set via AAT_PARALLEL_TOOL_CALLS=true in
    configs/aat_mcp_optimized.env) lets the model emit multiple tool
    calls per turn, reducing MCP round-trips.
  - MCP connection reuse: when invoked with --scenarios-glob, all
    scenario×trial runs share the same four MCP subprocesses, eliminating
    per-trial subprocess startup/teardown overhead.

Single-scenario invocation (Cells A and B, and Cell C single-trial):
    aat_runner.py --prompt TEXT --output PATH --model-id ID --mcp-mode MODE

Multi-scenario batch invocation (Cell C connection reuse):
    aat_runner.py --scenarios-glob GLOB --trials N --output-dir DIR
                  --run-basename NAME --model-id ID --mcp-mode optimized

The runner code is otherwise identical across cells — only the tool
surface and invocation mode differ. That is the fairness contract for
latency comparisons between cells.

Spec: docs/specs/2026-04-24-aat-runner-design.md
Issue: #31 (Cell C batch mode), #104 (runner design) → unblocks #25 (Experiment 1).
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as _dt
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


def _json_default(obj: Any) -> Any:
    """JSON encoder for trial output payloads. Type-specific, fail-closed.

    Replaces the prior `default=str` which silently stringified anything —
    fine for `pandas.Timestamp`/`datetime` (roundtrippable ISO-8601) but
    lossy for `numpy.ndarray` (str() truncates above ~1000 elements per
    `numpy.set_printoptions`) and outright wrong for `pandas.DataFrame`
    (str() is the human-readable table). #131 / PR #130 review Medium 5.

    Accept: stdlib datetime + date, plus pandas.Timestamp and
    numpy.datetime64 if those packages are importable. Anything else
    raises TypeError so the caller sees the failure instead of a
    silently-corrupted artifact downstream.
    """
    if isinstance(obj, (_dt.datetime, _dt.date)):
        return obj.isoformat()

    # pandas / numpy are optional dependencies — import lazily and fall
    # through to TypeError if absent so we don't pretend to handle them.
    try:
        import pandas as _pd  # type: ignore

        if isinstance(obj, _pd.Timestamp):
            # pandas.Timestamp.isoformat() is roundtrippable.
            return obj.isoformat()
    except ImportError:
        pass
    try:
        import numpy as _np  # type: ignore

        if isinstance(obj, _np.datetime64):
            # `_np.datetime64` doesn't have isoformat(); cast through pandas
            # if available for an ISO string, else emit the str() form which
            # IS roundtrippable for datetime64 specifically (e.g.
            # '2026-04-28T17:00:00.000000000').
            try:
                import pandas as _pd  # type: ignore

                return _pd.Timestamp(obj).isoformat()
            except ImportError:
                return str(obj)
    except ImportError:
        pass

    raise TypeError(
        f"unserializable type {type(obj).__module__}.{type(obj).__name__!r}: "
        f"{_json_default.__module__} only handles datetime / date / "
        f"pandas.Timestamp / numpy.datetime64. If a tool is returning a "
        f"numpy array or pandas DataFrame, convert it inside the tool to a "
        f"plain list/dict before returning, since str() on those types is "
        f"silently lossy."
    )


# Importable without the SDK installed, so unit tests can patch before import.
# Real imports happen lazily inside _main().


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="aat_runner",
        description="Team-local Agent-as-Tool runner for Cells A, B, and C of Experiment 1.",
    )
    p.add_argument(
        "--prompt",
        default=None,
        help="Scenario text — required in single-scenario mode (omit when using --scenarios-glob).",
    )
    p.add_argument(
        "--output",
        default=None,
        help="Trial JSON output path — required in single-scenario mode.",
    )
    p.add_argument(
        "--scenarios-glob",
        default=None,
        dest="scenarios_glob",
        help=(
            "Multi-scenario batch mode: glob pattern relative to repo root "
            "(e.g. 'data/scenarios/multi_*.json'). MCP servers are reused "
            "across all scenario×trial runs. Replaces --prompt/--output."
        ),
    )
    p.add_argument(
        "--trials",
        type=int,
        default=1,
        help="Trials per scenario in multi-scenario batch mode (default 1).",
    )
    p.add_argument(
        "--output-dir",
        default=None,
        dest="output_dir",
        help="Output directory for batch mode (required when --scenarios-glob is set).",
    )
    p.add_argument(
        "--run-basename",
        default="batch",
        dest="run_basename",
        help=(
            "Filename prefix for batch-mode trial outputs. "
            "run_experiment.sh passes RUN_BASENAME here so naming matches single-trial convention."
        ),
    )
    p.add_argument(
        "--model-id",
        required=True,
        help="LiteLLM-style model string, e.g. openai/Llama-3.1-8B-Instruct",
    )
    p.add_argument(
        "--mcp-mode",
        required=True,
        choices=("direct", "baseline", "optimized"),
        help=(
            "direct = Cell A in-process callables; "
            "baseline = Cell B MCP stdio; "
            "optimized = Cell C MCP stdio (parallel tool calls configured separately)"
        ),
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
    scenario_file: str | None = None,
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

    # Token usage — pulled from the OpenAI Agents SDK's
    # RunContextWrapper.usage. The SDK accumulates per-LLM-call counters
    # across the run loop, so this single read covers every turn the
    # agent took. Missing on stubbed test results / older SDKs; fall
    # through to None values so summary aggregation can detect missing
    # data instead of treating it as zero. (#133 / PR #130 review Low 9)
    usage_block: dict[str, Any] = {
        "input_tokens": None,
        "output_tokens": None,
        "total_tokens": None,
        "requests": None,
    }
    ctx_wrapper = getattr(result, "context_wrapper", None)
    sdk_usage = getattr(ctx_wrapper, "usage", None) if ctx_wrapper else None
    if sdk_usage is not None:
        for field_name in ("input_tokens", "output_tokens", "total_tokens", "requests"):
            value = getattr(sdk_usage, field_name, None)
            if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                usage_block[field_name] = value

    return {
        "question": prompt,
        "answer": answer,
        "success": success,
        "failed_tools": failed_tools,
        "max_turns_exhausted": max_turns_reached,
        "turn_count": turn,
        "tool_call_count": tool_call_count,
        "usage": usage_block,
        "history": history,
        "runner_meta": {
            "model_id": args.model_id,
            "mcp_mode": args.mcp_mode,
            "aob_prompt_sha": AOB_PROMPT_SHA,
            "max_turns": args.max_turns,
            "parallel_tool_calls": args.parallel_tool_calls,
            "sdk_version": f"openai-agents=={sdk_version}",
            "duration_seconds": duration_seconds,
            "scenario_file": scenario_file,
        },
    }


def _write_output(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, default=_json_default) + "\n",
        encoding="utf-8",
    )


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


async def _main_multi(args: argparse.Namespace, repo_root: Path) -> int:
    """Multi-scenario batch mode: keeps MCP servers alive across all runs.

    Globs scenario files, runs each scenario for args.trials trials, writes
    per-trial JSON to args.output_dir, and appends a _batch_latencies.jsonl
    with per-trial latency records in the same format as latencies.jsonl.
    """
    if args.mcp_mode != "optimized":
        _LOG.error(
            "--scenarios-glob is only supported with --mcp-mode optimized; got %r",
            args.mcp_mode,
        )
        return 2

    if args.trials < 1:
        _LOG.error("--trials must be >= 1; got %d", args.trials)
        return 2

    from scripts.aat_tools_mcp import build_mcp_servers

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = repo_root / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    scenario_files = sorted(repo_root.glob(args.scenarios_glob))
    if not scenario_files:
        _LOG.error("no scenario files matched --scenarios-glob %r", args.scenarios_glob)
        return 2

    _LOG.info(
        "batch mode: %d scenario(s) × %d trial(s), output → %s",
        len(scenario_files),
        args.trials,
        output_dir,
    )

    mcp_servers: list = []
    latency_records: list[dict[str, Any]] = []
    any_failed = False

    try:
        mcp_setup_start = time.time()
        mcp_servers = await build_mcp_servers(repo_root)
        mcp_setup_seconds = time.time() - mcp_setup_start
        _LOG.info("MCP servers ready (setup=%.1fs)", mcp_setup_seconds)

        runner = AaTRunner(
            model_id=args.model_id,
            mcp_mode=args.mcp_mode,
            max_turns=args.max_turns,
            mcp_servers=mcp_servers,
            parallel_tool_calls=args.parallel_tool_calls,
        )

        for sf in scenario_files:
            try:
                scenario_payload = json.loads(sf.read_text(encoding="utf-8"))
                if not isinstance(scenario_payload, dict):
                    raise TypeError(
                        f"scenario payload must be a JSON object, got {type(scenario_payload).__name__}"
                    )
                prompt = scenario_payload["text"]
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                _LOG.error("skipping %s — failed to read prompt: %s", sf, exc)
                any_failed = True
                continue

            sf_rel = sf.relative_to(repo_root).as_posix()

            for trial in range(1, args.trials + 1):
                out_name = f"{args.run_basename}_{sf.stem}_run{trial:02d}.json"
                out_path = output_dir / out_name

                start = time.time()
                # False is the correct safe default: exception path leaves it False.
                trial_ok = False
                try:
                    result = await runner.run(prompt)
                    # run_only_duration measures only runner.run(prompt).
                    # It excludes file write and later shared-resource cleanup,
                    # so batch runner_meta.duration_seconds is run-only time.
                    run_only_duration = time.time() - start
                    output = _serialize_run_result(
                        args, prompt, result, run_only_duration, scenario_file=sf_rel
                    )
                    output["scenario"] = scenario_payload
                    _write_output(out_path, output)
                    trial_ok = output["success"]
                    if not trial_ok:
                        any_failed = True
                    if output["max_turns_exhausted"]:
                        _LOG.warning(
                            "max_turns=%d exhausted (%s trial %d)",
                            args.max_turns,
                            sf.name,
                            trial,
                        )
                except Exception as exc:
                    _LOG.exception(
                        "trial failed (%s trial %d): %s", sf.name, trial, exc
                    )
                    from scripts.aat_system_prompt import AOB_PROMPT_SHA

                    error_payload = {
                        "question": prompt,
                        "answer": "",
                        "success": False,
                        "error": f"{type(exc).__name__}: {exc}",
                        "failed_tools": [],
                        "max_turns_exhausted": False,
                        "turn_count": 0,
                        "tool_call_count": 0,
                        "history": [],
                        "scenario": scenario_payload,
                        "runner_meta": {
                            "model_id": args.model_id,
                            "mcp_mode": args.mcp_mode,
                            "aob_prompt_sha": AOB_PROMPT_SHA,
                            "max_turns": args.max_turns,
                            "parallel_tool_calls": args.parallel_tool_calls,
                            "sdk_version": "unknown",
                            "duration_seconds": time.time() - start,
                            "scenario_file": sf_rel,
                        },
                    }
                    _write_output(out_path, error_payload)
                    any_failed = True

                # wall_clock_duration: ends after the JSON write to match
                # single-trial path semantics (run_experiment.sh measures
                # END_EPOCH after the runner process exits, which includes
                # the file write).
                wall_clock_duration = time.time() - start

                try:
                    _rel_path = out_path.relative_to(repo_root).as_posix()
                except ValueError:
                    _rel_path = out_path.as_posix()
                latency_records.append(
                    {
                        "scenario_file": sf_rel,
                        "trial_index": trial,
                        "latency_seconds": wall_clock_duration,
                        "output_path": _rel_path,
                        # One-time MCP setup cost: notebooks can compute total
                        # batch cost as sum(latency_seconds) + mcp_setup_seconds.
                        # Per-trial latency_seconds remains comparable to the
                        # single-trial path (where each trial pays MCP startup).
                        "mcp_setup_seconds": mcp_setup_seconds,
                    }
                )
                _LOG.info(
                    "wrote %s (%.1fs, success=%s)",
                    out_path.name,
                    wall_clock_duration,
                    trial_ok,
                )

    finally:
        for srv in mcp_servers:
            try:
                await srv.cleanup()
            except (asyncio.CancelledError, Exception) as cleanup_exc:
                _LOG.warning("cleanup failed for %s: %s", srv, cleanup_exc)

    latency_path = output_dir / "_batch_latencies.jsonl"
    latency_path.write_text(
        "\n".join(json.dumps(r) for r in latency_records) + "\n",
        encoding="utf-8",
    )
    _LOG.info("wrote %d latency records → %s", len(latency_records), latency_path)

    return 1 if any_failed else 0


async def _main(args: argparse.Namespace) -> int:
    repo_root = Path(__file__).resolve().parent.parent

    # Batch mode: multi-scenario with MCP connection reuse (Cell C optimized).
    if args.scenarios_glob:
        if not args.output_dir:
            _LOG.error("--output-dir is required when --scenarios-glob is set")
            return 2
        return await _main_multi(args, repo_root)

    # Single-scenario mode: validate that --prompt and --output are present.
    if not args.prompt or not args.output:
        _LOG.error("--prompt and --output are required in single-scenario mode")
        return 2

    tools: list = []
    mcp_servers: list = []

    if args.mcp_mode == "direct":
        from scripts.aat_tools_direct import build_direct_tools

        tools = build_direct_tools()
    elif args.mcp_mode == "baseline":
        from scripts.aat_tools_mcp import build_mcp_servers

        mcp_servers = await build_mcp_servers(repo_root)
    elif args.mcp_mode == "optimized":
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
                "scenario_file": None,
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
    output = _serialize_run_result(
        args, args.prompt, result, duration, scenario_file=None
    )
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
