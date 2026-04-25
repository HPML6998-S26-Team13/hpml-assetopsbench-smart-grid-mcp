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
            except (asyncio.CancelledError, Exception):
                # asyncio.CancelledError is a BaseException in Py3.8+, not an
                # Exception; widen the catch so partial-failure cleanup can't
                # mask the original connection error with a teardown leak.
                pass
        raise
