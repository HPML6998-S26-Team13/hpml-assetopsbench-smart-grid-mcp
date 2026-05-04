# Grounding Notes — Scenarios SGT-021 through SGT-030

*Owner: Akshat Bhandari | Created: 2026-05-03 | Issue: #33*

This note documents how the second batch of 10 hand-crafted scenarios
(SGT-021–SGT-030) is grounded in standards, the existing data pipeline, and
documented utility-practice patterns. It complements
[`docs/scenario_realism_validation.md`](scenario_realism_validation.md) (the
mentor-review pack from the first batch) and the
[`docs/methodology_fact_pack.md`](methodology_fact_pack.md) Scenario Set summary.

## Grounding sources used

Each scenario in this batch draws from one or more of the following:

| Source | Artifact | What it provides |
|---|---|---|
| **Schema** | `data/scenarios/validate_scenarios.py` | Hard-enforced: asset IDs must exist in `data/processed/asset_metadata.csv`, tools must be in canonical 19-tool list, single/multi-domain consistency. All 10 new files pass. |
| **Standards** | `data/knowledge/transformer_standards.json` (#50) | IEC 60599:2022 Rogers Ratio fault table, IEEE C57.104-2019 condition tiers, `scenario_generator_hints` for DGA/RUL field grounding. |
| **Domain realism** | `docs/scenario_realism_validation.md` (#60) | 5 documented patterns: DGA needs trending, condition-dependent decision horizons, real WO field schemas, operating context must-haves, emergency-vs-high priority triggers. |
| **Data pipeline** | `data/generate_synthetic.py` + `data/processed/` | Asset health tiers are deterministic: T-001–T-010 healthy, T-011–T-015 degraded, T-016–T-020 critical. Voltage classes and ratings drawn from realistic enumerations (132kV/33kV, 33kV/11kV, 11kV/0.4kV; 500–5000 kVA). |
| **Authoring contract** | `docs/methodology_fact_pack.md` | No tool hints in prompts; no ratio/threshold/IEC-code leaks in task text; ≤80 words; ground truth via `must_include` strings. |

## Per-scenario grounding

| ID | Real-world workflow | Asset rationale | Standards / pattern reference |
|---|---|---|---|
| **SGT-021** Sensor Coverage Audit | Reliability engineer audits monitoring on a high-voltage transmission unit before planning a sensor retrofit or determining what fault classes are detectable. | T-007 = 132kV/33kV, 5000 kVA, ABB, Industrial Park A — the largest healthy transmission-class unit in the fleet. | Operating-context must-have #2 (asset criticality / load served) from `scenario_realism_validation.md` §4. |
| **SGT-022** Fleet Status Snapshot | Asset manager pulls a comparative healthy-vs-degraded telemetry view for daily fleet awareness or shift handoff. The agent enumerates installed sensor channels per asset before pulling readings (mirroring how an operator first orients to what is monitored). | T-005 (healthy, 11kV/0.4kV) vs T-013 (degraded, 33kV/11kV) — the comparison frames the difference between a baseline unit and a Condition 2-equivalent unit. | Condition framework from IEEE C57.104-2019 (`ieee_c57_104` block in standards JSON): Condition 1 = healthy, Condition 2 = trending. Tools: `iot.list_assets` + `iot.list_sensors` + `iot.get_sensor_readings`; difficulty medium (3-tool, 2-asset iteration). |
| **SGT-023** DGA Record Interpretation | Maintenance engineer reviews an existing DGA report and traces gas signature to a failure family, prior to ordering a confirmatory sample. | T-013 = degraded tier, 33kV/11kV — typical Condition 2 unit where DGA interpretation is the actionable next step. | IEC 60599:2022 Rogers Ratio (`iec_60599` block) — the `analyze_dga` tool implements this method and `failure_modes.csv` enumerates the matching IEC fault codes (PD, T1, T2, T3, D1, D2). |
| **SGT-024** Severity-Filtered Failure Mode Review | Operations planner builds a spare-parts and inspection plan focused on worst-case modes (high/critical only). | No asset reference — catalog-level query against `failure_modes.csv` (FM-001 through FM-006). | `failure_modes.csv` has explicit `severity` column (low/medium/high/critical) sourced from IEC fault-code severity ratings. |
| **SGT-025** Anomaly Burst vs Trend Disambiguation | Operator triages a short window of unusual readings and needs to determine if it's a transient or the start of a sustained shift, before escalating. The agent first identifies which sensor channels exist on T-014, then runs anomaly + trend analysis on the relevant channel(s). | T-014 = degraded tier — realistic candidate for marginal anomalies that could go either way. | DGA-trending finding from `scenario_realism_validation.md` §1 (single sample is not sufficient — requires trend evaluation). The same principle applies to all sensor streams, not just DGA. **Now Multi (IoT+TSFM)**, file `multi_07_iot_tsfm_anomaly_burst.json`. |
| **SGT-026** RUL Current vs Forecast Comparison | Capital planner compares today's RUL value against forecasted RUL over a planning horizon to defend a defer/advance decision in the next budget cycle. | T-011 = degraded tier (RUL ~730-day base from `generate_synthetic.py`) — realistic unit at a budget-cycle decision boundary. | Maintenance decision horizons from `scenario_realism_validation.md` §2: 1–6 months = "Medium-term planned" for Condition 2 units. 180-day window matches that band. |
| **SGT-027** Work Order Lifecycle (Open and Close) | Field-completed inspection logged via the full open→close lifecycle — agent calls `wo.create_work_order` (returns WO-ID), then chains that ID into `wo.update_work_order(status="closed")`. Tests output→input chaining and the only WO lifecycle pair not exercised elsewhere in the corpus. | T-009 = healthy tier — routine closure, low-stakes. | WO field schema from `scenario_realism_validation.md` §3 — completion section requires findings + updated condition data. Output→input chaining is itself the test surface. |
| **SGT-028** Downtime Estimation for Planned Outage | Planner estimates outage duration ahead of a high-severity corrective shutdown, using fault history to characterise the dominant repair pattern. Severity tier is named in the prompt (high) because `list_fault_records` does not return severity directly, so naming it preserves a deterministic grading target. | T-018 = critical tier — realistic candidate for a planned corrective outage where downtime estimation matters for cost/customer-impact analysis. | WO planning-section field "estimated duration" from `scenario_realism_validation.md` §3. The `wo.estimate_downtime` tool requires `(transformer_id, severity)` so severity is supplied by the prompt. |
| **SGT-029** DGA Finding to Inspection Work Order | Maintenance team converts a fresh DGA result into a prioritized field action — classic FMSR → WO triage pattern. | T-019 = critical tier — DGA-driven escalation is most realistic on a unit already in the critical band. | Emergency vs high-priority triggers from `scenario_realism_validation.md` §5: Condition 4 gas levels = emergency; Condition 3 with rising trend = high. The `must_include` requires the priority to be justified by the severity tier. |
| **SGT-030** Anomaly Detection and RUL Forecast to Work Order | Four-step pipeline: identify sensor channels → anomaly detection → RUL forecast → work-order creation. Anomaly findings and RUL forecast are framed as parallel evidence streams that jointly inform WO scope/priority (no false claim that the forecast is "conditioned on" the anomaly result — `tsfm.forecast_rul` only takes `transformer_id` and `horizon_days`). | T-020 = critical tier — realistic candidate for an automated CBM trigger and immediate WO. | Combines the DGA-trending principle (§1) with maintenance-decision horizons (§2) and emergency-vs-high triggers (§5). The 90-day horizon corresponds to "Short-term corrective" (1–4 wk) extending into early "Medium-term planned" (1–6 mo). **Now Multi (IoT+TSFM+WO)**, 4 tools. |

## What this batch does NOT do

To set expectations for the upstream PR review:

- **No real-asset references.** All transformer attributes (manufacturer, location, install date) are synthesized by `data/generate_synthetic.py` (SEED=42) — see [`data/README.md`](../data/README.md) §"The transformer_id key" for the synthetic-fleet rationale.
- **No real maintenance-ticket corpus.** The prompts are designed against IEC/IEEE patterns and the deep-research artifact (`deep-research-runs/20260411_*/report.md`), not transcribed from real utility tickets. The synthetic prompts are *believable transformer O&M tasks*, not transcripts.
- **No statistical fidelity proof on the underlying data.** That validation is the L3 validator (`data/scenarios/validate_realism_statistical.py`, issue #84) — orthogonal to scenario design and tracked separately.

## v1 review correction (2026-05-04)

The first-cut versions of SGT-022, SGT-025, SGT-027, SGT-028, and SGT-030 passed the schema validator but failed at **tool-signature precondition** time: the validator confirms each tool name is canonical, but does not check whether the prompt + chain provides every required argument the actual MCP server functions need (e.g. `iot.get_sensor_readings` and `tsfm.detect_anomalies` require a `sensor_id` the prompt did not name; `wo.update_work_order` requires a session-resident WO ID the corpus did not preload; `wo.estimate_downtime` requires a `severity` string `list_fault_records` does not return).

The five scenarios above were reworked after a direct read of `mcp_servers/{iot,fmsr,tsfm,wo}_server/server.py` and a Python REPL dry-run of each chain's first call. SGT-025 was reclassified TSFM → Multi (IoT+TSFM) and the file renamed to `multi_07_iot_tsfm_anomaly_burst.json`. SGT-030 was widened to Multi (IoT+TSFM+WO).

A follow-up issue should extend `validate_scenarios.py` to do tool-signature precondition checks (e.g. introspect `inspect.signature()` on each canonical tool and assert that `expected_tools` covers any required arg without a default).

## Verification

```bash
python data/scenarios/validate_scenarios.py
# Expected: Validation passed for 31 scenario files and 5 negative fixtures.
```

## Cross-references

- Issue: #33 (Reach 30+ scenarios)
- Companion validation note (first batch, mentor-review pack): `docs/scenario_realism_validation.md`
- Methodology summary: `docs/methodology_fact_pack.md`
- IEC standards artifact: `data/knowledge/transformer_standards.json`
- Synthetic data pipeline: `data/generate_synthetic.py`
- Validator: `data/scenarios/validate_scenarios.py`
