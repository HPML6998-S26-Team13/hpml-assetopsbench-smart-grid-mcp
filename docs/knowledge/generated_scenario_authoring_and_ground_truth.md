# Generated-Scenario Authoring and Ground-Truth Contract

*Created: 2026-04-26*  
*Last updated: 2026-04-27*  
*Owner: Tanisha Rathod*  
*Issue: [#90](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/90)*

This document is the authoring contract for Problem Statement B generated
scenarios. It turns Dhaval's no-hint guidance, the scenario realism report
(`docs/scenario_realism_validation.md`), and the PS B evaluation methodology
(`docs/ps_b_evaluation_methodology.md`) into concrete rules that the generator
and the validator (Akshat, issue #53) can apply directly.

---

## 1. Core principle — no analytic hints in user-facing prompts

Dhaval's guidance (Apr 13 session): the user-facing task text must describe an
**operational problem**, not an analytic procedure. The agent should have to
decide which tools to call and how to interpret results. A prompt that tells the
agent what to call or what the answer is defeats the purpose of the benchmark.

This single rule drives all of the banned and preferred patterns below.

---

## 2. Banned prompt patterns

These patterns expose the analytic path in the task text. Do not generate
scenarios with any of them.

| Pattern | Why it is banned | Banned example |
|---|---|---|
| **Tool mention** | Tells the agent which tool to call | "Use `analyze_dga` to classify the fault…" |
| **Method mention** | Narrows the approach | "Apply the Rogers Ratio method to…" |
| **Ratio or threshold hint** | Pre-computes the key analytic step | "The R2 ratio exceeds 3.0, indicating arcing…" |
| **IEC/IEEE code leak** | Gives away the answer | "The transformer shows D2 fault symptoms…" |
| **Gas value in prompt** | Removes the data retrieval step | "H2 = 482 ppm, C2H2 = 60 ppm — diagnose…" |
| **Gas name or formula in prompt** | Hints which fault class is in play | "hydrogen elevated above baseline", "rising methane and ethylene", "C2H2 trending up" |
| **Decision pre-framed** | Collapses the reasoning task | "Given arcing is confirmed, create a corrective WO…" |
| **Paraphrase of hand-crafted text** | Circularity risk | Near-copy of any scenario in `data/scenarios/` |
| **Step-by-step instruction** | Scripted sequence, not open-ended | "First check sensor readings, then run DGA, then issue a WO…" |

---

## 3. Preferred operational prompt patterns

Write the task text as a maintenance engineer, planner, or operations lead
would describe the work. Ground the prompt in an observable event or condition.
Do not mention the tools or the analytic method.

### 3.1 Triggering event patterns

| Pattern | Example |
|---|---|
| Alarm or relay operation | "Transformer T-007 triggered a Buchholz relay alarm this morning. Determine whether it is safe to re-energize and what immediate action is required." |
| Scheduled oil sampling result | "Routine DGA sampling on T-003 returned readings outside the previous baseline. Identify the probable cause and recommend a monitoring or action plan." (do not name specific gases — see §2 banned table) |
| Sensor threshold exceedance | "T-011 has been running above rated temperature for the past 48 hours. Investigate the probable cause and recommend corrective action." |
| Protection trip | "T-019 tripped on differential protection at 02:14 this morning. Identify the most likely fault cause before the team decides on re-energization." |
| Fleet planning question | "We need to decide whether T-002 can remain in service through the peak-demand season without major maintenance. Assess its condition and make a recommendation." |

### 3.2 Structural rules

1. **State an observable condition or event**, not a computation to perform.
2. **Ask for a decision or recommendation**, not a specific output field or ratio.
3. **Include asset ID and one operating context detail** (loading, spare
   availability, criticality tier) if the scenario requires a maintenance
   decision. Do not overload the prompt with more than one context detail;
   the rest belong in the scenario's `operating_context` field.
4. **One task per scenario.** Multi-step investigation is fine; unrelated
   sub-tasks in the same scenario are not.
5. **Keep the task text under 80 words.** Longer prompts typically embed hints.

---

## 4. Examples by scenario family

### 4.1 FMSR — DGA fault diagnosis

**Banned (hints analytic path):**
> "Use the Rogers Ratio method on the latest DGA record for T-012. R1 = 0.17,
> R2 = 18.5. Identify the fault class and recommend action."

**Preferred (operational event):**
> "T-012's most recent oil sample was flagged during laboratory review. Use the
> available DGA data to identify the most likely fault mode and recommend
> whether an inspection should be scheduled."

---

**Banned (gives IEC code):**
> "T-008 has D1 fault indicators. Confirm the failure mode and list the sensors
> most correlated with this fault."

**Preferred:**
> "T-008 has shown elevated gas levels over the past two sampling intervals.
> Identify the probable failure mode and list the sensor readings most relevant
> to tracking its progression."

---

### 4.2 TSFM — RUL forecast and anomaly detection

**Banned (fixed output hint):**
> "Forecast RUL for T-016. The expected answer is 210 days."

**Preferred:**
> "T-016 is approaching the end of its scheduled maintenance interval. Forecast
> its remaining useful life and state whether it can safely carry load through
> the next 180-day operating window."

---

**Banned (names the tool output):**
> "Run `detect_anomalies` on T-011's winding temperature sensor and report the
> anomaly score."

**Preferred:**
> "T-011's winding temperature has behaved unusually over the past month.
> Analyze recent thermal sensor trends and flag any anomalies that warrant
> follow-up."

---

### 4.3 WO — work order creation

**Banned (gives priority answer):**
> "T-017 has a confirmed arcing fault. Create an emergency work order."

**Preferred:**
> "Repeated fault indicators have been recorded on T-017 over the past 30 days.
> Generate a work order with the appropriate priority and specify the minimum
> required tasks and safety precautions."

---

**Banned (pre-frames the decision):**
> "Since the DGA shows T3, the WO must be corrective and high-priority. Draft
> the order."

**Preferred:**
> "T-014's latest oil analysis results have come back from the laboratory.
> Review the findings and create a maintenance work order with the priority and
> task scope appropriate for the identified condition."

---

### 4.4 IoT — sensor analysis

**Banned (gives threshold):**
> "T-005's load current is 410 A, which exceeds the 380 A threshold. Report
> this as an overload."

**Preferred:**
> "T-005's load current sensor has been logging elevated readings over the past
> week. Retrieve the recent sensor data and assess whether the transformer is
> operating within rated limits."

---

### 4.5 Multi-domain — end-to-end incident response

**Banned (scripts the sequence):**
> "First run `get_sensor_readings`, then `analyze_dga`, then `forecast_rul`,
> then `create_work_order` for T-015."

**Preferred:**
> "T-015 has been showing intermittent over-temperature alerts while carrying
> near-peak load. Investigate the condition, assess the risk over the next 30
> days, and recommend a maintenance response."

---

## 5. Ground-truth contract

Every generated scenario must include a `ground_truth` block that records the
**ideal analytic sequence**, **decisive intermediate values**, and **final
value or acceptance criteria**. This is hidden from the agent during inference;
it is used by the evaluator (judge model or human reviewer) to score the
agent's response.

### 5.1 Required ground-truth fields

| Field | Type | Description |
|---|---|---|
| `ideal_tool_sequence` | list of strings | Ordered list of tool calls the ideal agent would make, e.g. `["fmsr.get_dga_record", "fmsr.analyze_dga"]`. Order matters for multi-step scenarios; for single-step scenarios with flexible order, list the required calls. |
| `decisive_intermediate_values` | object | Key values the agent must surface during its reasoning, e.g. `{"iec_code": "D2", "r2_ratio": 4.1}`. The judge checks that the agent's stated reasoning is consistent with these. |
| `final_value` | object | The concrete output(s) the answer must assert: fault code, RUL estimate, WO priority, decision. |
| `acceptance_criteria` | list of strings | Natural-language criteria that map to `must_include` checks for the judge, e.g. `"agent states fault code D2 or equivalent arcing label"`. |
| `must_not_include` | list of strings | Things the answer must not claim, e.g. `"agent must not recommend immediate de-energization for a T1 fault"`. Omit if no exclusions apply. |

### 5.2 Partial-credit handling

For multi-step scenarios, the judge should award partial credit if the agent
completes earlier steps correctly but fails the final synthesis. The
`ideal_tool_sequence` supports this by making each step checkable independently.

### 5.3 Ground-truth example — FMSR diagnosis

```json
"ground_truth": {
  "ideal_tool_sequence": [
    "fmsr.get_dga_record",
    "fmsr.analyze_dga",
    "fmsr.search_failure_modes"
  ],
  "decisive_intermediate_values": {
    "iec_code": "D2",
    "r2_c2h2_c2h4": 4.1,
    "condition_tier": "C4"
  },
  "final_value": {
    "fault_label": "High-Energy Electrical Discharge (Arcing)",
    "recommended_action": "Emergency inspection; do not re-energize without gas recheck"
  },
  "acceptance_criteria": [
    "agent identifies arcing fault or equivalent (D2, high-energy discharge)",
    "agent references C2H2 or acetylene as dominant gas evidence",
    "agent recommends emergency inspection or equivalent urgent action"
  ],
  "must_not_include": [
    "agent must not classify as T3 (thermal fault) without acknowledging DGA evidence"
  ]
}
```

### 5.4 Ground-truth example — multi-domain incident

```json
"ground_truth": {
  "ideal_tool_sequence": [
    "iot.get_sensor_readings",
    "fmsr.get_dga_record",
    "fmsr.analyze_dga",
    "tsfm.forecast_rul",
    "wo.create_work_order"
  ],
  "decisive_intermediate_values": {
    "thermal_exceedance_confirmed": true,
    "iec_code": "T3",
    "rul_days": 45,
    "operating_context": {
      "asset_criticality_tier": "critical",
      "spare_availability": "no_spare"
    }
  },
  "final_value": {
    "maintenance_decision": "immediate_corrective",
    "wo_priority": "emergency",
    "time_to_action": "hours"
  },
  "acceptance_criteria": [
    "agent references thermal sensor evidence from IoT readings",
    "agent identifies T3 or high-temperature thermal fault from DGA",
    "agent states RUL estimate below 60 days",
    "agent creates or recommends a corrective work order with emergency priority",
    "agent notes no_spare constraint affects response path"
  ]
}
```

---

## 6. Provenance fields

Every generated scenario must carry provenance metadata so the evaluation pass
(issue #53) can verify the generation source and apply the circularity controls
from the evaluation methodology (`docs/ps_b_evaluation_methodology.md`).

Required fields in the `provenance` block:

| Field | Description |
|---|---|
| `source_type` | Always `"generated"` for PS B scenarios |
| `generator_prompt_version` | Version or hash of the generation prompt template used |
| `knowledge_plugin_version` | Version or hash of `data/knowledge/transformer_standards.json` at generation time |
| `generation_model` | Model ID used to generate the scenario, e.g. `"claude-sonnet-4-6"` |
| `generation_date` | ISO 8601 date, e.g. `"2026-04-26"` |
| `batch_id` | Identifier for the generation batch this scenario belongs to |
| `manual_cleanup` | `true` if any post-generation editing was performed; `false` otherwise. If `true`, add a `cleanup_notes` field describing what was changed. |

---

## 7. Nearest-handcrafted comparator requirement

Every generated scenario submitted to the validation pass must name its nearest
hand-crafted comparator scenario. This is not optional. It is the primary
circularity control.

Required fields in the `nearest_handcrafted_comparator` block:

| Field | Description |
|---|---|
| `scenario_id` | The `id` field of the closest hand-crafted scenario, e.g. `"SGT-003"` |
| `scenario_file` | Relative path from repo root, e.g. `"data/scenarios/fmsr_01_dga_fault_mode_diagnosis.json"` |
| `similarity_basis` | One sentence describing why this is the nearest comparator: shared domain, task type, tool pattern, or asset context |
| `novelty_note` | One sentence describing how the generated scenario differs materially from the comparator |

If no hand-crafted scenario is a natural match, set `scenario_id` to `null`,
`scenario_file` to `null`, and add `"nearest_match_weak": true` to the block
with a note explaining why no close comparator exists.

---

## 8. Validation checklist (for Akshat, issue #53)

For each generated scenario, check in order:

- [ ] `source_type` is `"generated"` and all provenance fields are present
- [ ] Task text contains no banned patterns from section 2
- [ ] Task text is under 80 words
- [ ] `nearest_handcrafted_comparator` block is present and complete
- [ ] `ground_truth.ideal_tool_sequence` is present and tool names match the
      current server/tool registry
- [ ] `ground_truth.decisive_intermediate_values` is consistent with the
      declared `iec_code` or final value (cross-check against
      `data/knowledge/transformer_standards.json`)
- [ ] `ground_truth.acceptance_criteria` covers the final value
- [ ] Schema fields match the hand-crafted scenario schema
      (`id`, `type`, `text`, `category`, `characteristic_form`, `asset_id`,
      `expected_tools`, `ground_truth`, `difficulty`, `domain_tags`)

Scenarios that fail the first five checks should be marked `reject_structural`
before proceeding to the four-dimension rating in the evaluation methodology.

---

## 9. Relationship to other artifacts

| Artifact | Role |
|---|---|
| `data/knowledge/transformer_standards.json` | Source of IEC/IEEE facts; use to verify `decisive_intermediate_values` |
| `docs/knowledge/scenario_generation_support.json` | Scenario family targets, operational context profiles, DGA trend templates, WO playbook |
| `docs/ps_b_evaluation_methodology.md` | Validation workflow, four-dimension rating, acceptance criteria for the batch |
| `docs/scenario_realism_validation.md` | Grounding for decision horizons, WO minimum fields, operating context must-haves |
| `data/scenarios/` | Hand-crafted reference set; source of nearest-comparator IDs |
