# `first_review_20260503` — INSPECTION-ONLY BATCH

> **Do not use these scenarios as benchmark inputs.** Their `ground_truth` values are model-asserted, not validated against the actual repo data fixtures or MCP tool outputs. A correct tool-using agent would be scored wrong on at least three of the five scenarios.

This batch is the first end-to-end output of `scripts/generate_scenarios.py` (PS B prototype, `#2`). It exists to prove that the generator pipeline runs end-to-end, that the validator + nested-provenance contract works, and to surface the first concrete prompt-iteration signal for `#68` scale-up. The scenarios themselves are not paper-corpus material.

## Why inspection-only and not benchmark-ready

Verified by Alex's PR #178 review against the actual MCP tool outputs and `data/processed/*.csv` fixtures:

| Scenario | Severity | Issue |
|---|---|---|
| `SGT-GEN-001` | High | Text says "stable gas levels" but `ground_truth.final_value.primary_fault: D2` (low-energy discharge). `get_dga_record("T-005")` actually returns `fault_label="Normal"` with stable gases — does NOT support D2/R-ratio. |
| `SGT-GEN-002` | High | `ground_truth.final_value.rul_estimate_days: 540` and `decisive_intermediate_values.health_index: 0.6`, but `forecast_rul("T-005")` actually returns `current_rul_days=3364` / `projected_rul_days=3334`. |
| `SGT-GEN-003` | High | `expected_tools` includes `wo.estimate_downtime` which requires a `severity` argument; the prompt provides no severity source. The tool sequence isn't callable from prompt context alone. |
| `SGT-GEN-004` | Medium | `iot.get_sensor_readings` requires an exact `sensor_id` and returns historical fixture rows. Scenario doesn't pin sensor/channel/timestamp → the answer is non-reproducible. Either pin the sensor, or add an `iot.list_sensors` discovery step. |
| `SGT-GEN-005` | High | Multi-domain. Prompt names `methane` + `ethylene` (CH4 + C2H4 → thermal pattern T1-T3) but `ground_truth.fault_code: D2` (arc-discharge, characterized by C2H2). Gases don't match the labeled fault. Also `expected_tools` includes `iot.get_sensor_readings` (needs sensor_id source) and `fmsr.analyze_dga` (needs all 5 gases) but omits `fmsr.get_dga_record`. |
| All five | Medium | Every scenario uses asset `T-005`. Family matrix `variation_axes` says "vary across T-001 to T-020"; the RNG (seed=42) independently picked T-005 for each family because the prompt template doesn't enforce cross-scenario asset variation. |

## Reproducibility caveat (#178 review M2)

The `seed=42` recorded in `batch_manifest.json:invocations[0].seed` controls **only the generator's RNG for context / template selection**. It is **not** passed to `litellm.completion()`, and the model runs at `temperature=0.7`, so re-running with the same seed will give different scenario text. The committed `SGT-GEN-001..005.json` files plus manifest provenance capture the reviewed artifact; they do not let a re-runner re-derive the exact text from seed alone. Raw prompts and responses were kept as uncommitted debug artifacts, not as part of the public scenario contract.

## How this is segregated from the benchmark corpus

- The team's CI gate (`python data/scenarios/validate_scenarios.py`) only globs `data/scenarios/*.json` (top-level, non-recursive). This subdirectory is not picked up.
- The `nearest_handcrafted_comparator` block on each scenario points at the canonical comparator so promotion to the corpus would be a per-scenario decision, not a bulk move.
- The generator's contract validator passes (5/5) — the issues above are **semantic** (data-grounding + tool-call preconditions), not structural.

## What `#68` scale-up needs to add to fix this

These become the prompt-iteration backlog for `#68`. Bump `PROMPT_VERSION` from `v0.1` to `v0.2` when these land:

1. Inject explicit constraint: "the gases / sensor evidence in the text MUST be consistent with the fault label in `ground_truth.final_value`."
2. Either inline the actual MCP-tool outputs into the prompt at generation time so ground truth is data-grounded, or do a post-generation grounding pass that runs the `ideal_tool_sequence` against the live MCP servers and overwrites `decisive_intermediate_values` + `final_value` with what the tools actually return.
3. For each `expected_tools` entry, the prompt must supply a source for every required argument — or the generator must include the appropriate discovery tool (e.g. `iot.list_sensors` before `iot.get_sensor_readings`).
4. Add a per-family asset-variation override that rotates through `T-001..T-020` deterministically per `--seed` instead of relying on independent RNG draws.
5. Decide whether naming gases by chemical formula or common name counts as a no-hint violation (Akshat's call under `#53`).

## Hand-off

`#53` validation rubric application owns the official quality call. The findings above are offered as a starting signal for that review, not as a substitute.
