# Cross-Repo Review Remediation Plan

## Goal

Run a single, consolidated remediation cycle for the HPML SmartGridBench project across:

- the team repo: `/Users/wax/coding/hpml-assetopsbench-smart-grid-mcp`
- the personal planning repo: `/Users/wax/coding/Classes/COMS-E6998/Final Project`

The objective is to:

1. finish bounded review coverage across code and live docs in both repos
2. triage and cross-reference the findings against current GitHub issues/statuses
3. implement the fixes in one coherent branch-based pass rather than asking teammates to patch the same area repeatedly
4. run `claude-pr-review` on the implementation PR until no Critical/High findings remain
5. update affected GitHub issues with short resolution notes and PR links after merge

## Current Review Baseline

Completed review slices so far:

1. W2 Smart Grid scenario + harness diff (`780b32b^..eed81fb`)
   - `docs/eval_harness_readme.md`
2. Team repo runtime / ops slice
   - `scripts/setup_insomnia.sh`
   - `scripts/vllm_serve.sh`
   - `scripts/test_inference.sh`
   - `scripts/verify_watsonx.py`
   - `benchmarks/README.md`
   - `data/README.md`
   - `mcp_servers/README.md`
   - `docs/compute_plan.md`
   - `docs/watsonx_access.md`
3. Personal repo live planning/docs slice
   - `notes/current_team_status.md`
   - `notes/roadmap.md`
   - `notes/2026-04-07_call_prep.md`
   - `notes/2026-04-14_call_prep.md`
   - `notes/mcp_comparison_experiment.md`
   - `notes/task_tracker.md`
   - `notes/task_specs.md`
   - `project_archive/Dhaval_guest_lecture_insights.md`
   - `project_archive/2026-04-01_meeting_notes.md`
4. Team repo core code slice
   - `data/build_processed.py`
   - `data/generate_synthetic.py`
   - `data/scenarios/validate_scenarios.py`
   - `scripts/run_harness_smoke.cmd`
   - `mcp_servers/base.py`
   - `mcp_servers/fmsr_server/server.py`
   - `mcp_servers/iot_server/server.py`
   - `mcp_servers/tsfm_server/server.py`
   - `mcp_servers/wo_server/server.py`
5. Team repo live-doc slice
   - `README.md`
   - `docs/README.md`
   - `docs/project_reference.md`
   - `docs/project_synopsis.md`
   - `docs/repo_strategy.md`
   - `reports/README.md`
6. Team repo live-planning slice
   - `planning/2026-04-07_meeting_notes.md`
   - `planning/2026-04-14_call_agenda.md`
   - `planning/2026-04-14_call_prep.md`
   - `planning/2026-04-21_call_agenda.md`
   - `planning/2026-04-21_call_prep.md`
7. Personal repo live-notes slice
   - `notes/updates_20260409.md`
   - `notes/report_format_mapping.md`
   - `notes/agent_audit.md`
   - `notes/Dhaval_Email_Thread.md`
8. Personal repo report-scaffold slice
   - `resources/report-ieee/main.tex`
   - `resources/report-neurips/main.tex`

Current aggregated finding counts from those completed slices, before Phase 1 deduplication:

- Critical: 17
- High: 36
- Medium: 52
- Low: 44

These findings are saved in the companion spec and should be treated as open until triage/reconciliation says otherwise.

## Phase 0 - Finish Review Coverage

Review coverage is now complete for the planned high-signal surfaces across both repos. Phase 0 is closed, and the remaining work is to deduplicate, map, and batch the findings cleanly before implementation.

### Phase 0 output

- The spec's Review Coverage Matrix should list all eight completed slices with their severity counts.
- Any file still not cleanly covered by one of those slices must be called out explicitly in the spec before implementation begins.

### Acceptance Gate - Review Coverage Complete

- All live code in the team repo has been reviewed in at least one bounded slice, specifically everything under:
  - `scripts/`
  - `mcp_servers/*/server.py`
  - `data/*.py`
  - `data/scenarios/validate_scenarios.py`
- All live docs used for current execution/planning in both repos have been reviewed in at least one bounded slice.
- Findings from each completed slice are captured in the companion spec.

## Phase 1 - Triage and Cross-Reference

Consolidate the review findings into one remediation matrix.

### Required outputs

1. Deduplicate overlapping findings across slices.
2. Cross-reference each finding to:
   - affected repo
   - affected file(s)
   - existing GitHub issue(s), if any
   - current issue status (`Open` / `Closed`)
3. Identify closed issues that must be reopened or superseded by a follow-up issue.
4. Split findings into implementation batches:
   - contract/correctness blockers
   - reproducibility/security blockers
   - doc drift / stale guidance
   - lower-priority polish
5. Record the remediation matrix in the companion spec under a dedicated `Remediation Matrix` section so the triage output has one canonical home.

### Acceptance Gate - Triage Complete

- Canonical Tool Name Table has been verified against live `mcp_servers/*/server.py` registrations and corrected in the spec if needed.
- Every Critical/High finding has an explicit target file set and issue mapping.
- Theme D has an explicit policy/action decision:
  - docs-only clarification, or
  - regenerated public-safe outputs, or
  - removal/untracking of restricted-derived artifacts
  - confirmed not restricted / no remediation needed
  - plus an explicit decision on whether git-history purge is required or intentionally out of scope
- No finding is left as “someone should check this.”
- Every Critical/High finding has either a corresponding GitHub issue mapping or an explicit `no corresponding issue` note with rationale in the matrix row or corresponding theme section.
- Every affected closed issue has a recorded reconciliation decision (`reopen` or `keep closed + PR note`) before implementation begins.
- Phase 1 plan/spec updates should land on this planning branch and merge to the org repo `main` branch before the Phase 2 implementation branch is created from `main`.
- Phase 2 implementation must not begin until all Phase 1 checklist items are complete and this acceptance gate is fully met.

## Phase 2 - Team Repo Implementation Branch

Implement the consolidated fixes in one dedicated team-repo branch.

### Batch A - Scenario / contract correctness and data/server runtime correctness

Target problems:

- scenario `expected_tools` mismatching real MCP tool names
- validator false-greens on tool names and schema consistency
- multi-domain routing ambiguity
- benchmark proof requirements clarified where current issues rely on evidence
- synthetic dataset fields missing or incompatible with server expectations
- server-side crash/correctness bugs in the MCP implementations
- brittle or misleading processed-data assumptions in the data pipeline
- write paths with insufficient referential validation

### Batch B - Serving / ops reproducibility and safety

Target problems:

- unsafe or non-portable serving defaults
- missing precondition checks
- non-reproducible dependency/model installs
- invalid or misleading smoke-test success criteria
- missing portability in runbooks and compute instructions
- WatsonX verification robustness issues

### Batch C - Team repo live docs and planning surfaces

Target problems:

- stale or contradictory usage guidance
- portability gaps
- dead file references
- missing service-composition details
- licensing/redist documentation gaps
- planning surfaces that still encode the wrong execution state or acceptance criteria

Recommended sequence inside Phase 2:

1. Batch A first, because tool-name and contract decisions feed downstream docs.
2. Batch B second, because the serve path, verification tooling, and setup scripts need to be stable before doc cleanup and final planning surfaces are updated.
3. Batch C third, so docs and planning surfaces reflect the corrected implementation, contract names, and current execution state.
4. If any server-specific fix requires matching changes in `mcp_servers/base.py`, that shared helper is in scope under the same Batch A checklist item rather than as a separate remediation stream.

### Acceptance Gate - Team Repo Changes Ready

- Scenario files and validator agree with the actual server contract.
- Serving/verification scripts fail clearly on bad setup rather than silently or cryptically.
- Reproduction docs are teammate-portable and do not depend on one user’s machine paths.
- If Theme D requires removal/untracking, `git ls-files data/processed/` no longer lists restricted-derived tracked files after Batch C and `git check-ignore` confirms the ignore rule covers the removed path. If Theme D requires regenerated public-safe outputs, `git ls-files data/processed/` shows only the newly generated public-safe files after Batch C. If Theme D is confirmed clean or docs-only, that decision is explicitly recorded in the spec and PR body.
- Concrete verification passes for the touched team-repo changes:
  - corrected synthetic/processed data satisfies the upgraded validator and server expectations across the MCP stack, including a non-empty IoT sensor-reading path and FMSR rejection of invalid negative gas concentrations
  - `mcp_servers/tsfm_server/server.py` handles a valid `get_rul` call with a non-null `rul_days` result and rejects out-of-range inputs with a structured error
  - `python3 data/scenarios/validate_scenarios.py` passes on the corrected scenario set and fails on committed negative-check fixtures
  - `scripts/setup_insomnia.sh` fails non-zero with a clear message when `HF_TOKEN` is unset or empty
  - `scripts/setup_insomnia.sh` uses pinned dependency versions and an explicit pinned model revision/checkpoint
  - `scripts/vllm_serve.sh` fails non-zero with a clear message when the expected venv or model directory is missing, and it auto-creates `logs/` before referencing SLURM output paths, verified either by a local dry-run with deliberately broken preconditions or by asserting the concrete guard expressions in the modified script when cluster execution is unavailable, with that unavailability explicitly noted in the remediation PR body
  - `scripts/test_inference.sh` rejects invalid/error JSON and only reports success on a real inference response
  - `scripts/verify_watsonx.py` does not print secret values at any log level, correctly parses quoted `.env` values, returns a non-empty completion for a passing verification request, and clearly caveats benchmark measurements

## Phase 3 - Review, Merge, and Issue Closure

### Team repo

1. Open a PR from the remediation branch.
2. Run `claude-pr-review` iteratively until no Critical/High findings remain.
3. Merge, sync local root `main`, and clean up the branch.

### Personal repo handoff to Phase 4

1. In Phase 4, review the diff with `claude-review` (or PR review if a PR is created for that repo).
2. Merge/sync only after the team repo remediation PR has merged into the team repo `main`.

### GitHub issue follow-through

After merge:

- add short issue comments describing what changed
- include the PR link
- reopen previously closed issues if the remediation demonstrates they were closed too early, or leave them closed and document that the follow-up was completed in the remediation PR if that is cleaner
- for `#16`, which Phase 1 already schedules for reopening, post the resolution comment and close the issue after merge if the remediation fully addresses the validator finding

### Acceptance Gate - Phase 3 Complete

- Team repo remediation PR is merged after a clean final Claude PR review pass with no Critical/High findings.
- CI checks are green, or the absence of automated CI is explicitly documented in the remediation PR body.
- If Theme D policy requires git-history purge, the remediation PR body explicitly records that the merged PR only performs forward-state cleanup and hands off the history rewrite to a separate approved flow.
- Affected issues have brief closure/follow-up comments with PR links.

## Phase 4 - Personal Repo Sync

Update the personal repo only after the team repo remediation PR has passed the final clean review pass and merged.

### Scope

- Remove stale workflow language that contradicts the canonical org repo / GitHub Projects model.
- Mark local tracker/spec references as historical/supporting, not execution-authoritative.
- Sync current-team-status and roadmap language to the post-Apr 7 decisions.
- Keep archive docs as archive docs; annotate them only when needed to prevent obvious factual drift.

### Acceptance Gate - Personal Repo Sync Complete

- No live personal-repo doc contradicts the team repo’s canonical execution model.
- Local helper docs correctly point back to the canonical team repo `main` branch and GitHub Project when appropriate.
- F-26 is resolved: the teammate-update note contains no unsafe or incomplete git instructions.
- F-27 is resolved: the audit prompt references valid file paths and has complete executable scope.
- F-30 is resolved: the NeurIPS scaffold either includes the required style file or explicitly documents the missing manual prerequisite.

## Risks / Preconditions

- The two repos cannot be remediated by one PR; the plan must keep the team repo as the gated implementation center and sync the personal repo deliberately afterward.
- Findings that touch already-closed issues must be triaged carefully to avoid misleading board history.
- The restricted-data finding in `data/README.md` may require a policy decision, not just a code edit.

## Implementation-Ready Checklist

### Phase 0 - Coverage completion

- [x] `docs/plans/cross_repo_review_remediation.md`
  Task: keep the plan updated as remaining review slices are completed and triage decisions are made.
  Acceptance: plan reflects completed vs pending slices accurately.

- [x] `docs/plans/cross_repo_review_remediation_spec.md`
  Task: maintain the canonical findings inventory, issue cross-reference table, and remediation decisions.
  Acceptance: all Critical/High findings from every completed slice appear in the spec with deduped wording.

- [x] `data/build_processed.py`, `data/generate_synthetic.py`, `data/scenarios/validate_scenarios.py`, `mcp_servers/fmsr_server/server.py`, `mcp_servers/iot_server/server.py`, `mcp_servers/tsfm_server/server.py`, `mcp_servers/wo_server/server.py`, `docs/eval_harness_readme.md`
  Task: explicitly map each of these files to a completed review slice or add a final bounded coverage pass for any file not yet cleanly covered.
  Acceptance: the spec's coverage matrix names the completed or pending slice for each listed file before Phase 0 is closed.

- [x] `README.md`
  Task: review for contradictions with current canonical repo/task workflow.
  Acceptance: any drift findings are captured in the spec before implementation starts.

- [x] `docs/README.md`
  Task: review for stale references and doc-routing problems.
  Acceptance: any drift findings are captured in the spec before implementation starts.

- [x] `docs/project_reference.md`
  Task: review for stale references, wrong counts, or obsolete workflow assumptions.
  Acceptance: spec captures any contradictions or confirms the file is consistent.

- [x] `docs/project_synopsis.md`
  Task: review current positioning, milestone framing, and repo/workflow references.
  Acceptance: spec captures any contradictions or confirms the file is consistent.

- [x] `docs/repo_strategy.md`
  Task: review current repo/canonical-branch guidance against actual org-repo workflow.
  Acceptance: spec captures any contradictions or confirms the file is consistent.

- [x] `reports/README.md`
  Task: review report artifact guidance for stale assumptions.
  Acceptance: spec captures any contradictions or confirms the file is consistent.

- [x] `planning/2026-04-07_meeting_notes.md`
  Task: review final meeting notes for contradictions with current decisions/issue mapping.
  Acceptance: spec captures any contradictions or confirms the file is consistent.

- [x] `planning/2026-04-14_call_agenda.md`
  Task: review for stale asks or outdated tracker references.
  Acceptance: spec captures any contradictions or confirms the file is consistent.

- [x] `planning/2026-04-14_call_prep.md`
  Task: review for stale asks or outdated tracker references.
  Acceptance: spec captures any contradictions or confirms the file is consistent.

- [x] `planning/2026-04-21_call_agenda.md`
  Task: review for asks or prompts that are already rendered moot by resolved decisions, plus any outdated tracker references.
  Acceptance: spec captures any contradictions or confirms the file is consistent.

- [x] `planning/2026-04-21_call_prep.md`
  Task: review for asks or prompts that are already rendered moot by resolved decisions, plus any outdated tracker references.
  Acceptance: spec captures any contradictions or confirms the file is consistent.

- [x] `/Users/wax/coding/Classes/COMS-E6998/Final Project/notes/updates_20260409.md`
  Task: review live teammate-update guidance against the canonical project state.
  Acceptance: spec captures any contradictions or confirms the file is consistent.

- [x] `/Users/wax/coding/Classes/COMS-E6998/Final Project/notes/report_format_mapping.md`
  Task: review for stale report-structure assumptions.
  Acceptance: spec captures any contradictions or confirms the file is consistent.

- [x] `/Users/wax/coding/Classes/COMS-E6998/Final Project/notes/agent_audit.md`
  Task: review for stale agent/process assumptions that affect current execution.
  Acceptance: spec captures any contradictions or confirms the file is consistent.

- [x] `/Users/wax/coding/Classes/COMS-E6998/Final Project/notes/Dhaval_Email_Thread.md`
  Task: review for mentor-decision facts that conflict with current live docs.
  Acceptance: spec captures any contradictions or confirms the file is consistent.

- [x] `/Users/wax/coding/Classes/COMS-E6998/Final Project/resources/report-ieee/main.tex`
  Task: review for stale structure/claim dependencies relative to current plan.
  Acceptance: spec captures any contradictions or confirms the file is consistent.

- [x] `/Users/wax/coding/Classes/COMS-E6998/Final Project/resources/report-neurips/main.tex`
  Task: review for stale structure/claim dependencies relative to current plan.
  Acceptance: spec captures any contradictions or confirms the file is consistent.

### Phase 1 - Triage and cross-reference

- [ ] `docs/plans/cross_repo_review_remediation_spec.md`
  Task: verify and complete the existing `Remediation Matrix` section so every deduped Critical/High finding has final severity, theme, affected files, GitHub issue mapping, current issue status, reconciliation decision, and implementation batch, including final confirmation of tool-name mappings, processed-file inventory inputs, and the Theme D policy decision.
  Acceptance: every Critical/High finding from completed review slices appears in the matrix with an explicit batch assignment, closed/open issue status, and any prerequisite Phase 1 decisions recorded clearly enough that Phase 2 can start without reinterpretation.

- [ ] `mcp_servers/fmsr_server/server.py`, `mcp_servers/iot_server/server.py`, `mcp_servers/tsfm_server/server.py`, `mcp_servers/wo_server/server.py`
  Task: verify the Canonical Tool Name Table in the spec against the live server registrations before Batch A assignments are finalized.
  Acceptance: the spec tool table is confirmed or corrected from live code before F-01/F-02 receive final batch assignments.

- [ ] `data/processed/`
  Task: inventory the currently tracked processed CSV artifacts to complete the Theme D triage determination, and record the exact tracked files in the Theme D triage decision.
  Acceptance: `git ls-files data/processed/` output is reflected in the triage matrix and used as input to the Theme D policy decision before Phase 2 implementation begins.

- [ ] `docs/plans/cross_repo_review_remediation_spec.md` (Theme D policy)
  Task: record the explicit Theme D policy decision (`docs-only`, `regen public-safe outputs`, `remove/untrack restricted-derived artifacts`, or `confirmed not restricted / no remediation needed`) after the tracked-file inventory and license review, plus an explicit note on whether git-history purge is required or intentionally out of scope with rationale.
  Acceptance: the Theme D section and remediation matrix both record the chosen policy and the git-history decision before Phase 2 begins.

### Phase 2 - Team repo remediation

Batch A - scenario / contract correctness

- [ ] `data/scenarios/*.json`
  Task: align scenario contracts with actual MCP tool names and any revised multi-domain schema decisions.
  Acceptance: scenario files match the chosen canonical tool naming and pass the upgraded validator.

- [ ] `data/scenarios/validate_scenarios.py`
  Task: upgrade validation to catch tool-name mismatches, schema gaps, and cross-field inconsistencies.
  Acceptance: validator fails on the previously false-green cases via committed reproducible negative checks (fixture files or equivalent regression payloads), including the multi-domain routing case addressed by F-02, and passes on the corrected scenario set.

- [ ] `mcp_servers/fmsr_server/server.py`
  Task: confirm documented/validated tool names and server contract remain consistent with scenario expectations, and address F-20 by rejecting invalid negative gas concentrations with a structured error before computing Rogers-ratio outputs.
  Acceptance: tool naming in code matches the chosen canonical contract, no hidden mismatch remains, and invalid negative gas concentrations are rejected with a structured error before misleading analysis is returned.

- [ ] `data/generate_synthetic.py`
  Task: implement the Batch A synthetic-data compatibility fixes required by F-14/F-15/F-16/F-17/F-18 so the generated dataset satisfies the live server expectations before any Theme D follow-up is layered on top.
  Acceptance: the generated synthetic outputs contain the fields needed by the FMSR, IoT, TSFM, and WO servers, the chosen monotonic-RUL rule is documented in code or nearby docs, and generation remains deterministic via a fixed documented seed.

- [ ] `data/build_processed.py`
  Task: implement the Batch A processed-data correctness fixes required by F-19 before any Theme D/public-safe publication work is layered on top of the same file.
  Acceptance: the build script no longer silently zeroes or assumes critical fields in ways that would mislead downstream FMSR reasoning, and the relevant raw/Kaggle preconditions are guarded clearly.

- [ ] `mcp_servers/iot_server/server.py`
  Task: implement the F-13 timestamp-serialization fix in `get_sensor_readings` so non-empty responses do not crash.
  Acceptance: a `get_sensor_readings` call with valid data returns a non-empty serialized response without error.

- [ ] `mcp_servers/tsfm_server/server.py`
  Task: address confidence/output and input-bounds issues identified during review.
  Acceptance: a `tsfm.get_rul` call with a valid asset ID and date returns a non-null `rul_days` value with confidence in `[0.0, 1.0]`, and an out-of-range input returns a structured error rather than a silently clamped or nonsensical result.

- [ ] `mcp_servers/wo_server/server.py`
  Task: confirm documented/validated tool names and server contract remain consistent with scenario expectations, and enforce referential integrity for work-order creation against the known asset set.
  Acceptance: tool naming in code matches the chosen canonical contract, no hidden mismatch remains, and work-order creation rejects transformer IDs not present in the known asset set.

- [ ] `mcp_servers/README.md`
  Task: document actual server composition/transport/endpoint expectations clearly, anchored to the Batch A `mcp_servers/README.md` portion of F-21.
  Acceptance: a teammate can understand how the multi-server setup is composed without guessing, and the updated content is explicitly reconciled against F-21 in the remediation matrix.

Batch B - serving / ops reproducibility and safety

- [ ] `scripts/setup_insomnia.sh`
  Task: harden setup preconditions, portability, reproducibility, and any critical cluster/runtime issues.
  Acceptance: setup behavior is reproducible, fails clearly, and no Critical/High review findings remain unresolved.

- [ ] `scripts/vllm_serve.sh`
  Task: fix serving safety, portability, readiness, and job-precondition issues.
  Acceptance: the serving job is safe to run on the shared cluster and fails clearly on missing prerequisites.

- [ ] `scripts/test_inference.sh`
  Task: ensure success criteria actually validate a correct inference response.
  Acceptance: the script fails on invalid/error JSON and passes only on a real inference response, defined as HTTP 200 with no `error` field and a non-empty completion payload in the expected response shape.

- [ ] `scripts/run_harness_smoke.cmd`
  Task: confirm whether any change is needed after the Batch A/B contract and smoke-test fixes land, and either update the script or explicitly record a no-change rationale tied to the findings absorbed into F-05/F-08/F-11.
  Acceptance: the remediation branch either contains the required `scripts/run_harness_smoke.cmd` update or a documented no-change determination under the F-05/F-08/F-11 matrix rows showing the script is still valid after the surrounding contract/proof changes.

- [ ] `scripts/verify_watsonx.py`
  Task: fix env parsing, output safety, and benchmark caveats identified in review.
  Acceptance: quoted `.env` values work, a passing verification request returns a non-empty completion payload, secrets are not printed at any log level, and benchmark output is clearly caveated.

Batch C - team repo live docs and planning surfaces

- [ ] `benchmarks/README.md`
  Task: align benchmark guidance with actual implemented tooling and metadata requirements, anchored to the Batch C benchmark/doc-routing portion of F-21.
  Acceptance: no required field or workflow is documented unless the repo actually supports it, and the updated content is explicitly reconciled against F-21 in the remediation matrix.

- [ ] `data/README.md`
  Task: resolve licensing/redist documentation gaps and any public-data policy clarifications.
  Acceptance: a reader can tell what is safe to publish and what is restricted without relying on slide decks.

- [ ] `data/build_processed.py`
  Task: implement any Theme D policy outcome that requires changing how processed outputs are built or filtered for public-safe publication. Note: this file is also touched in Batch A for F-19; review the Batch A changes before adding Theme D changes to avoid overlap.
  Acceptance: if Theme D requires generation changes, this script reflects them; if not, the remediation matrix `Resolution path` field records why no code change was needed.

- [ ] `data/generate_synthetic.py`
  Task: implement any Theme D policy outcome that requires synthetic replacement outputs or a documented public-safe generation path. Note: this file is also modified in Batch A for F-14/F-15/F-16/F-17; review the Batch A changes before layering Theme D changes to avoid overlap.
  Acceptance: if Theme D requires synthetic/public-safe output generation changes, this script reflects them; if not, the remediation matrix `Resolution path` field records why no code change was needed.

- [ ] `data/processed/`
  Task: if Theme D policy requires removal/untracking, remove restricted-derived processed artifacts from Git tracking and update ignore rules accordingly. If Theme D policy is `regenerate public-safe outputs`, run the updated generation/build scripts and commit the resulting public-safe files to `data/processed/`.
  Acceptance: if removal/untracking is the chosen policy, `git ls-files data/processed/` no longer shows restricted-derived tracked files after the change and `git check-ignore` confirms the ignore rule is in place. If regeneration is the chosen policy, `git ls-files data/processed/` shows only the newly generated public-safe outputs after the change. If the Theme D decision says git-history purge is required, this plan must explicitly stop at forward-state cleanup and hand off to a separate approved history-rewrite flow before claiming the repo is fully clean, with that handoff explicitly documented in the remediation PR body.

- [ ] `docs/compute_plan.md`
  Task: remove dead references and make cluster instructions teammate-portable and scheduler-accurate.
  Acceptance: compute instructions can be followed by any teammate without personal-path or stale-script failures.

- [ ] `docs/eval_harness_readme.md`
  Task: remove machine-specific paths and clarify canonical run proof expectations.
  Acceptance: the runbook is portable and reproducible for teammates.

- [ ] `docs/watsonx_access.md`
  Task: tighten secret-handling and usage guidance to match actual scripts and team workflow.
  Acceptance: WatsonX setup docs do not contradict the verification script and include concrete operational guidance.

- [ ] `README.md`
  Task: apply the repo-level onboarding and workflow corrections captured in the Batch C repo-doc portion of F-21.
  Acceptance: repo-level onboarding guidance matches the canonical org-repo workflow, and the updated content is explicitly reconciled against F-21 in the remediation matrix.

- [ ] `docs/README.md`
  Task: apply the doc-index and routing corrections captured in the Batch C repo-doc portion of F-21.
  Acceptance: doc-routing guidance matches the current live doc set, and the updated content is explicitly reconciled against F-21 in the remediation matrix.

- [ ] `docs/project_reference.md`
  Task: apply the stale-reference and project-fact corrections captured in the Batch C repo-doc portion of F-21.
  Acceptance: the reference doc matches current live project facts, and the updated content is explicitly reconciled against F-21 in the remediation matrix.

- [ ] `docs/project_synopsis.md`
  Task: apply the stale-positioning and milestone corrections captured in the Batch C repo-doc portion of F-21.
  Acceptance: the synopsis matches the committed W3/W4/W5 plan and current execution model, and the updated content is explicitly reconciled against F-21 in the remediation matrix.

- [ ] `docs/repo_strategy.md`
  Task: apply the repo-workflow corrections captured in the Batch C repo-doc portion of F-21.
  Acceptance: repo strategy reflects the canonical org repo `main` branch and GitHub Projects workflow, and the updated content is explicitly reconciled against F-21 in the remediation matrix.

- [ ] `reports/README.md`
  Task: apply the report-artifact workflow corrections captured in the Batch C repo-doc portion of F-21.
  Acceptance: report guidance does not contradict current execution reality, and the updated content is explicitly reconciled against F-21 in the remediation matrix.

- [ ] `planning/2026-04-07_meeting_notes.md`, `planning/2026-04-14_call_agenda.md`, `planning/2026-04-14_call_prep.md`, `planning/2026-04-21_call_agenda.md`, `planning/2026-04-21_call_prep.md`
  Task: update live planning docs so they encode the correct execution state, Tier-1 fallback gate, and explicit artifact-based acceptance criteria, as captured in F-22.
  Acceptance: no live planning doc still treats a resolved decision as open, and the Apr 21 agenda includes a concrete Tier-1 gate statement.

### Phase 3 - Review, merge, and issue closure

- [ ] `gh pr create` / team repo PR body
  Task: open a remediation PR from the dedicated team-repo branch with a concise summary, verification notes, and links to the plan/spec.
  Acceptance: the PR exists and clearly describes the remediation batches being merged.

- [ ] `claude-pr-review`
  Task: run iterative Claude PR review on the team repo PR until no Critical/High findings remain, including one final confirmation pass.
  Acceptance: final Claude PR review pass is clean on Critical/High findings.

- [ ] `gh pr checks`
  Task: verify the remediation PR checks are green before merge.
  Acceptance: required checks pass, or if no automated CI is configured the final clean `claude-pr-review` pass serves as the review gate and the lack of CI is explicitly documented.

- [ ] Team repo issue comments
  Task: add short follow-up comments to affected issues summarizing what changed and linking the remediation PR.
  Acceptance: each affected issue has a brief PR-linked follow-up note using the `Issue Follow-Through Format` defined in the companion spec.

### Phase 4 - Personal repo sync

- [ ] Team repo merge state
  Task: do not begin personal-repo sync until the team repo remediation PR has passed the final `claude-pr-review` pass with no Critical/High findings and has merged.
  Acceptance: personal-repo sync starts only after the team repo remediation PR has merged into `main`.

- [ ] `/Users/wax/coding/Classes/COMS-E6998/Final Project/notes/current_team_status.md`
  Task: sync the status doc with the merged team-repo reality and fix any stale helper references.
  Acceptance: the status doc correctly points to current files and canonical systems.

- [ ] `/Users/wax/coding/Classes/COMS-E6998/Final Project/notes/roadmap.md`
  Task: sync roadmap wording with the merged team-repo reality and current decision state.
  Acceptance: roadmap phases and blockers align with live project decisions.

- [ ] `/Users/wax/coding/Classes/COMS-E6998/Final Project/notes/2026-04-07_call_prep.md`
  Task: annotate or correct any pre-call language that now conflicts with final Apr 7 outcomes.
  Acceptance: the file cannot be misread as current unresolved guidance.

- [ ] `/Users/wax/coding/Classes/COMS-E6998/Final Project/notes/2026-04-14_call_prep.md`
  Task: correct stale tracker/task-system references and any resolved questions that survived the template.
  Acceptance: the next-call prep points to the live board and current open decisions.

- [ ] `/Users/wax/coding/Classes/COMS-E6998/Final Project/notes/mcp_comparison_experiment.md`
  Task: sync experiment framing with the chosen remediation decisions if needed, especially any canonical tool-name or benchmark-contract assumptions touched by the remediation.
  Acceptance: experiment framing does not contradict the remediated team-repo docs or the final canonical MCP contract.

- [ ] `/Users/wax/coding/Classes/COMS-E6998/Final Project/notes/updates_20260409.md`, `/Users/wax/coding/Classes/COMS-E6998/Final Project/notes/report_format_mapping.md`, `/Users/wax/coding/Classes/COMS-E6998/Final Project/notes/agent_audit.md`, `/Users/wax/coding/Classes/COMS-E6998/Final Project/notes/Dhaval_Email_Thread.md`, `/Users/wax/coding/Classes/COMS-E6998/Final Project/resources/report-ieee/main.tex`, `/Users/wax/coding/Classes/COMS-E6998/Final Project/resources/report-neurips/main.tex`
  Task: apply or explicitly decline any follow-up generated by the Phase 0 remaining-slice reviews so those files do not get reviewed without a Phase 4 resolution path.
  Acceptance: each reviewed file in this group is either updated or recorded as requiring no change after the team repo remediation stabilizes.

- [ ] `/Users/wax/coding/Classes/COMS-E6998/Final Project/notes/task_tracker.md`
  Task: preserve as historical/supporting reference only, with corrected issue/doc references if retained. This is a consistency check for a historical support doc rather than a response to a current Critical/High finding.
  Acceptance: the file cannot be mistaken for the live execution surface.

- [ ] `/Users/wax/coding/Classes/COMS-E6998/Final Project/notes/task_specs.md`
  Task: preserve as historical/supporting reference only, with corrected issue/doc references if retained.
  Acceptance: the file cannot be mistaken for the live execution surface and all issue-number cross-references are correct.

- [ ] `/Users/wax/coding/Classes/COMS-E6998/Final Project/project_archive/2026-04-01_meeting_notes.md`
  Task: add any minimal archive note needed to avoid obvious factual drift without rewriting the archive.
  Acceptance: archived historical context remains readable and is not misleading on key facts.

- [ ] `/Users/wax/coding/Classes/COMS-E6998/Final Project/project_archive/Dhaval_guest_lecture_insights.md`
  Task: confirm whether any archive annotation or no-op note is needed after the personal-repo sync review.
  Acceptance: the file is either intentionally unchanged with a recorded no-op rationale or minimally annotated to avoid misleading drift.

- [ ] `docs/archive/`
  Task: grep for inbound references to `docs/plans/cross_repo_review_remediation*` in both the team repo and the personal repo, update them as needed, create `docs/archive/` if it does not exist, and then archive the plan/spec after the remediation PR is merged and the personal repo sync is complete.
  Acceptance: the plan and spec live under `docs/archive/`, and any doc-routing references no longer point to stale `docs/plans/` paths.

### Acceptance Gate - Program Complete

- Team repo remediation PR is merged after a clean final Claude PR review pass with no Critical/High findings.
- Personal repo live docs are synced to the merged reality.
- If Theme D policy requires git-history purge, the merged remediation PR explicitly documents that the repository is only clean in forward state and records the handoff to the separate history-rewrite flow.
- Affected issues have brief closure/follow-up comments with PR links.
- Plan and spec are archived under `docs/archive/` once the remediation program is complete and any live references have been updated.
