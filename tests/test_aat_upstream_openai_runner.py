"""Tests for the upstream AOB OpenAIAgentRunner parity wrapper."""

from __future__ import annotations

import pathlib
import sys
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


def test_upstream_patch_replaces_expected_symbols(monkeypatch) -> None:
    from scripts.aat_upstream_openai_runner import _patch_aob_openai_runner

    def original_build() -> list[object]:
        return []

    def original_agent(*_args: object, **_kwargs: object) -> None:
        return None

    module = SimpleNamespace(
        _build_mcp_servers=original_build,
        Agent=original_agent,
    )

    monkeypatch.setitem(
        sys.modules,
        "agents",
        SimpleNamespace(Agent=original_agent, ModelSettings=lambda **_kwargs: None),
    )
    monkeypatch.setitem(
        sys.modules,
        "agents.mcp",
        SimpleNamespace(MCPServerStdio=lambda **_kwargs: None),
    )

    patches = _patch_aob_openai_runner(module, pathlib.Path.cwd())

    assert module._build_mcp_servers is not original_build
    assert module.Agent is not original_agent
    assert "mcp_server_launch" in patches
    assert any(patch.startswith("parallel_tool_calls=") for patch in patches)


def test_upstream_patch_omits_watsonx_parallel_setting(monkeypatch) -> None:
    from scripts.aat_upstream_openai_runner import _patch_aob_openai_runner

    captured: dict[str, object] = {}

    def original_build() -> list[object]:
        return []

    def sdk_agent(*_args: object, **kwargs: object) -> None:
        captured["kwargs"] = kwargs
        return None

    class FakeModelSettings:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    fake_litellm = SimpleNamespace(drop_params=False)
    monkeypatch.setitem(sys.modules, "litellm", fake_litellm)
    monkeypatch.setitem(
        sys.modules,
        "agents",
        SimpleNamespace(Agent=sdk_agent, ModelSettings=FakeModelSettings),
    )
    monkeypatch.setitem(
        sys.modules,
        "agents.mcp",
        SimpleNamespace(MCPServerStdio=lambda **_kwargs: None),
    )

    module = SimpleNamespace(
        _build_mcp_servers=original_build,
        Agent=sdk_agent,
    )

    patches = _patch_aob_openai_runner(
        module,
        pathlib.Path.cwd(),
        model_id="watsonx/meta-llama/llama-3-3-70b-instruct",
    )
    module.Agent(name="x")

    assert "model_settings" not in captured["kwargs"]
    assert "watsonx_drop_unsupported_params" in patches
    assert fake_litellm.drop_params is True


def test_upstream_serialize_marks_max_turns_unsuccessful(tmp_path) -> None:
    from scripts.aat_upstream_openai_runner import _serialize_result

    result = SimpleNamespace(
        answer="partial answer",
        max_turns_reached=True,
        trajectory=SimpleNamespace(turns=[]),
    )
    args = SimpleNamespace(
        aob_path=str(tmp_path),
        model_id="litellm_proxy/test",
        max_turns=3,
    )

    payload = _serialize_result(
        args=args,
        prompt="question",
        result=result,
        duration_seconds=1.0,
        server_paths={},
        patches=[],
    )

    assert payload["answer"] == "partial answer"
    assert payload["success"] is False
    assert payload["max_turns_exhausted"] is True


def test_smartgrid_server_paths_fail_early(tmp_path) -> None:
    from scripts.aat_upstream_openai_runner import _smartgrid_server_paths

    with pytest.raises(FileNotFoundError, match="Smart Grid MCP server missing"):
        _smartgrid_server_paths(tmp_path)
