#!/usr/bin/env bash
# PR review watcher engine for hpml-assetopsbench-smart-grid-mcp.
#
# Filters open PRs to those that need a fresh cross-agent review and emits
# them as JSON lines for an agentic-AI runner that acts as both watcher and
# reviewer. Reuses the cross-agent review filename convention for claim
# packets:
#
#   review/claude-prompts/<YYYYMMDD_HHMMSS>_ADHOC_PR<N>_<slug>-vK.md
#   review/codex-prompts/<YYYYMMDD_HHMMSS>_ADHOC_PR<N>_<slug>-vK.md
#
# Subcommands:
#   find-candidates                     List qualifying PRs as JSON, no claim.
#   claim <pr> <reviewer>               Write claim packet for reviewer side.
#                                       reviewer = claude | codex.
#   is-claimed <pr>                     Exit 0 if claimed in any inbox.
#   author-hint <pr> [branch]           Print claude | codex | unknown.
#   loop --reviewer <claude|codex>      Poll forever, claim-and-emit JSON
#         [--interval SECONDS]          per new candidate. Default 600s.
#
# Filter logic for "needs review" (all six must hold):
#   1. state == OPEN
#   2. isDraft == false
#   3. reviewDecision != APPROVED
#   4. no review body of state COMMENTED|APPROVED contains a word-bounded
#      LGTM (case-insensitive). PR-comment text is ignored to avoid false
#      positives from quoted or conditional mentions.
#   5. no prior claim packet covers the current head: a top-level packet
#      under review/claude-prompts/ or review/codex-prompts/ matching
#      *_PR<N>_* (case-sensitive on the canonical slot, with _signal/ and
#      other underscore-prefixed subdirs excluded), whose mtime is later
#      than the head commit's committedDate.
#   6. no formal GitHub review covers the current head: most recent
#      CHANGES_REQUESTED review with non-empty body, submittedAt strictly
#      after head_at.
#
# Re-emit semantics: criteria 5 and 6 are independent skip predicates.
# A PR is emitted (claimed) whenever both predicates say "not covered."
# If an author pushes new commits past a prior packet or review, the
# next iteration emits a vN+1 packet for the new diff.
#
# Author hint reads docs/coordination/shift_coordination_note__*.md and
# picks the side whose note mentions PR #<N>, pull request <N>, pull/<N>,
# or the head branch name. Both sides hit -> unknown. Neither -> unknown.

set -euo pipefail

REPO_ROOT="${REPO_ROOT:-$(git -C "$(dirname "$0")" rev-parse --show-toplevel 2>/dev/null || pwd)}"
# When invoked from a worktree, write claim packets and read shift notes
# from the shared common dir so all sessions see the same state.
COMMON_DIR="$(git -C "$REPO_ROOT" rev-parse --git-common-dir 2>/dev/null || true)"
if [[ -n "$COMMON_DIR" ]]; then
  SHARED_ROOT="$(cd "$(dirname "$COMMON_DIR")" && pwd)"
else
  SHARED_ROOT="$REPO_ROOT"
fi

INBOX_CLAUDE="${SHARED_ROOT}/review/claude-prompts"
INBOX_CODEX="${SHARED_ROOT}/review/codex-prompts"
COORD_DIR="${SHARED_ROOT}/docs/coordination"
LOCK_DIR="${SHARED_ROOT}/review"

WATCHER_REPO="${WATCHER_REPO:-HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp}"
GH=(gh --repo "$WATCHER_REPO")

mkdir -p "$INBOX_CLAUDE" "$INBOX_CODEX" "$LOCK_DIR"

usage() {
  sed -n '2,44p' "$0" | sed 's/^# \{0,1\}//'
  exit 1
}

need_gh() {
  command -v gh >/dev/null 2>&1 || { echo "gh CLI required" >&2; exit 2; }
}

need_jq() {
  command -v jq >/dev/null 2>&1 || { echo "jq required" >&2; exit 2; }
}

# Match prior top-level claim packets for this PR, including renamed
# _REVIEWED.md. Case-sensitive on the canonical `_PR<N>_` slot so
# slugified content (slugify lowercases everything) cannot collide
# with the PR-number slot. Excludes any underscore-prefixed subdirectory
# (_signal/, _archive/, _templates/) so claim_covers_head's
# sort-r|head-1 picks the actual claim packet rather than a signal
# file. Without the path guard, LC_ALL=C locales (cron, CI, headless
# containers) sort _signal/ paths first, so the signal mtime would
# stand in for the packet mtime and silently skip PRs with stale
# claims.
existing_claims() {
  local pr="$1"
  { find "$INBOX_CLAUDE" "$INBOX_CODEX" -type f \
      -name "*_PR${pr}_*" \
      -not -path "*/_*/*" 2>/dev/null \
      || true; }
}

is_claimed() {
  local pr="$1"
  local hits
  hits=$(existing_claims "$pr" | wc -l | tr -d ' ')
  [[ "$hits" -gt 0 ]]
}

# Highest existing version (-vN) across all packets for this PR. Returns 0
# if no prior packet exists.
max_version_for() {
  local pr="$1"
  existing_claims "$pr" \
    | sed -E 's/.*-v([0-9]+)(_REVIEWED)?\.md$/\1/' \
    | grep -E '^[0-9]+$' \
    | sort -n \
    | tail -1
}

slugify() {
  echo "$1" | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[^a-z0-9]+/_/g; s/^_+//; s/_+$//' \
    | cut -c1-48
}

author_hint() {
  local pr="$1"
  local branch="${2:-}"
  if [[ ! -d "$COORD_DIR" ]]; then
    echo unknown
    return
  fi
  # Tightened: match PR-context phrasing only, not bare #NNN that may refer
  # to issues or Slurm job IDs. Branch name remains a fallback.
  local pat="(PR ?#?${pr}\b|pull[-_ ]?request[s]? ?#?${pr}\b|pull/${pr}\b)"
  if [[ -n "$branch" ]]; then
    pat="${pat}|$(printf '%s' "$branch" | sed 's/[][\.*^$(){}+?|/\\]/\\&/g')"
  fi
  local claude_hits codex_hits
  claude_hits=$( { grep -liE "$pat" "$COORD_DIR"/shift_coordination_note__claude_*.md 2>/dev/null || true; } | wc -l | tr -d ' ')
  codex_hits=$( { grep -liE "$pat" "$COORD_DIR"/shift_coordination_note__codex_*.md 2>/dev/null || true; } | wc -l | tr -d ' ')
  if [[ "$claude_hits" -gt 0 && "$codex_hits" -eq 0 ]]; then
    echo claude
  elif [[ "$codex_hits" -gt 0 && "$claude_hits" -eq 0 ]]; then
    echo codex
  else
    echo unknown
  fi
}

# ---------------------------------------------------------------------------
# JSON-driven helpers operate on a per-PR JSON blob already fetched once.
# This avoids per-PR re-invocations of gh and keeps a single failure mode
# per PR per iteration (M4, M6).
# ---------------------------------------------------------------------------

has_lgtm_in_data() {
  local data="$1"
  # Scope to review bodies of state COMMENTED or APPROVED; ignore PR
  # comments entirely. A reviewer who genuinely intends "ship it" submits
  # the review with state APPROVED (already filtered by criterion 3) or
  # COMMENTED with the LGTM marker. Quoted or conditional mentions in
  # general comments are not enough to skip.
  echo "$data" | jq -e '
    [.reviews[]?
      | select(.state == "COMMENTED" or .state == "APPROVED")
      | (.body // "")]
    | map(test("\\bLGTM\\b"; "i"))
    | any
  ' >/dev/null 2>&1
}

# Convert RFC 3339 UTC timestamp ("2026-04-27T08:56:32Z") to epoch seconds.
# macOS uses BSD date, Linux uses GNU date; try both forms.
rfc3339_to_epoch() {
  local s="$1"
  TZ=UTC date -j -f "%Y-%m-%dT%H:%M:%SZ" "$s" +%s 2>/dev/null \
    || date -u -d "$s" +%s 2>/dev/null \
    || return 1
}

# File mtime in epoch seconds. macOS BSD vs Linux GNU.
mtime_epoch() {
  local f="$1"
  stat -f "%m" "$f" 2>/dev/null || stat --format=%Y "$f" 2>/dev/null
}

# Path 1: a GitHub formal review record covers the current head. Most
# recent CHANGES_REQUESTED review with non-empty body, submittedAt strictly
# after head_at. Drops the prior 200-char threshold (M3) and tie semantics
# (M1).
formal_review_covers_head() {
  local data="$1"
  local head_at
  head_at=$(echo "$data" | jq -r '(.commits // []) | last | .commit.committedDate // .committedDate // empty')
  [[ -z "$head_at" || "$head_at" == "null" ]] && return 1
  local last_review
  last_review=$(echo "$data" | jq -c '
    [.reviews[]?
      | select(.state == "CHANGES_REQUESTED" or .state == "APPROVED")
      | select((.body // "") != "")]
    | sort_by(.submittedAt) | last // empty
  ')
  [[ -z "$last_review" || "$last_review" == "null" ]] && return 1
  local last_state last_at
  last_state=$(echo "$last_review" | jq -r .state)
  last_at=$(echo "$last_review" | jq -r .submittedAt)
  [[ "$last_state" != "CHANGES_REQUESTED" ]] && return 1
  [[ "$last_at" > "$head_at" ]]
}

# Path 2: a prior claim packet covers the current head. Cross-agent
# reviewers that fall back to `gh pr comment` (because GitHub blocks
# self-authored `gh pr review` on shared identities) leave no formal
# review record, but they leave a packet (renamed to _REVIEWED.md if a
# response was written). Compare the newest packet's mtime to head_at:
# packet newer than head means the request was filed for the current
# diff, so the watcher should not re-claim until commits move past it.
claim_covers_head() {
  local pr="$1"
  local data="$2"
  local newest_claim mtime head_at head_epoch
  newest_claim=$(existing_claims "$pr" | sort -r | head -1)
  [[ -z "$newest_claim" ]] && return 1
  mtime=$(mtime_epoch "$newest_claim") || return 1
  head_at=$(echo "$data" | jq -r '(.commits // []) | last | .commit.committedDate // .committedDate // empty')
  [[ -z "$head_at" || "$head_at" == "null" ]] && return 1
  head_epoch=$(rfc3339_to_epoch "$head_at") || return 1
  [[ "$mtime" -gt "$head_epoch" ]]
}

claim_packet_path() {
  local pr="$1"
  local slug="$2"
  local reviewer="$3"
  local version="${4:-1}"
  local ts
  ts=$(date +%Y%m%d_%H%M%S)
  local inbox
  case "$reviewer" in
    claude) inbox="$INBOX_CLAUDE" ;;
    codex)  inbox="$INBOX_CODEX"  ;;
    *) echo "unknown reviewer: $reviewer" >&2; exit 2 ;;
  esac
  echo "${inbox}/${ts}_ADHOC_PR${pr}_${slug}-v${version}.md"
}

# write_claim_from_data <pr> <reviewer> <data-json>
# Reuses the per-PR JSON fetched by find_candidates so no extra gh calls
# happen inside the inner loop (M4).
write_claim_from_data() {
  local pr="$1"
  local reviewer="$2"
  local data="$3"
  local title branch url hint slug pkt next_version extra
  title=$(echo "$data" | jq -r .title)
  branch=$(echo "$data" | jq -r .headRefName)
  url=$(echo "$data" | jq -r .url)
  # Reuse the hint find_candidates already computed; fall back to a fresh
  # compute if the caller passed JSON without it (e.g., legacy write_claim).
  hint=$(echo "$data" | jq -r '.author_hint // empty')
  if [[ -z "$hint" ]]; then
    hint=$(author_hint "$pr" "$branch")
  fi
  slug=$(slugify "$title")
  next_version=$(( $(max_version_for "$pr" | grep -E '^[0-9]+$' || echo 0) + 1 ))
  pkt=$(claim_packet_path "$pr" "$slug" "$reviewer" "$next_version")

  extra=""
  if [[ "$hint" == "claude" || "$hint" == "unknown" ]]; then
    extra=$'\n\n**Heightened scrutiny -- apparent same-runner or unknown authorship.**\nAssume the implementation has subtle bugs and edge cases that a same-source review would normalize. Read the diff line-by-line, question every assumption, prefer over-reporting to under-reporting, and explicitly verify that preconditions hold rather than trusting prose claims. When this watcher session is itself the apparent author, escalate to a different reviewer for genuine independence; same-session self-review is a fallback only.'
  fi

  cat > "$pkt" <<EOF
# review request

- Mode: pr-review
- Requester: pr_review_watcher.sh
- Reviewer inbox: $(dirname "$pkt")
- Repo: ${SHARED_ROOT}
- Branch: ${branch}
- Target: ${url}
- Version: v${next_version}
- PR: #${pr}
- Apparent author: ${hint}
- Prior response: $( [[ "$next_version" -gt 1 ]] && echo "see prior _REVIEWED packets in inbox" || echo "none" )
- Verification: none
- Constraints: cross-agent independence required
- Deferred: none

## Request

Please review and provide all feedback, including nits, style, and everything.
Be comprehensive and thorough, so we can reduce the number of iterations
before the PR merges.

Be sure to check error masking, idempotence, preconditions, verification
reproducibility. Look at upstream and downstream references, data
interfaces, and artifact handling.

We don't need to worry so much about documenting how to revert. Everything
is version-controlled via Git. The audience is a highly skilled agentic AI;
limit coding-practice notes to especially niche, non-obvious tips.

Mainly we want to look closely at everything with each iteration, rather
than only what changed. We want to finalize the review in as few iterations
as possible.

Return findings sorted by Critical, High, Medium, Low. For each finding
include file, line when applicable, issue, and suggested fix. Post the
review to GitHub via \`gh pr review ${pr}\` with \`--body\` populated, before
writing the signal file.${extra}
EOF
  echo "$pkt"
}

# Legacy single-arg claim subcommand: makes its own gh call. Used for
# manual one-offs only.
write_claim() {
  local pr="$1"
  local reviewer="$2"
  local data
  data=$("${GH[@]}" pr view "$pr" --json title,headRefName,url,reviews,commits 2>/dev/null) \
    || { echo "gh pr view $pr failed" >&2; return 1; }
  write_claim_from_data "$pr" "$reviewer" "$data"
}

# Hybrid fetch: one cheap pr list for metadata, then a per-PR pr view for
# the heavy review/comment/commit fields. Bundling everything into pr list
# blows the GitHub GraphQL 500k-node connection limit on busy repos. Per-PR
# view calls are guarded so a transient gh failure abandons that PR for
# this iteration but does not kill the loop (H2, M6).
find_candidates() {
  local prs
  prs=$("${GH[@]}" pr list --state open \
        --json number,title,isDraft,reviewDecision,headRefName,url \
        --limit 100 2>/dev/null) \
    || { echo "gh pr list failed" >&2; return 1; }
  echo "$prs" | jq -c '.[]' | while read -r meta; do
    local n is_draft decision branch
    n=$(echo "$meta" | jq -r .number)
    is_draft=$(echo "$meta" | jq -r .isDraft)
    decision=$(echo "$meta" | jq -r .reviewDecision)
    branch=$(echo "$meta" | jq -r .headRefName)
    [[ "$is_draft" == "true" ]] && continue
    [[ "$decision" == "APPROVED" ]] && continue
    local detail
    detail=$("${GH[@]}" pr view "$n" --json reviews,comments,commits 2>/dev/null) \
      || { echo "gh pr view $n failed; skipping this iteration" >&2; continue; }
    local data
    data=$(jq -nc --argjson m "$meta" --argjson d "$detail" '$m + $d')
    has_lgtm_in_data "$data" && continue
    # Criterion 6: a formal GitHub review covers the current head.
    formal_review_covers_head "$data" && continue
    # Criterion 5: a prior claim packet exists AND its mtime is after the
    # head commit time. Either the reviewer is mid-process (raw .md still
    # waiting) or already responded (_REVIEWED.md). Either way the queue
    # is current and the watcher should not re-claim until new commits
    # land past the packet mtime.
    if is_claimed "$n" && claim_covers_head "$n" "$data"; then
      continue
    fi
    local hint
    hint=$(author_hint "$n" "$branch")
    echo "$data" | jq -c --arg hint "$hint" '. + {author_hint: $hint}'
  done
}

cmd="${1:-}"
shift || true

case "$cmd" in
  find-candidates)
    need_gh; need_jq
    find_candidates
    ;;
  claim)
    need_gh; need_jq
    [[ $# -ge 2 ]] || usage
    write_claim "$1" "$2"
    ;;
  is-claimed)
    [[ $# -ge 1 ]] || usage
    if is_claimed "$1"; then exit 0; else exit 1; fi
    ;;
  author-hint)
    [[ $# -ge 1 ]] || usage
    author_hint "$1" "${2:-}"
    ;;
  loop)
    need_gh; need_jq
    interval=600
    reviewer=""
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --interval) interval="$2"; shift 2 ;;
        --reviewer) reviewer="$2"; shift 2 ;;
        *) usage ;;
      esac
    done
    case "$reviewer" in
      claude|codex) ;;
      *) echo "loop requires --reviewer claude|codex" >&2; exit 2 ;;
    esac
    case "$interval" in
      ''|*[!0-9]*) echo "--interval must be a positive integer (seconds)" >&2; exit 2 ;;
    esac
    [[ "$interval" -gt 0 ]] || { echo "--interval must be > 0" >&2; exit 2; }
    # Single-watcher invariant: hold a non-blocking lockfile on the shared
    # review/ directory keyed by reviewer side. Two concurrent watcher
    # processes for the same side would otherwise race the
    # is_claimed/write_claim window and produce duplicate packets (M5).
    command -v flock >/dev/null 2>&1 \
      || { echo "flock not found; install via 'brew install flock' (macOS) or 'apt-get install util-linux' (Linux)" >&2; exit 2; }
    LOCK_FILE="${LOCK_DIR}/.watcher.${reviewer}.lock"
    exec 9>"$LOCK_FILE"
    if ! flock -n 9; then
      echo "another watcher already holds $LOCK_FILE; refusing to start" >&2
      exit 3
    fi
    trap 'kill 0 2>/dev/null; exit 130' INT TERM
    while true; do
      if data=$(find_candidates); then
        while read -r line; do
          [[ -z "$line" ]] && continue
          n=$(echo "$line" | jq -r .number)
          # Re-fetch the per-PR slice to pass into write_claim_from_data;
          # the candidate JSON is already complete, so no extra gh call.
          pkt=$(write_claim_from_data "$n" "$reviewer" "$line") \
            || { echo "claim write failed for PR $n; continuing" >&2; continue; }
          echo "$line" | jq -c --arg packet "$pkt" '. + {claim_packet: $packet}'
        done <<< "$data"
      fi
      sleep "$interval"
    done
    ;;
  ""|-h|--help)
    usage
    ;;
  *)
    echo "unknown subcommand: $cmd" >&2
    usage
    ;;
esac
