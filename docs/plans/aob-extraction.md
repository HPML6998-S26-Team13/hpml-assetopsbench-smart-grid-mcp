# Plan: extract docs/code from team repo into Alex's AOB fork

*Plan for Alex Xin (eggrollofchaos). Companion spec at [aob-extraction_spec.md](aob-extraction_spec.md).*

## Origin

This plan formalizes the multi-phase extraction of Smart Grid Bench artifacts
from the team repo (`HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp`)
into Alex's AssetOpsBench fork (`eggrollofchaos/AssetOpsBench`), with eventual
upstream PRs to `IBM/AssetOpsBench`.

**Seed artifacts:**
- `pm/backlog.md` 2026-04-27 pin (b) — migrate to upstream AOB's
  `feat/evaluation-module` (branch tip `fcff318` upstream); write adapter
  from per-trial JSON shape to AOB's `PersistedTrajectory`; retire
  `scripts/judge_trajectory.py` after parity is proven.
- `pm/backlog.md` 2026-04-27 pin (c) — vLLM replay-phase aat_runner design
  question; resolved separately in `docs/replay_phase_analysis.md` (Option 1
  recommended); the cell-aware-replay mechanics are referenced here only as a
  potential future AOB-side feature.
- `docs/coordination/live_repo_summary.md` § 1 Executive Snapshot bullets
  covering the AOB code-dive 2026-04-27 (Y baseline runs upstream Plan-Execute
  on Python 3.12; PE/Verified PE/Self-Ask wrappers in our `scripts/` are thin
  repo-local layers around the AOB `plan_execute` slice; vanilla AaT now has
  `scripts/aat_runner.py` after `#104` closure).
- `Final_Project/planning/Dhaval_Email_Thread.md` Apr 28 entry — the four
  pinned questions for Dhaval, including upstream-merge timing for
  `feat/evaluation-module` and judge-model intent.
- AOB code dive notes implicitly captured in
  `docs/orchestration_wiring.md` and `docs/experiment2_capture_plan.md`.

**Backlog lineage:**
- Root umbrella: not yet filed as a single GitHub Issue; recommend filing one
  as `IDEA-AOB-EXTRACT` ("Extract Smart Grid Bench artifacts into
  eggrollofchaos/AssetOpsBench fork; upstream selectively") under the team
  repo's `pm/` taxonomy.
- Pre-existing pins: `pm/backlog.md` items (b) + (c) flow into Phase 1 and
  Phase 4 below respectively.
- New child issues to file as work begins per phase (see Implementation-Ready
  Checklist).

**Reference context (state-of-the-world to consult before each phase):**
- AOB upstream `main` snapshot: ~/coding/AssetOpsBench at `669a4f5` (today).
- AOB upstream branches: `feat/evaluation-module` (`fcff318`),
  `feat/openai-agents-runner`, `feat/add-deep-agent-runner`,
  `feat/skills-evaluation-framework`, `feat/vibration-mcp-server` — see
  spec for which branches are relevant per phase.
- Team repo extraction sources:
  - `mcp_servers/{iot,fmsr,tsfm,wo}_server/`, `mcp_servers/base.py`,
    `mcp_servers/direct_adapter.py`
  - `data/scenarios/*.json` (Smart Grid 7th-domain scenarios)
  - `scripts/aat_runner.py`, `scripts/aat_tools_{mcp,direct}.py`,
    `scripts/aat_system_prompt.py`, `scripts/aat_upstream_openai_runner.py`
  - `scripts/plan_execute_self_ask_runner.py`,
    `scripts/verified_pe_runner.py`, `scripts/orchestration_utils.py`
  - `scripts/judge_trajectory.py` (to retire after Phase 1)
  - `docs/orchestration_wiring.md`, `docs/judge_schema.md`
- Current AOB-side reference docs to align with: `INSTRUCTIONS.md`,
  `README.md`, `src/agent/openai_agent/runner.py:171-203`
  (`OpenAIAgentRunner` contract), `src/agent/plan_execute/runner.py:81-111`
  (`PlanExecuteRunner` contract).

## Goals

1. **Move evaluation logic to AOB.** Adopt `feat/evaluation-module` as the
   judge plumbing. Retire `scripts/judge_trajectory.py` from the team repo
   once parity is proven.
2. **Make the Smart Grid 7th domain a first-class AOB citizen.** Land MCP
   servers, scenarios, and the direct adapter under AOB's namespace so
   downstream researchers can run Smart Grid Bench from a single AOB checkout.
3. **Upstream the orchestration improvements.** PE + Self-Ask, Verified PE,
   and the AaT runner-pair (team `aat_runner` + upstream-parity wrapper)
   solve real gaps in AOB; once cleaned up, these are PR-able to upstream.
4. **Keep the team repo as the active research surface during the paper push.**
   Extraction must not destabilize ongoing experiment captures or block the
   May 6 NeurIPS deadline. Phases 1-3 land in Alex's fork; only Phase 4
   touches the upstream IBM repo.

## Out of scope

- Migrating notebook authoring (`notebooks/`) — those stay in the team repo
  as research artifacts.
- Migrating Slurm/Insomnia operational docs (`docs/runbook.md`,
  `docs/insomnia_runbook.md`) — those are repo-cluster-specific.
- Migrating coordination infrastructure (`docs/coordination/*`,
  `pm/backlog.md`) — team-repo-only.
- Renaming our team-repo cell directories or summary.json schemas.

## Phases

### Phase 0 — Decide design questions (2-3 hr; no code) — **DONE 2026-04-28**

Locked answers in spec § Phase 0 sign-off. Phase 1 may begin.

Original questions (for context):

- Q-NAMING: how do Smart Grid servers integrate alongside AOB's existing
  `src/servers/{fmsr,iot,tsfm,wo,utilities,vibration}/` (which share names
  but are general-purpose)? Options in spec § Design Decisions.
- Q-SCENARIOS: does the team repo's one-scenario-per-file JSON convert to
  AOB's array-of-scenarios format, or do we propose a new convention upstream?
- Q-EVAL-PARITY: what does "parity" mean for retiring
  `scripts/judge_trajectory.py` (per backlog pin b)? Side-by-side scoring on
  N trials at agreement threshold X?
- Q-UPSTREAM-PR-CADENCE: one combined upstream PR or per-phase PRs?
- Q-DHAVAL-COORDINATION: which steps require Dhaval's go-ahead; which are
  pure local refactor work in Alex's fork?

**Acceptance gate:** spec § Design Decisions filled in for all five
questions, signed off (informally) with Dhaval where applicable.

#### Files

- [ ] `docs/plans/aob-extraction_spec.md` — fill out § Design Decisions
- [ ] (Optional) draft Dhaval reply or new Slack message capturing the
  upstream-coordination questions

### Phase 1 — Adopt `feat/evaluation-module`; retire `scripts/judge_trajectory.py` (1-2 days) — **CODE COMPLETE 2026-04-28**

Backlog pin (b). Smallest blast radius; immediate utility.

**Status (2026-04-28):**
- ✅ Feature branch `aob/sg-evaluation-adapter` created in `~/coding/AssetOpsBench`.
- ✅ `feat/evaluation-module` cherry-picked at AOB commit `9661c4d` (pyproject.toml conflict resolved to keep both `src/servers` and `src/evaluation` in wheel).
- ✅ `src/evaluation/adapters/sg_per_trial.py` written + 18 unit tests at AOB commit `328c39b`. Full evaluation suite 57/57 green (39 inherited + 18 new).
- ✅ Smoke test on 6 canonical run dirs: 36/36 trajectories adapted with proper scenario_id, runner, and model identifiers.
- ✅ Static-analysis parity report at `~/coding/AssetOpsBench/src/evaluation/adapters/parity_report.md` (AOB commit `470d745`). Rubric keys identical; aggregate score formulas differ; reconciliation paths captured.
- ⚠️ Live LLM-judge parity run deferred — requires Watsonx or Insomnia access. Adapter + parity-report scaffold are ready; `compute_parity` script is the next follow-up.

**Local-only:** all three AOB-fork commits on `aob/sg-evaluation-adapter`; not pushed to `origin/eggrollofchaos` per user direction.

#### Files

- [x] `~/coding/AssetOpsBench/.git` — fetched `upstream/feat/evaluation-module`
  (tip `fcff318`). Cherry-picked at AOB commit `9661c4d` onto branch
  `aob/sg-evaluation-adapter`.
  - **Acceptance met:** `uv run pytest src/evaluation -q` → 60/60 green
    on branch tip (post-v2 review fixes); `uv run evaluate --help` shows
    the CLI.

- [x] `~/coding/AssetOpsBench/src/evaluation/adapters/sg_per_trial.py` (AOB
  commit `328c39b` + v2 fix `c7bc99e`).
  - **Acceptance met:** 18 unit tests + 3 metrics-integration tests green
    (60/60). Smoke against 6 canonical run dirs adapts 36/36 trajectories.

- [ ] `~/coding/AssetOpsBench/src/evaluation/graders/llm_judge.py` (live
  parity run) — **deferred → D1** in `aob-extraction_deferred.md` (needs
  Watsonx/Insomnia credentials).
  - Static-analysis parity captured in `parity_report.md` at AOB commit
    `470d745`: rubric keys identical; aggregate score formulas diverge
    (team evenly-weighted-6 vs AOB 5+penalty).

- [x] `~/coding/AssetOpsBench/src/evaluation/adapters/parity_report.md`
  (AOB commit `470d745`).
  - **Acceptance met (static):** rubric-key parity verified; aggregate
    formula divergence documented with three reconciliation paths. Live
    LLM-judge parity run remains deferred — see D1.

- [ ] Team repo: `pm/backlog.md`, `CHANGELOG.md` — partially done. AOB
  extraction pin updated (Phase 1 status). Phase 1 CHANGELOG entry will
  land with the team-repo docs PR after v2 review approval.

### Phase 2 — Smart Grid 7th domain into AOB (3-5 days) — **CODE COMPLETE 2026-04-28**

Smart Grid as a first-class AOB domain.

**Status (2026-04-28; updated 2026-04-29 post-v2 review):**
- ✅ Branch `aob/sg-domain-port` rebased onto `aob/sg-evaluation-adapter` post-v2 review consolidation. Original commit `7012e61` reordered as `77ce1c0`; v2 fix `bece2fa` (IEC 60599:2022 + JSON-safe divergent ratios per PR #149) on top.
- ✅ Servers under `src/servers/smart_grid/{iot,fmsr,tsfm,wo}/main.py` + shared `base.py` (env-var `SG_DATA_DIR`). Each has a `def main()` CLI entry. 19 tools total (4/5/4/6 by domain).
- ✅ Direct adapter at `src/servers/smart_grid/direct_adapter.py` (in-process callable registry for Cell A's MCP-overhead-baseline path).
- ✅ Scenarios converted: `src/scenarios/local/smart_grid.json` (11 main) + `src/scenarios/local/smart_grid_negative_checks.json` (5 negative). Both validate via AOB `Scenario.from_raw` on the consolidated branch tip (the `pytest.importorskip("evaluation.models")` guard now resolves).
- ✅ Tests: 25/25 green on the consolidated tip (8 direct-adapter + 5 scenarios + 12 fmsr).
- ✅ `pyproject.toml` entry points: `sg-iot-mcp-server`, `sg-fmsr-mcp-server`, `sg-tsfm-mcp-server`, `sg-wo-mcp-server`.
- ✅ `README.md` updated: Smart Grid 7th-domain add-on documented; cross-link to HPML Smart Grid MCP project for the source data pipeline.
- ⚠️ Processed CSV data files NOT ported (intentional — too large; license / provenance considerations). User must populate `$SG_DATA_DIR` from the HPML team repo's `data/processed/`.
- ⚠️ End-to-end MCP transport smoke (live data + LLM) deferred. Adapter unit tests cover the Python contract; full smoke is a Phase 2 follow-up after Cell C smoke artifact lands in team repo (PR `#134` v4).

**Local-only:** all on `aob/sg-domain-port`; not pushed to `origin/eggrollofchaos`.

#### Files

- [x] `~/coding/AssetOpsBench/src/servers/smart_grid/` (AOB commit
  `7012e61`, rebased to `77ce1c0` after v2 review consolidation; v2 fix
  `bece2fa` adds IEC 60599:2022 + JSON-safe divergent ratios per PR #149).
  Sub-namespace per Q-NAMING decision: `src/servers/smart_grid/{iot,fmsr,tsfm,wo}/`
  with shared `base.py`. Each has `def main()` CLI entry point.
  - **Acceptance met:** `uv run pytest src/servers/smart_grid -q` →
    25/25 green (8 direct-adapter + 5 scenarios + 12 fmsr).

- [x] `~/coding/AssetOpsBench/src/scenarios/local/smart_grid.json` (AOB
  commit `7012e61`/`77ce1c0`). All 11 main scenarios in AOB array format
  per Q-SCENARIOS decision. `aob_fmsr_01_list_failure_modes` included.
  - **Acceptance met:** scenarios validate via AOB `Scenario.from_raw`
    (test gated via `pytest.importorskip("evaluation.models")` until
    consolidated stack ran post-v2; now passes on consolidated tip).

- [x] `~/coding/AssetOpsBench/src/servers/smart_grid/direct_adapter.py`
  (AOB commit `7012e61`/`77ce1c0`). 19-tool in-process callable registry.
  - **Acceptance met:** 8 direct-adapter unit tests green.

- [x] `~/coding/AssetOpsBench/src/scenarios/local/smart_grid_negative_checks.json`
  (AOB commit `7012e61`/`77ce1c0`). 5 negative-check scenarios in AOB
  array format.
  - **Acceptance met:** validates via AOB `Scenario.from_raw`.

- [x] `~/coding/AssetOpsBench/README.md` (AOB commit `7012e61`/`77ce1c0`).
  Smart Grid 7th-domain section added with cross-link back to HPML team
  repo for source data pipeline.

- [ ] Team repo: `docs/orchestration_wiring.md`, `docs/judge_schema.md`,
  `mcp_servers/README.md` — pointer-update pass deferred until upstream
  PR(s) under Phase 4 land. Tracked in this plan; not yet a deferred
  registry entry (will become one only if Phase 4 slips materially).

**Phase 2 deferred items:** processed-CSV data port (D3), live MCP transport
smoke (D4) — both gated on Phase 4 reviewer / paper timing.

### Phase 3 — Upstream the orchestration runners (2-4 days) — **3a+3b+3c CODE COMPLETE 2026-04-30**

Upstream PE + Self-Ask, Verified PE, and the AaT runner-pair to AOB. These
fix real gaps in AOB's orchestration surface.

**Status (2026-04-29; updated 2026-04-29 post-v2 review):**
- ✅ Branch `aob/sg-orchestration-runners` rebased onto `aob/sg-domain-port` post-v2 review consolidation. Original commit `269e9a8` reordered as `0892b92` on top of the consolidated stack.
- ✅ **Phase 3a** — `src/agent/plan_execute/self_ask.py` + `src/agent/plan_execute/self_ask_runner.py`. `SelfAskDecision` dataclass + `maybe_self_ask` + `PlanExecuteSelfAskRunner` subclass. Falls back gracefully on LLM error / malformed JSON.
- ✅ **Phase 3b** — `src/agent/plan_execute/verified.py`. `VerificationDecision` + `verify_step` + `build_retry_question` + `build_suffix_replan_question` + `renumber_plan` + `VerifiedPlanExecuteRunner` subclass. Bounded by `max_replans` + `max_retries_per_step`. Self-Ask pre-pass optional via `enable_self_ask`.
- ✅ **Phase 3c** — `src/agent/openai_agent/runner.py` extended with `parallel_tool_calls` parameter + `run_batch(prompts, trials)` method. MCP servers entered exactly once per batch via `AsyncExitStack`. Per-trial errors captured in new `AgentResult.error` field. Branch `aob/sg-aat-batch-mode` off the consolidated 3a+3b tip (commit `9477bef`).
- ✅ Tests: 45 new (13 Self-Ask + 22 Verified + 9 batch-mode + 1 batch empty-prompts guard for v1 M1). Full agent suite 177/177 green on `aob/sg-aat-batch-mode @ 6872cea` (132 prior + 45 new).
- ⚠️ Smart-Grid-specific repair logic (sensor-task repair, invalid-sensor skip, sensor ID alias map) NOT ported — domain-specific, stays at team-repo customization layer.

**Local-only:** all on `aob/sg-orchestration-runners` (3a+3b) and `aob/sg-aat-batch-mode` (3c); not pushed to `origin/eggrollofchaos`.

#### Files

- [x] `~/coding/AssetOpsBench/src/agent/plan_execute/self_ask.py` +
  `self_ask_runner.py` (AOB commit `269e9a8`, rebased to `0892b92` after
  v2 review consolidation). `SelfAskDecision` + `maybe_self_ask` +
  `PlanExecuteSelfAskRunner` subclass.
  - **Acceptance met:** 13 unit tests green; full agent suite
    (`uv run pytest src/agent -q`) → 167/167 on consolidated tip.

- [x] `~/coding/AssetOpsBench/src/agent/plan_execute/verified.py` (AOB
  commit `269e9a8`/`0892b92`). `VerificationDecision` + `verify_step` +
  `build_retry_question` + `build_suffix_replan_question` + `renumber_plan`
  + `VerifiedPlanExecuteRunner`. Bounded by `max_replans` (default 2) +
  `max_retries_per_step` (default 1).
  - **Acceptance met:** 22 unit tests green.

- [x] `~/coding/AssetOpsBench/src/agent/openai_agent/runner.py` (Phase 3c,
  AOB commits `9477bef` initial port + `6872cea` v1 M1 empty-prompts
  guard, on branch `aob/sg-aat-batch-mode`). Extended
  `OpenAIAgentRunner.__init__` with `parallel_tool_calls` (default
  `False`); added `run_batch(prompts, trials)` method that builds the
  MCP server stack once via `AsyncExitStack` and reuses it across
  every (prompt × trial). Per-trial errors land in the new
  `AgentResult.error` field instead of aborting the batch. `run_batch`
  rejects `trials < 1` and empty `prompts` with `ValueError` before
  starting any MCP server.
  - **Acceptance met:** 10 unit tests in
    `src/agent/openai_agent/tests/test_runner_batch.py` cover the
    constructor knob, `_build_agent` `ModelSettings` plumbing, error
    isolation, server-reuse counts, prompt-major output ordering, and
    both ValueError guards. `uv run pytest src/agent -q` → 177/177
    green.

- [x] `~/coding/AssetOpsBench/src/agent/plan_execute/tests/` (AOB commit
  `269e9a8`/`0892b92`). 35 new tests: 13 Self-Ask + 22 Verified PE.
  - **Acceptance met:** `uv run pytest src/agent -q` → 167/167 green
    (132 inherited + 35 new).

### Phase 4 — Upstream PR(s) to IBM/AssetOpsBench (1-2 weeks; gated on Dhaval)

Once Phases 1-3 are stable in `eggrollofchaos/AssetOpsBench`, prepare upstream
PRs per the cadence decided in Q-UPSTREAM-PR-CADENCE.

#### Files (PR scoping)

- [ ] One PR per phase (recommended): evaluation adapter, Smart Grid domain,
  orchestration runners. Each PR sized for review-cycle health (<2k LOC
  delta where feasible).
- [ ] Or one combined PR if Dhaval prefers: clearly-staged commits within
  the single PR.

**Acceptance gates per PR:**
- Upstream review approval from Dhaval / repo maintainers.
- AOB CI green.
- No regressions in AOB's existing test suite.

## Acceptance gates (cross-phase)

- **Phase 1 → 2:** ✅ parity report (`parity_report.md`) drafted; rubric
  keys identical, aggregate-formula divergence documented with three
  remediation paths. Live LLM-judge κ confirmation deferred → D1; not a
  Phase 2 blocker since Phase 2 is independent code.
- **Phase 2 → 3:** ✅ Smart Grid is a first-class AOB domain; 25/25
  unit tests green on the consolidated stack. End-to-end MCP transport
  smoke deferred → D4; not a Phase 3 blocker since Phase 3 is independent
  code.
- **Phase 3 → 4:** ✅ All three runner types (PE+SA, Verified PE, team-AaT
  batch mode) pass smoke + unit tests (177/177 agent suite) with no
  regression in AOB's existing `OpenAIAgentRunner` / `PlanExecuteRunner`
  paths. Phase 3c landed 2026-04-30 as `aob/sg-aat-batch-mode @ 6872cea`
  (initial port `9477bef` + v1 M1 empty-prompts guard `6872cea`).
  Phase 4 PR scoping per Q-UPSTREAM-PR-CADENCE: hybrid (Phase 1
  standalone, Phases 2+3 combined). 3c can ride with 2+3 in the
  combined upstream PR or split out as its own follow-up.

## Risks

- **Paper-deadline collision.** May 6 NeurIPS submission deadline + paper
  freeze. Phase 2-3 should not start until canonical 5×6 captures are
  complete and Notebook 02/03 finalized. Phase 1 (evaluation adapter) is
  paper-relevant and can run in parallel with capture work.
- **Upstream merge timing.** AOB `feat/evaluation-module` is not yet
  merged to AOB main. Phase 1 either depends on that merge or runs against
  the branch tip until it merges. Spec § "Upstream merge timing" details.
- **Naming collision** (Q-NAMING). AOB already has `src/servers/{fmsr,iot,tsfm,wo}/`
  for general-purpose servers; ours are Smart-Grid-specific implementations
  with the same names. Spec covers three resolution options.
- **Authorship/attribution.** Code authored by team members
  (Aaron, Tanisha, Akshat) needs attribution preserved on extraction.
  Aaron, Tanisha, Akshat must be aware before any extraction PR lands in
  Alex's fork.

## Implementation-Ready Checklist

### Phase 0 — Design decisions

- [x] `docs/plans/aob-extraction_spec.md` § Phase 0 sign-off — Q-NAMING /
  Q-SCENARIOS / Q-EVAL-PARITY / Q-UPSTREAM-PR-CADENCE /
  Q-DHAVAL-COORDINATION all answered. Dhaval ack on Q-DHAVAL-COORDINATION
  remains a Phase 4 prerequisite (not a Phase 0 blocker since Phases 1-3
  are local-only fork work).

### Phase 1 — Evaluation adapter

- [x] `~/coding/AssetOpsBench/aob/sg-evaluation-adapter/src/evaluation/`
  lifted from `feat/evaluation-module` (commit `9661c4d`)
- [x] `src/evaluation/adapters/sg_per_trial.py` written + smoke-tested on 6
  canonical run dirs (commits `328c39b` + v2 fix `c7bc99e`)
- [x] Rubric parity report (`src/evaluation/adapters/parity_report.md`)
  drafted (commit `470d745`); live LLM-judge κ confirmation deferred → D1
- [ ] Team-repo CHANGELOG + `pm/backlog.md` updated — partial; pin updated,
  CHANGELOG entry pending v2 review approval

### Phase 2 — Smart Grid 7th domain

- [x] AOB-side server tree under `src/servers/smart_grid/` (sub-namespace
  per Q-NAMING)
- [x] Scenarios converted to AOB array format
- [x] Direct adapter ported
- [x] AOB README updated; INSTRUCTIONS update deferred to Phase 4 PR pass

### Phase 3 — Orchestration runners

- [x] `PlanExecuteSelfAskRunner` ported with 13 unit tests
- [x] `VerifiedPlanExecuteRunner` ported with 22 unit tests
- [x] Team-AaT runner ported as `OpenAIAgentRunner.run_batch()` method
  (AOB commits `9477bef` + `6872cea` on `aob/sg-aat-batch-mode`).
  10 unit tests + 177/177 full agent suite green. D6 closed.
- [x] Tests ported, all green — 177/177 full agent suite on
  `aob/sg-aat-batch-mode @ 6872cea` (132 prior + 35 PE-family + 9
  batch + 1 batch-empty-guard regression for v1 M1)

### Phase 4 — Upstream PR(s)

- [ ] PR scoping decision (per-phase vs combined) — Q-UPSTREAM-PR-CADENCE
  decision: hybrid (Phase 1 standalone, Phases 2+3 combined)
- [ ] PR(s) opened against `IBM/AssetOpsBench` — gated on Dhaval
  coordination per Q-DHAVAL-COORDINATION
- [ ] Review iterations until merge

## Cross-references

- Companion spec: [aob-extraction_spec.md](aob-extraction_spec.md)
- Backlog pin (b): `pm/backlog.md` 2026-04-27 — `feat/evaluation-module` migration
- Backlog pin (c): resolved in `docs/replay_phase_analysis.md` (separate plan track)
- Live state: `docs/coordination/live_repo_summary.md` § 1 Executive Snapshot
- AOB code dive notes: `docs/orchestration_wiring.md`
- Dhaval coordination: `Final_Project/planning/Dhaval_Email_Thread.md` (personal repo)
