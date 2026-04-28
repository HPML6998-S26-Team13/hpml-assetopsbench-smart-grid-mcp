# Team 13 Call - April 28, 2026 (Tuesday, 2:45 PM ET)

*Draft agenda. Goal: freeze the evidence story, lock W5 writing / presentation ownership, and decide what still makes the final cut.*

## Live update as of Apr 28, 14:20 ET

- PR [#129](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/pull/129) merged: INT8 is validated but deferred from Cell C; prefix caching is the selected KV/cache knob for Cell C via `EXTRA_VLLM_ARGS`.
- PR [#146](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/pull/146) merged: Insomnia runbook / profiling docs were reconciled after PR #143 / #144 and the Apr 26 worktree-permissions incident.
- Open PRs to triage before/after the call:
  - PR [#134](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/pull/134) — Cell C batched tool calls / MCP connection reuse; `CHANGES_REQUESTED`.
  - PR [#145](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/pull/145) — pre-W5 capture hardening for #135 / #132; approved, black green.
  - PR [#147](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/pull/147) — PS B generator scaffold; `CHANGES_REQUESTED`.
- Dhaval pre-call email was sent. Use the call to confirm framing, judge/evaluation-module direction, failure taxonomy framing, and whether Verified PE + Self-Ask can be reported as a co-reported variant.

## Post-Apr-21 context to refresh before the call

- Apr 21 meeting record: [planning/2026-04-21_meeting_notes.md](2026-04-21_meeting_notes.md).
- The Apr 21 meeting made [#25](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/25) the practical proof gate for Experiment 1 instrumentation readiness; PR [#130](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/pull/130) has since closed that A/B gate for first-canonical evidence.
- [#111](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/111) is closed by PR [#125](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/pull/125); the live question is whether any follow-on Insomnia/model-revision docs are still missing.
- [#104](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/104) is closed / Done by PR [#127](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/pull/127): Cell A, Cell B, and upstream AOB `OpenAIAgentRunner` parity are smoke-proven.
- [#50](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/50), [#83](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/83), and [#90](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/90) are closed. PS B's live path is now generator + validation: PR [#147](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/pull/147), then #53 / #68.

## Agenda (35 min)

**0:00-0:06 - W4 scorecard**
- Which W4 tasks actually closed?
  - Default suggestion: count #25, #29, #30, #32, #50/#83/#90, #104, #111, and the runbook/profiling doc cascade as closed or landed; keep #26, #31, #34, #35/#64/#65/#66, #85/#86, #131/#133, and PS B generation/validation as live.
- Which open issues still matter for the final submission versus the stretch lane?
  - Default suggestion: final-critical = #26, #34, #39, #40, #44, #49, #35/#64; conditional = #31/#85/#86 and #145; stretch/future unless accelerated = #2/#53/#68 PS B scale-up, #131/#133, 70B full rerun.
- What is still only in PR form or local artifacts?
  - Default suggestion: PR-only = #134, #145, #147. Local-only should not be treated as final evidence unless it is promoted to a committed artifact or issue comment before writing freeze.
- Did [#25](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/25) advance beyond smoke proof into full A/B `multi_*.json` x 3-trial captures?
  - Default answer: yes for first-canonical A/B via PR #130 / Slurm `8979314`; no for A/B/C because Cell C is split to #85/#86 and remains conditional on #134.
- Did [#111](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/111)'s closeout leave any residual Insomnia setup / model-revision documentation gaps?
  - Default answer: no meeting blocker after PR #146. Ask Aaron for a quick owner ack only; do not spend core call time unless he sees a reproducibility gap.

**0:06-0:14 - Final experiment evidence**
- Which Experiment 1 cells are clean enough to cite?
  - Default suggestion: cite A/B first-canonical evidence; cite Cell C only if #134 + #145 land and #85 produces comparable artifacts. Otherwise mark Cell C deferred.
- Is Experiment 2 now honestly comparative, or still mostly a PE-first story with partial AaT evidence?
  - Default suggestion: honestly comparative as first-canonical B/Y/Z(+SA) judge evidence, but Notebook 03 consumer cleanup (#34) must clear metadata/output mismatch before paper-ready figures.
- What reruns, if any, are still worth spending time on before the 3:30 PM ET Dhaval call and W5 writing freeze?
  - Default suggestion: before Dhaval, no new rerun; carry current evidence and ask about framing. For W5, prioritize one clean final 5×6 or 70B spot-check only if owners/time are explicit.

**0:14-0:20 - Problem Statement B final framing**
- Is PS B strong enough to stay visible in the final story?
  - Default suggestion: visible as methodology/supporting extension, not core evidence, until PR #147 plus a generated batch and #53 validation land.
- If yes, which parts of the support-doc -> generated-scenario -> validation chain are actually landed, and which parts still wait on PR [#147](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/pull/147) / #53?
  - Default answer: support docs are fixed by PR #128, but generation chain now depends on PR #147 and #53. Do not claim generated-scenario evaluation yet.
- If not, what remains as future work only?
  - Default suggestion: scale-up to 18+ generated scenarios, 50+ total scenarios, and hand-crafted-vs-generated performance comparison remain future/stretch unless #147/#53 close fast.

**0:20-0:27 - Writing and presentation lock**
- abstract path
  - Default suggestion: Alex owns the abstract and paper spine; teammates feed section briefs.
- paper outline and evidence map
  - Default suggestion: anchor on SmartGridBench extension, MCP/AaT artifact contract, A/B overhead, B/Y/Z judge-quality tradeoff, failure taxonomy; keep PS B as secondary unless validated.
- class-report back-port plan
  - Default suggestion: write NeurIPS-style first, then back-port to IEEE/class template under #40.
- presentation structure and figure list
  - Default suggestion: use 5-slide structure: problem/domain, system/artifact pipeline, Experiment 1, Experiment 2/failure taxonomy, final takeaways/next steps.
- teammate content-brief deadlines
  - Default suggestion: one-page briefs due Apr 29 noon ET: Tanisha (#41), Akshat (#42), Aaron (#43); Alex integrates into #39/#40/#44.

**0:27-0:32 - Reproducibility / docs check**
- what a teammate or reviewer can reproduce today from docs
  - Default suggestion: A/B and Exp 2 first-canonical artifact reading is reproducible; full Cell C and generated-scenario flow are not yet reproducible as final evidence.
- what still needs a final runbook / artifact cleanup pass
  - Default suggestion: PR #146 handled the major Insomnia/profiling doc gap; #49 should be a focused final pass over runbook, artifact table, and notebook commands.
- whether any live docs still belong in archive or reference instead
  - Default suggestion: after May 4, archive volatile planning docs; keep experiment matrix, runbooks, scenario-generation docs, and result contracts as reference.

**0:32-0:35 - Final-week cut line**
- what gets cut if time is tight
  - Default suggestion: cut Cell C final claim, PS B evaluation claim, 70B full rerun, and upstream AOB PR if they threaten writing/deck.
- what absolutely must land before May 4
  - Default suggestion: #26/#34 paper-ready outputs, #39/#40/#44, #49 final reproducibility check, and enough #35/#64 failure-taxonomy material for the results story.
- what can safely remain backlog or future work
  - Default suggestion: #31/#85/#86 if not stable, #2/#53/#68 scale-up, #131/#133, AOB upstream migration, and final 5×6 rerun.

## Decisions needed

1. Which experiment results are final enough to anchor the report and slides?
   - Default suggestion: A/B first-canonical and Exp 2 judge-score ranking are anchors; Cell C is conditional; PS B is secondary.
2. Is Problem Statement B a reported contribution or explicitly future work flavor?
   - Default suggestion: reported as methodology/scaffold if #147 lands, but empirical contribution only after generated batch + #53 validation.
3. What is the last acceptable day for reruns before writing freezes?
   - Default suggestion: Apr 30 end-of-day for new evidence, May 1 only for bugfix/repro reruns.
4. What is each person's W5 deliverable with no ambiguity?
   - Default suggestion: Alex paper/report/deck integration; Aaron infra/profiling/capture facts and #145/#85 support; Akshat #34/#35/#42 judge/scenario facts; Tanisha #41/#54 methodology/data/PS B framing.
5. Which still-open PRs are genuinely worth landing versus explicitly deferring?
   - Default suggestion: land #145; land #134 only if review blockers clear today; land #147 only as PS B scaffold, not evidence; defer anything that starts a new matrix axis.
6. What should Alex carry into the Dhaval call at 3:30 PM ET as proof, blocker, and ask?
   - Default suggestion: proof = A/B + Exp 2 judge scores; blocker = final framing / 8B caveat / Notebook 03 cleanup; ask = evaluation-module timeline, judge model, failure taxonomy framing, and whether Verified PE + Self-Ask can be co-reported.
