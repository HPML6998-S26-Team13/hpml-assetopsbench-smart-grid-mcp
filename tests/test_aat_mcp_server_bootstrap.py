"""Tests for the AaT MCP server bootstrap helper."""

from __future__ import annotations

import pathlib

import pytest


def test_resolve_repo_root_prefers_env(monkeypatch) -> None:
    from scripts.aat_mcp_server_bootstrap import _resolve_repo_root

    repo_root = pathlib.Path.cwd()
    target = repo_root / "mcp_servers/iot_server/server.py"
    monkeypatch.setenv("AAT_MCP_REPO_ROOT", str(repo_root))

    assert _resolve_repo_root(target) == repo_root


def test_resolve_repo_root_rejects_bad_env(monkeypatch, tmp_path) -> None:
    from scripts.aat_mcp_server_bootstrap import _resolve_repo_root

    repo_root = pathlib.Path.cwd()
    target = repo_root / "mcp_servers/iot_server/server.py"
    monkeypatch.setenv("AAT_MCP_REPO_ROOT", str(tmp_path))

    with pytest.raises(FileNotFoundError, match="does not look like the repo root"):
        _resolve_repo_root(target)


def test_resolve_repo_root_can_infer_from_target(monkeypatch) -> None:
    from scripts.aat_mcp_server_bootstrap import _resolve_repo_root

    repo_root = pathlib.Path.cwd()
    target = repo_root / "mcp_servers/iot_server/server.py"
    monkeypatch.delenv("AAT_MCP_REPO_ROOT", raising=False)

    assert _resolve_repo_root(target) == repo_root
