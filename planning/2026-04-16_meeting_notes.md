# Apr 16, 2026 | HPML Final Project - Team 13 Sync

Attendees: [Alex Xin](mailto:wax1@columbia.edu), [Akshat Bhandari](mailto:ab6174@columbia.edu), [Tanisha Rathod](mailto:tr2828@columbia.edu), [Aaron Fan](mailto:af3623@columbia.edu)

## Overview

This call happened after the repo crossed its first real benchmark threshold on Apr 13. The team now has a proven Insomnia smoke path, a first real WandB run, and a first benchmark-facing Plan-Execute Smart Grid artifact flow on canonical history via a WatsonX-hosted 70B / Mac smoke run. The meeting therefore shifted from "can anything run yet?" to "which overdue W2 items still matter, what exactly closes them, and what should W3 actually optimize for?"

The main coordination theme was honesty about project state. The repo is healthier than the board alone suggests, but several W2 carryover items still gate broader profiling, judge, and scenario-scale work. The team used the call to clarify where real evidence exists already, what still only exists locally or in open PRs, and which W3 tasks should be treated as core rather than stretch.

## Summary

- **What had already landed by the time of the call:**
  - shared Insomnia A6000 vLLM smoke proof
  - first real shared WandB run
  - first benchmark-facing Plan-Execute Smart Grid artifact flow with committed WatsonX smoke artifacts
  - scenario realism validation note for Dhaval-facing review

- **Aaron status / discussion:**
  - Insomnia serving path is now real
  - the next real bottleneck is profiling capture, not basic serving
  - open W3/W2-linked items are still the profiler / GPU wrappers, profiling-to-WandB linkage, the first Experiment 1 captures, and the infra-serving-profiling runbook consolidation

- **Tanisha status / discussion:**
  - Smart Grid MCP servers are benchmark-reachable through the successful PE proof path
  - the remaining open work is now about hardening, tests, and explicit benchmark-path proof rather than whether the servers can be reached at all
  - the WO architecture review question is effectively a design-decision task, separate from the still-open server-hardening PR
  - follow-up after the call: PR `#115` later gained a real Insomnia A6000 / self-hosted 8B / all-4-server proof artifact for `#58`, plus concrete vLLM serve notes for longer benchmark contexts

- **Akshat status / discussion:**
  - scenario replay work and harness notes had already landed earlier
  - the big remaining W2 carryover is still canonical benchmark proof, judge wiring, first trajectory artifacts, and scenario-count growth
  - current canonical scenario count is still below the planned benchmark corpus size

- **Alex status / discussion:**
  - PS B evaluation methodology and abstract-outline work moved from "to be planned" into active writing tasks
  - the repo-side orchestration plumbing is good enough to separate what is real now from what is only adapter-ready
  - Hybrid should not stay in the critical path by default

- **Experiment framing discussed on the call:**
  - Experiment 1 is still the immediate W3 execution priority because it unlocks Notebook 02 and the MCP-overhead story
  - Experiment 2 should stay honest: PE is real now, AaT is adapter-ready, Hybrid should not be treated as a required third condition unless it becomes runnable without derailing the schedule
  - Reemphasized that not every scenario must be duplicated across every model and orchestration, Experiment 1 and 2 share one common lane.

- **Problem Statement B discussion:**
  - the current artifact chain is still:
    - Knowledge Plugin / standards artifact
    - first generation prototype
    - evaluation methodology
    - validation / comparison
  - W3 should prioritize a believable first artifact chain over optimistic scale language

## Decisions / Status

### Decided during the call
- The team should treat the repo's Apr 13 proof runs as real progress, not as "setup still in progress."
- Experiment 1 artifact production is the most important W3 technical priority.
- The main orchestration comparison remains centered on vanilla Agent-as-Tool versus vanilla Plan-Execute.
- Problem Statement B should be evaluated by artifact quality and trustworthiness before scale.

### Resolved later in post-call planning

- **[#13](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/13) WO architecture review** - closed during the post-call audit. Tanisha's design-decision note is specific enough to resolve the keep-vs-pivot question, while the remaining implementation work stays with [#9](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/9)-[#12](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/12) and [#58](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/58).
- **[#28](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/28) first WandB experiment logs live** - closed during the post-call audit against the already-landed shared WandB run `9d4442ja` and the committed WatsonX smoke artifacts under `benchmarks/cell_Y_plan_execute/`. Future profiling-linked logging milestones stay with [#25](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/25) and [#27](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/27).
- **Hybrid orchestration scope** - explicitly deferred out of the active class-project critical path. [#23](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/23) remains as optional backlog / future-work scope, not as a W3 blocker.
- **Self-Ask scope** - [#24](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/24) is no longer treated as an immediate three-mode coding task. It should only reactivate once the set of active orchestration modes is real rather than aspirational.
- **Primary experiment model** - use Llama-3.1-8B-Instruct on Insomnia as the main local benchmark model. Keep WatsonX-hosted 70B as a selective scaling spot-check, not as a duplicate full-grid obligation.
- **[#37](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/37) runbook ownership** - Aaron owns the substantive infra / serving / profiling path. Alex can help with editorial cleanup later, but [#37](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/37) is Aaron's lane.
- **What closes [#3](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/3) and [#58](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/58)** - both require proof on canonical `main`, not only in open PRs or local branches. This stays the bar going forward.

### Status updates after the call

- **Tanisha benchmark-path proof follow-up** - after the call, PR `#115` gained a real Insomnia A6000 Plan-Execute validation artifact for [#58](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/58). The committed artifacts clearly show a successful all-4-server proof and a `32768` context-length validation run, but the shared serve script and runbook still need merge cleanup before that path becomes canonical.

## Action Items

See the live [GitHub Project](https://github.com/orgs/HPML6998-S26-Team13/projects/1/views/1) for canonical task tracking. The list below reflects what the meeting implied plus what the post-call audit later clarified. As of the Apr 20 board reset, the remaining W2 carryover is now hard-dated Apr 20-21 and the spillover W3 tasks were moved into W4 explicitly.

**Immediate follow-up after the call**
- [ ] Aaron: use Apr 20 for [#111](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/111), Apr 21 for [#27](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/27), Apr 22 for [#25](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/25), and Apr 23 for [#37](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/37) so the [#7](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/7) / [#59](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/59) Experiment 1 capture chain stops drifting
- [ ] Tanisha: use Apr 20 for [#9](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/9) and [#58](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/58), then Apr 21 for [#10](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/10)-[#12](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/12); the real proof artifact is now present in PR `#115`, but merge/readme cleanup still remain
- [ ] Tanisha: finish the structured standards artifact for [#50](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/50) by Apr 21 in a form Aaron can actually consume
- [ ] Akshat: resolve the open PR feedback and land the canonical proof / judge / trajectory ladder for [#3](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/3), [#17](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/17), [#18](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/18), and [#20](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/20) by Apr 21
- [ ] Akshat: increase the canonical scenario set beyond the current 10-file state so [#15](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/15) is credibly addressed by Apr 21 and later [#33](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/33) is no longer a fantasy milestone
- [x] Alex: review open PRs [#112](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/pull/112)-[#115](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/pull/115) and post concrete feedback
- [x] Alex: land the post-call planning sync, close the scope-decision issues that were already effectively resolved, and update the tracker surfaces
- [ ] Alex: keep Experiment 2 scoped to the honest runnable conditions and keep [#51](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/51) / [#77](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/77) moving for the Apr 20 board target even while upstream artifacts are still catching up

## Notes

- The project is no longer waiting on generic setup success; it is now waiting on a smaller set of evidence-producing tasks.
- Hybrid is no longer a silent blocking assumption in the tracker or the call-prep docs.
- The W3 story is cleaner if the team treats profiling capture, PS B first artifacts, and writing scaffolding as the real week, with the remaining W2 carryover called out by name rather than buried.
