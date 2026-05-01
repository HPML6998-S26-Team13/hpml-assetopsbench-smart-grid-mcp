# Apr 28 Post-Meeting Action Plan

*Last updated: 2026-04-30*

This plan reconciles the Apr 28 team sync, the Apr 28 Dhaval / Shuxin mentor call, live GitHub PR/issue state, and the current team-repo/AOB CodeGraph map. It is not a transcript; canonical meeting records live in:

- `planning/2026-04-28_meeting_notes.md`
- `planning/2026-04-28_dhaval_shuxin_meeting_notes.md`

## Status Refresh (2026-04-30)

This file began as an Apr 28 final-week plan. The core scope guidance still
holds, but the PR-status section below is now historical: PRs #145, #134,
#147, #148, and #149 have since merged, and Cell C, Cell D, and
Z + Self-Ask + D proof captures plus Maverick judge rows are on main. Use this
document for cut-line rationale and upstream-AOB strategy; use the GitHub
Project board for current task status.

## Hard Deadlines

| Date | Deliverable | Planning meaning |
|---|---|---|
| 2026-05-04 | HPML class project package: code/repo, paper/report, and presentation package | Treat as the hard class deadline unless the course staff explicitly changes it. |
| 2026-05-04 | NeurIPS 2026 abstract | The abstract can use the class-story spine, but must be evaluation/benchmark focused. |
| 2026-05-06 | NeurIPS 2026 full paper | Continue only if the May 4 class package is stable enough not to be endangered. |
| After May 4 / May 6, or earlier only if trivial | Upstream AssetOpsBench PRs | Split into small focused PRs; do not block class/NeurIPS on upstream integration. |

## Current Repo Truth

### Landed / stable enough to cite

- SmartGridBench MCP server stack, data pipeline, scenario schema, and core runbook surfaces are in the team repo.
- Experiment 1 Cells A/B have canonical capture evidence from the AaT/direct and MCP-baseline lanes.
- Experiment 1 Cell C has a successful optimized-MCP proof capture and judge
  rows on main; use it for analysis with the documented cold-prefix caveat.
- Experiment 2 has first canonical small-N evidence for Cell B, Cell Y, Cell Y + Self-Ask, Cell Z, and Cell Z + Self-Ask.
- Cell D and Z + Self-Ask + D have successful optimized-serving proof captures
  and judge rows on main; treat them as exploratory ablations/ceilings rather
  than replacements for the clean transport-only matrix.
- The Maverick judge path produced first six-dimension scores and raw judge logs; the writeup must clearly distinguish judge-pass from runner completion-pass.
- Insomnia operational docs and profiling docs were hardened after the Apr 27 / Apr 28 runbook sweep.

### Resolved after this plan

- PR #145 merged the W5 capture-prep hardening for MAX_MODEL_LEN / GPU metadata.
- PR #134 merged Cell C batched tool calls + MCP connection reuse; Cell C now
  has a successful proof capture and judge rows on main.
- PR #147 merged the PS B scenario generator scaffold. Generated-scenario
  validation is still the gate before treating generator output as empirical
  evidence.
- PRs #148 and #149 merged the L3 statistical-fidelity validator / DGA realism
  doc and the IEC 60599:2022 Rogers-Ratio fix.
- Cell D and Z + Self-Ask + D now have successful optimized-serving proof
  captures and Maverick judge rows. They are useful ablations/ceilings, not a
  replacement for the clean A/B/C transport-only story.

### Open issue gates

- Experiment 1 optimized Cell C analysis / paper promotion: #85, #86.
- Experiment 2 notebook/failure-analysis story: #34, #35, #64, then possible mitigation/rerun follow-ons #65 / #66.
- Problem Statement B: #2, #33, #52, #53, #54, #55, #68, with generated-scenario validation still required before strong empirical claims.
- Writing/delivery: #39, #40, #44, #45, #47, #48, #49, plus content briefs #41-#43.
- Upstream AOB contribution: #46.

## Final-Week Critical Path

The schedule below preserves the Apr 28 planning sequence. Items that landed
afterward are noted in the status refresh above; the remaining value of this
section is its cut-line logic.

1. **Apr 28-29: merge or consciously cut near-ready infra.**
   - Take PR #145 if still green/approved.
   - Decide whether PR #134 can be rescued quickly; if not, Cell C becomes a limitation/future-work result.
   - Keep PR #147 moving, but do not let PS B generator polish block core deliverables.

2. **Apr 29-30: freeze empirical evidence.**
   - Decide which run artifacts are final enough for Notebook 02, Notebook 03, and the report.
   - If Cell C does not land, write the overhead story as Direct vs MCP-baseline plus optimized-path plan/caveat.
   - If generated scenarios are not validated, write PS B as a method/scaffold with validation plan rather than a measured performance claim.

3. **Apr 30-May 1: convert evidence into analysis surfaces.**
   - Notebook 02: latency/profiling story for Experiment 1.
   - Notebook 03: orchestration comparison, Self-Ask ablation, Verified PE interpretation, and failure taxonomy hooks.
   - Failure taxonomy: map observed failures to a cited taxonomy with artifact-backed rows, not impressionistic labels.

4. **May 1-3: write and package.**
   - NeurIPS draft first where possible, then back-port to IEEE/class report.
   - Deck should mirror the final evidence spine, not every branch/PR.
   - WandB dashboard and runbook should be checked for reproducibility claims.

5. **May 4: submit class package and NeurIPS abstract.**
   - No late scope expansion on May 4.
   - Any unlanded code becomes a clearly labeled limitation or future-work item.

6. **May 5-6: only continue NeurIPS full-paper push if class package is safe.**
   - Tighten evaluation framing, scenario validation, LLM-as-judge details, and limitations.
   - Decide whether to include AOB PR status as "open-source contribution in progress" rather than a completed claim.

## AOB PR Strategy

Dhaval and Shuxin's guidance changes the upstream strategy: do not try to transplant the entire HPML repo. Use the AOB fork as the integration target only after selecting durable contributions.

### AOB structure that matters

CodeGraph confirms the current AOB surfaces most relevant to us:

- Agent base/runtime:
  - `src/agent/runner.py`
  - `src/agent/openai_agent/runner.py`
  - `src/agent/plan_execute/runner.py`
  - `src/agent/plan_execute/planner.py`
  - `src/agent/plan_execute/executor.py`
  - `src/llm/litellm.py`
- Scenario client/server and grading:
  - `aobench/scenario-client/src/scenario_client/`
  - `aobench/scenario-server/src/scenario_server/`
  - `aobench/scenario-server/src/scenario_server/grading/graders.py`
  - `aobench/scenario-server/src/scenario_server/handlers/`
- Scenario authoring guidance:
  - `docs/guideline/utterance_design_guideline.md`
  - `docs/guideline/ground_truth_design_guideline.md`

### Recommended PR stack

1. **Smart Grid scenario pack PR.**
   - Add a validated Smart Grid scenario subset that matches AOB schema/guidelines.
   - Include ground-truth rationale and validation notes.
   - This is the highest-value upstream piece because scenarios survive code refactors.

2. **Validation / LLM-as-judge PR or design discussion.**
   - Bridge our per-trial JSON / six-dimension judge evidence to AOB's current evaluation-module direction.
   - Keep the adapter small; do not force AOB to accept the team repo's whole result layout.

3. **Smart Grid tool/server integration PR.**
   - Add only the minimal tool surfaces needed for the accepted Smart Grid scenarios.
   - Prefer AOB's current scenario-server/handler conventions over copying our repo tree wholesale.

4. **Optional agent/runtime PR.**
   - Only pursue if the delta is small and legible in AOB's `src/agent` structure.
   - A tiny Verified PE / Self-Ask-inspired agent is more plausible than a large orchestration subsystem.

## Cut Lines

- **Cell C:** central result only if PR #134 + capture artifacts land by the evidence freeze. Otherwise report it as an optimization design and future rerun.
- **PS B generated scenarios:** central result only if generator plus validation land. Otherwise include methodology, examples, and validation plan.
- **70B full rerun:** not required for the class package. A selective spot-check is useful only if it does not displace writing.
- **Upstream AOB PR:** valuable, but secondary to class and NeurIPS. It can be submitted after May 4 / May 6 with stronger evidence.

## Recommended Final Story

SmartGridBench extends AssetOpsBench with a Smart Grid transformer domain and evaluates the cost and behavior of MCP-mediated tool use under realistic maintenance scenarios. The strongest final-week story is:

1. **Benchmark contribution:** Smart Grid scenarios, MCP tool servers, and validation/ground-truth design.
2. **Systems contribution:** measured overhead of MCP versus direct tool access, with profiling and optimization evidence where landed.
3. **Agent/evaluation contribution:** orchestration comparison showing that completion, latency, and judge-scored answer quality can disagree; Self-Ask and verifier-gated PE are useful mitigation directions.
4. **Open-source contribution:** upstream-ready scenario/evaluation assets will be contributed to AOB as small PRs after the class/NeurIPS critical path is safe.
