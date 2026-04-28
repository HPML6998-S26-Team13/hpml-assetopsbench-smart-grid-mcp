# Generated Smart Grid scenario batches

Output directory for `scripts/generate_scenarios.py` (PS B auto-generation prototype, `#2`).

Each subdirectory is one batch:

```
<batch_id>/
    SGT-GEN-NNN.json          # validator-clean candidate scenarios
    invalid/                  # scenarios that failed the validator (with error lists)
    prompts/                  # exact LLM prompts (one per scenario, for reproducibility)
    raw_responses/            # raw LLM outputs before parsing
    batch_manifest.json       # provenance roll-up
```

Generated scenarios are intentionally NOT picked up by `data/scenarios/validate_scenarios.py`'s top-level `*.json` glob. Promotion into the canonical set happens per-scenario after Akshat's validation pass (`#53` rubric) — see [`docs/auto_scenario_generation_runbook.md`](../../../docs/auto_scenario_generation_runbook.md) §"Promoting a generated scenario into the canonical set".

Each generated scenario carries the full provenance + nearest-comparator metadata required by [`docs/knowledge/generated_scenario_authoring_and_ground_truth.md`](../../../docs/knowledge/generated_scenario_authoring_and_ground_truth.md): `source_type`, `family`, `generator_prompt_version`, `knowledge_plugin_version`, `generation_model`, `generation_date`, `batch_id`, `manual_cleanup`, `nearest_handcrafted`.
