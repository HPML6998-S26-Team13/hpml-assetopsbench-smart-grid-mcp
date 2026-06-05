---
title: Coordination Cascade For Long Multi-Agent Projects
slug: coordination-cascade
type: learning
status: live
created: 2026-06-05
updated: 2026-06-05
owner: Team 13
scope: project
project: hpml-assetopsbench-smart-grid-mcp
tags: [coordination, handoff, repo-memory, agents]
canonical: true
sources:
  - docs/retrospectives/2026-06-05_coordination-protocol-and-repo-memory-closeout.md
  - /Users/wax/coding/Classes/COMS-E6998/docs/coordination/shift_coordination_note_template.md
related:
  - docs/knowledge-base/learnings/2026-06-05_aat-smoke-runtime-preflight.md
  - /Users/wax/coding/ai-coding-agents/docs/knowledge-base/learnings/2026-05-29_multi-initiative-session-closeout-inventory.md
---

# Coordination Cascade For Long Multi-Agent Projects

## Pattern

Use three coordination layers instead of one ever-growing handoff note:

| Layer | Job | Retention rule |
|---|---|---|
| Shift note | Per-agent, per-session active delta | Keep only current action context, open loops, and not-a-blocker guidance |
| Live summary | Current repo truth | Keep facts that are still live blockers, proof anchors, or next-agent context |
| History | Condensed audit trail | Move displaced live facts here when active work has made them stale |

This project eventually moved the coordination surfaces out of the public team
repo and into Alex's personal class repo because they are agent-operation
state, not team-facing project documentation.

## Apply This Rule

1. Before writing new coordination content, classify it as active delta,
   current truth, or historical audit context.
2. If a shift note grows beyond roughly 600 words or 20 bullets, compact it.
3. Promote settled current facts from the shift note into the live summary.
4. Move displaced live-summary detail into history only when newer active work
   makes it no longer useful in the live memo.
5. Do not evict content solely because a time window elapsed. The window is a
   configured emphasis range, not a garbage collector.

## Anti-Pattern

Do not use a shift note as a transcript. The transcript already exists in chat,
commits, issue comments, validation logs, and run artifacts. A shift note should
make the next agent faster, not preserve every step.

## SmartGridBench-Specific Note

The canonical coordination directory for this project is:

`/Users/wax/coding/Classes/COMS-E6998/docs/coordination/`

The team repo should continue to avoid publishing agent-tooling coordination
details as if they were teammate-facing project docs.
