#!/usr/bin/env bash
# PR review watcher engine for hpml-assetopsbench-smart-grid-mcp.
#
# Filters open PRs to those that need a fresh cross-agent review and emits
# them as JSON lines for a Claude (Monitor) or Codex (poll loop) reviewer
# session. Reuses the review-agent / review-request file convention:
#
#   review/claude-prompts/<YYYYMMDD_HHMMSS>_ADHOC_PR<N>_<slug>-v1.md
#   review/codex-prompts/<YYYYMMDD_HHMMSS>_ADHOC_PR<N>_<slug>-v1.md
#
# Subcommands:
#   find-candidates                 List qualifying PRs as JSON, no claim.
#   claim <pr> <reviewer>           Write claim packet for reviewer side.
#                                   reviewer = claude | codex.
#   is-claimed <pr>                 Exit 0 if claimed in any review/*-prompts.
#   author-hint <pr> [branch]       Print claude | codex | unknown.
#   loop [--interval SECONDS]       Poll forever, emit one JSON line per
#                                   newly-claimed candidate. Default 600s.
#
# Filter logic for "needs review":
#   * state == OPEN
#   * isDraft == false
#   * reviewDecision != APPROVED
#   * no comment or review body contains LGTM (case-insensitive)
#   * unclaimed: no file matching *PR<N>* under review/claude-prompts/
#     or review/codex-prompts/ (recursive, case-insensitive)
#
# Author hint reads docs/coordination/shift_coordination_note__*.md and
# picks the side whose note mentions the PR number or branch name. Both
# sides hit -> unknown. Neither -> unknown.

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

# Target the team repo, not Alex's personal fork. Override with WATCHER_REPO.
WATCHER_REPO="${WATCHER_REPO:-HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp}"
GH=(gh --repo "$WATCHER_REPO")

mkdir -p "$INBOX_CLAUDE" "$INBOX_CODEX"

usage() {
  sed -n '2,40p' "$0" | sed 's/^# \{0,1\}//'
  exit 1
}

need_gh() {
  command -v gh >/dev/null 2>&1 || { echo "gh CLI required" >&2; exit 2; }
}

need_jq() {
  command -v jq >/dev/null 2>&1 || { echo "jq required" >&2; exit 2; }
}

is_claimed() {
  local pr="$1"
  local hits
  hits=$( { find "$INBOX_CLAUDE" "$INBOX_CODEX" -type f \( -iname "*PR${pr}_*" -o -iname "*PR_${pr}_*" -o -iname "*pr_${pr}_*" -o -iname "*pr${pr}_*" \) 2>/dev/null || true; } | wc -l | tr -d ' ')
  [[ "$hits" -gt 0 ]]
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
  local pat="(PR ?#?${pr}\b|#${pr}\b)"
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

# Body LGTM scan: pull comments and review bodies in one shot.
has_lgtm() {
  local pr="$1"
  local body
  body=$("${GH[@]}" pr view "$pr" --json comments,reviews --jq \
    '[.comments[].body, .reviews[].body] | map(select(. != null)) | join("\n")' 2>/dev/null || true)
  echo "$body" | grep -iq '\bLGTM\b'
}

# Returns 0 (true) if the most recent substantive review on this PR already
# requested changes AND no commit has landed since that review, i.e. the
# review covers the current head. A "substantive" review is one whose body
# is at least 200 characters; shorter reviews are treated as discussion
# comments rather than full review responses.
already_reviewed_at_head() {
  local pr="$1"
  local data
  data=$("${GH[@]}" pr view "$pr" --json reviews,commits 2>/dev/null || true)
  [[ -z "$data" ]] && return 1
  local last_review
  last_review=$(echo "$data" | jq -c '
    [.reviews[]
      | select(.state == "CHANGES_REQUESTED" or .state == "APPROVED")
      | select((.body // "") | length >= 200)]
    | sort_by(.submittedAt) | last // empty
  ')
  [[ -z "$last_review" || "$last_review" == "null" ]] && return 1
  local last_state last_at head_at
  last_state=$(echo "$last_review" | jq -r .state)
  last_at=$(echo "$last_review" | jq -r .submittedAt)
  head_at=$(echo "$data" | jq -r '.commits[-1].committedDate')
  [[ "$last_state" != "CHANGES_REQUESTED" ]] && return 1
  # ISO 8601 timestamps sort lexically.
  [[ "$last_at" > "$head_at" || "$last_at" == "$head_at" ]]
}

claim_packet_path() {
  local pr="$1"
  local slug="$2"
  local reviewer="$3"
  local ts
  ts=$(date +%Y%m%d_%H%M%S)
  local inbox
  case "$reviewer" in
    claude) inbox="$INBOX_CLAUDE" ;;
    codex)  inbox="$INBOX_CODEX"  ;;
    *) echo "unknown reviewer: $reviewer" >&2; exit 2 ;;
  esac
  echo "${inbox}/${ts}_ADHOC_PR${pr}_${slug}-v1.md"
}

write_claim() {
  local pr="$1"
  local reviewer="$2"
  local title branch url author_hint slug pkt
  title=$("${GH[@]}" pr view "$pr" --json title --jq .title)
  branch=$("${GH[@]}" pr view "$pr" --json headRefName --jq .headRefName)
  url=$("${GH[@]}" pr view "$pr" --json url --jq .url)
  author_hint=$(author_hint "$pr" "$branch")
  slug=$(slugify "$title")
  pkt=$(claim_packet_path "$pr" "$slug" "$reviewer")
  cat > "$pkt" <<EOF
# review request

- Mode: pr-review
- Requester: pr_review_watcher.sh
- Reviewer inbox: $(dirname "$pkt")
- Repo: ${SHARED_ROOT}
- Branch: ${branch}
- Target: ${url}
- Version: v1
- PR: #${pr}
- Apparent author: ${author_hint}
- Prior response: none
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
writing the signal file.
EOF
  echo "$pkt"
}

find_candidates() {
  local out_json="${1:-}"
  local prs
  prs=$("${GH[@]}" pr list --state open --json number,title,isDraft,reviewDecision,headRefName,url --limit 100)
  echo "$prs" | jq -c '.[]' | while read -r pr_json; do
    local n is_draft decision branch
    n=$(echo "$pr_json" | jq -r .number)
    is_draft=$(echo "$pr_json" | jq -r .isDraft)
    decision=$(echo "$pr_json" | jq -r .reviewDecision)
    branch=$(echo "$pr_json" | jq -r .headRefName)
    [[ "$is_draft" == "true" ]] && continue
    [[ "$decision" == "APPROVED" ]] && continue
    is_claimed "$n" && continue
    has_lgtm "$n" && continue
    already_reviewed_at_head "$n" && continue
    local hint
    hint=$(author_hint "$n" "$branch")
    echo "$pr_json" | jq -c --arg hint "$hint" '. + {author_hint: $hint}'
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
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --interval) interval="$2"; shift 2 ;;
        *) usage ;;
      esac
    done
    while true; do
      while read -r line; do
        [[ -z "$line" ]] && continue
        n=$(echo "$line" | jq -r .number)
        hint=$(echo "$line" | jq -r .author_hint)
        # Reviewer side: if author hint = codex (different agent), this Claude
        # session reviews directly -> claim in claude-prompts. If author hint
        # is claude or unknown, we still claim in claude-prompts because the
        # current session is Claude, and the review prompt itself enforces
        # heightened scrutiny.
        pkt=$(write_claim "$n" claude)
        echo "$line" | jq -c --arg packet "$pkt" '. + {claim_packet: $packet}'
      done < <(find_candidates)
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
