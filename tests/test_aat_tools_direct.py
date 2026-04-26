"""Tests for the Cell A tool builder.

The builder wraps every entry in mcp_servers.direct_adapter as an
agents SDK function_tool, preserving the MCP-visible name and description.
"""

from __future__ import annotations

import asyncio
import pathlib
from types import SimpleNamespace

import pytest


def test_build_direct_tools_returns_one_per_registry_entry() -> None:
    from mcp_servers import direct_adapter
    from scripts.aat_tools_direct import build_direct_tools

    tools = build_direct_tools()
    registry = direct_adapter.get_tools()

    assert len(tools) == len(
        registry
    ), f"Expected {len(registry)} tools wrapped, got {len(tools)}"


def test_build_direct_tools_uses_mcp_visible_names() -> None:
    from mcp_servers import direct_adapter
    from scripts.aat_tools_direct import build_direct_tools

    tools = build_direct_tools()
    registry_names = {
        spec.name.rsplit(".", 1)[-1] for spec in direct_adapter.get_tools()
    }
    wrapped_names = {getattr(tool, "name", None) for tool in tools}

    assert wrapped_names == registry_names, (
        f"Missing or renamed tools.\n"
        f"Only in registry: {registry_names - wrapped_names}\n"
        f"Only in wrapped:  {wrapped_names - registry_names}"
    )


def test_build_direct_tools_rejects_duplicate_visible_names(monkeypatch) -> None:
    from scripts import aat_tools_direct

    def first_tool() -> None:
        pass

    def second_tool() -> None:
        pass

    monkeypatch.setattr(
        aat_tools_direct.direct_adapter,
        "get_tools",
        lambda: [
            SimpleNamespace(name="iot.duplicate", fn=first_tool, doc="first"),
            SimpleNamespace(name="fmsr.duplicate", fn=second_tool, doc="second"),
        ],
    )

    with pytest.raises(ValueError, match="Duplicate Agent-visible AaT tool name"):
        aat_tools_direct.build_direct_tools()


@pytest.mark.slow
def test_direct_and_mcp_tool_schemas_match(monkeypatch):
    """Fairness-contract enforcer for Experiment 1.

    The Cell A tool surface (in-process callables) and the Cell B tool
    surface (MCP stdio) must expose the same tool names and parameter
    requiredness. If this test
    fails, (Cell B - Cell A) is no longer a clean measurement of MCP
    transport overhead — there's an additional tool-surface delta.

    Marked @pytest.mark.slow because it launches 4 MCP stdio subprocesses.
    """
    from mcp_servers import direct_adapter
    from scripts.aat_tools_mcp import build_mcp_servers

    from scripts.aat_tools_direct import build_direct_tools

    monkeypatch.setenv("AAT_MCP_SERVER_LAUNCH_MODE", "uv")
    monkeypatch.delenv("AAT_MCP_SERVER_PYTHON", raising=False)

    def schema_contract(schema: dict) -> dict[str, bool]:
        properties = schema.get("properties", {}) or {}
        required = set(schema.get("required", []) or [])
        return {name: name in required for name in properties}

    direct_tools = build_direct_tools()
    direct_names = {getattr(tool, "name", None) for tool in direct_tools}
    direct_schemas = {
        getattr(tool, "name", None): schema_contract(tool.params_json_schema)
        for tool in direct_tools
    }

    async def collect_mcp_schemas() -> tuple[set[str], dict[str, dict[str, bool]]]:
        servers = await build_mcp_servers(pathlib.Path.cwd())
        try:
            names: set[str] = set()
            schemas: dict[str, dict[str, bool]] = {}
            for srv in servers:
                tools_result = await srv.list_tools()
                for t in tools_result:
                    names.add(t.name)
                    schemas[t.name] = schema_contract(t.inputSchema)
            return names, schemas
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

    mcp_names, mcp_schemas = asyncio.run(collect_mcp_schemas())

    assert direct_names == mcp_names, (
        f"Cell A and Cell B tool surfaces diverge.\n"
        f"Only in direct_adapter: {direct_names - mcp_names}\n"
        f"Only in MCP stdio:      {mcp_names - direct_names}\n"
        f"If tanisha's MCP server hardening renamed or added tools, "
        f"resync mcp_servers/direct_adapter.py."
    )
    assert direct_schemas == mcp_schemas
