"""Upstream AssetOpsBench OpenAIAgentRunner smoke wrapper.

This is intentionally separate from ``scripts/aat_runner.py``. The production
Experiment 1 Cell A/B path uses the team-local OpenAI Agents SDK wrapper so the
direct and MCP arms share the same agent loop. This script is only for the
parity smoke required by #104: instantiate AssetOpsBench's upstream
``OpenAIAgentRunner`` Python API with this repo's Smart Grid MCP server paths,
then translate the result into the benchmark artifact schema.

The upstream ``openai-agent`` CLI does not expose a server-path override, so the
Python API is the narrowest way to run the upstream runner against Smart Grid.
The Python API still assumes AOB's own MCP server entry points; for this smoke
we patch its MCP server factory to launch this repo's Smart Grid servers through
the warmed Insomnia Python/bootstrap path used by the benchmark runner.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import shlex
import sys
import time
import types
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_LOG = logging.getLogger("aat_upstream_openai_runner")


SERVER_PATHS = {
    "iot": "mcp_servers/iot_server/server.py",
    "fmsr": "mcp_servers/fmsr_server/server.py",
    "tsfm": "mcp_servers/tsfm_server/server.py",
    "wo": "mcp_servers/wo_server/server.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aat_upstream_openai_runner",
        description="Run AOB's upstream OpenAIAgentRunner against Smart Grid MCP servers.",
    )
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--aob-path", required=True)
    parser.add_argument("--max-turns", type=int, default=30)
    parser.add_argument("--verbose", action="store_true")
    return parser


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _bootstrap_aob(aob_path: Path) -> None:
    src = aob_path / "src"
    if not src.exists():
        raise FileNotFoundError(f"AssetOpsBench src/ not found under {aob_path}")
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    _install_unused_claude_sdk_stub()


def _install_unused_claude_sdk_stub() -> None:
    """Avoid AOB's top-level Claude runner import for this OpenAI-only smoke.

    ``agent.openai_agent.runner`` is the only upstream surface used here, but
    importing it normally first executes ``agent.__init__``, which imports the
    Claude runner and requires ``claude_agent_sdk``. That SDK is irrelevant to
    the OpenAI parity smoke and is not available in the Insomnia AaT runtime.
    """
    if "claude_agent_sdk" in sys.modules:
        return
    stub = types.ModuleType("claude_agent_sdk")
    for name in (
        "AssistantMessage",
        "ClaudeAgentOptions",
        "HookMatcher",
        "ResultMessage",
        "TextBlock",
        "ToolUseBlock",
    ):
        setattr(stub, name, type(name, (), {}))

    async def _query(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError(
            "claude_agent_sdk stub is unavailable in OpenAI parity smoke"
        )

    stub.query = _query
    sys.modules["claude_agent_sdk"] = stub


def _smartgrid_server_paths(repo_root: Path) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for name, rel in SERVER_PATHS.items():
        path = repo_root / rel
        if not path.exists():
            raise FileNotFoundError(f"Smart Grid MCP server missing: {path}")
        paths[name] = path
    return paths


def _parse_parallel_tool_calls() -> bool | None:
    raw = os.environ.get("AAT_PARALLEL_TOOL_CALLS", "false").strip().lower()
    if raw in {"", "false", "0", "no", "off"}:
        return False
    if raw in {"true", "1", "yes", "on"}:
        return True
    if raw in {"auto", "default", "none"}:
        return None
    raise ValueError(
        "AAT_PARALLEL_TOOL_CALLS must be true, false, or auto; " f"got {raw!r}"
    )


def _patch_aob_openai_runner(aob_openai_runner: Any, repo_root: Path) -> list[str]:
    """Patch AOB runner dependencies while leaving OpenAIAgentRunner.run intact."""
    from agents import Agent as SDKAgent, ModelSettings
    from agents.mcp import MCPServerStdio
    from scripts.aat_tools_mcp import _client_timeout_seconds, _server_params

    patches: list[str] = []

    def _build_smartgrid_mcp_servers(
        server_paths: dict[str, Path | str],
    ) -> list[MCPServerStdio]:
        client_timeout = _client_timeout_seconds()
        servers: list[MCPServerStdio] = []
        for name, spec in server_paths.items():
            path = Path(spec)
            if not path.is_absolute():
                path = repo_root / path
            params = _server_params(repo_root, path)
            command_line = [
                str(params["command"]),
                *[str(arg) for arg in params["args"]],
            ]
            print(
                "Upstream parity MCP server "
                f"{name}: timeout={client_timeout:g}s {shlex.join(command_line)}",
                file=sys.stderr,
            )
            servers.append(
                MCPServerStdio(
                    name=name,
                    params=params,
                    cache_tools_list=True,
                    client_session_timeout_seconds=client_timeout,
                )
            )
        return servers

    parallel_tool_calls = _parse_parallel_tool_calls()

    def _agent_with_model_settings(*args: Any, **kwargs: Any) -> Any:
        kwargs.setdefault(
            "model_settings",
            ModelSettings(parallel_tool_calls=parallel_tool_calls),
        )
        return SDKAgent(*args, **kwargs)

    aob_openai_runner._build_mcp_servers = _build_smartgrid_mcp_servers
    patches.append("mcp_server_launch")

    aob_openai_runner.Agent = _agent_with_model_settings
    patches.append(f"parallel_tool_calls={parallel_tool_calls}")

    return patches


def _tool_call_payload(tool_call: Any) -> dict[str, Any]:
    return {
        "name": getattr(tool_call, "name", "") or "",
        "arguments": getattr(tool_call, "input", {}) or {},
        "call_id": getattr(tool_call, "id", "") or "",
        "output": getattr(tool_call, "output", None),
    }


def _serialize_result(
    *,
    args: argparse.Namespace,
    prompt: str,
    result: Any,
    duration_seconds: float,
    server_paths: dict[str, Path],
    patches: list[str],
) -> dict[str, Any]:
    trajectory = getattr(result, "trajectory", None)
    turns = list(getattr(trajectory, "turns", []) or [])
    history = []
    tool_call_count = 0

    for index, turn in enumerate(turns, start=1):
        tool_calls = [
            _tool_call_payload(call)
            for call in list(getattr(turn, "tool_calls", []) or [])
        ]
        tool_call_count += len(tool_calls)
        history.append(
            {
                "turn": index,
                "role": "assistant",
                "content": getattr(turn, "text", "") or "",
                "tool_calls": tool_calls,
                "input_tokens": getattr(turn, "input_tokens", 0) or 0,
                "output_tokens": getattr(turn, "output_tokens", 0) or 0,
            }
        )

    answer = getattr(result, "answer", "") or ""
    return {
        "question": prompt,
        "answer": answer,
        "success": bool(answer),
        "failed_tools": [],
        "max_turns_exhausted": False,
        "turn_count": len(history),
        "tool_call_count": tool_call_count,
        "history": history,
        "runner_meta": {
            "runner": "AssetOpsBench OpenAIAgentRunner",
            "runner_source": "upstream_python_api",
            "aob_path": str(Path(args.aob_path).resolve()),
            "model_id": args.model_id,
            "max_turns": args.max_turns,
            "server_paths": {name: str(path) for name, path in server_paths.items()},
            "import_shims": ["claude_agent_sdk"],
            "aob_runner_patches": patches,
            "duration_seconds": duration_seconds,
        },
    }


def _write_output(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


async def _main(args: argparse.Namespace) -> int:
    repo_root = Path(__file__).resolve().parent.parent
    aob_path = Path(args.aob_path).resolve()
    _bootstrap_aob(aob_path)

    from agent.openai_agent import runner as aob_openai_runner

    server_paths = _smartgrid_server_paths(repo_root)
    patches = _patch_aob_openai_runner(aob_openai_runner, repo_root)
    OpenAIAgentRunner = aob_openai_runner.OpenAIAgentRunner
    runner = OpenAIAgentRunner(
        server_paths=server_paths,
        model=args.model_id,
        max_turns=args.max_turns,
    )

    start = time.time()
    try:
        result = await runner.run(args.prompt)
    except Exception as exc:
        _LOG.exception("upstream OpenAIAgentRunner failed: %s", exc)
        _write_output(
            Path(args.output),
            {
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
                    "runner": "AssetOpsBench OpenAIAgentRunner",
                    "runner_source": "upstream_python_api",
                    "aob_path": str(aob_path),
                    "model_id": args.model_id,
                    "max_turns": args.max_turns,
                    "server_paths": {
                        name: str(path) for name, path in server_paths.items()
                    },
                    "import_shims": ["claude_agent_sdk"],
                    "aob_runner_patches": patches,
                    "duration_seconds": time.time() - start,
                },
            },
        )
        return 1

    payload = _serialize_result(
        args=args,
        prompt=args.prompt,
        result=result,
        duration_seconds=time.time() - start,
        server_paths=server_paths,
        patches=patches,
    )
    _write_output(Path(args.output), payload)
    return 0 if payload["success"] else 1


def main() -> None:
    args = build_parser().parse_args()
    _setup_logging(args.verbose)
    sys.exit(asyncio.run(_main(args)))


if __name__ == "__main__":
    main()
