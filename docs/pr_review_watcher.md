# PR Review Watcher

Repo-level helper that monitors open pull requests in the team repo and
identifies the ones that need a fresh review. The watcher can be driven by
any agentic-AI runner; the runner's session acts as both the watcher and
the reviewer (no separate dispatch).

The script is `scripts/pr_review_watcher.sh`. It targets
`HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp` by default
(override with `WATCHER_REPO=<owner/repo>`).

## "Needs review" criteria

A PR qualifies when **all** of the following hold:

1. State is `OPEN` (unmerged).
2. `isDraft == false`.
3. `reviewDecision != APPROVED`.
4. No comment or review body contains `LGTM` (case-insensitive, word boundary).
5. **Unclaimed** — no prior request packet for this PR exists in the
   reviewer-inbox directories the runner uses for cross-agent review (those
   directories are gitignored runtime state; see [Inbox conventions](#inbox-conventions)
   below).
6. **No substantive review already on the current head.** The most recent
   `CHANGES_REQUESTED` or `APPROVED` review whose body is at least 200
   characters (i.e. a real review response, not a one-liner discussion
   comment) must pre-date the most recent commit on the PR branch. If the
   review is newer than the head commit, a previous reviewer (often a
   different Claude session) has already covered this diff and the
   author needs to push new commits before another review is useful.

The fifth check is the duplicate-suppression mechanism within a single
runner. The sixth check covers the cross-runner case where another
session has already reviewed the current diff.

## Subcommands

| Subcommand                  | Purpose                                            |
| --------------------------- | -------------------------------------------------- |
| `find-candidates`           | List qualifying PRs as JSON lines (no claim).      |
| `claim <pr> <side>`         | Write request packet for the given reviewer side.  |
| `is-claimed <pr>`           | Exit 0 if a packet already exists for this PR.     |
| `author-hint <pr> [branch]` | Print apparent author kind: a, b, or `unknown`.    |
| `loop [--interval N]`       | Poll forever, claim-and-emit one JSON line per new candidate. Default interval 600s. |

Each emitted JSON line includes `number`, `title`, `headRefName`, `url`,
`author_hint`, and (in `loop` mode) `claim_packet` path.

## Author hint and reviewer style

The watcher infers the apparent author by scanning shift coordination notes
under `docs/coordination/shift_coordination_note__<runner>_*.md`. A note
mentioning the PR number or branch name signals authorship from that runner
side. Both sides matched (or neither) → `unknown`.

How that shapes the review:

- **Different runner from the reviewer** — standard cross-agent review.
- **Same runner** or **`unknown`** — heightened-scrutiny independent pass.
  Assume the implementation has subtle bugs and edge cases that a
  same-source review would normalize. Read the diff line-by-line, question
  every assumption, prefer over-reporting to under-reporting, and
  explicitly verify that preconditions hold rather than trusting prose
  claims.

The request packet embeds this guidance in its `## Request` section when
`Apparent author` is `claude` or `unknown`.

When the watcher session **is itself the apparent author**, the runner
should escalate to a different reviewer (e.g., a different model via MCP)
for genuine independence. Same-session self-review is a fallback only.

## Reproducible invocation

- **From the repo root** under any agentic runner:
  ```bash
  bash scripts/pr_review_watcher.sh loop --interval 600
  ```
- The runner subscribes to the loop's stdout (one JSON line per new
  candidate) and treats each line as a wake-up cue to read the request
  packet, run the review, and post findings via
  `gh pr review <N> --request-changes --body "..."` or `--comment`.
- Stop the watcher by killing the loop process.

The Claude side of this project ordinarily drives the loop with the
in-session `Monitor` tool (persistent), and the Codex side drives the loop
under its own polling automation; both consume the same stdout schema.

## Inbox conventions

Request packets and signals follow the existing cross-agent review
conventions used elsewhere in this repo (gitignored runtime directories,
`<YYYYMMDD_HHMMSS>_ADHOC_PR<N>_<slug>-v1.md` filename pattern, `_signal/`
subdirectory for response-ready notifications). The runner that drives the
watcher is responsible for the per-iteration reviewer protocol (rename to
`_REVIEWED.md`, write the signal file). The script itself only handles
discovery and claiming.

## Verification before posting a review

Before posting any review:

- Confirm the PR's `headRefName` matches what the script reported.
- Run `gh pr diff <N>` and read the changed files end-to-end (not just the
  hunks).
- Spot-check the apparent-author classification against the matched shift
  note.
- Re-confirm no third party has approved or LGTM'd in the meantime
  (`gh pr view <N> --json reviews,comments`).

## Stopping and restarting

Killing the loop process is enough; the script is stateless beyond the
request packets it has already written. Restart with the same command at
any time. Already-claimed PRs stay skipped until their packets are removed
or the PR closes.

## Cleanup after a PR closes

When a PR merges or closes, leave the historical request packets in place;
they are part of the cross-agent review audit trail. The next iteration's
`is-claimed` check still skips the closed PR because it is no longer in
`gh pr list --state open`.
