"""Bootstrap a Smart Grid MCP server with startup diagnostics.

OpenAI Agents SDK starts MCP stdio servers as subprocesses. This wrapper keeps
server stdout reserved for JSON-RPC while writing a few startup milestones to
stderr, which lands in the harness log when a server hangs before initialize.
"""

from __future__ import annotations

import runpy
import os
import sys
from pathlib import Path


def _log(message: str) -> None:
    print(f"[aat-mcp-server-bootstrap] {message}", file=sys.stderr, flush=True)


def _resolve_repo_root(target: Path) -> Path:
    configured = os.environ.get("AAT_MCP_REPO_ROOT", "").strip()
    if configured:
        repo_root = Path(configured).resolve()
        if not (repo_root / "mcp_servers").is_dir():
            raise FileNotFoundError(
                f"AAT_MCP_REPO_ROOT does not look like the repo root: {repo_root}"
            )
        return repo_root

    for parent in target.parents:
        if (parent / "mcp_servers").is_dir() and (parent / "scripts").is_dir():
            return parent
    raise FileNotFoundError(
        f"Could not infer repo root for MCP server target: {target}"
    )


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: aat_mcp_server_bootstrap.py <server.py>")

    target = Path(sys.argv[1]).resolve()
    if not target.exists():
        raise FileNotFoundError(f"MCP server target not found: {target}")

    repo_root = _resolve_repo_root(target)
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    _log(f"python={sys.executable}")
    _log(f"cwd={Path.cwd()}")
    _log(f"target={target}")
    namespace = runpy.run_path(str(target), run_name="__aat_mcp_server__")
    server = namespace.get("mcp")
    if server is None:
        raise RuntimeError(
            f"{target} did not define a global FastMCP object named 'mcp'"
        )
    _log("server module imported; starting stdio loop")
    server.run()


if __name__ == "__main__":
    main()
