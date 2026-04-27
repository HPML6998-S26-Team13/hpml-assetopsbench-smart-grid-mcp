# Backlog

- [ ] 2026-04-20 - Explore `claude_agent_sdk`: determine why AssetOpsBench imports it, whether it is installable in our environments, and whether any part of that dependency should be incorporated here to better mirror AssetOpsBench behavior even though this project does not directly use Claude-agent orchestration today. Source: Codex / user follow-up.
- [x] 2026-04-27 - Set up a GitHub PR-review watcher for this repo: monitor opened/updated PRs, trigger the appropriate cross-agent code review flow for each PR, avoid duplicate/stale review comments, and respect the repo rule that agents review work authored by a different source. Source: Codex / user follow-up. Resolved: `scripts/pr_review_watcher.sh` + `docs/pr_review_watcher.md` on branch `fnd/pr-review-watcher`.
