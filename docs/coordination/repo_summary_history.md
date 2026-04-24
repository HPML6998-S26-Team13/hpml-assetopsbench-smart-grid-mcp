# Repo Summary History

Created: 2026-04-21  
Updated: 2026-04-24 01:56 EDT

This file records material deliberately removed or condensed out of `docs/coordination/live_repo_summary.md`.
It is not a verbatim changelog of every edit. The goal is to preserve useful historical context
without making the live summary unreadable.

## 2026-04-21 — First history extraction from the live summary

### Why this file was created

The live summary had started mixing three different jobs:

1. current-state handoff
2. milestone/proof ledger
3. historical review commentary

That made it harder to use as a fast agent handoff. The active-state doc was trimmed, and the
older material below was moved here.

### Material removed from the live summary

#### Aaron’s five canonical-main commits review block

The old live summary had a long section summarizing post-review findings on Aaron’s Apr 20
canonical-main series:

- `01043c5` — profiling ↔ WandB linkage
- `91cb21e` — Experiment 1 Cell A/B/C scaffolding
- `f2f3083` — canonical infra runbook
- `77fc11d` — GCP fallback runbook
- `b0f0d40` — `#111` Insomnia reconciliation

That section was useful during active triage, but by Apr 21 most of it had become historical:

- `#37` follow-up doc fixes were already reflected in `docs/runbook.md` and `docs/insomnia_runbook.md`
- the `#111` story had narrowed from “general reconciliation” to one concrete shell bug plus rerun
- the “candidate doc-only cleanups” list was no longer a forward-looking todo list; most of it had already happened

The live doc now points here instead of carrying the full review narrative.

### State transitions since the first live summary draft

The first versions of the live summary predated several important outcomes. These are the major
status transitions worth preserving:

- PR `#113` merged:
  - harness smoke proof
  - six-dimension LLM-as-Judge scorer
  - Smart Grid trajectory artifact
- PR `#114` merged:
  - Maverick-17B judge audit logs
  - repo-relative path fix
- PR `#115` merged:
  - self-hosted benchmark-path hardening
  - canonical Insomnia-serving fixes
  - linked closeouts for `#9`, `#10`, `#11`, `#12`, `#58`
- PR `#119` merged:
  - repo-local PE + Self-Ask runner
  - repo-local Verified PE runner
  - truthful runner accounting
  - clean smoke proofs for `#23` and `#24`
- PR `#120` merged:
  - Notebook 02 / 03 analysis scaffolds
  - `#26` / `#32` remain open because the missing piece is execution data, not notebook structure

### Orchestration / AOB lessons from Apr 20–21

These were worth keeping, but not in the front-page live handoff:

- Treat AssetOpsBench as a **library slice**, not a package you import wholesale.
- The real model boundary is **LiteLLM + OpenAI-compatible serving**.
- Import the actual orchestrator surfaces directly rather than relying on package-level
  `__init__` imports that pull in unrelated dependencies.
- Large tool payloads must be compacted before they are recycled into verifier prompts,
  retry prompts, or final summarization.

### `#111` narrowing

The issue moved through three distinct states:

1. broad setup/docs reconciliation issue
2. post-merge “prove canonical main matches the proven branch stack” issue
3. concrete last-mile bug:
   - `run_experiment.sh` and `vllm_serve.sh` source `insomnia_env.sh` via `BASH_SOURCE[0]`
   - under `sbatch`, that resolves into Slurm’s spool dir and fails immediately

Apr 21 proof results:

- job `8859923` exposed the bug on shared `main`
- job `8859928` validated the 2-line local fix in a temp Insomnia proof worktree and finished `2/2`

At this point the issue is no longer a vague reconciliation bucket. It is a tiny ship-and-rerun item.

### Documentation note

Going forward:

- keep `docs/coordination/live_repo_summary.md` for current state only
- whenever something important is removed from the live summary because it is now historical,
  add a short note here instead of losing the context entirely

## 2026-04-21 evening — issue-body boilerplate cleanup

### What changed

The team issue bodies had accumulated a repeated two-line header:

- `Canonical task source: GitHub Project + this issue body.`
- `Historical planning snapshots live in planning/archive/task_tracker.md and planning/archive/task_specs.md.`

That guidance was redundant once the repo docs had a stable single-source location for it.

### What was removed

- The duplicated boilerplate was stripped from the team repo issue bodies.
- The single-source explanation remains in `docs/README.md`, under the `planning/` bullet.

### Why it mattered

- It reduced noise in issue bodies, especially for the W2/W3/W4 task set.
- It made the issue bodies read as task definitions rather than partially duplicated repo-governance notes.
- It established a maintenance rule worth keeping: repo-wide planning/navigation guidance belongs in one doc index, not copied into every issue.

### Ongoing summary-maintenance rule

When material is removed from `docs/coordination/live_repo_summary.md`, preserve the substance here in condensed form:

- enough detail to reconstruct the state transition
- enough detail to function as a lightweight audit trail
- not a verbatim copy of the removed live text

## 2026-04-22 — coordination docs moved under `docs/coordination/`

### What changed

- The coordination surfaces were moved out of the top-level `docs/` namespace and into `docs/coordination/`:
  - `live_repo_summary.md`
  - `repo_summary_history.md`
  - `shift_coordination_note_template.md`
- The old tracked singleton `docs/shift_coordination_note.md` was retired in favor of local per-agent notes matching the `shift_coordination_note__*.md` convention.

### Why it mattered

- It separates durable project docs from the narrower coordination layer.
- It makes the per-agent/local status of `shift_coordination_note__*.md` clearer under the current gitignore setup.
- The retired singleton note did not need to remain tracked because its unique substance had already graduated into the live summary and orchestration docs.

## 2026-04-22 early morning — `#26/#32/#34` staging details pulled into the live summary

### What changed

The live summary now carries a more precise staged-execution story for the
analysis lane:

- Notebook 02 still needs A / B / C for the headline Experiment 1 result, but
  the first real Cell B artifact from `#104` is now treated as a meaningful
  intermediate milestone for shared-anchor schema checks.
- Notebook 03 is no longer described as all-or-nothing. Y can start from the
  canonical PE lane once raw artifacts exist; Z / Self-Ask follow-ons are
  smoke-proven but still need promoted canonical configs and raw artifacts before
  they are analysis-ready.
- The draft staging branch proposed replacing the stale
  `exp2_cell_Z_hybrid_mcp_baseline.env` placeholder with a real Verified PE
  baseline config and adding baseline Self-Ask variants for Y and Z. Those
  concrete config edits remain draft-PR work, not current canonical-main truth.

### Why this mattered

The earlier live-summary wording compressed all of `#26` / `#32` into "needs
real captures," which was directionally true but too coarse:

- it hid the fact that some PE-family Experiment 2 evidence can be generated
  once the relevant canonical configs and raw-artifact runs are promoted
- it made Notebook 03 sound more blocked than it really is
- it did not capture the new role of Cell B as a shared Experiment 1 / 2
  milestone once `#104` lands

### Later split

Shortly after this staging pass, the concrete notebook/config changes were
parked onto local worktree branch `codex-fnd/exp-26-32-34-staging` so root
`main` could keep only the shared planning/docs layer. The conceptual staging
story stayed in the live docs; the more iterative execution-surface edits moved
out of root `main`.

## 2026-04-23 — `#111` closed after Insomnia verification

### What changed

`#111` moved from an active "commit the setup fix and rerun proof" item to a
closed infra cleanup.

The final landed fix came through PR `#125`, which corrected the
`huggingface_hub` CLI path in `scripts/setup_insomnia.sh` for the actual
shared Insomnia environment.

### Proof retained from the live summary

- PR `#125` merged as `b480604`.
- The shared Insomnia checkout was fast-forwarded to `main@b480604`.
- `bash -n scripts/setup_insomnia.sh` passed.
- The shared `.venv-insomnia` package metadata matched the newer stack:
  `torch==2.10.0`, `vllm==0.19.0`, `transformers==4.57.6`,
  `huggingface-hub==0.36.2`.
- `huggingface_cli login --help` worked, while `auth login` was rejected on
  that same environment.
- The GitHub Project card was already `Done`, so closing the issue did not
  require board cleanup.

### Why this was moved here

The failed Apr 21 proof attempts and temporary-worktree validation are still
useful audit context, but `#111` should no longer appear as a live blocker.

## 2026-04-24 — live-summary window clarified

The live summary's time window is now documented as configurable by repo
cadence. A repo can choose a window in hours or days, and older material should
not be evicted solely because it crossed that threshold. Move material to this
history file only when there is enough newer active work that the older material
is no longer useful in the live memo.

## 2026-04-24 — shift-note compaction clarified

Shift coordination notes are now explicitly treated as working buffers, not
session transcripts. If a note grows past the target budget, the owning agent
should compact it in place before yielding: keep active deltas, promote settled
current-state facts to the live summary, summarize only otherwise-unrecoverable
context here, and rely on commits, PRs, issues, logs, meeting notes, and run
artifacts for full detail.
