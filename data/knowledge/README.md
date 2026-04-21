# data/knowledge/

Structured standards artifacts for the PS B scenario generation pipeline. Issue #50.

## Files

| File | Contents |
|------|----------|
| `transformer_standards.json` | IEC 60599 Rogers Ratio table, representative gas profiles, IEEE C57.104-2019 condition thresholds, operational context, and generator hints |

---

## Schema — `transformer_standards.json`

Top-level keys:

| Key | Purpose |
|-----|---------|
| `meta` | Source citations, schema version, server alignment note |
| `iec_60599` | Rogers Ratio fault table, key gas guide, representative gas profiles |
| `ieee_c57_104` | Four-condition framework, per-gas thresholds (Table 1), rate-of-generation rule |
| `operational_context` | Maintenance decision horizons, work order minimum fields, asset operating context |
| `scenario_generator_hints` | Direct per-scenario-type instructions for the generation pipeline |

### `iec_60599.rogers_ratio_method.fault_table`

Each entry maps a fault code to its R1/R2/R3 ratio ranges:

```json
{
  "iec_code": "D2",
  "label": "High-Energy Electrical Discharge (Arcing)",
  "R1_range": [0.1, 3.0],
  "R2_range": [3.0, null],
  "R3_range": [3.0, null],
  "severity": "critical",
  "condition_4_trigger": true
}
```

`null` in a range means unbounded. `condition_4_trigger: true` means this fault
code should be paired with IEEE C57.104 Condition 3–4 gas values.

### `iec_60599.representative_gas_profiles`

Pre-computed gas values (ppm) that produce each fault code from the
`fmsr_server.analyze_dga` MCP tool. Use these as the base for scenario gas
inputs — vary each value ±20% to create distinct instances while preserving
the target `iec_code`.

```json
"D2": {
  "H2": 500, "CH4": 100, "C2H2": 60, "C2H4": 120, "C2H6": 50,
  "CO": 300, "CO2": 2800,
  "expected_iec_code": "D2"
}
```

### `ieee_c57_104.gas_thresholds_ppm`

Per-gas condition boundaries from IEEE C57.104-2019 Table 1. Use these to set
realistic gas values that land in the target condition level:

```json
"C2H2": { "C1_max": 1, "C2_max": 9, "C3_max": 35, "C4": ">35" }
```

### `operational_context`

Contains three sub-sections used for multi-domain scenario context:

- `maintenance_decision_horizons` — maps urgency level to realistic time windows and trigger conditions
- `work_order_minimum_fields` — minimum fields for a realistic corrective WO
- `asset_operating_context` — the three must-have fields for realistic multi-domain scenarios: `asset_criticality_tier`, `spare_availability`, `current_loading_pct`

---

## Generator consumption instructions

The `scenario_generator_hints` section at the bottom of `transformer_standards.json`
contains per-scenario-type instructions. Quick reference:

### Step 1 — Pick a fault type

Choose a target `iec_code` from `iec_60599.rogers_ratio_method.fault_table`.
Use `representative_gas_profiles[iec_code]` as the gas input baseline.

### Step 2 — Set condition level

Look up each gas in `ieee_c57_104.gas_thresholds_ppm`. Choose values that land
in Condition 2 or 3 for interesting scenarios. Condition 1 is normal (trivial);
Condition 4 should be reserved for emergency/critical scenarios.

### Step 3 — Assign urgency and horizon

Use `operational_context.maintenance_decision_horizons` to pick the urgency
and time window appropriate for the fault code:

| iec_code | Urgency | Horizon |
|----------|---------|---------|
| D2, T3   | emergency | Hours to days |
| D1, T2   | high | Days to 2 weeks |
| PD, T1   | medium | 1–6 months |
| N        | low | 6 months+ |

### Step 4 — Add operating context

For multi-domain scenarios, always set:
- `asset_criticality_tier` (critical / important / standard)
- `spare_availability` (in_stock / lead_time_2_weeks / lead_time_3_months / no_spare)
- `current_loading_pct` (30–110)

### Step 5 — Gas consistency

If the scenario involves both IoT sensor readings and a DGA analysis call,
use the same gas values from step 1 in both places.

### Step 6 — Variation

Vary each gas ±10%, vary `transformer_id` (T-001 to T-030), and vary one
operating context field per scenario instance to ensure distinct decision paths.
Do not exceed ±10% — some profiles sit close to ratio boundaries and larger
variation flips the fault code.

---

## Citation

When Alex uses these facts in the paper, cite the two source standards listed
in `meta.sources`:

- IEC 60599:2022 (3rd edition) — Rogers Ratio method and fault code definitions
- IEEE C57.104-2019 — Condition 1–4 framework and per-gas thresholds

---

## Alignment

This artifact was coordinated with the generation pipeline owner (Aaron, issue #2)
before finalization. If the generator needs additional fields or a different
representation, update this file and note the change in the issue.
