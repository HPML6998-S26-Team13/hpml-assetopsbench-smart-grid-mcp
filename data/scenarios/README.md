---
status: canonical-index
scope: team-repo
owner: Team 13
canonical: true
---

# data/scenarios/

*Last updated: 2026-05-07*

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

## Status (2026-05-07)

- **Canonical:** 51 scenarios + 5 negative fixtures. Validator (`python data/scenarios/validate_scenarios.py`) reports `Validation passed for 51 scenario files and 5 negative fixtures.` Domain mix: FMSR 10, IoT 12, Multi 10, TSFM 8, WO 10, plus the upstream-portable `aob_fmsr_01_list_failure_modes.json`.
- **Provenance breakdown:** 46 hand-authored (`SGT-001..SGT-030`, `SGT-036..SGT-050`, plus `AOB-FMSR-001`) and 5 promoted-from-generated with explicit `provenance` blocks (`SGT-031..SGT-035`). Hand-authored files do not carry a `provenance` block; promoted files do — that absence/presence is the canonical provenance marker.
- **Generated (PS B):** 15 candidates across 3 batches under `data/scenarios/generated/`. PR #191 (merged) landed the disposition table at `data/scenarios/generated/disposition_2026-05-06.csv` — 5 `accept_with_edits`, 10 `reject_duplicate`, 0 `reject_unusable`, 0 `reject_structural`. Both methodology bars (≥70% accept-or-edits; <20% reject_dup) fail at 33% / 67%; the batch is not benchmark-ready as a whole.
- **HPML #55 batch (2026-05-07):** 15 hand-authored scenarios `SGT-036..SGT-050` add coverage for under-exercised tools (`fmsr.search_failure_modes`, `wo.list_work_orders`, `wo.get_fault_record`), the `power_factor` and `voltage_hv_kv`/`voltage_lv_kv` sensor channels, the arc-discharge and low-temperature-overheating DGA fixtures (T-013/T-018), and the previously empty `tsfm_05` slot.
- **Eval coverage (current evidence):** 2,420 paper-grade judge rows across the 31 canonical scenarios per `results/metrics/evidence_registry.csv`. Refresh against the 51-floor will follow the next paper-grade evidence pull.
- **For the paper:** see `docs/content_brief_scenarios_eval.md` for the 1-page fact pack of safe-to-cite numbers.
