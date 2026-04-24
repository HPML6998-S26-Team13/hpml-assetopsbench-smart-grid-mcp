# data/scenarios/

*Last updated: 2026-04-21*

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

- **W2 (Apr 7-13):** 15+ validated scenarios (Akshat)
- **W4 (Apr 21-27):** 30+ scenarios (Akshat + team) — stretch goal per mid-point report

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

## Status (Apr 7, 2026)

Scaffolding only. First batch of 5-10 scenarios owed by Akshat from Sun Apr 5 (delivery "tonight" per Apr 6 20:31 message); target 15+ by Apr 13.
