---
title: AaT Runner Smoke Debugging Closeout
slug: aat-runner-smoke-debugging-closeout
type: retrospective
status: live
created: 2026-06-05
updated: 2026-06-05
owner: Alex Xin
scope: project
project: hpml-assetopsbench-smart-grid-mcp
tags: [aat-runner, insomnia, mcp, vllm, experiment-1]
work-items: []
related:
  - docs/archive/2026-04-24-aat-runner.md
  - docs/specs/2026-04-24-aat-runner-design.md
  - docs/validation_log.md
  - docs/experiment1_capture_plan.md
agent: Codex
agent-provider: OpenAI
agent-interface: Codex Desktop
agent-session-id: 019d697e-964d-7302-8114-6e243f1d69b7
session-label: "FND: Coordination and AaT Review"
invocation-context: "session-closeout: closeable"
session-lifecycle: closeable
session-closeout-note: .agent-sessions/closed/session-closeout-019d697e-964d-7302-8114-6e243f1d69b7.md
---

# AaT Runner Smoke Debugging Closeout - 2026-06-05

## Metadata

| Field | Value |
|---|---|
| Unit | Agent-as-Tool runner review, squash, and Insomnia smoke debugging |
| Unit type | Initiative closeout |
| Status | Completed and superseded by later smoke/capture validation entries |
| Repo | hpml-assetopsbench-smart-grid-mcp |
| Branch / PR | Historical `codex-fnd/aat-smoke-fix`, PR #127, Aaron's #25/#104 work |
| Work item IDs | Runtime placeholder AUX-3f1d69b7 only |
| Sources inspected | `docs/archive/2026-04-24-aat-runner.md`, `docs/specs/2026-04-24-aat-runner-design.md`, `docs/validation_log.md`, `docs/experiment1_capture_plan.md`, CHANGELOG, personal coordination notes |

## 1. Work Completed

| What | Why | How | Evidence |
|---|---|---|---|
| Reviewed Aaron's AaT runner implementation | #104 shipped a runner stack that affected #25 and Experiment 1 validity | Compared actual code architecture to the agreed Option 1b runner shape | Archived plan/spec; validation log #104 section |
| Squashed Aaron's many local commits into three logical commits | Main history needed to stay human-scannable and attribution-clean | Repartitioned the work into runner/tooling/tests, configs/smoke targets, and docs/plan | Historical team13/main commits `2264fb7`, `0de35f1`, `e2b3f48` noted in conversation |
| Reopened #104 with concrete findings instead of treating it as fully done | The runner was mostly correct but smoke/runtime evidence and routing details still needed proof | Posted findings around LiteLLM local-vLLM routing, tool-name parity, output shape, and smoke status | Conversation and issue-comment work; later validation log records resolved state |
| Built and pushed a smoke-fix branch | Cell B failed before model/tool execution because MCP server subprocess initialization was timing out | Added dependency preflights, env/base URL wiring, warmed Python launch mode, configurable timeout, and bootstrap diagnostics | CHANGELOG 2026-04-25 AaT smoke hardening entries; validation log #104 section |
| Diagnosed the Cell B MCP initialize failure | Failures were initially ambiguous: vLLM, dependencies, SDK timeout, or server launch | Successive Slurm jobs narrowed it to cold per-server `uv run` dependency downloads inside MCP initialize deadline | Conversation run IDs 8963732, 8968252, 8968860; validation log caveats |
| Preserved the upstream parity distinction | AOB's `OpenAIAgentRunner` was useful for parity but not sufficient for Cell A direct tools | Kept team-local runner as benchmark path and AOB runner as Cell B parity smoke | `docs/orchestration_wiring.md`; validation log upstream parity jobs 8970383 and 8970468 |

## 2. Ideas, Decisions, Questions Addressed

| Item | Type | Resolution | Rationale | Evidence |
|---|---|---|---|---|
| Does PE-family use AOB's `PlanExecuteRunner` while AaT wraps `OpenAIAgentRunner`? | Decision | PE-family uses the AOB plan-execute slice; AaT benchmark path uses a team-local OpenAI Agents SDK runner, with AOB `OpenAIAgentRunner` only for parity | AOB's AaT runner had no clean Cell A direct-tool injection point | `docs/specs/2026-04-24-aat-runner-design.md` |
| Should we try the broken smoke first or patch LiteLLM routing? | Decision | We tried and instrumented enough to isolate; then patched | The observed object had no base URL/API key and local-vLLM routing needed explicit env threading | Conversation and CHANGELOG 2026-04-25 |
| Which tool names should Cell A and Cell B expose? | Decision | Model-visible bare names should match; internal dotted names are not the comparison contract | Experiment 1 fairness requires same visible tool surface | `docs/validation_log.md` fairness guard; `tests/test_orchestration_utils.py` references |
| Should Cell B use per-server `uv run` in production smoke? | Decision | No for Insomnia canonical smoke; use warmed `.venv-insomnia` Python and preflight deps before vLLM | Cold dependency resolution inside MCP initialize measures package setup, not MCP transport | CHANGELOG 2026-04-25; validation log |

## 3. Issues Encountered And Resolved

| Issue | Impact | Resolution | Verification | Prevention / Learning |
|---|---|---|---|---|
| SSH/Slurm access was inconsistent | Codex could not reliably inspect jobs via `ssh insomnia` and Slurm CLI | User submitted jobs manually when needed; later docs captured shell/SLURM_CONF gotchas | User handoff; later Insomnia docs and shift notes | Do not assume remote command shape equals interactive SSH shape |
| vLLM startup and MCP initialize failures overlapped | Early failures looked like one "runner broken" bucket | Added staged preflights and stderr milestones before model launch | Jobs narrowed from CUDA/env/deps to MCP initialize | Expensive GPU startup should happen after cheap dependency checks |
| Per-server `uv run` cold-start downloaded pandas/numpy inside SDK timeout | Cell B initialized too slowly before first tool call | Switched server launch mode to warmed `.venv-insomnia` Python for Insomnia smoke | Later Cell B smoke job 8969519 succeeded; validation log records 1/1 success | Benchmark runtime should not include environment resolution unless deliberately measuring setup time |
| Local vLLM rejected parallel tool calls | Cell B could reach tool execution but local Llama 3 path only supported sequential tool calls | Defaulted `parallel_tool_calls` false for local vLLM path | Validation log records successful Cell B and later Cell C sequential-tool-call config | Tool-call capability is provider/model-specific; do not inherit hosted-provider assumptions |
| AaT artifacts did not initially feed summaries/judges cleanly | Successful runs risked looking tool-less or parser-incompatible | Updated summary aggregation and output shape handling | CHANGELOG 2026-04-25; later #25 capture validation | Consumer contracts must be checked with real artifacts, not just runner return objects |

## 4. Remaining Ideas, Decisions, Questions

| Item | Type | Priority | Time Horizon | Owner / Next Action | Tracking |
|---|---|---|---|---|---|
| Treat old failed job IDs as historical debugging evidence only | Decision | P3 | done | Current proof is validation-log jobs 8962310, 8969519, 8970383, 8970468, and full capture 8979314 | `docs/validation_log.md` |
| Re-run final A/B/C only after scenario/stack freeze | Follow-up | P2 | superseded by later final matrix work | Use final matrix/cohort docs rather than old smoke branch state | `docs/experiment_matrix.md`; `docs/validation_log.md` |

## 5. Remaining Issues

| Issue | Risk | Priority | Time Horizon | Owner / Next Action | Tracking |
|---|---|---|---|---|---|
| Historical smoke branch SHAs were rewritten during attribution cleanup | Old `meta.json` SHAs may not resolve on remote | P2 | ongoing | Use validation log's "historical Slurm-recorded SHAs" caveat and current reachable branch/commit references | `docs/validation_log.md` |
| One-scenario smoke proof is not the same as full experiment capture | Future readers might overstate #104 smoke as #25 complete | P2 | ongoing | Cite #25 full capture section for canonical A/B capture | `docs/validation_log.md` 2026-04-26 section |

## 6. Learnings

### Local

- The actual blocker for Cell B was not "MCP is slow" or "vLLM is broken." It was cold dependency resolution inside the MCP server launch path, hidden under the OpenAI Agents SDK initialize timeout.
- For local-vLLM tool calling, set provider-specific request shape explicitly: base URL/API key, tool parser, sequential tool calls, and warmed server Python.

### Project

- Expensive Slurm jobs should fail fast on Python package imports, server importability, and config requirements before launching vLLM.
- Parity against upstream AOB is valuable, but the benchmark runner can still be team-local when the experiment requires a tool-source hook upstream does not expose.

### Global Candidates

- For cluster-based agent benchmarks, distinguish three time budgets: environment setup, server initialize, and model inference. If they share one timeout, the failure mode is opaque.

## 7. Strategic Fit

| Level | Fit |
|---|---|
| Task / sprint | #104 runner landing and #25 Experiment 1 unblock |
| Epic / initiative | Experiment 1 MCP overhead |
| Product / program / engagement | SmartGridBench benchmark reproducibility |
| Repo / project | Established the direct-vs-MCP AaT fairness contract and generated the first smoke proof path |
| Global framework | Reusable cluster-smoke debugging pattern for MCP + local-vLLM agent runners |
