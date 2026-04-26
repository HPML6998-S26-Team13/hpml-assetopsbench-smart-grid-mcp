"""Tests for the Cell B MCP tool builder."""

from __future__ import annotations

import pathlib
import sys

import pytest


def test_mcp_client_timeout_default(monkeypatch):
    from scripts.aat_tools_mcp import _client_timeout_seconds

    monkeypatch.delenv("AAT_MCP_CLIENT_TIMEOUT_SECONDS", raising=False)

    assert _client_timeout_seconds() == 30


def test_mcp_client_timeout_env(monkeypatch):
    from scripts.aat_tools_mcp import _client_timeout_seconds

    monkeypatch.setenv("AAT_MCP_CLIENT_TIMEOUT_SECONDS", "45.5")

    assert _client_timeout_seconds() == 45.5


def test_mcp_client_timeout_rejects_invalid_env(monkeypatch):
    from scripts.aat_tools_mcp import _client_timeout_seconds

    monkeypatch.setenv("AAT_MCP_CLIENT_TIMEOUT_SECONDS", "nope")

    with pytest.raises(ValueError, match="must be numeric"):
        _client_timeout_seconds()


def test_server_launch_mode_rejects_invalid_env(monkeypatch):
    from scripts.aat_tools_mcp import _server_launch_mode

    monkeypatch.setenv("AAT_MCP_SERVER_LAUNCH_MODE", "bogus")

    with pytest.raises(ValueError, match="must be either"):
        _server_launch_mode()


def test_server_params_python_uses_bootstrap(monkeypatch):
    from scripts.aat_tools_mcp import _server_params

    repo_root = pathlib.Path.cwd()
    server_path = repo_root / "mcp_servers/iot_server/server.py"
    monkeypatch.setenv("AAT_MCP_SERVER_LAUNCH_MODE", "python")
    monkeypatch.setenv("AAT_MCP_SERVER_PYTHON", sys.executable)

    params = _server_params(repo_root, server_path)

    assert params["command"] == sys.executable
    assert params["args"][:2] == [
        "-u",
        str(repo_root / "scripts/aat_mcp_server_bootstrap.py"),
    ]
    assert params["args"][-1] == str(server_path)
    assert params["cwd"] == str(repo_root)
    assert params["env"] == {
        "PYTHONUNBUFFERED": "1",
        "AAT_MCP_REPO_ROOT": str(repo_root),
    }


def test_server_params_python_requires_server_python(monkeypatch):
    from scripts.aat_tools_mcp import _server_params

    repo_root = pathlib.Path.cwd()
    server_path = repo_root / "mcp_servers/iot_server/server.py"
    monkeypatch.setenv("AAT_MCP_SERVER_LAUNCH_MODE", "python")
    monkeypatch.delenv("AAT_MCP_SERVER_PYTHON", raising=False)

    with pytest.raises(ValueError, match="requires AAT_MCP_SERVER_PYTHON"):
        _server_params(repo_root, server_path)


def test_server_params_uv_ignores_server_python(monkeypatch):
    from scripts.aat_tools_mcp import _server_params

    repo_root = pathlib.Path.cwd()
    server_path = repo_root / "mcp_servers/iot_server/server.py"
    monkeypatch.setenv("AAT_MCP_SERVER_LAUNCH_MODE", "uv")
    monkeypatch.setenv("AAT_MCP_SERVER_PYTHON", "/usr/bin/python3")

    params = _server_params(repo_root, server_path)

    assert params["command"] == "uv"
    assert "python" in params["args"]
    assert "-u" in params["args"]
    assert str(repo_root / "scripts/aat_mcp_server_bootstrap.py") in params["args"]
    assert params["args"][-1] == str(server_path)
    assert params["env"] == {
        "PYTHONUNBUFFERED": "1",
        "AAT_MCP_REPO_ROOT": str(repo_root),
    }
