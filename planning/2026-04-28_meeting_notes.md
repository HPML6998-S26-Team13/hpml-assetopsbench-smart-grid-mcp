# Apr 28, 2026 | HPML Final Project - Team 13 Sync

Attendees: [Alex Xin](mailto:wax1@columbia.edu), [Akshat Bhandari](mailto:ab6174@columbia.edu), [Tanisha Rathod](mailto:tr2828@columbia.edu), [Aaron Fan](mailto:af3623@columbia.edu)

Sources: Notion page `HPML Final Project - Team 13 Sync @Today 2:45 PM (EDT)` and its transcript. Google Drive recording metadata for `HPML Final Project - Team 13 Sync - 2026/04/28 14:47 EDT - Recording` was visible, but the caption tracks were not retrievable through the in-session Drive connector or direct download path during this pass.

## Overview

This sync was the final evidence-readiness check before the 3:30 PM Dhaval / Shuxin call. The team had a substantially stronger project story than the Apr 21 meeting: Experiment 1 Cells A/B were captured, Experiment 2 had first canonical PE-family captures plus Maverick judge scores, and the Insomnia/runbook surface had been hardened. The unresolved question was no longer "can the benchmark path run?" but "which evidence is mature enough to claim by the May 4 class deadline and the May 4 / May 6 NeurIPS deadlines?"

The team also aligned on how to present open work honestly: Cell C optimization remains its own capture lane, Problem Statement B is promising but not yet a final empirical result, and the Dhaval call should ask about evaluation framing, judge-model expectations, failure-taxonomy citation, and whether the Verified PE / Self-Ask story belongs in the final narrative.

## Status Postscript (2026-04-30)

This note preserves the Apr 28 team-sync snapshot. Since then, PRs #134, #145,
#147, #148, and #149 have merged, and the repo now has Cell C, Cell D, and
Z + Self-Ask + D proof captures plus Maverick judge rows on main. Treat this
file as historical meeting context; use the GitHub Project board for current task status.

## Summary

- **Repo / board status discussed during the call:**
  - Experiment 1 Cells A/B were no longer blocked on the AaT runner path; full Cell C evidence remains split into the optimized implementation and capture lanes.
  - Experiment 2 had first canonical evidence for the PE-family cells at the same small-N depth as the Exp 1 canonical A/B captures.
  - The Insomnia runbook and profiling docs had been refreshed after the Apr 27 / Apr 28 capture hardening work.
  - The team still needed to convert the recent capture wave into notebooks, figures, failure taxonomy, and report/deck language.

- **Experiment 1 discussion:**
  - Current evidence supports Direct / AaT Cell A and MCP-baseline Cell B claims.
  - Cell C is not part of the closed #25 story; it remains the optimized-MCP follow-on through the Cell C implementation/capture path.
  - The class-facing story should report before/after overhead only where artifacts are real, and keep Cell C conditional until the batched/reuse implementation and capture are complete.

- **Experiment 2 discussion:**
  - The first canonical matrix covers Cell B plus Y, Y + Self-Ask, Z, and Z + Self-Ask on two multi-domain scenarios with three trials each.
  - Completion-pass and judge-pass tell different stories: B is fast at closing the loop, while Z + Self-Ask is the quality leader in the Maverick judge view.
  - Self-Ask improved every cell that used it in the first capture set, but the team should keep the small-N caveat visible until the final rerun policy is settled.

- **Problem Statement B discussion:**
  - Tanisha's Knowledge Plugin/support artifacts and Aaron's scenario-generation pipeline make the extension real enough to describe methodologically.
  - The empirical PS B claim still depends on generated-scenario validation and a defensible comparison against the handcrafted scenario set.
  - The team discussed a likely longer-term target of scaling the Smart Grid scenario corpus beyond the current handcrafted set, with generated scenarios validated rather than accepted automatically.

- **Dhaval / Shuxin prep questions:**
  - Which evaluation harness should the project align with: the team-local judge path or the newer AssetOpsBench evaluation-module work?
  - Is the Maverick judge model acceptable for the paper/class story, or should the final writeup align with the AOB default judge model where possible?
  - Is the Berkeley multi-agent failure taxonomy the right citation/framing for observed failures?
  - Should Verified PE and Self-Ask appear as central results, or only as mitigation/ablation follow-ons to the AaT vs Plan-Execute comparison?
  - What should be prioritized for an upstream AssetOpsBench contribution: code, scenarios, validation, LLM-as-judge, or all of the above?

- **Team bandwidth / deadline discussion:**
  - The team is inside the final delivery window. Class paper/project/presentation planning should treat May 4, 2026 as the hard package deadline.
  - NeurIPS abstract is due May 4, 2026; full paper is due May 6, 2026.
  - Several teammates have finals this week, so the evidence freeze and writing cut lines need to be explicit.

## Decisions / Status

### Decided during the call

- Treat the Apr 28 Dhaval / Shuxin meeting as the gating source for final scope and upstream-AOB strategy.
- Keep Cell C separate from the closed Experiment 1 A/B evidence story until its implementation and captures are actually stable.
- Keep Problem Statement B as a methodology-plus-partial-evidence lane unless generated-scenario validation lands in time.
- Use the final week to convert committed evidence into notebooks, figures, report text, deck material, and reproducibility notes rather than expanding scope indiscriminately.
- Ask Dhaval / Shuxin directly whether the upstream AssetOpsBench contribution should prioritize scenarios/evaluation over runnable team-repo code.

### Resolved later in the Dhaval / Shuxin call

- Upstream PRs to AssetOpsBench are useful but should not derail the class or NeurIPS deadlines.
- Dhaval and Shuxin care most about scenarios, validation, LLM-as-judge, and evaluation framing; code can change later.
- The upstream contribution should be split into small focused PRs rather than one giant repository transplant.
- The team should read the NeurIPS call carefully and make evaluation/scenario quality the center of the paper, not only dataset quantity.

## Action Items Captured on Apr 28

Current execution status has moved since this meeting; see the GitHub Project
board before treating any checkbox here as live work.

- [ ] Alex: convert the team sync and Dhaval / Shuxin meeting into canonical meeting notes, a final-week action plan, and a personal reconciliation update.
- [ ] Alex: use the Dhaval / Shuxin guidance to reframe the class report, NeurIPS draft, and deck around scenarios, validation, LLM-as-judge, and measured system behavior.
- [ ] Aaron: finish the approved W5 capture-prep path and continue PS B scenario generator work after requested changes are addressed.
- [ ] Akshat: resolve the Cell C batched-tool-call PR conflicts/review findings or explicitly cut Cell C from final empirical claims.
- [ ] Akshat: finish Notebook 03 cleanup and failure-taxonomy evidence needed for the orchestration story.
- [ ] Tanisha: keep PS B methodology/data support ready for the report, especially circularity handling and generated-vs-handcrafted scenario validation.
- [ ] Team: decide by Apr 30 which results are final evidence, which are appendix/ablation, and which are future work.

## Notes

- The transcript source also captured some transition into the following Dhaval / Shuxin meeting. This file records the team-sync portion only; the mentor meeting has its own record at `planning/2026-04-28_dhaval_shuxin_meeting_notes.md`.
- Where repo state moved after the meeting, the canonical status is the GitHub Project board; this note records the meeting record, not every subsequent GitHub edit.
