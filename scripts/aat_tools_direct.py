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
