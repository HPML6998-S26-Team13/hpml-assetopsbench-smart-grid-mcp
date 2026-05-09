---
status: canonical-index
scope: team-repo
owner: Team 13
canonical: true
---

# data/scenarios/

*Last updated: 2026-05-08*

Smart Grid transformer maintenance scenarios, following the AssetOpsBench scenario format. Each scenario is a multi-turn agentic task where an LLM agent must use the IoT / FMSR / TSFM / WO MCP tools to diagnose, forecast, or remediate a transformer fault.

## Format

Scenarios follow AssetOpsBench's existing utterance schema with required keys:

- `id` — unique identifier
- `type` — domain label (`IoT`, `FMSR`, `TSFM`, `WO`, or empty for mixed/general)
- `text` — user instruction for the agent
- `category` — task category label
- `characteristic_form` — objective expected answer pattern for grading

For Smart Grid authoring in this repo, we keep additional optional keys:

- `asset_id` — fictional transformer ID (`T-001` to `T-020`)
- `expected_tools` — expected MCP tools in rough order
- `ground_truth` — checkable target answer/action
- `difficulty` — easy / medium / hard
- `domain_tags` — exercised domains (`IoT`, `FMSR`, `TSFM`, `WO`)

See the upstream AssetOpsBench structure in `src/scenarios/local/vibration_utterance.json` and `aobench/scenario-server/src/scenario_server/handlers/*.py` (which consume `id`, `type`, `text`, `category`, `characteristic_form`).

## Targets

- **W2 (Apr 7-13):** 15+ validated scenarios (Akshat) — **met.** HPML #15 closed.
- **W4 (Apr 21-27):** 30+ scenarios (Akshat + team) — stretch goal per mid-point report. **Met.** HPML #33 closed at 31 hand-authored scenarios.
- **PS B promotion lane:** 5 generated scenarios queued for canonical promotion in PR #195 (`SGT-031..SGT-035`); validator goes 31+5 -> 36+5 on merge. See `data/scenarios/generated/README.md` for the disposition table.
- **HPML #55 / AOB #36 (50+ corpus):** 15 hand-authored scenarios `SGT-036..SGT-050` added 2026-05-07 take canonical to 51. Validator reports 51+5 on merge.
- **HPML #55 (capability-targeted batch, 2026-05-08):** 10 hand-authored scenarios `SGT-051..SGT-060` carrying explicit `benchmark_design` blocks (target_capability + discrimination_hypothesis) and `must_NOT_include` anti-hallucination guards take canonical to 61. Designed to fill empty capability-matrix cells (anti-hallucination, calibration/abstention, distractor filtering, cross-tool consistency, argument extraction, specification compliance, numerical reasoning, tool-error recovery, anti-prompt-leak triangulation). Validator reports 61+5 on merge.

## Conventions

- **File naming:** `<domain>_<NN>_<short_slug>.json`
  - e.g. `fmsr_01_dga_arcing_diagnosis.json`, `tsfm_03_rul_forecast_weekly.json`
- **Multi-domain scenarios:** `multi_<NN>_<slug>.json`
  - e.g. `multi_01_full_fault_response.json` (IoT sensor alert → FMSR diagnosis → TSFM RUL check → WO creation)
- **Before committing**, validate against the AssetOpsBench scenario schema and confirm the referenced `asset_id` exists in `data/processed/asset_metadata.csv`.
- **Ground truth must be objectively checkable** — if scoring depends on subjective judgment, add a scoring rubric field.

## Validation

Run the validator from repo root before committing scenario changes:

```bash
python data/scenarios/validate_scenarios.py
```

This catches schema violations and negative-fixture regressions before you get to
the heavier harness path. For the full harness workflow, see
[../../docs/eval_harness_readme.md](../../docs/eval_harness_readme.md).

## Status (2026-05-08)

- **Canonical:** 61 scenarios + 5 negative fixtures. Validator (`python data/scenarios/validate_scenarios.py`) reports `Validation passed for 61 scenario files and 5 negative fixtures.` Domain mix: FMSR 11, IoT 14, Multi 14, TSFM 9, WO 12, plus the upstream-portable `aob_fmsr_01_list_failure_modes.json`.
- **Provenance breakdown:** 56 hand-authored (`SGT-001..SGT-030`, `SGT-036..SGT-060`, plus `AOB-FMSR-001`) and 5 promoted-from-generated with explicit `provenance` blocks (`SGT-031..SGT-035`). Hand-authored files do not carry a `provenance` block; promoted files do — that absence/presence is the canonical provenance marker.
- **Generated (PS B):** 15 candidates across 3 batches under `data/scenarios/generated/`. PR #191 (merged) landed the disposition table at `data/scenarios/generated/disposition_2026-05-06.csv` — 5 `accept_with_edits`, 10 `reject_duplicate`, 0 `reject_unusable`, 0 `reject_structural`. Both methodology bars (≥70% accept-or-edits; <20% reject_dup) fail at 33% / 67%; the batch is not benchmark-ready as a whole.
- **HPML #55 batch A — gap-fill (2026-05-07):** 15 hand-authored scenarios `SGT-036..SGT-050` add coverage for under-exercised tools (`fmsr.search_failure_modes`, `wo.list_work_orders`, `wo.get_fault_record`), the `power_factor` and `voltage_hv_kv`/`voltage_lv_kv` sensor channels, the arc-discharge and low-temperature-overheating DGA fixtures (T-013/T-018), and the previously empty `tsfm_05` slot.
- **HPML #55 batch B — capability-targeted (2026-05-08):** 10 hand-authored scenarios `SGT-051..SGT-060` carry explicit `benchmark_design.target_capability` and `benchmark_design.discrimination_hypothesis` fields, plus `ground_truth.must_NOT_include` anti-hallucination guards. Capabilities targeted: `anti_hallucination_under_misleading_prompt` (SGT-051), `calibration_and_abstention` (SGT-052), `negative_result_calibration` (SGT-053), `distractor_filtering_retrieval_discipline` (SGT-054), `cross_tool_consistency_reconciliation` (SGT-055), `argument_extraction_across_tool_returns` (SGT-056), `specification_compliance_format_strict` (SGT-057), `numerical_reasoning_over_tool_outputs` (SGT-058), `tool_error_recovery_and_fallback` (SGT-059), `anti_prompt_leak_evidence_triangulation` (SGT-060). Each scenario states the discrimination hypothesis it tests so per-capability score gaps can be reported in the paper.
- **Eval coverage (current evidence):** 2,420 paper-grade judge rows across the 31 canonical scenarios per `results/metrics/evidence_registry.csv`. Refresh against the 61-floor will follow the next paper-grade evidence pull.
- **For the paper:** see `docs/content_brief_scenarios_eval.md` for the 1-page fact pack of safe-to-cite numbers.

## Optional benchmark-design fields (2026-05-08, batch B onward)

Scenarios authored 2026-05-08 onward may carry two optional top-level extensions intended to support per-capability benchmark scoring:

- `benchmark_design.target_capability` — short snake_case identifier of the capability the scenario isolates (e.g. `calibration_and_abstention`, `tool_error_recovery_and_fallback`).
- `benchmark_design.discrimination_hypothesis` — prose description of why the scenario is expected to separate strong from weak models, ideally citing fixture values that anchor the hypothesis.
- `ground_truth.must_NOT_include` — list of strings the answer must avoid (e.g. fabricated values, prose around a JSON-strict response, fault codes the fixture does not support).

These fields are **optional** and **not yet schema-enforced** by `validate_scenarios.py`. Existing scenarios (`SGT-001..SGT-050`) are unaffected.
