# Repository Strategy

*Last updated: April 10, 2026 - org repo is canonical*

## Canonical repo layout

We now use three code/document surfaces for different purposes:

### 1. Canonical collaboration repo: `HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp`

This is the team repo and the source of truth for all shared project work.
The org repo `main` branch is the canonical branch. GitHub Projects, planning docs, MCP
server code, scenarios, benchmark scripts, and public-facing project docs all
live here.

### 2. Personal mirror: `eggrollofchaos/hpml-assetopsbench-smart-grid-mcp`

This repo mirrors the canonical team repo after pushes land on the org repo `main` branch.
It exists as a backup / personal mirror, not as the planning or collaboration
surface. Day-to-day work should not branch from this mirror.

### 3. Upstream PR staging fork: `eggrollofchaos/AssetOpsBench`

This is the eventual staging area for the open-source contribution back to IBM's
AssetOpsBench. We will copy only the PR-bound subset here once the Smart Grid
extension stabilizes.

## Private notes repo

Alex also keeps private planning notes in the local class repo at:

`~/coding/Classes/COMS-E6998/Final Project/`

That repo is for private prep notes, meeting prep, and personal status tracking.
It is not the canonical source for shared team code or shared task state.

## What goes where

| Item | org canonical repo | personal mirror | AssetOpsBench fork |
|---|---|---|---|
| MCP server implementations | yes | mirrored copy | later, PR-bound subset only |
| Smart Grid scenarios | yes | mirrored copy | later, PR-bound subset only |
| Data pipeline scripts | yes | mirrored copy | later, PR-bound subset only |
| Processed CSVs and project-specific artifacts | yes | mirrored copy | likely no, or replaced with loaders / generators |
| Shared planning docs and call notes | yes | mirrored copy | no |
| Private prep notes and personal status docs | no | no | no |
| WatsonX setup, compute notes, benchmark prompts | yes | mirrored copy | mostly no |

## Day-to-day workflow

1. Treat the org repo `main` branch as canonical.
2. Push to the org repo first.
3. Mirror the same commit to `origin` after the canonical push succeeds.
4. Keep local planning notes or rough prep material in the personal class repo until
   they are ready to become shared documentation.
5. Near W5, stage the clean upstream contribution in `eggrollofchaos/AssetOpsBench`
   against `upstream/main`.

## Practical git guidance

- Local `main` should track the org repo `main` branch.
- If you use a local remote alias like `team13`, remember that alias is only local shorthand for the org repo.
- Plain `git push` should update the canonical team repo first.
- After a successful canonical push, mirror to `origin/main`.
- If history is rewritten on `main`, teammates should reset local `main` to
  the org repo `main` branch and replay any in-flight work from feature branches.

## Why this split works

- The canonical team repo stays understandable for the whole team.
- The personal mirror remains a safety copy, not a second source of truth.
- The IBM fork stays clean until we are ready to upstream only the subset that
  belongs in AssetOpsBench.
- The private class repo can hold candid status notes and prep material without
  polluting the shared repo.
