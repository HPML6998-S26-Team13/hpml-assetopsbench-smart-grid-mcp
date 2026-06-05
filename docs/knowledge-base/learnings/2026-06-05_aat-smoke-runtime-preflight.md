---
title: AaT Smoke Runtime Preflight Before GPU Launch
slug: aat-smoke-runtime-preflight
type: learning
status: live
created: 2026-06-05
updated: 2026-06-05
owner: Team 13
scope: project
project: hpml-assetopsbench-smart-grid-mcp
tags: [aat-runner, insomnia, mcp, vllm, preflight]
canonical: true
sources:
  - docs/retrospectives/2026-06-05_aat-runner-smoke-debugging-closeout.md
  - docs/validation_log.md
related:
  - docs/knowledge-base/learnings/2026-06-05_coordination-cascade.md
  - docs/experiment1_capture_plan.md
---

# AaT Smoke Runtime Preflight Before GPU Launch

## Pattern

For MCP-backed AaT smoke runs on Insomnia, fail fast on local Python and MCP
server readiness before launching vLLM. The expensive GPU allocation should not
be the first place we discover missing `agents`, `pandas`, `numpy`, server
import failures, or an MCP initialize timeout caused by per-server dependency
downloads.

## Apply This Rule

1. Preflight runner dependencies with the same Python environment the Slurm job
   will use.
2. Preflight each MCP server's import dependencies before vLLM starts.
3. Launch MCP servers with the warmed `.venv-insomnia` Python for canonical
   Insomnia smokes, not cold per-server `uv run` environments.
4. Keep MCP initialize timeout configurable and long enough for real server
   startup, but do not use it to hide package-resolution work.
5. Log bootstrap milestones to stderr so a timeout tells us whether the server
   reached Python, import, FastMCP setup, or tool-listing.
6. Set local-vLLM tool-call shape explicitly: OpenAI-compatible base URL/API
   key, Llama 3 JSON tool parser, and sequential tool calls when the served
   model rejects parallel tool calls.

## What Triggered This

During the April 2026 AaT smoke-fix loop, Cell B reached vLLM startup but hung
while the OpenAI Agents SDK initialized the first MCP stdio server. Increasing
the timeout from the SDK default to 30 seconds did not solve it. Bootstrap
diagnostics showed the process never reached the wrapper's Python milestone
because per-server `uv run` was still downloading data dependencies. Switching
to the warmed `.venv-insomnia` Python turned the timeout into a normal MCP
server startup path and led to the successful Cell B smoke recorded in
`docs/validation_log.md`.

## Boundary

This is a benchmark-smoke rule, not a general ban on `uv run`. For local
developer checks, `uv run` is fine. For cluster benchmark jobs, environment
resolution belongs in setup/preflight, not inside the measured runtime or the
SDK initialize deadline.
