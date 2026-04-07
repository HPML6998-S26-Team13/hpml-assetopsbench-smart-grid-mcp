# data/scenarios/

Smart Grid transformer maintenance scenarios, following the AssetOpsBench scenario format. Each scenario is a multi-turn agentic task where an LLM agent must use the IoT / FMSR / TSFM / WO MCP tools to diagnose, forecast, or remediate a transformer fault.

## Format

Scenarios follow AssetOpsBench's existing schema (JSON, one per file). Each scenario specifies:

- `scenario_id` — unique identifier
- `asset_id` — which fictional transformer (T-001–T-020, see `data/processed/asset_metadata.csv`)
- `prompt` — the user instruction given to the agent
- `expected_tools` — which MCP tool calls the agent should make, in rough sequence
- `ground_truth` — the correct answer or action (for LLM-as-Judge scoring)
- `difficulty` — easy / medium / hard
- `domain_tags` — which of IoT, FMSR, TSFM, WO are exercised

See the upstream AssetOpsBench repo (`src/agent/scenarios/`) for reference examples from existing asset domains.

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

## Status (Apr 7, 2026)

Scaffolding only. First batch of 5-10 scenarios owed by Akshat from Sun Apr 5 (delivery "tonight" per Apr 6 20:31 message); target 15+ by Apr 13.
