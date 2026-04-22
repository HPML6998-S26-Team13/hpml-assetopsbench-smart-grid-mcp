# Shift Coordination Note Template

*Last updated: 2026-04-22*
*Target length: 250-600 words*
*Purpose: short coordination memo for either concurrent work or handoff. Do not restate the full repo. Current-state context belongs in `live_repo_summary.md`; removed/stale detail belongs in `repo_summary_history.md`.*
*Local-only note: under the current gitignore setup, `shift_coordination_note__*.md` files are expected to remain local/untracked.*

## Position in the MECE coordination hierarchy

This doc is one of five surfaces that coordinate Claude and Codex agents in this repo. Keep them best-effort MECE (mutually exclusive, collectively exhaustive):

1. **`CLAUDE.md` / `AGENTS.md`** — durable repo-wide rules, loaded every session.
2. **`.claude/rules/*.md`** — path-scoped rules that load when matching files are touched.
3. **`docs/coordination/live_repo_summary.md`** — current state of the repo (merged PRs, open loops, validation ledger).
4. **`docs/coordination/shift_coordination_note__*.md`** — *this file type*. Short per-agent-session delta. One file per session, not one shared file.
5. **`docs/coordination/repo_summary_history.md`** — rolling archive of removed historical detail for audit/timeline.

## Filename convention (per-agent-session)

Each agent maintains its **own persistent shift note**; concurrent sessions do not share a single file. Naming:

```
docs/coordination/shift_coordination_note__<agent>_<sessionid8>_<domain>_<short-desc>.md
```

- `<agent>` — `claude` or `codex` (or a specific product line if needed).
- `<sessionid8>` — the stable 8-character suffix used to identify the session in agent/session state (for example the `AUX-xxxxxxxx` suffix or the short session handle shown in the note itself). This is the stable anchor for finding "your" file even if domain or description changes later.
- `<domain>` — a domain code (`fnd`, `obs`, `mle`, `trd`, etc.) or `aux` for non-governed sessions.
- `<short-desc>` — kebab-case description of the session's focus.

The session ID part is the identity anchor. Domain and short description are allowed to evolve. If they change, rename the file but keep the same `<sessionid8>` segment so future turns can still recover it deterministically.

To make recovery human-visible as well as filename-visible, add this field to the session registry / state file when available:

```
coordination_note: docs/coordination/shift_coordination_note__<agent>_<sessionid8>_<domain>_<short-desc>.md
```

Startup recovery rule:

1. Read all sibling shift notes.
2. Look for your own note via `coordination_note:` in your current state file.
3. If that field is missing or stale, recover by globbing on your `<sessionid8>`.
4. If no file exists, create one using the naming convention above.

Cadence (sync'd with team-repo `CLAUDE.md` MECE item 4):

- **Read** all sibling `shift_coordination_note__*.md` files **at the start of each turn at minimum**, and more often during long turns as needed to stay current. There is no canonical master note.
- **Write** your own note **at the end of each turn at minimum** (before yielding control back to the user), and more often during long turns as the material delta evolves. Do not leave your local note stale while relying on others to read it.

## Retirement pattern (what happens to stuff as it ages)

Content flows through the coordination surfaces in a cascade:

```
shift_coordination_note__*.md  →  live_repo_summary.md  →  repo_summary_history.md
```

- **Leaving a shift note.** When a fact, decision, or loop in the shift note has **settled** (no longer an active delta — it is just "how things are now"), move it to `live_repo_summary.md` before removing it from the shift note. Do not delete; the live summary is the next stop.
- **Leaving the live summary.** Covered by team `CLAUDE.md` hard rule 8: append a corresponding note to `docs/coordination/repo_summary_history.md` when removing stale material from the live surface, with enough detail to function as a timeline and lightweight audit trail.
- **Retiring the shift note itself.** When a session wraps and its shift note has been fully absorbed into `docs/coordination/live_repo_summary.md`, the file can be deleted (its content has graduated). If it still carries unique information, leave it in place; retirement is lazy.

## When to use this

Use a shift-coordination note when:

- one agent is handing off to another
- two or more agents are working concurrently and need a compact shared delta
- the next agent needs a fast update without rereading the live summary

It should answer:

- what changed during the shift
- what is now true
- what still needs attention
- what to ignore

If the note starts trying to explain the whole repo, stop and move stable context into
`live_repo_summary.md` instead.

## Recommended structure

### 1. Snapshot

- Agent / session: (e.g. `claude d6519b31 (Opus 4.7)` or `codex 3f1d69b7 foundation-review`)
- Previous note: (filename or SHA of prior shift note this one follows, or `none`)
- Current branch / SHA:
- Scope of this note:
- Biggest thing that changed:
- Biggest thing still open:
- Coordination mode:
  - concurrent work
  - handoff / takeover

### 2. What changed

- Change 1:
- Change 2:
- Change 3:

Keep this to the material delta, not generic project background.

### 3. What is now true

- Verified fact 1:
- Verified fact 2:
- Verified fact 3:

These should be the things another agent can now rely on without rereading the whole repo.

### 4. Open loops

- Loop 1:
  - current blocker:
  - next action:
- Loop 2:
  - current blocker:
  - next action:

### 5. Do next

1. First action:
2. Second action:
3. Optional follow-up:

### 6. Ignore / not a blocker

- Item 1:
- Item 2:

This section is important. It keeps another agent from re-opening already-resolved noise.

## Style rules

- Prefer 8-20 bullets or 5-10 short paragraphs.
- Name exact issues, PRs, run IDs, and SHAs where useful.
- Use absolute dates (`2026-04-22`), not relative ("yesterday", "next Tuesday"). Shift notes are read out-of-order.
- Keep it at roughly one-quarter to one-sixth the size of `live_repo_summary.md`.
- Avoid deep history. If you need older context, point to `repo_summary_history.md`.
- Do not duplicate the full proof ledger unless one proof result changed this shift.
- It should work both as:
  - a "here's what changed since you last looked" note for concurrent work
  - a "here's what you should pick up next" note for handoff

## Mini example

### Snapshot

- Agent / session: `claude abc12345 (Opus 4.7)`
- Previous note: `none`
- Current branch / SHA: `main@abc1234`
- Scope of this note: merged PR `#119`, reran smoke proofs, updated validation log
- Biggest thing that changed: Verified PE is now smoke-clean on canonical history
- Biggest thing still open: `#25` Cell A runner
- Coordination mode: handoff / takeover

### What changed

- PR `#119` merged to `team13/main`
- clean smoke runs recorded in `docs/validation_log.md`
- `#23` / `#24` closed with rollout notes

### What is now true

- PE + Self-Ask and Verified PE are both runnable
- Notebook scaffolds are merged
- remaining blocker is capture generation, not runner plumbing

### Open loops

- `#111`
  - current blocker: one shell-path fix still local
  - next action: commit it, rerun proof, close issue

### Do next

1. Publish the `#111` fix
2. Rerun the canonical proof
3. Then review Aaron's `#25` runner work

### Ignore / not a blocker

- old review comments on pre-merge `#119`
- earlier intermediate smoke failures superseded by clean proofs
