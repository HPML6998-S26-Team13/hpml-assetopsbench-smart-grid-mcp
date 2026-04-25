"""Unit tests for scripts/aat_runner.py.

These tests use stubbed RunResult objects and mocked Runner.run() so
they don't require network, MCP subprocesses, or WatsonX.
"""

from __future__ import annotations

import argparse
import json
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


def _stub_run_result(items=None, final_output="final answer text", max_turns_reached=False):
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
    result = _stub_run_result(items=[
        _tool_call_item("iot.list_sensors", {"asset_id": "T-1"}, "c1"),
        _tool_output_item("[]"),
        _msg_item("final answer text"),
    ])

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
    assert out["runner_meta"]["duration_seconds"] == 12.5
    assert "aob_prompt_sha" in out["runner_meta"]

    # Regression guard: a tool call appearing before any message text must
    # still surface in history[0].tool_calls (not just tool_call_count).
    assert len(out["history"]) >= 1
    turn0 = out["history"][0]
    assert len(turn0["tool_calls"]) == 1
    assert turn0["tool_calls"][0]["name"] == "iot.list_sensors"
    assert turn0["tool_calls"][0]["output"] == "[]"
    # Sanity check: the final assistant content made it into the last turn.
    assert out["history"][-1]["content"] == "final answer text"


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
    args = parser.parse_args([
        "--prompt", "p",
        "--output", "/tmp/o.json",
        "--model-id", "watsonx/x",
        "--mcp-mode", "direct",
    ])
    assert args.prompt == "p"
    assert args.mcp_mode == "direct"
    assert args.max_turns == 30  # default


def test_cli_missing_args_errors():
    from scripts.aat_runner import build_parser

    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--prompt", "p"])  # missing everything else


def test_cli_invalid_mcp_mode_errors():
    from scripts.aat_runner import build_parser

    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([
            "--prompt", "p",
            "--output", "/tmp/o.json",
            "--model-id", "x",
            "--mcp-mode", "nonsense",
        ])
