# Validation Summary

Batch: `first_review_20260502`
Generated: 2026-05-03 03:26 UTC
Issue: #2
Model: `watsonx/meta-llama/llama-3-3-70b-instruct`
Prompt version: `v0.1`
Knowledge/plugin hash: `0eacec24441e`

## Batch Contents

| Scenario | Family | Type | Structural status | Notes for #53 |
|---|---|---|---|---|
| `SGT-GEN-001` | `FMSR_DGA_DIAGNOSIS` | `FMSR` | PASS | Manually cleaned up after review: the original raw response contradicted the stable-normal template by labelling the profile `T3`; committed JSON now records `N` / no active fault. |
| `SGT-GEN-002` | `TSFM_RUL_FORECAST` | `TSFM` | PASS | Manually cleaned up after review: prompt now asks for long-term RUL plus explicit 60-day operability, matching the 420-day ground truth. |
| `SGT-GEN-003` | `WO_CREATION` | `WO` | PASS | Manually cleaned up after review: WO-only ground truth no longer requires unsupported hidden FMSR fault code / condition tier evidence. |
| `SGT-GEN-004` | `IOT_SENSOR_ANALYSIS` | `IoT` | PASS | No obvious structural issue. |
| `SGT-GEN-005` | `MULTI_DOMAIN_INCIDENT` | `Multi` | PASS | Manually cleaned up after review: D2 ratios now match the repo-standard representative profile (`R1=0.40`, `R2=1.20`, `R3=3.33`). Prompt mentions gas names but no concentrations/codes/methods; #53 should decide if this is acceptable or too leading. |

## Cleanup After v1 Review

The raw responses remain committed unchanged as generation evidence. The committed
`SGT-GEN-*.json` files are the reviewable candidate artifacts. Four candidates
have `provenance.manual_cleanup=true` because the v1 file review found content
bugs in the raw model output:

- `SGT-GEN-001`: corrected `T3` to `N` / normal based on the committed
  `stable_normal` prompt template and final-sample `R1=0.056`.
- `SGT-GEN-002`: aligned prompt and ground-truth horizon.
- `SGT-GEN-003`: removed unsupported diagnostic ground truth from the WO-only
  scenario; after v2 review, removed the non-contract `must_not_include` field
  and kept the same intent in `acceptance_criteria`.
- `SGT-GEN-005`: corrected D2 Rogers-ratio values to match
  `data/knowledge/transformer_standards.json`.

Known remaining human-review items:

- All five candidates still use asset `T-005`; this weakens batch diversity but
  does not affect structural validity.
- The nearest-handcrafted comparator is based on type/tool overlap, so #53
  should still perform an explicit novelty check.
- Raw responses show the model sometimes emitted markdown fences despite the
  prompt; the parser stripped them before writing the committed JSON.

## Checks Run

```bash
uv run --with jsonschema python data/scenarios/validate_scenarios.py
```

Result: `Validation passed for 11 scenario files and 5 negative fixtures.`

```bash
uv run --with litellm==1.81.13 --with python-dotenv --with ibm-watsonx-ai python - <<'PY'
import json, pathlib
import scripts.generate_scenarios as gen
valid_asset_ids = gen._validator.load_valid_asset_ids(gen.ASSET_CSV)
root = pathlib.Path('data/scenarios/generated/first_review_20260502')
for p in sorted(root.glob('SGT-GEN-*.json')):
    d = json.loads(p.read_text())
    errors = gen.validate_scenario(d, valid_asset_ids)
    print(f"{d['id']}\t{'PASS' if not errors else 'FAIL'}\t{'; '.join(errors)}")
PY
```

Result: all five generated candidates passed the canonical schema plus generated-scenario provenance/comparator contract.

## Handoff

This batch is ready for #53-style human validation. Do not promote any file from this directory into top-level `data/scenarios/` until #53 assigns a disposition (`accept`, `accept_with_edits`, `reject_duplicate`, or `reject_unusable`).
