"""Unit tests for scripts/aat_runner.py.

These tests use stubbed RunResult objects and mocked Runner.run() so
they don't require network, MCP subprocesses, or WatsonX.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from types import SimpleNamespace
from unittest.mock import patch

import pytest


def _stub_args(**overrides):
    defaults = dict(
        prompt="test prompt",
        output="/tmp/out.json",
        model_id="watsonx/meta-llama/llama-3-3-70b-instruct",
        mcp_mode="direct",
        max_turns=30,
        parallel_tool_calls=False,
        verbose=False,
    )
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def _msg_item(text: str):
    """Build a stub message_output_item matching AOB's parser."""
    return SimpleNamespace(
        type="message_output_item",
        raw_item=SimpleNamespace(content=[SimpleNamespace(text=text)]),
    )


def _tool_call_item(name: str, args: dict, call_id: str = "c1"):
    """Build a stub tool_call_item."""
    import json as _json

    return SimpleNamespace(
        type="tool_call_item",
        raw_item=SimpleNamespace(
            name=name,
            arguments=_json.dumps(args),
            call_id=call_id,
            id=call_id,
        ),
    )


def _tool_output_item(output: str):
    return SimpleNamespace(type="tool_call_output_item", output=output)


def _stub_run_result(
    items=None, final_output="final answer text", max_turns_reached=False
):
    """Build a minimal RunResult-shaped object for serializer tests.

    Matches the shape AOB's _build_trajectory in
    ../AssetOpsBench/src/agent/openai_agent/runner.py:121 walks.
    """
    return SimpleNamespace(
        new_items=items or [],
        final_output=final_output,
        max_turns_reached=max_turns_reached,
        raw_responses=[],
    )


def test_serialize_run_result_happy_path():
    from scripts.aat_runner import _serialize_run_result

    args = _stub_args()
    result = _stub_run_result(
        items=[
            _tool_call_item("iot.list_sensors", {"asset_id": "T-1"}, "c1"),
            _tool_output_item("[]"),
            _msg_item("final answer text"),
        ]
    )

    out = _serialize_run_result(args, "test prompt", result, duration_seconds=12.5)

    assert out["question"] == "test prompt"
    assert out["answer"] == "final answer text"
    assert out["success"] is True
    assert out["max_turns_exhausted"] is False
    assert out["turn_count"] >= 1
    assert out["tool_call_count"] == 1
    assert out["runner_meta"]["model_id"] == args.model_id
    assert out["runner_meta"]["mcp_mode"] == "direct"
    assert out["runner_meta"]["max_turns"] == 30
    assert out["runner_meta"]["parallel_tool_calls"] is False
    assert out["runner_meta"]["duration_seconds"] == 12.5
    assert "aob_prompt_sha" in out["runner_meta"]

    # Regression guard: a tool call appearing before any message text must
    # still surface in history[0].tool_calls (not just tool_call_count).
    assert len(out["history"]) >= 1
    turn0 = out["history"][0]
    assert turn0["content"] == ""
    assert len(turn0["tool_calls"]) == 1
    assert turn0["tool_calls"][0]["name"] == "iot.list_sensors"
    assert turn0["tool_calls"][0]["output"] == "[]"
    # Sanity check: the final assistant content made it into the last turn.
    assert out["history"][-1]["content"] == "final answer text"


def test_serialize_run_result_warns_on_orphan_tool_output(caplog):
    from scripts.aat_runner import _serialize_run_result

    args = _stub_args()
    result = _stub_run_result(items=[_tool_output_item("late output")])

    with caplog.at_level(logging.WARNING, logger="aat_runner"):
        out = _serialize_run_result(args, "test prompt", result, duration_seconds=1.0)

    assert out["success"] is True
    assert "without a pending tool call" in caplog.text


def test_serialize_run_result_max_turns_exhausted():
    from scripts.aat_runner import _serialize_run_result

    args = _stub_args()
    result = _stub_run_result(
        items=[_msg_item("still thinking")],
        final_output=None,
        max_turns_reached=True,
    )

    out = _serialize_run_result(args, "test prompt", result, duration_seconds=99.0)

    assert out["success"] is False
    assert out["max_turns_exhausted"] is True


def test_cli_parses_required_args():
    from scripts.aat_runner import build_parser

    parser = build_parser()
    args = parser.parse_args(
        [
            "--prompt",
            "p",
            "--output",
            "/tmp/o.json",
            "--model-id",
            "watsonx/x",
            "--mcp-mode",
            "direct",
        ]
    )
    assert args.prompt == "p"
    assert args.mcp_mode == "direct"
    assert args.max_turns == 30  # default
    assert args.parallel_tool_calls is False  # vLLM-compatible default


def test_cli_parses_parallel_tool_call_modes():
    from scripts.aat_runner import build_parser

    parser = build_parser()
    common = [
        "--prompt",
        "p",
        "--output",
        "/tmp/o.json",
        "--model-id",
        "watsonx/x",
        "--mcp-mode",
        "direct",
        "--parallel-tool-calls",
    ]

    assert parser.parse_args(common + ["false"]).parallel_tool_calls is False
    assert parser.parse_args(common + ["true"]).parallel_tool_calls is True
    assert parser.parse_args(common + ["auto"]).parallel_tool_calls is None


def test_cli_missing_args_errors():
    from scripts.aat_runner import build_parser

    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--prompt", "p"])  # missing everything else


def test_cli_invalid_mcp_mode_errors():
    from scripts.aat_runner import build_parser

    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "--prompt",
                "p",
                "--output",
                "/tmp/o.json",
                "--model-id",
                "x",
                "--mcp-mode",
                "nonsense",
            ]
        )


def test_runner_threads_litellm_env(monkeypatch):
    from scripts.aat_runner import AaTRunner

    captured: dict[str, object] = {}

    class FakeLitellmModel:
        def __init__(self, model, base_url=None, api_key=None):
            captured["model"] = model
            captured["base_url"] = base_url
            captured["api_key"] = api_key

    class FakeModelSettings:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeAgent:
        def __init__(self, **kwargs):
            captured["agent_kwargs"] = kwargs

    class FakeRunner:
        @staticmethod
        async def run(agent, prompt, max_turns):
            captured["prompt"] = prompt
            captured["max_turns"] = max_turns
            return _stub_run_result()

    monkeypatch.setenv("LITELLM_BASE_URL", "http://127.0.0.1:8000/v1")
    monkeypatch.setenv("LITELLM_API_KEY", "dummy-vllm-not-checked")
    monkeypatch.setitem(
        sys.modules,
        "agents",
        SimpleNamespace(
            Agent=FakeAgent,
            ModelSettings=FakeModelSettings,
            Runner=FakeRunner,
            __version__="test",
        ),
    )
    monkeypatch.setitem(sys.modules, "agents.extensions", SimpleNamespace())
    monkeypatch.setitem(sys.modules, "agents.extensions.models", SimpleNamespace())
    monkeypatch.setitem(
        sys.modules,
        "agents.extensions.models.litellm_model",
        SimpleNamespace(LitellmModel=FakeLitellmModel),
    )

    runner = AaTRunner(model_id="openai/Llama-3.1-8B-Instruct", mcp_mode="direct")
    asyncio.run(runner.run("hello"))

    assert captured["model"] == "openai/Llama-3.1-8B-Instruct"
    assert captured["base_url"] == "http://127.0.0.1:8000/v1"
    assert captured["api_key"] == "dummy-vllm-not-checked"
    assert captured["prompt"] == "hello"
    assert captured["max_turns"] == 30
    settings = captured["agent_kwargs"]["model_settings"]
    assert settings.kwargs["parallel_tool_calls"] is False


def test_batch_mode_requires_output_dir():
    from scripts.aat_runner import _main

    args = argparse.Namespace(
        scenarios_glob="data/scenarios/*.json",
        output_dir=None,
        prompt=None,
        output=None,
        model_id="x",
        mcp_mode="optimized",
        max_turns=30,
        parallel_tool_calls=False,
        verbose=False,
        trials=1,
        run_basename="batch",
    )
    assert asyncio.run(_main(args)) == 2


def test_batch_mode_rejects_non_optimized_mcp_mode(tmp_path):
    from scripts.aat_runner import _main

    args = argparse.Namespace(
        scenarios_glob="nonexistent_xyzzy_*.json",
        output_dir=str(tmp_path),
        prompt=None,
        output=None,
        model_id="x",
        mcp_mode="direct",
        max_turns=30,
        parallel_tool_calls=False,
        verbose=False,
        trials=1,
        run_basename="batch",
    )
    assert asyncio.run(_main(args)) == 2


def test_batch_output_dir_normalization():
    """Regression: relative --output-dir must not raise ValueError in relative_to().

    Directly exercises the path arithmetic that crashed before the fix, without
    calling _main_multi (which would mkdir under the repo and never reach
    relative_to due to the empty-glob early-return).
    """
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent.parent
    # Simulate what _main_multi does: resolve relative arg under repo_root.
    raw = Path("benchmarks/cell_C_mcp_optimized/raw/test-run")
    output_dir = repo_root / raw  # normalization step added by the fix
    out_path = output_dir / "batch_scenario_run01.json"
    # This is the exact call that raised ValueError before the fix.
    rel = out_path.relative_to(repo_root)
    assert rel == Path(
        "benchmarks/cell_C_mcp_optimized/raw/test-run/batch_scenario_run01.json"
    )


def test_batch_mode_rejects_non_optimized_before_mkdir(tmp_path):
    """M1 regression: mcp_mode guard must fire before output_dir is created."""
    from scripts.aat_runner import _main_multi
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent.parent
    new_subdir = tmp_path / "should_not_be_created"
    args = argparse.Namespace(
        scenarios_glob="nonexistent_xyzzy_*.json",
        output_dir=str(new_subdir),
        model_id="x",
        mcp_mode="direct",
        max_turns=30,
        parallel_tool_calls=False,
        trials=1,
        run_basename="batch",
    )
    rc = asyncio.run(_main_multi(args, repo_root))
    assert rc == 2
    assert not new_subdir.exists()


def test_batch_latency_path_outside_repo_root(tmp_path):
    """M3 regression: relative_to() fallback must not raise for absolute out-of-repo path."""
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent.parent
    out_path = tmp_path / "trial_01.json"  # tmp_path is outside repo_root
    # Reproduce the exact try/except logic from _main_multi latency record construction.
    try:
        result = out_path.relative_to(repo_root).as_posix()
    except ValueError:
        result = out_path.as_posix()
    # tmp_path is outside repo_root, so the fallback must kick in.
    assert result == out_path.as_posix()
