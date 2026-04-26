"""Tests for the upstream AOB OpenAIAgentRunner parity wrapper."""

from __future__ import annotations

import pathlib
from types import SimpleNamespace

import pytest


def test_upstream_patch_requires_mcp_factory() -> None:
    from scripts.aat_system_prompt import AOB_SOURCE_SHA
    from scripts.aat_upstream_openai_runner import _patch_aob_openai_runner

    module = SimpleNamespace(Agent=lambda *args, **kwargs: None)

    with pytest.raises(RuntimeError) as excinfo:
        _patch_aob_openai_runner(module, pathlib.Path.cwd())

    message = str(excinfo.value)
    assert "_build_mcp_servers" in message
    assert AOB_SOURCE_SHA in message


def test_upstream_patch_requires_agent_symbol() -> None:
    from scripts.aat_system_prompt import AOB_SOURCE_SHA
    from scripts.aat_upstream_openai_runner import _patch_aob_openai_runner

    module = SimpleNamespace(_build_mcp_servers=lambda *_args, **_kwargs: [])

    with pytest.raises(RuntimeError) as excinfo:
        _patch_aob_openai_runner(module, pathlib.Path.cwd())

    message = str(excinfo.value)
    assert "Agent" in message
    assert AOB_SOURCE_SHA in message


def test_upstream_patch_replaces_expected_symbols() -> None:
    from scripts.aat_upstream_openai_runner import _patch_aob_openai_runner

    def original_build() -> list[object]:
        return []

    def original_agent(*_args: object, **_kwargs: object) -> None:
        return None

    module = SimpleNamespace(
        _build_mcp_servers=original_build,
        Agent=original_agent,
    )

    patches = _patch_aob_openai_runner(module, pathlib.Path.cwd())

    assert module._build_mcp_servers is not original_build
    assert module.Agent is not original_agent
    assert "mcp_server_launch" in patches
    assert any(patch.startswith("parallel_tool_calls=") for patch in patches)
