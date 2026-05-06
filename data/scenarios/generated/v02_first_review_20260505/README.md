# `v02_first_review_20260505` — INSPECTION-ONLY BATCH (prompt v0.2 evaluation)

> **Do not use these scenarios as benchmark inputs.** Same inspection-only framing as `data/scenarios/generated/first_review_20260503/`: ground-truth values are model-asserted, not validated against actual repo data fixtures or MCP tool outputs. The point of this batch is to **evaluate whether the v0.2 prompt-template iteration (PR #185) materially fixes the v0.1 inspection findings.**

This batch was generated with **PROMPT_VERSION v0.2** (PR #185), against the same model (`watsonx/meta-llama/llama-3-3-70b-instruct`) and seed (`42`) as the v0.1 batch (`first_review_20260503`). Holding everything else constant lets us isolate the prompt-template change as the only variable.

## v0.1 → v0.2 audit comparison

PR #178's review surfaced 9 distinct issues across the v0.1 batch. Here's how each fared under v0.2:

| # | Issue | v0.1 (`first_review_20260503`) | v0.2 (this batch) | Verdict |
|---|---|---|---|---|
| 1 | Asset variation (RNG collapse) | ❌ all 5 scenarios used `T-005` | ✅ `T-001..T-005` distinct (one per family by deterministic rotation) | **FIXED** |
| 2 | Gas-name mention in text (no-hint violation) | ❌ SGT-GEN-005 said "rising methane and ethylene" | ✅ all 5 use generic phrasings ("elevated activity", "unusual activity") | **FIXED** |
| 3 | SGT-GEN-001 text↔ground_truth consistency (text said "stable" but labeled D2) | ❌ | ⚠️ Text fixed ("elevated activity"), but `ground_truth.final_value.dominant_gas_rationale` says "Elevated methane and ethane" — that's a thermal pattern (T1/T2 territory), not D2 (arc discharge → C2H2-driven). Inconsistency moved from text↔GT to within-GT. | **PARTIAL** |
| 4 | SGT-GEN-002 value-range mismatch (rul_range_days=360 vs rul_estimate_days=540) | ❌ | ✅ no range field; only `health_index` in `decisive_intermediate_values`, single `rul_estimate_days: 540` in `final_value`. No internal contradiction. | **FIXED** |
| 5 | SGT-GEN-003 missing `severity` source for `wo.estimate_downtime` | ❌ | ✅ added `wo.list_fault_records` first in `ideal_tool_sequence`; text gives explicit operational context ("temperature exceeds threshold", "spare procurement pending"). | **FIXED** |
| 6 | SGT-GEN-004 unpinned `sensor_id` for `iot.get_sensor_readings` | ⚠️ | ✅ `decisive_intermediate_values.sensor_id: "oil_temp_c"` pins it; text says "oil temperature" which the agent can map. | **PARTIAL** (still relies on agent inference rather than explicit `iot.list_sensors` discovery, but materially better than v0.1) |
| 7 | SGT-GEN-005 missing `fmsr.get_dga_record` before `fmsr.analyze_dga` (CONSISTENCY_CONSTRAINTS rule explicitly requires this) | ❌ | ❌ **STILL VIOLATED** — `ideal_tool_sequence` is `[iot.get_sensor_readings, fmsr.analyze_dga, tsfm.forecast_rul, wo.create_work_order]`. Model ignored the explicit rule for this multi-domain case. | **STILL VIOLATED** |
| 8 | SGT-GEN-005 missing `sensor_id` source for `iot.get_sensor_readings` | ❌ | ❌ **STILL VIOLATED** — same as v0.1; text doesn't pin a sensor and there's no `iot.list_sensors` discovery step. | **STILL VIOLATED** |
| 9 | Data-grounding (`get_dga_record(T-NNN)` actually returns what?) | ❌ | ❌ **DEFERRED** — needs MCP runtime access at generation time; tracked for v0.3 in PR #185 PROMPT_VERSION changelog. | **DEFERRED** |

**Net:** 4 fully fixed + 2 partial + 2 still violated + 1 deferred on a 5-scenario, `temperature=0.7` inspection-only batch. First concrete (small-sample) evidence that the v0.2 prompt iteration shifts most v0.1 violations; needs confirmation on a larger batch + Akshat's #53 rubric pass before generalising.

## What v0.3 still needs to fix

The 2 remaining violations both occurred on the same scenario (SGT-GEN-005, the multi-domain incident response). The CONSISTENCY_CONSTRAINTS section explicitly states:

> `fmsr.analyze_dga(...)` requires all five gas values (H2/CH4/C2H2/C2H4/C2H6). It MUST be preceded by `fmsr.get_dga_record` in `ideal_tool_sequence`.

The model honored this rule for SGT-GEN-001 (FMSR-only) but ignored it for SGT-GEN-005 (multi-domain). Two hypotheses for v0.3:

1. **Multi-domain prompts are too long** (~10500 chars vs ~5000-7800 for single-domain). The CONSISTENCY_CONSTRAINTS section may be far enough from the schema reminder that the model loses focus by the time it generates. Mitigation: repeat the rule inside the multi-domain template block, or move CONSISTENCY_CONSTRAINTS closer to the OUTPUT FORMAT section.
2. **Post-generation validator** that mechanically rejects scenarios where `fmsr.analyze_dga` appears in `ideal_tool_sequence` without a preceding `fmsr.get_dga_record`, and similar for `iot.get_sensor_readings` without a `sensor_id` source. This catches what the model misses regardless of prompt size.

Option 2 is more robust and probably the right v0.3 direction — adds the rule to `_validate_generated_contract()` so violations land in `invalid/` instead of the valid output path.

## Files

- `SGT-GEN-001..005.json` — five scenarios, one per family
- `batch_manifest.json` — provenance roll-up + reproducibility caveat + `batch_status: inspection_only`
- `README.md` — this audit document

`prompts/` and `raw_responses/` from the generation run are kept locally on the operator's Insomnia clone (not in a shared path). Not committed here for the same reason as v0.1: they're debugging artifacts, not contract. The `generator_commit_sha` + `generator_source_sha256` + `authoring_contract_sha256` fields in `batch_manifest.json` are the immutable provenance for re-derivation; reach out to the batch operator (af3623) if a reviewer needs the prompts/responses.

## Reproduction

Same shape as v0.1 — only the branch / prompt version changes:

```bash
git checkout aaron/issue68-prompt-v02   # or wait for PR #185 to merge then use main
export WATSONX_API_KEY=... WATSONX_PROJECT_ID=... WATSONX_URL=...
export WX_API_KEY="$WATSONX_API_KEY" WX_PROJECT_ID="$WATSONX_PROJECT_ID" WX_URL="$WATSONX_URL"
.venv-insomnia/bin/python scripts/generate_scenarios.py \
    --family FMSR_DGA_DIAGNOSIS --family TSFM_RUL_FORECAST \
    --family WO_CREATION --family IOT_SENSOR_ANALYSIS --family MULTI_DOMAIN_INCIDENT \
    --n 1 --batch-id v02_first_review_20260505 --seed 42
```

(WatsonX env aliases to WX_* will become automatic once PR #177 merges.)

The same caveat applies as v0.1: `temperature=0.7` means re-runs aren't text-deterministic from seed alone. The committed JSON files capture *what produced this batch*; the seed reproduces context/template selection, not model output.

## Hand-off

#53 validation rubric application now has **two batches to validate side-by-side** (v0.1 inspection-only at `first_review_20260503/` and v0.2 inspection-only at this dir). The v0.1↔v0.2 delta is the strongest available signal that prompt iteration works as a methodology — particularly relevant if the paper claims iterative prompt refinement as part of the PS B contribution.
