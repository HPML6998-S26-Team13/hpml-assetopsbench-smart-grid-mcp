# data/scenarios/

*Last updated: 2026-05-06*

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

## Status (2026-05-06)

- **Canonical:** 31 hand-authored scenarios + 5 negative fixtures. Validator (`python data/scenarios/validate_scenarios.py`) reports `Validation passed for 31 scenario files and 5 negative fixtures.` Domain mix: FMSR 7, IoT 6, Multi 8, TSFM 4, WO 6.
- **Generated (PS B):** 15 candidates across 3 batches under `data/scenarios/generated/`. PR #191 (merged) landed the disposition table at `data/scenarios/generated/disposition_2026-05-06.csv` — 5 `accept_with_edits`, 10 `reject_duplicate`, 0 `reject_unusable`, 0 `reject_structural`. Both methodology bars (≥70% accept-or-edits; <20% reject_dup) fail at 33% / 67%; the batch is not benchmark-ready as a whole.
- **Promotion in flight:** PR #195 promotes the 5 `accept_with_edits` rows into canonical with bounded edits applied + provenance retained. Once merged, validator reports 36+5 and the corpus has both hand-authored and (clearly-flagged) generated-source records.
- **Eval coverage (current evidence):** 2,420 paper-grade judge rows across the 31 canonical scenarios per `results/metrics/evidence_registry.csv`. Refresh against the 36-floor will follow the next paper-grade evidence pull.
- **For the paper:** see `docs/content_brief_scenarios_eval.md` for the 1-page fact pack of safe-to-cite numbers.
