---
title: Scenario Realism And PS B Knowledge Closeout
slug: scenario-realism-and-psb-knowledge-closeout
type: retrospective
status: live
created: 2026-06-05
updated: 2026-06-05
owner: Alex Xin
scope: project
project: hpml-assetopsbench-smart-grid-mcp
tags: [scenario-generation, problem-statement-b, knowledge, dga, ground-truth]
work-items: []
related:
  - docs/knowledge/generated_scenario_authoring_and_ground_truth.md
  - docs/knowledge/scenario_generation_support.json
  - docs/archive/scenario_realism_validation.md
  - docs/ps_b_evaluation_methodology.md
agent: Codex
agent-provider: OpenAI
agent-interface: Codex Desktop
agent-session-id: 019d697e-964d-7302-8114-6e243f1d69b7
session-label: "FND: Coordination and AaT Review"
invocation-context: "session-closeout: closeable"
session-lifecycle: closeable
session-closeout-note: .agent-sessions/closed/session-closeout-019d697e-964d-7302-8114-6e243f1d69b7.md
---

# Scenario Realism And PS B Knowledge Closeout - 2026-06-05

## Metadata

| Field | Value |
|---|---|
| Unit | Scenario realism research and PS B knowledge support |
| Unit type | Initiative closeout |
| Status | Completed as support docs; downstream generator/validation continued in later issues and PRs |
| Repo | hpml-assetopsbench-smart-grid-mcp |
| Branch / PR | Historical PR #128 / issues #83 and #90 after issue reuse; later docs now canonical |
| Work item IDs | Runtime placeholder AUX-3f1d69b7 only |
| Sources inspected | `docs/knowledge/README.md`, `docs/knowledge/generated_scenario_authoring_and_ground_truth.md`, `docs/knowledge/scenario_generation_support.json`, `docs/archive/scenario_realism_validation.md`, `docs/ps_b_evaluation_methodology.md`, personal research folio summaries in conversation |

## 1. Work Completed

| What | Why | How | Evidence |
|---|---|---|---|
| Combined the early realism folio and the later curated scenario-generation folio into a practical support plan | The team needed one streamlined handoff rather than two research artifacts with overlapping advice | Crystallized the split: old folio tests whether current scenarios are believable; new folio specifies reusable generator supports | Conversation planning; archived `docs/archive/scenario_realism_validation.md`; current `docs/knowledge/` docs |
| Preserved Dhaval's no-hint rule as an authoring contract | Generated prompts must test tool-selection reasoning, not reveal the analytic path | Wrote explicit banned/preferred prompt patterns and hidden ground-truth requirements | `docs/knowledge/generated_scenario_authoring_and_ground_truth.md` |
| Turned realism gaps into generator supports | DGA trends, operating context, work-order realism, and family coverage needed concrete data structures | Produced structured support data: family matrix, context profiles, DGA trend templates, event/alarm templates, work-order playbook, RUL/health context | `docs/knowledge/scenario_generation_support.json` |
| Kept Tanisha's standards knowledge separate from scenario assembly guidance | IEC/IEEE facts and generator assembly rules are complementary, not replacements | Positioned the support JSON as "how to assemble" and standards artifact as "source of standards content" | `docs/knowledge/README.md`; `scenario_generation_support.json` metadata |
| Reviewed PR #128 through correctness | Early support artifacts contained DGA templates whose sample gases did not classify as claimed | Verified sample rows against live `analyze_dga`, required fixes, then approved after classifications matched | PR #128 review trail summarized in personal shift note `codex_72ad124b` |

## 2. Ideas, Decisions, Questions Addressed

| Item | Type | Resolution | Rationale | Evidence |
|---|---|---|---|---|
| Does the new curated folio supersede the old realism folio? | Decision | No. The curated folio extends the old one | The old folio answered "are current scenarios believable"; the new one answered "what generator supports should exist" | User-quoted analysis; current docs keep both archive and support-doc references |
| Should generated scenarios reveal RUL/DGA/work-order tasks in the prompt? | Decision | No. The prompt should describe an operational situation; hidden ground truth records ideal tools and final values | This matches Dhaval's guidance and keeps tool selection part of the benchmark | `generated_scenario_authoring_and_ground_truth.md` |
| Should all PS B support artifacts be one issue? | Decision | Two issue-sized work chunks were reasonable, but the final implementation could be one coherent support pack if scoped tightly | Artifact authoring is bounded; generator integration and validation are separate downstream work | Issue reuse and PR #128 planning |
| Should the knowledge docs live under `data/knowledge` or `docs/knowledge`? | Decision | Support docs belong in `docs/knowledge`; canonical scenario data and generated candidates belong under `data/` | They are human/generator guidance, not benchmark input data | `docs/knowledge/README.md` |

## 3. Issues Encountered And Resolved

| Issue | Impact | Resolution | Verification | Prevention / Learning |
|---|---|---|---|---|
| DGA trend examples claimed labels the live classifier did not produce | Would silently poison generated scenario ground truth | Required every DGA trend endpoint and intermediate sample to classify as claimed or carry explicit caveat | PR #128 review and final approval after all template rows matched | Scenario supports must be tool-verified, not just standards-plausible |
| The team risked confusing "standards facts" with "scenario-generation policy" | Could duplicate or contradict Tanisha's knowledge plugin | Kept support docs MECE: standards artifact carries IEC/IEEE facts; support JSON carries families, contexts, templates, playbooks | `scenario_generation_support.json` usage note | Separate source-of-truth content from generation-control content |
| Too many artifact candidates could inflate scope | PS B could become a new research lane instead of support for generator/validation | Sized artifacts as bounded support pack and routed integration to existing generator/validation issues | Conversation planning and issue reuse | Authoring supports is moderate work; full consumption/regeneration/validation is the larger task |

## 4. Remaining Ideas, Decisions, Questions

| Item | Type | Priority | Time Horizon | Owner / Next Action | Tracking |
|---|---|---|---|---|---|
| Upstream AssetOpsBench documentation contribution | Idea | P3 | later | Near project completion, consider whether the ground-truth/scenario-generation guidance should be proposed to IBM AssetOpsBench as a separate doc or inline guideline extension | Mentioned in this closeout; no team PM row because PM backlog was intentionally removed |
| Keep generated scenario supports synchronized with validator behavior | Follow-up | P2 | ongoing | When validators or tool outputs change, re-run support artifact sanity checks | `docs/knowledge/`; `data/scenarios/validate_scenarios.py`; GitHub issues #2, #53, #68 as historical downstream owners |
| Avoid circularity between generator and evaluator | Follow-up | P1 | ongoing | Generated prompts and ground truth should use support artifacts, while validation checks against promoted scenario files and live tool behavior | `docs/ps_b_evaluation_methodology.md` |

## 5. Remaining Issues

| Issue | Risk | Priority | Time Horizon | Owner / Next Action | Tracking |
|---|---|---|---|---|---|
| Support docs alone do not make generated scenarios canonical | A generator can produce plausible but invalid candidates | P1 | ongoing | Promote only after schema validation, tool-output checks, and duplication review | `docs/knowledge/README.md`; `data/scenarios/README.md` |
| Standards thresholds are intellectual-property-sensitive | Over-copying standards text could create citation/copyright risk | P2 | ongoing | Keep encoded predicates and summaries; do not paste protected standard text | `docs/knowledge/`; repo IEC/IP guardrails |

## 6. Learnings

### Local

- The clean split is: standards knowledge answers what domain facts are valid; scenario-generation support answers how to assemble benchmark tasks without leaking the solution path.
- DGA support rows should be executable examples against the repo classifier. A support file that "sounds right" but fails `analyze_dga` is worse than no support file.

### Project

- Scenario prompts should be operational and sparse; hidden ground truth should be structured and concrete.
- PS B artifact authoring is bounded, but generator consumption plus regeneration plus validation is materially more work and belongs in downstream implementation issues.

### Global Candidates

- For benchmark generation, "anti-hints" should be a first-class artifact. It is easier to prevent hint leakage with explicit banned patterns than by reviewing free-form generated prompts after the fact.

## 7. Strategic Fit

| Level | Fit |
|---|---|
| Task / sprint | PS B support pack and generated scenario quality |
| Epic / initiative | Problem Statement B scenario generation |
| Product / program / engagement | SmartGridBench scenario corpus realism |
| Repo / project | Makes generated scenarios less toy-like and more defensible |
| Global framework | Reusable pattern for separating domain facts, generation controls, and evaluator ground truth |
