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

import asyncio
import os
import shlex
import sys
from pathlib import Path
from typing import List

from agents.mcp import MCPServerStdio

SERVER_MODULES: list[tuple[str, str]] = [
    ("iot", "mcp_servers/iot_server/server.py"),
    ("fmsr", "mcp_servers/fmsr_server/server.py"),
    ("tsfm", "mcp_servers/tsfm_server/server.py"),
    ("wo", "mcp_servers/wo_server/server.py"),
]

SERVER_UV_DEPS = [
    "mcp[cli]==1.27.0",
    "pandas",
    "numpy",
]


def _client_timeout_seconds() -> float:
    raw = os.environ.get("AAT_MCP_CLIENT_TIMEOUT_SECONDS", "30").strip()
    try:
        timeout = float(raw)
    except ValueError as exc:
        raise ValueError(
            f"AAT_MCP_CLIENT_TIMEOUT_SECONDS must be numeric, got {raw!r}"
        ) from exc
    if timeout <= 0:
        raise ValueError(f"AAT_MCP_CLIENT_TIMEOUT_SECONDS must be > 0, got {timeout!r}")
    return timeout


def _server_launch_mode() -> str:
    mode = os.environ.get("AAT_MCP_SERVER_LAUNCH_MODE", "python").strip().lower()
    if mode not in {"python", "uv"}:
        raise ValueError(
            "AAT_MCP_SERVER_LAUNCH_MODE must be either 'python' or 'uv', "
            f"got {mode!r}"
        )
    return mode


def _server_params(repo_root: Path, abs_path: Path) -> dict[str, object]:
    bootstrap_path = repo_root / "scripts" / "aat_mcp_server_bootstrap.py"
    if not bootstrap_path.exists():
        raise FileNotFoundError(f"AaT MCP server bootstrap missing: {bootstrap_path}")

    launch_mode = _server_launch_mode()
    env = {"PYTHONUNBUFFERED": "1"}

    if launch_mode == "uv":
        return {
            "command": "uv",
            "args": [
                "run",
                *(arg for dep in SERVER_UV_DEPS for arg in ("--with", dep)),
                "python",
                "-u",
                str(bootstrap_path),
                str(abs_path),
            ],
            "cwd": str(repo_root),
            "env": env,
        }

    server_python = os.environ.get("AAT_MCP_SERVER_PYTHON", "").strip()
    if server_python:
        python_path = Path(server_python)
        if not python_path.exists():
            raise FileNotFoundError(f"AAT_MCP_SERVER_PYTHON not found: {python_path}")
        return {
            "command": str(python_path),
            "args": ["-u", str(bootstrap_path), str(abs_path)],
            "cwd": str(repo_root),
            "env": env,
        }

    return {
        "command": "uv",
        "args": [
            "run",
            *(arg for dep in SERVER_UV_DEPS for arg in ("--with", dep)),
            "python",
            "-u",
            str(bootstrap_path),
            str(abs_path),
        ],
        "cwd": str(repo_root),
        "env": env,
    }


async def build_mcp_servers(repo_root: Path) -> List[MCPServerStdio]:
    """Return a list of connected MCPServerStdio objects.

    On failure mid-way through, cleans up already-connected servers
    before re-raising, so callers don't have to handle partial state.
    """
    connected: List[MCPServerStdio] = []
    try:
        client_timeout = _client_timeout_seconds()
        print(
            f"AaT MCP client initialize timeout: {client_timeout:g}s",
            file=sys.stderr,
        )
        print(
            f"AaT MCP server launch mode: {_server_launch_mode()}",
            file=sys.stderr,
        )
        for name, rel in SERVER_MODULES:
            abs_path = repo_root / rel
            if not abs_path.exists():
                raise FileNotFoundError(
                    f"MCP server module missing: {abs_path} "
                    f"(expected under the shared team checkout)"
                )
            # Use an explicit uv dependency envelope: the AaT runner itself runs
            # from a temporary uv env, which may not include server data deps.
            # cache_tools_list=True avoids a list_tools round-trip per turn.
            srv = MCPServerStdio(
                name=name,
                params=_server_params(repo_root, abs_path),
                cache_tools_list=True,
                client_session_timeout_seconds=client_timeout,
            )
            command_line = [srv.params.command, *srv.params.args]
            print(
                f"Connecting MCP server {name}: {shlex.join(command_line)}",
                file=sys.stderr,
            )
            await srv.connect()
            print(f"Connected MCP server {name}", file=sys.stderr)
            connected.append(srv)
        return connected
    except Exception:
        for srv in connected:
            try:
                await srv.cleanup()
            except (asyncio.CancelledError, Exception):
                # asyncio.CancelledError is a BaseException in Py3.8+, not an
                # Exception; widen the catch so partial-failure cleanup can't
                # mask the original connection error with a teardown leak.
                pass
        raise
