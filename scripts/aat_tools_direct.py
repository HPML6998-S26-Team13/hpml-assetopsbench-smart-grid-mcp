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


def _agent_visible_name(registry_name: str) -> str:
    """Return the tool name the model should see.

    The direct adapter keeps domain-qualified names internally
    (``iot.list_assets``), but MCP stdio exposes bare names
    (``list_assets``). Cell A must match Cell B's model-visible names for
    the transport-overhead comparison to stay fair.
    """
    return registry_name.rsplit(".", 1)[-1]


def build_direct_tools() -> List[Any]:
    """Return a list of function_tool objects, one per entry in the
    direct_adapter registry.
    """
    wrapped: List[Any] = []
    seen_names: dict[str, str] = {}
    for spec in direct_adapter.get_tools():
        callable_fn: Callable[..., Any] = spec.fn
        tool_name = _agent_visible_name(spec.name)
        if tool_name in seen_names:
            raise ValueError(
                "Duplicate Agent-visible AaT tool name after stripping domain "
                f"prefix: {tool_name!r} from {seen_names[tool_name]!r} and "
                f"{spec.name!r}"
            )
        seen_names[tool_name] = spec.name
        wrapped.append(
            function_tool(
                callable_fn,
                name_override=tool_name,
                description_override=spec.doc or f"Direct call to {tool_name}",
                strict_mode=False,
            )
        )
    return wrapped
