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

## Per-scenario disposition (issue #53)

Per-scenario rubric application against `docs/ps_b_evaluation_methodology.md` —
machine-readable table at [`disposition_2026-05-06.csv`](disposition_2026-05-06.csv).

CSV header conforms to the methodology's required-artifact shape (§ Required
artifact shape, lines 277-292): `scenario_id`, `source_type`,
`provenance_batch_id`, `nearest_handcrafted_scenario_id` (reviewer-selected),
`realism_rating`, `novelty_rating`, `tool_path_rating`,
`benchmark_usefulness_rating`, `disposition`, `needs_edit`, `validator_notes`.
Three additional columns are kept for downstream consumers:
`nearest_handcrafted_embedded` (the comparator the scenario JSON itself
records, useful for spotting metadata drift before promotion),
`promotion_decision` (explicit issue #53 handoff: `promote_with_edits` or
`reject`), and `required_edit` (the bounded edits to apply before promotion).
`domain` and `asset_id` are also retained for grouping.

| Batch | n | accept | accept_with_edits | reject_unusable | reject_duplicate | reject_structural |
|---|---:|---:|---:|---:|---:|---:|
| `first_review_20260502` | 5 | 0 | 2 | 0 | 3 | 0 |
| `first_review_20260503` | 5 | 0 | 1 | 0 | 4 | 0 |
| `v02_first_review_20260505` | 5 | 0 | 2 | 0 | 3 | 0 |
| **Total** | **15** | **0** | **5** | **0** | **10** | **0** |

**Batch acceptance vs the methodology bar:** the rubric in
`docs/ps_b_evaluation_methodology.md` § Acceptance criteria requires **≥70%
accept/accept_with_edits** AND **<20% reject_duplicate**. Strict application
of the Stage 3 deterministic decision rule (rule 2: novelty=near-duplicate
takes precedence over realism/tool-path) yields 5/15 = 33% promotable and
10/15 = 67% reject_duplicate. **Both criteria fail.** Per § "Failure path"
of the methodology, the per-scenario ratings are retained and the
`accept_with_edits` subset is available for descriptive analysis under
explicit caveat — no batch is published as benchmark-ready, and no
generated scenario should be promoted into top-level `data/scenarios/`
without applying the bounded edits in the CSV's `required_edit` column
and getting a fresh review.

**Recurring failure patterns** (informs the v0.3 prompt iteration on PR #186):

1. **Ground truth not MCP-grounded** — every `T-001..T-005` asset in
   `data/processed/` has `fault_label=Normal` and `health_index=1.0`, but
   most generated scenarios assert D2 / T3 / specific RUL values. A correct
   tool-using agent would be scored wrong against the fabricated ground truth.
2. **`wo.estimate_downtime` severity-source missing** (502/SGT-GEN-003,
   503/SGT-GEN-003, 505/SGT-GEN-003) — `wo.estimate_downtime` requires a
   `severity` argument, but `wo.list_fault_records()` (the v0.2 prompt fix's
   added precondition) does not return a `severity` field. The
   `data/processed/fault_records.csv` schema has `maintenance_status`,
   `component_health`, `temperature_c`, `duration_hrs`, `downtime_hrs` — no
   `severity`/`priority` column. **The v0.2 fix is therefore incomplete**:
   inserting `wo.list_fault_records` before `wo.estimate_downtime` does not
   actually supply severity. Fix path for v0.3 prompts: pin `severity` in the
   prompt or in `decisive_intermediate_values` (e.g. derived deterministically
   from `temperature_c` and `maintenance_status`), or extend
   `wo.list_fault_records` to surface a derived severity. `505/SGT-GEN-003` is
   downgraded from `tool_path_rating=good` to `fixable` accordingly.
3. **`fmsr.analyze_dga` without preceding `fmsr.get_dga_record`** — fixed
   for FMSR-only scenarios in v0.2 but still violated for multi-domain
   (505/SGT-GEN-005). The v0.2 README's option-2 (post-generation validator)
   would catch this regardless of prompt size.
4. **Sensor unpinned** — `iot.get_sensor_readings` without `iot.list_sensors`
   discovery or an explicit `sensor_id` source recurs across IoT scenarios.
5. **Internal contradictions** — gas-rationale text and labeled fault code
   disagree (502/SGT-GEN-005, 503/SGT-GEN-001, 505/SGT-GEN-001).

**Promotion-eligible subset:** the 5 `accept_with_edits` rows
(`first_review_20260502/SGT-GEN-001`, `first_review_20260502/SGT-GEN-004`,
`first_review_20260503/SGT-GEN-004`, `v02_first_review_20260505/SGT-GEN-003`,
`v02_first_review_20260505/SGT-GEN-004`) are candidates for the canonical
`data/scenarios/` corpus once the bounded edits in the CSV's `required_edit`
column are applied with provenance retained (`source_type: generated`, batch
metadata preserved, **and** `nearest_handcrafted_comparator.scenario_file`
updated to the reviewer-selected comparator where it diverges from the
embedded one — see CSV columns `nearest_handcrafted_scenario_id` vs
`nearest_handcrafted_embedded`; all 5 promotion-eligible rows have a
divergence that must be reconciled before promotion). At 5 promotions, the canonical
floor moves from 31 → 36 — **insufficient to clear the issue #55 stretch goal
of 50+ on its own.** Promotion lives in a separate PR per the issue #55 lane;
no generated scenario is moved into top-level `data/scenarios/` by this PR.

**Recommendation for issue #55:** generated-scenario promotion alone cannot
hit 50; combine with a hand-crafted batch of ≥14 new scenarios. Alternatively,
defer #55 per its `post-class-defer` label and ship at 31 + 5 = 36 once the
edits land in a follow-up PR.
