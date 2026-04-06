# Repository Strategy

*Last updated: April 6, 2026 — pending team finalization on April 7 call*

## Two repos, two purposes

We work out of two related repositories:

### 1. Team repo (this one): `eggrollofchaos/hpml-assetopsbench-smart-grid-mcp`

Day-to-day project work and team coordination. This is where everyone pushes
and where the bulk of activity happens during the project.

**Contents:**
- Internal planning and coordination docs (`docs/`, `planning/`)
- Mid-report drafts and meeting notes
- Compute plan, WatsonX setup docs, internal tooling
- MCP server implementations (work-in-progress)
- Smart Grid scenario authoring (work-in-progress)
- Data pipeline + processed datasets
- Profiling code, benchmark prompts
- Class-project-specific configuration and credentials (gitignored)

### 2. PR staging: `eggrollofchaos/AssetOpsBench`

Alex's existing fork of IBM/AssetOpsBench, with `upstream` configured to track
IBM's main. This is the eventual home for our open-source contribution back to
AssetOpsBench.

**Contents (when we get there):**
- A feature branch (e.g., `smartgrid-mcp`) containing only the PR-bound subset:
  - MCP server implementations (final, cleaned up)
  - Smart Grid scenario JSON files
  - Data pipeline scripts (`data/build_processed.py`, `data/generate_synthetic.py`)
  - Loader / download scripts for the processed Kaggle datasets
  - A short "Smart Grid extension" doc explaining the new asset class
- Stays in sync with `upstream/main` via periodic
  `git fetch upstream && git merge upstream/main`

## What goes where

| Item | Team repo | Fork |
|---|---|---|
| MCP server implementations (during dev) | yes | no (until W4-W5) |
| MCP server implementations (final, for PR) | yes | yes (cherry-picked) |
| Smart Grid scenarios | yes | yes (cherry-picked at end) |
| Data pipeline scripts | yes | yes (cherry-picked at end) |
| Processed Kaggle CSVs | yes | TBD (full data vs download scripts vs LFS) |
| Mid-report drafts (PPT, MD) | yes | no |
| `planning/` (internal coordination) | yes | no |
| `docs/compute_plan.md` (Insomnia/GCP-specific) | yes | no |
| `docs/watsonx_access.md` (project-specific access route) | yes | no |
| `docs/mid_checkpoint_notes.md`, `roadmap.md`, `project_synopsis.md` | yes | no |
| `scripts/verify_watsonx.py`, `scripts/benchmark_prompts/` | yes | no |
| `codex_mcp_prompts/` | yes | no |
| `.env` (credentials) | gitignored | gitignored |

## Workflow

1. **Day-to-day:** push to the team repo as usual.
2. **Periodic upstream sync:** roughly weekly, sync `eggrollofchaos/AssetOpsBench`
   with `upstream/main` to stay current with IBM's changes (e.g., recent
   `src/workflow/` → `src/agent/` rename).
3. **Closer to W4-W5:** when MCP servers and scenarios are stable, copy /
   cherry-pick the PR-bound subset into a feature branch on the fork. Clean up,
   test against upstream, and PR from there.

## Why two repos instead of one

**Pros of separation:**
- Internal team docs (planning, mid-report drafts, compute plans, WatsonX setup,
  Codex review notes) never risk leaking into the upstream PR
- The fork stays clean — `git diff upstream/main fork/smartgrid-mcp` is exactly
  what we're contributing
- Periodic upstream sync on the fork is safe — no merge conflicts with our
  internal docs
- We can keep the team repo around as a "how we built it" record after the
  upstream PR merges, useful for the final report and the NeurIPS submission

**Cons of separation:**
- Two URLs to remember, slight context-switching cost
- When we're ready to PR, we have to copy code over to the fork (some manual
  work)
- Potential for the two repos to drift if we're not careful about which one
  has the canonical version of MCP server code

**Mitigations:**
- Treat the team repo as canonical for MCP server code during development
- Only copy to the fork close to PR-submission time, when the code is stable
- Use `git diff` between the two before PR to confirm parity

## Open questions

To finalize on the April 7 call:

- Confirm all four team members are on board with the two-repo split (vs
  single-repo with subdirectory split)
- Decide who owns the periodic upstream sync on the fork
- Decide how to handle processed Kaggle CSV files in the upstream PR
  (full data via Git LFS vs download scripts vs reference loaders)
- Decide who runs the eventual cleanup + PR submission near W5
