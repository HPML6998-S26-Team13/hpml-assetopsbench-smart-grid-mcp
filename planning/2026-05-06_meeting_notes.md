---
status: active-reference
scope: team-repo planning
owner: Team 13
canonical: true
---

# May 6, 2026 | HPML Final Project - Team 13 Final Sync

Attendees: Alex Xin, Akshat Bhandari, Aaron Fan, Tanisha Rathod

Sources: Notion page `HPML Final Project - Team 13 Final Sync @Yesterday 3:30 PM (EDT)` and its transcript/summary; Google Drive recording metadata for `HPML Final Project - Team 13 Final Sync - 2026/05/06 15:30 EDT - Recording`. The recording includes caption tracks, but they were not extractable through the in-session Drive connector during this pass.

Related prep: `planning/2026-05-06_call_agenda.md` and `planning/2026-05-06_call_prep.md`.

## Overview

This final sync aligned the team around the last submission window: finish the NeurIPS full paper first, then immediately split into Thursday presentation prep and the Friday CourseWorks package. The call did not reopen the whole project plan. It focused on what had landed, what was still in review, and what each person needed to finish for the final deliverables.

The main presentation correction was about framing. The Thursday deck should stay close to the original HPML proposal: profiling, benchmarking, optimization evidence, and measured system behavior. Scenario generation, failure taxonomy, L3 validation, and extra 70B/Cell-D work are useful updates and supporting evidence, but should not become the spine of the ten-minute presentation.

## Current State Discussed

- The scenario floor had moved from a preliminary generated-candidate story to a canonical corpus with 31 hand-authored scenarios and generated-scenario validation in progress.
- The final evidence stack had become broad enough for the paper: benchmark result summaries, mitigation before/after artifacts, manual judge audit material, and reviewer artifact links existed.
- Scenario generation was still valuable but remained validation-gated. Generated scenarios should be promoted only after human review and fixture/tool consistency checks.
- Failure taxonomy had a current programmatic table and still needed a clean manual-audit layer for paper examples.
- L3 DGA validation had produced a useful report-card signal, but its distributional-realism gaps should be framed as methodology/limitations rather than overclaimed as final synthetic-data fidelity.
- Insomnia instability and WatsonX credential expiry forced fallback planning; GCP and other validated evidence paths should be used for final claims only after pullback, judging, and paper integration.

## Decisions

- Freeze NeurIPS-facing claims to evidence that is already pulled back, judged, validated, and integrated into the paper. Late compute can be appendix or future-work material unless it clears the full evidence path before export.
- Keep the Thursday presentation simple: profiling/benchmarking and proposal alignment first; scenario generation and failure analysis as supporting updates.
- Treat the final PR wave as execution work unless a real Critical/High blocker appears. The call should not spend time re-litigating reviewed implementation details.
- Keep the AOB/IBM upstream contribution secondary to NeurIPS and CourseWorks deadlines. It remains valuable, but it should not delay the required submissions.
- Use explicit caveats for any failure-taxonomy or scenario-generation material that is current in the repo but not yet present in the anonymous reviewer artifact.

## Action Items

- [ ] Alex: finish NeurIPS paper export, final checklist, metadata, anonymity/PII scrub, and OpenReview upload by the AOE deadline.
- [ ] Alex: make the Thursday deck reflect the original profiling/benchmarking proposal and keep scenario-generation/failure-taxonomy material as supporting evidence.
- [ ] Alex: after NeurIPS upload, split into class deck, IEEE report back-port, README, deliverables, dashboard/public-link checks, and CourseWorks upload.
- [ ] Akshat: finish the remaining failure-taxonomy manual-audit review loop and generated-scenario promotion/disposition cleanup.
- [ ] Akshat: continue scenario generation toward the larger target, but do not count new generated files as canonical without review/promotion.
- [ ] Aaron: provide/runbook-check infra, profiling, serving, dashboard, and reproducibility facts needed for the deck/report/README.
- [ ] Tanisha: keep data-pipeline, methodology, W&B/dashboard, and reproducibility wording aligned with the final package.
- [ ] Team: do a final deck speak-through before the Thursday 2026-05-07 15:00 ET presentation.

## Post-Meeting Repo Postscript

After this meeting, PRs #183, #189, #190, #191, #193, #195, and #196 landed. The live top-level scenario corpus is now 36: 31 hand-authored plus 5 promoted generated scenarios from PR #195. Issues #42 and #53 have canonical closeouts, and #84 is closed from the L3 v1 report-card work.

Issue #35 should remain open until the PR #197 / #194 manual-audit lane lands cleanly or is explicitly caveated/deferred. If it lands, the closeout should say that `failure_taxonomy_current.csv` plus the #197 audit supersede the older PR #151 / PR #189 35-row table, and that any stale derived taxonomy artifacts have been refreshed or caveated.

Issue #67 remains open for the final-report / CourseWorks reproducibility package. It is not a hard blocker for the NeurIPS paper cut or the Thursday deck.

Issue #55 is closed on GitHub, but current main has 36 canonical top-level scenarios, not the 50+ target in the issue. Treat it as stale-scoped until a post-deadline corpus-expansion decision is made.
