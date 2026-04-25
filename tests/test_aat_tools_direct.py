"""Tests for the Cell A tool builder.

The builder wraps every entry in mcp_servers.direct_adapter as an
agents SDK function_tool, preserving name and description.
"""

from __future__ import annotations

import asyncio
import pathlib

import pytest


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
                try:
                    await srv.cleanup()
                except (asyncio.CancelledError, Exception):
                    # asyncio.CancelledError is a BaseException in Py3.8+, not
                    # an Exception. The openai-agents MCP stdio teardown can
                    # leak a benign CancelledError from the anyio subprocess
                    # wait() — absorb it here so the parity assertion still runs.
                    pass

    mcp_names = asyncio.run(collect_mcp_names())

    assert direct_names == mcp_names, (
        f"Cell A and Cell B tool surfaces diverge.\n"
        f"Only in direct_adapter: {direct_names - mcp_names}\n"
        f"Only in MCP stdio:      {mcp_names - direct_names}\n"
        f"If tanisha's MCP server hardening renamed or added tools, "
        f"resync mcp_servers/direct_adapter.py."
    )
