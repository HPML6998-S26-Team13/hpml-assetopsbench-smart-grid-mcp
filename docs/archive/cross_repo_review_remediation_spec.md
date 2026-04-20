# Cross-Repo Review Remediation Spec

## Overview

This spec defines the scope, decision rules, and findings inventory for a consolidated remediation pass across:

- team repo: `/Users/wax/coding/hpml-assetopsbench-smart-grid-mcp`
- personal repo: `/Users/wax/coding/Classes/COMS-E6998/Final Project`

The intent is to avoid piecemeal teammate churn. Findings should be reviewed, deduplicated, and then addressed in one coherent implementation program rather than as scattered one-off fixes.

## Objectives

1. Repair correctness and contract mismatches in the team repo.
2. Fix reproducibility, portability, and security gaps in setup/runbook/runtime flows.
3. Remove contradictory or stale workflow guidance in both repos.
4. Preserve issue history cleanly by documenting which findings affect already-closed issues.
5. Use one reviewed implementation branch/PR in the team repo as the main remediation vehicle.

## Non-Goals

- Rewriting archive docs for style-only reasons.
- Re-opening every related issue immediately before triage is complete.
- Refactoring MCP servers or benchmark systems beyond what the review findings require.
- Turning the personal repo into the canonical execution surface.

## Definitions

- **Org repo `main` branch**: the canonical execution branch in `HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp`.
- **Teammate-portable**: documentation or scripts that do not depend on one person’s username, workstation path, secret-sharing style, or manually inferred environment assumptions. In practice this means:
  - no hard-coded personal filesystem paths
  - no hard-coded personal logins/usernames except as examples with placeholders
  - explicit prerequisites and failure messages
  - clear indication of which values must come from env vars, config, or repo-relative files
- **Remediation matrix**: the deduplicated findings table maintained in this spec during Phase 1 triage.

## Canonical Tool Name Table

These names are the current intended MCP tool contract and should be used as the starting point for Theme A triage unless live server inspection proves otherwise.

| Domain | Canonical tool names |
|---|---|
| FMSR | `fmsr.list_failure_modes`, `fmsr.search_failure_modes`, `fmsr.get_sensor_correlation`, `fmsr.get_dga_record`, `fmsr.analyze_dga` |
| IoT | `iot.list_assets`, `iot.get_asset_metadata`, `iot.list_sensors`, `iot.get_sensor_readings` |
| TSFM | `tsfm.get_rul`, `tsfm.forecast_rul`, `tsfm.detect_anomalies`, `tsfm.trend_analysis` |
| WO | `wo.list_fault_records`, `wo.get_fault_record`, `wo.create_work_order`, `wo.list_work_orders`, `wo.update_work_order`, `wo.estimate_downtime` |

If Phase 1 triage finds a mismatch between this table and the actual live server registrations, update this table first and then treat it as the source of truth for scenario/validator remediation.

## Review Coverage Matrix

### Completed slices

1. **W2 Smart Grid scenario + harness diff**
   - Scope: `780b32b^..eed81fb`
   - Focus: scenario JSONs, validator, `docs/eval_harness_readme.md`, harness smoke script, touched server/data files
   - Counts: 2 Critical / 3 High / 5 Medium / 3 Low

2. **Team repo runtime / ops slice**
   - Files:
     - `scripts/setup_insomnia.sh`
     - `scripts/vllm_serve.sh`
     - `scripts/test_inference.sh`
     - `scripts/verify_watsonx.py`
     - `benchmarks/README.md`
     - `data/README.md`
     - `mcp_servers/README.md`
     - `docs/compute_plan.md`
     - `docs/reference/watsonx_access.md`
   - Counts: 3 Critical / 6 High / 10 Medium / 10 Low

3. **Personal repo live planning/docs slice**
   - Files:
     - `notes/current_team_status.md`
     - `notes/roadmap.md`
     - `notes/2026-04-07_call_prep.md`
     - `notes/2026-04-14_call_prep.md`
     - `notes/mcp_comparison_experiment.md`
     - `notes/task_tracker.md`
     - `notes/task_specs.md`
     - `project_archive/Dhaval_guest_lecture_insights.md`
     - `project_archive/2026-04-01_meeting_notes.md`
   - Counts: 0 Critical / 3 High / 3 Medium / 2 Low
4. **Team repo core code slice**
   - Files:
     - `data/build_processed.py`
     - `data/generate_synthetic.py`
     - `data/scenarios/validate_scenarios.py`
     - `scripts/run_harness_smoke.cmd`
     - `mcp_servers/base.py`
     - `mcp_servers/fmsr_server/server.py`
     - `mcp_servers/iot_server/server.py`
     - `mcp_servers/tsfm_server/server.py`
     - `mcp_servers/wo_server/server.py`
   - Counts: 5 Critical / 7 High / 6 Medium / 7 Low
5. **Team repo live-doc slice**
   - Files:
     - `README.md`
     - `docs/README.md`
     - `docs/reference/project_reference.md`
     - `docs/project_synopsis.md`
     - `docs/repo_strategy.md`
     - `reports/README.md`
   - Counts: 0 Critical / 3 High / 6 Medium / 6 Low
6. **Team repo live-planning slice**
   - Files:
     - `planning/2026-04-07_meeting_notes.md`
     - `planning/2026-04-14_call_agenda.md`
     - `planning/2026-04-14_call_prep.md`
     - `planning/2026-04-21_call_agenda.md`
     - `planning/2026-04-21_call_prep.md`
   - Counts: 1 Critical / 3 High / 8 Medium / 5 Low
7. **Personal repo live-notes slice**
   - Files:
     - `notes/updates_20260409.md`
     - `notes/report_format_mapping.md`
     - `notes/agent_audit.md`
     - `notes/Dhaval_Email_Thread.md`
   - Counts: 5 Critical / 5 High / 7 Medium / 5 Low
8. **Personal repo report-scaffold slice**
   - Files:
     - `resources/report-ieee/main.tex`
     - `resources/report-neurips/main.tex`
   - Counts: 1 Critical / 6 High / 7 Medium / 6 Low

### Remaining planned slices before implementation

- None. Phase 0 review coverage is complete for the planned live surfaces in both repos.
- Explicitly excluded from coverage as non-live / non-actionable for this remediation pass:
  - binary artifacts (`.pdf`, `.pptx`, `.zip`, `.png`, `.jpg`)
  - generated caches (`__pycache__/`, `.DS_Store`)
  - archived docs not used for current execution unless a live doc points to them as current truth

## Source Review Records

- Prompt logs for Claude review runs live under `claude-prompts/` in the repo whose files were reviewed for that slice.
- This spec is the canonical place to lift forward deduplicated Critical/High findings and, during Phase 1, any Medium/Low findings that still matter for implementation.
- Until a finding is lifted into the Remediation Matrix, its source of truth is the completed review slice summary that produced it and this plan/spec pair under `docs/plans/`.
- Aggregate slice totals before deduplication: 17 Critical / 36 High / 52 Medium / 44 Low.
- `mcp_servers/base.py` was reviewed in slice 4 and currently has no deduped Critical/High findings; its open concerns are Medium/Low only and are not gating this remediation pass.
- `scripts/run_harness_smoke.cmd` was reviewed in slice 4; its Critical/High concerns are fully absorbed into F-05, F-08, and F-11, so no standalone row for that file is required.

## Severity by Theme

| Theme | Current severity mix | Notes |
|---|---|---|
| Theme A - Scenario / harness contract correctness | Critical, High, Medium, Low | Scenario metadata, validator rules, multi-domain routing, end-to-end proof expectations |
| Theme B - Data pipeline and server runtime correctness | Critical, High, Medium, Low | Synthetic/processed dataset schema integrity, server behavior, write-path validation |
| Theme C - Serving / setup reproducibility and cluster safety | Critical, High, Medium, Low | Cluster-safe defaults, preconditions, smoke-test fidelity, portability |
| Theme D - Data licensing / redistribution risk | Critical | Public repo safety for processed artifacts and any required history posture |
| Theme E - WatsonX / secret-handling / verification robustness | High, Medium, Low | Verification script behavior, secret hygiene, project instrumentation expectations |
| Theme F - Team repo live docs / planning drift | Critical, High, Medium, Low | README/docs/planning surfaces that encode the wrong execution state or workflow |
| Theme G - Personal repo coordination / audit doc correctness | Critical, High, Medium, Low | Teammate messages, audit prompts, mentor-thread state, stale personal support docs |
| Theme H - Report scaffold / citation build readiness | Critical, High, Medium, Low | LaTeX build prerequisites, bibliography scaffolding, publication-appropriate framing |

## Remediation Matrix

This section is the required Phase 1 triage artifact and is now the canonical deduplicated Critical/High set.

Field conventions:

- **Batch**: `A`, `B`, `C`, `A/C`, `B/C`, `Phase 1 -> A/B/C`, or `N/A` for triage-only / personal-repo sync items.
- **Reconciliation**: closed-issue handling decision when applicable: `reopen`, `keep closed + PR note`, or `N/A`.
- **Reconciliation** may also use `dismissed - <reason>` if Phase 1 confirms a finding is already resolved or not applicable.
- **Issue status**: use issue number + current state; use `no corresponding issue` when the finding is not yet represented on the team board.
- **Resolution path**: brief fix approach or explicit no-op rationale, for example:
  - `rename expected_tools to match verified server registrations`
  - `bind vLLM to loopback and add precondition checks`
  - `no code change needed — Theme D policy is docs-only clarification`

| Finding ID | Theme | Severity | Affected files | GitHub issue(s) | Issue status | Reconciliation | Batch | Resolution path |
|---|---|---|---|---|---|---|---|---|
| F-01 | A | Critical | `data/scenarios/*.json` | `#3`, `#4`, `#16`, `#18` | `#3 Open; #4 Closed; #16 Closed; #18 Open` | `#4 keep closed + PR note; #16 reopen` | `A (provisional — confirm after Phase 1 tool-name verification)` | Rename scenario `expected_tools` to the verified live server tool names. |
| F-02 | A | Critical | `data/scenarios/validate_scenarios.py`, `data/scenarios/*.json` | `#16`, `#17`, `#18` | `#16 Closed; #17 Open; #18 Open` | `#16 reopen` | `A (provisional — confirm after Phase 1 tool-name verification)` | Upgrade validator to require `expected_tools`, reject empty type strings, validate multi-domain `domain_tags` consistency, and define committed negative-check fixtures for the contract cases it enforces. |
| F-03 | D | Critical | `data/README.md`, `data/build_processed.py`, `data/generate_synthetic.py`, `data/processed/*` | no corresponding issue | `no corresponding issue` | N/A | `Phase 1 -> C` | Phase 1: inventory tracked processed files, decide docs-only vs regenerate vs untrack, and record whether history purge is required or explicitly out of scope. Batch C: implement the chosen policy outcome. |
| F-04 | C | Critical | `scripts/vllm_serve.sh` | `#6`, `#37` | `#6 Open; #37 Open` | N/A | B | Bind vLLM to a safer interface or otherwise close the shared-cluster exposure by default. |
| F-05 | C | Critical | `scripts/setup_insomnia.sh`, `scripts/vllm_serve.sh` | `#6`, `#8`, `#37` | `#6 Open; #8 Open; #37 Open` | N/A | B | Ensure `logs/` exists before SLURM output is referenced, require key env vars including at minimum `HF_TOKEN`, and fail clearly if required directories or env preconditions are absent; implement together with F-11 in one serve-time precondition block. |
| F-06 | C | High | `scripts/setup_insomnia.sh` | `#6`, `#8` | `#6 Open; #8 Open` | N/A | B | Pin Python dependency versions used by the Insomnia setup path. |
| F-07 | C | High | `scripts/setup_insomnia.sh` | `#6`, `#8` | `#6 Open; #8 Open` | N/A | B | Pin the model revision/checkpoint used for server bring-up so later runs are reproducible. |
| F-08 | C | High | `scripts/test_inference.sh` | `#6`, `#57` | `#6 Open; #57 Closed` | `#57 keep closed + PR note` | B | Align model selection with the serve path and only report success on validated non-error responses. |
| F-09 | C | High | `docs/compute_plan.md` | `#6`, `#8`, `#37` | `#6 Open; #8 Open; #37 Open` | N/A | C | Remove stale scheduler assumptions, dead references, and teammate-specific examples from compute guidance. |
| F-10 | E | High | `scripts/verify_watsonx.py`, `docs/reference/watsonx_access.md` | `#19`, `#21` | `#19 Open; #21 Open` | N/A | B/C | Document a concrete shared-project / key-rotation workflow and make the verification tool safe to run/share. |
| F-11 | C | High | `scripts/vllm_serve.sh` | `#6`, `#8`, `#37` | `#6 Open; #8 Open; #37 Open` | N/A | B | Add explicit precondition checks for venv, model path, and related serve-time assumptions; implement together with F-05 in one serve-time precondition block. |
| F-12 | C | High | `docs/eval_harness_readme.md` | `#57`, `#37` | `#57 Closed; #37 Open` | `#57 keep closed + PR note` | C | Replace Akshat-local paths with teammate-portable instructions and canonical proof expectations. |
| F-13 | B | Critical | `mcp_servers/iot_server/server.py` | `#9`, `#58` | `#9 Open; #58 Open` | N/A | A | Fix `get_sensor_readings` timestamp serialization so non-empty responses do not crash. |
| F-14 | B | Critical | `data/generate_synthetic.py`, `mcp_servers/fmsr_server/server.py` | `#11`, `#58` | `#11 Open; #58 Open` | N/A | A | Align synthetic `failure_modes.csv` with the FMSR server's expected schema. |
| F-15 | B | Critical | `data/generate_synthetic.py`, `mcp_servers/iot_server/server.py` | `#9`, `#58` | `#9 Open; #58 Open` | N/A | A | Add the synthetic asset metadata fields needed by IoT server reads (`rul_days`, related compatibility fields). |
| F-16 | B | Critical | `data/generate_synthetic.py`, `mcp_servers/tsfm_server/server.py` | `#10`, `#58` | `#10 Open; #58 Open` | N/A | A | Add the synthetic RUL fields TSFM expects, including `fdd_category` compatibility. Implement together with F-17 in one RUL-generation pass. |
| F-17 | B | High | `data/generate_synthetic.py` | `#10` | `#10 Open` | N/A | A | Make synthetic RUL trajectories monotonic / physically plausible instead of re-sampling per-day degradation. Implement together with F-16 in one RUL-generation pass. |
| F-18 | B | High | `data/generate_synthetic.py`, `mcp_servers/wo_server/server.py` | `#12`, `#58` | `#12 Open; #58 Open` | N/A | A | Align synthetic fault-record schema with WO expectations and enforce transformer referential integrity on work-order creation. |
| F-19 | B | High | `data/build_processed.py` | `#11` | `#11 Open` | N/A | A | Replace brittle/possibly misleading processed-data assumptions: stop silently zeroing CO/CO2 and guard raw/Kaggle column expectations. |
| F-20 | B | High | `mcp_servers/fmsr_server/server.py` | `#11`, `#58` | `#11 Open; #58 Open` | N/A | A | Reject invalid negative gas concentrations rather than returning misleading Rogers-ratio outputs. |
| F-21 | F | High | `README.md`, `docs/README.md`, `docs/reference/project_reference.md`, `docs/project_synopsis.md`, `docs/repo_strategy.md`, `reports/README.md`, `benchmarks/README.md`, `mcp_servers/README.md` | no corresponding issue | `no corresponding issue — review-surfaced team-repo doc/planning drift that was never represented as a standalone issue` | N/A | A/C | Repair repo-level onboarding drift: remote naming, empty experiment instructions, malformed tree lines, stale doc-routing guidance, and missing benchmark/server-composition guidance. Note: the `mcp_servers/README.md` portion is handled alongside Batch A contract cleanup; the rest stays in Batch C. |
| F-22 | F | Critical | `planning/2026-04-07_meeting_notes.md`, `planning/2026-04-14_call_agenda.md`, `planning/2026-04-14_call_prep.md`, `planning/2026-04-21_call_agenda.md`, `planning/2026-04-21_call_prep.md` | no corresponding issue | `no corresponding issue — live team planning drift surfaced during review, not previously tracked on the board` | N/A | C | Update live planning docs so they encode the correct execution state, Tier-1 fallback gate, and explicit artifact-based acceptance criteria. |
| F-23 | G | High | `/Users/wax/coding/Classes/COMS-E6998/Final Project/notes/2026-04-07_call_prep.md` | no corresponding issue | `no corresponding issue — personal-repo support doc drift only` | N/A | N/A | Remove stale framing that still treats PS B as unresolved stretch work after the Apr 7 decisions. |
| F-24 | G | High | `/Users/wax/coding/Classes/COMS-E6998/Final Project/notes/2026-04-14_call_prep.md` | no corresponding issue | `no corresponding issue — personal-repo support doc drift only` | N/A | N/A | Replace archived tracker references with the canonical GitHub Project and current team-repo sources. |
| F-25 | G | High | `/Users/wax/coding/Classes/COMS-E6998/Final Project/notes/task_specs.md` | no corresponding issue | `no corresponding issue — personal-repo historical/supporting doc drift only` | N/A | N/A | Correct issue-number drift (`#68` vs `#55`) and any duplicated or stale IDs. |
| F-26 | G | Critical | `/Users/wax/coding/Classes/COMS-E6998/Final Project/notes/updates_20260409.md` | no corresponding issue | `no corresponding issue — outgoing teammate-draft note in personal repo` | N/A | N/A | Remove unsafe/incomplete teammate instructions, especially the wrong `reset --hard` guidance and unfinished message fragments. |
| F-27 | G | Critical | `/Users/wax/coding/Classes/COMS-E6998/Final Project/notes/agent_audit.md` | no corresponding issue | `no corresponding issue — personal-repo audit/support surface only` | N/A | N/A | Fix broken file paths, stale repo path assumptions, and missing scope in the audit prompt so it can actually execute. |
| F-28 | G | High | `/Users/wax/coding/Classes/COMS-E6998/Final Project/notes/Dhaval_Email_Thread.md` | `#63` | `#63 Open` | N/A | N/A | Mark still-pending mentor questions explicitly and label unconfirmed NeurIPS dates as unverified until externally checked. |
| F-29 | G | High | `/Users/wax/coding/Classes/COMS-E6998/Final Project/notes/report_format_mapping.md` | no corresponding issue | `no corresponding issue — personal-repo report-support doc drift only` | N/A | N/A | Fix stale paths and specify how shared NeurIPS/IEEE sections should actually split during back-porting. |
| F-30 | H | Critical | `/Users/wax/coding/Classes/COMS-E6998/Final Project/resources/report-neurips/main.tex` | no corresponding issue | `no corresponding issue — personal-repo report scaffold only` | N/A | N/A | Add the required NeurIPS style file (or documented manual prerequisite) so the scaffold actually compiles. |
| F-31 | H | High | `/Users/wax/coding/Classes/COMS-E6998/Final Project/resources/report-ieee/main.tex`, `/Users/wax/coding/Classes/COMS-E6998/Final Project/resources/report-neurips/main.tex` | no corresponding issue | `no corresponding issue — personal-repo report scaffold only` | N/A | N/A | Repair citation/bibliography scaffolding: real cite keys, no TODO bibitems, correct bibliography style, and a stable BibTeX path. |
| F-32 | H | High | `/Users/wax/coding/Classes/COMS-E6998/Final Project/resources/report-ieee/main.tex` | no corresponding issue | `no corresponding issue — personal-repo report scaffold only` | N/A | N/A | Rename the IEEE \"Training and Profiling Methodology\" framing so the scaffold reflects inference/profiling rather than nonexistent training work. |

### Theme A - Scenario / harness contract correctness

Key issues:

- scenario `expected_tools` entries do not match the live MCP tool registrations
- validator under-validates the contract and lets false-green scenarios through
- multi-domain routing and proof expectations are underspecified

Primary affected files:

- `data/scenarios/*.json`
- `data/scenarios/validate_scenarios.py`
- `docs/eval_harness_readme.md`

Primary affected issues:

- `#3`, `#4`, `#16`, `#17`, `#18`

Decision:

- Treat the live server registrations as the contract unless triage finds a compelling reason to rename server tools instead.
- Reopen `#16` before implementation; keep `#4` closed and document the follow-up in the remediation PR.

### Theme B - Data pipeline and server runtime correctness

Key issues:

- synthetic datasets do not currently satisfy several server expectations
- one IoT read path is outright broken at runtime
- processed-data generation contains brittle or misleading assumptions
- write paths do not enforce enough referential validity

Primary affected files:

- `data/build_processed.py`
- `data/generate_synthetic.py`
- `mcp_servers/iot_server/server.py`
- `mcp_servers/fmsr_server/server.py`
- `mcp_servers/tsfm_server/server.py`
- `mcp_servers/wo_server/server.py`

Primary affected issues:

- `#9`, `#10`, `#11`, `#12`, `#58`

Decision:

- Keep these fixes in Batch A so the entire benchmark/MCP path is internally consistent before docs and experiment claims are tightened.

### Theme C - Serving / setup reproducibility and cluster safety

Key issues:

- unsafe serving defaults on a shared cluster
- missing job/logging preconditions
- floating dependency/model versions
- smoke-test scripts that can pass without proving a correct response
- local-path runbooks and missing precondition checks

Primary affected files:

- `scripts/setup_insomnia.sh`
- `scripts/vllm_serve.sh`
- `scripts/test_inference.sh`
- `docs/compute_plan.md`
- `docs/eval_harness_readme.md`

Primary affected issues:

- `#6`, `#8`, `#37`, `#57`

Decision:

- Default to safe-by-default cluster behavior and teammate-portable runbooks.
- Keep `#57` closed and attach the remediation PR as a follow-up note rather than reopening it.

### Theme D - Data licensing / redistribution risk

Key issues:

- tracked processed CSVs may derive from restricted-license source datasets in a public repo

Primary affected files:

- `data/README.md`
- `data/build_processed.py`
- `data/generate_synthetic.py`
- tracked `data/processed/*`

Primary affected issues:

- no clean existing issue; treat as remediation-program scope unless a dedicated follow-up issue is created during implementation

Decision:

- This is a policy gate, not a docs nit.
- Phase 1 must record one of four explicit outcomes: `docs-only clarification`, `regenerate public-safe outputs`, `remove/untrack restricted-derived artifacts`, or `confirmed not restricted / no remediation needed`.
- `confirmed not restricted / no remediation needed` requires citing the specific source-dataset license or instructor-approved policy basis in the Theme D triage entry.
- Phase 1 must also record whether git-history purge is required or explicitly out of scope with rationale.

### Theme E - WatsonX / secret-handling / verification robustness

Key issues:

- shared-key/rotation workflow is under-specified
- verification tooling can mislead or leak too much detail
- WandB/verification expectations need to match the actual team workflow

Primary affected files:

- `scripts/verify_watsonx.py`
- `docs/reference/watsonx_access.md`

Primary affected issues:

- `#19`, `#21`

Decision:

- Verification tooling must be safe to share in logs/issues and must not overstate benchmark meaning.

### Theme F - Team repo live docs / planning drift

Key issues:

- repo-level onboarding and planning docs still contain malformed or stale workflow guidance
- the Apr 21 call agenda currently has no Tier 1 fallback gate
- Aaron's serving-acceptance artifact is still under-specified in live planning docs

Primary affected files:

- `README.md`
- `docs/README.md`
- `docs/reference/project_reference.md`
- `docs/project_synopsis.md`
- `docs/repo_strategy.md`
- `reports/README.md`
- `planning/2026-04-07_meeting_notes.md`
- `planning/2026-04-14_call_agenda.md`
- `planning/2026-04-14_call_prep.md`
- `planning/2026-04-21_call_agenda.md`
- `planning/2026-04-21_call_prep.md`

Primary affected issues:

- mostly indirect; no existing single GitHub issue cleanly represents this cluster

Decision:

- Fix these in the same remediation branch as the code changes so the live docs and planning surfaces reflect the corrected implementation and current execution state.

### Theme G - Personal repo coordination / audit doc correctness

Key issues:

- teammate-update notes contain unsafe or incomplete instructions
- the audit prompt currently references nonexistent files and incomplete scope
- mentor-thread state and pending questions are not clearly represented
- personal support docs still carry stale tracker/workflow assumptions

Primary affected files:

- `/Users/wax/coding/Classes/COMS-E6998/Final Project/notes/updates_20260409.md`
- `/Users/wax/coding/Classes/COMS-E6998/Final Project/notes/agent_audit.md`
- `/Users/wax/coding/Classes/COMS-E6998/Final Project/notes/Dhaval_Email_Thread.md`
- `/Users/wax/coding/Classes/COMS-E6998/Final Project/notes/2026-04-07_call_prep.md`
- `/Users/wax/coding/Classes/COMS-E6998/Final Project/notes/2026-04-14_call_prep.md`
- `/Users/wax/coding/Classes/COMS-E6998/Final Project/notes/task_specs.md`
- `/Users/wax/coding/Classes/COMS-E6998/Final Project/notes/report_format_mapping.md`

Primary affected issues:

- `#63` is indirectly relevant for mentor-question follow-through; most findings here are personal-repo-only and have no corresponding GitHub issue

Decision:

- These remain Phase 4 work so the personal repo is synced after the canonical team-repo remediation has merged and the references are stable.

### Theme H - Report scaffold / citation build readiness

Key issues:

- NeurIPS scaffold cannot compile without the required style file
- bibliography/citation scaffolding is incomplete or malformed
- IEEE scaffold still frames the work as training rather than inference/profiling

Primary affected files:

- `/Users/wax/coding/Classes/COMS-E6998/Final Project/resources/report-ieee/main.tex`
- `/Users/wax/coding/Classes/COMS-E6998/Final Project/resources/report-neurips/main.tex`

Primary affected issues:

- no corresponding GitHub issue; these are personal-repo/report-pipeline surfaces

Decision:

- Keep these in Phase 4 unless the team decides the report scaffolds should move into the canonical repo later.

## Closed-Issue Reconciliation

The following already-closed issues are currently implicated by review findings:

- `#4` - initial scenario batch landed, but follow-up corrections are still required
- `#16` - validator closure is contradicted by the false-green contract review
- `#57` - harness/runbook replay landed, but follow-up portability fixes are still required

Reconciliation rule:

1. `#16` should be reopened before implementation because the finding directly contradicts the issue's stated completion condition.
2. `#4` should stay closed, with a remediation-PR note documenting the follow-up contract fixes.
3. `#57` should stay closed, with a remediation-PR note documenting the portability cleanup.
4. Any additional closed issue discovered during implementation should be handled using the same explicit `reopen` vs `keep closed + PR note` rule.

## Implementation Topology

Because this work spans two repos, one PR cannot carry the entire remediation.

### Team repo

- Implementation will happen on a dedicated branch and PR created from the team repo `main` branch after this plan/spec pair is finalized.
- `claude-pr-review` is the gate for merge.
- This is the canonical remediation artifact.

### Personal repo

- Sync after the team repo remediation has merged.
- Review with `claude-review` unless a real PR is also created for that repo.
- Personal repo edits should not get ahead of the canonical team repo fixes they reference.

## Issue Follow-Through Format

Use one consistent post-merge issue-comment format:

`Fixed in PR #<number>. <One sentence on what changed>.`

If a previously closed issue stays closed rather than being reopened, use:

`Follow-up completed in PR #<number>. <One sentence on what changed>.`

If a previously closed issue is reopened and then resolved in the remediation pass, use:

`Reopened and resolved in PR #<number>. <One sentence on what changed>.`

When one remediation finding touches multiple issues, post a separate short follow-up comment to each affected issue rather than one omnibus note.

## Spec Lifecycle

- This spec stays active through discovery, triage, implementation, and PR review.
- Once the remediation PR is merged and the personal repo sync is complete, archive this spec together with the plan under `docs/archive/` and move any durable operating rules into the appropriate live docs/reference surfaces.

## Verification Expectations

### Team repo

- scenario validator passes on the corrected scenario set and fails on committed negative-check fixtures covering at least tool-name mismatches and multi-domain routing validation
- serving/setup scripts fail clearly on missing prerequisites
- if cluster execution is unavailable, the assertion-only verification path for `scripts/vllm_serve.sh` is acceptable only if the remediation PR body explicitly notes that unavailability
- smoke-test scripts validate real success, defined as HTTP 200 with no `error` field and a non-empty completion payload in the expected response shape
- server-level checks pass: IoT `get_sensor_readings` returns a non-empty serialized response, FMSR rejects invalid negative gas concentrations with a structured error, and TSFM `get_rul` returns non-null `rul_days` with confidence in `[0.0, 1.0]` for valid input while rejecting out-of-range input with a structured error
- doc examples use portable paths/placeholders
- any data-license mitigation is demonstrably safe for the public repo, including an explicit statement on whether git-history purge is required or out of scope, and if the chosen path is `regenerate public-safe outputs` the regenerated files are the ones actually committed under `data/processed/`
- repo-level onboarding docs (`README.md`, `docs/README.md`, and related F-21 surfaces) reflect the corrected canonical org-repo workflow
- planning docs and repo-level docs no longer encode the wrong execution state or acceptance criteria for W3/W4 work
- a passing WatsonX verification run returns a non-empty completion for a prompted request and does not print secret values at any log level

### Personal repo

- no live doc contradicts canonical repo/task-system reality
- any historical tracker/spec remains clearly marked as historical/supporting
- teammate-update and audit notes contain only executable commands/paths
- report scaffolds either compile with their required style assets present or explicitly document the missing manual prerequisite and bibliography workflow

## Review Decisions

### 2026-04-09 / 2026-04-10

- Prefer one consolidated remediation pass over repeated teammate-by-teammate patching.
- Save findings first; do not begin implementation until the cross-repo plan/spec is reviewed.
- Use the team repo PR as the primary reviewed artifact; sync the personal repo deliberately afterward.
- Review coverage is complete across the planned live surfaces in both repos; remaining work is triage, remediation planning, and later implementation.
