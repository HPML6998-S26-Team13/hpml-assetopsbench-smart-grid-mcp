# Methodology Fact Pack — SmartGridBench

*Issue #41 deliverable. 1-page bullet fact pack for paper/report data, server, and methodology sections.*
*Owner: Tanisha Rathod | Created: 2026-05-01*

---

## Data

**Sources (5 Kaggle datasets; 3 are CC0, 2 have redistribution restrictions):**
- Power Transformers FDD & RUL → IoT sensor readings + RUL labels *(CC0)*
- DGA Fault Classification → dissolved gas records + fault labels *(CC0)*
- Smart Grid Fault Records → maintenance/fault event history *(CC0)*
- Transformer Health Index → supplemental FMSR features *(redistribution restrictions; local-only)*
- Current & Voltage Monitoring → supplemental IoT time-series *(redistribution restrictions; local-only)*

**Processed outputs (6 CSVs, all synthetic-safe):**

| File | Rows | Key fields |
|---|---|---|
| `asset_metadata.csv` | 20 transformers (T-001–T-020) | name, manufacturer, voltage_class, rating_kva, health_status, rul_days |
| `sensor_readings.csv` | 86,400 readings | transformer_id, timestamp, sensor_id, value, unit |
| `dga_records.csv` | 20 records | H2, CH4, C2H2, C2H4, C2H6, CO, CO2 (ppm), fault_label |
| `failure_modes.csv` | 6 modes | iec_code, severity, recommended_action |
| `rul_labels.csv` | 620 records | rul_days, health_index, fdd_category |
| `fault_records.csv` | 41 events | fault_type, maintenance_status, component_health, downtime_hrs |

**No proprietary data shipped.** Raw Kaggle downloads remain local-only/gitignored; tracked `data/processed/` CSVs are public-safe synthetic outputs regenerable via `data/generate_synthetic.py`.

---

## MCP Servers (19 tools across 4 domains)

| Server | Tools | What it exposes |
|---|---|---|
| **IoT** (4) | `list_assets`, `get_asset_metadata`, `list_sensors`, `get_sensor_readings` | Asset registry + time-series sensor telemetry |
| **FMSR** (5) | `list_failure_modes`, `search_failure_modes`, `get_sensor_correlation`, `get_dga_record`, `analyze_dga` | DGA classification via IEC 60599:2022 Rogers Ratio; failure mode catalogue search |
| **TSFM** (4) | `get_rul`, `forecast_rul`, `detect_anomalies`, `trend_analysis` | Remaining useful life forecasting + sensor trend/anomaly analysis |
| **WO** (6) | `list_fault_records`, `get_fault_record`, `create_work_order`, `list_work_orders`, `update_work_order`, `estimate_downtime` | Work order lifecycle + historical fault record access |

**Transport modes:** MCP JSON-RPC stdio (Cells B/C/D/Y/Z) vs. direct Python callables (Cell A). Both surfaces backed by the same server logic.

**IEC 60599:2022 encoding:** `analyze_dga` implements the Rogers Ratio fault table (4th ed., publication 66491) classifying dissolved gas profiles into IEC fault codes (N, PD, D1, D2, T1, T2, T3). It does not return IEEE C57.104-2019 condition tiers.

---

## Scenario Set

- **31 hand-crafted scenarios** (SGT-001–SGT-030 + AOB-FMSR-001), validator-clean
- **Coverage:** IoT (6), FMSR (7), TSFM (4), WO (6), Multi-domain (8)
- **Difficulty:** easy (8), medium (15), hard (8)
- **Target:** 50+ as stretch (issue #55); generator-assisted batch tracked separately under PR #163 / issue #2
- **Authoring contract:** no tool hints, no ratio/threshold leaks, no IEC code reveals in task text; all prompts under 80 words; ground truth uses `must_include` string criteria

---

## Experiment Grid (9 cells, Llama-3.1-8B-Instruct, 3 trials/scenario — 6 judged runs/cell)

| Cell | Display | Orchestration | Transport | p50 lat (s) | Judge score | Judge pass |
|---|---|---|---|---|---|---|
| A | AT-I | Agent-as-Tool | Direct Python | 12.15 | 0.167 | 1/6 (16.7%) |
| B | AT-M | Agent-as-Tool | MCP baseline | 13.09 | 0.278 | 2/6 (33.3%) |
| C | AT-TP | Agent-as-Tool | MCP + prefix cache | 7.40 | 0.167 | 0/6 (0.0%) |
| D | AT-TPQ | Agent-as-Tool | MCP + INT8/BF16 KV | 6.17 | 0.167 | 1/6 (16.7%) |
| Y | PE-M | Plan-Execute | MCP baseline | 52.06 | 0.111 | 0/6 (0.0%) |
| YS | PE-S-M | Plan-Execute + Self-Ask | MCP baseline | 59.00 | 0.444 | 3/6 (50.0%) |
| Z | V-M | Verified PE | MCP baseline | 119.64 | 0.639 | 4/6 (66.7%) |
| ZS | V-S-M | Verified PE + Self-Ask | MCP baseline | 33.78 | **0.833** | 5/6 (83.3%) |
| ZSD | V-S-TPQ | Verified PE + Self-Ask | MCP + INT8/BF16 KV | 55.17 | 0.611 | 3/6 (50.0%) |

**Key findings:**
- MCP transport overhead (B − A): **+0.94s p50** per trial (+1.20s mean per notebook02_latency_summary.csv)
- Best quality: ZS (Verified PE + Self-Ask) at 0.833 judge score, 83.3% pass rate
- Optimized serving (C, D) cuts latency by 40–53% vs B but does not improve quality
- Self-Ask consistently improves quality within each orchestration family (Y→YS, Z→ZS)
- Adding optimized serving to the best PE configuration (ZS→ZSD) degraded both latency and quality in first-capture runs

---

## Evaluation

**Judge model:** Llama-4 Maverick 17B (WatsonX-hosted) — same model family as inference, different from task model to avoid self-grading bias.

**Rubric (6 binary criteria per trial):**
1. Correct tool(s) called
2. Tool arguments well-formed
3. Reasoning grounded in tool outputs
4. Final answer addresses the scenario task
5. No hallucinated facts contradicting tool outputs
6. Safety / operational soundness of recommendation

**Score:** `score_6d` = fraction of 6 criteria passing (0.0–1.0). Judge pass = `score_6d ≥ 0.6`.

**Scenarios per cell:** 2 multi-domain scenarios × 3 trials = 6 judged runs per cell.

---

## Paper-safe caveats

- DGA records use publicly-derived synthetic values; stored `fault_label` values reflect intended synthetic ground truth, but not all records round-trip through `analyze_dga` consistently — downstream users should verify any asset's DGA label against the analyzer before treating it as benchmark ground truth.
- First-capture results use 3 trials per scenario (6 judged runs per cell); final canonical run targets 5 trials per scenario.
- ZSD degradation vs ZS is a first-capture artifact; the optimized-serving benefit is cleaner in AaT cells (C, D) where orchestration overhead is lower.
