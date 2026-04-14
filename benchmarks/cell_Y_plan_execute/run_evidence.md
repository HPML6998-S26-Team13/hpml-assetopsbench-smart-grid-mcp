# Cell Y — Plan-Execute Benchmark Run Evidence

This document is the concrete proof package requested in issue #57 and the
subsequent review comment.  It records two successful end-to-end benchmark
runs on the canonical `main`-branch history of this repository:

1. **Watsonx plan-execute run** (2026-04-13) — full LLM + MCP tool-call path.
2. **Local MCP direct-smoke run** (2026-04-14) — no-credential CI-reproducible
   path exercising the same 8-tool-call sequence without an LLM.

Both runs target the same scenario and produce artifacts in the canonical
`benchmarks/cell_Y_plan_execute/raw/<run-id>/` layout from `benchmarks/README.md`.

---

## Run 1 — Watsonx plan-execute (2026-04-13)

### Scenario

| Field            | Value |
|------------------|-------|
| Scenario file    | `data/scenarios/multi_01_end_to_end_fault_response.json` |
| Scenario ID      | `SGT-009` |
| Category         | End-to-End Incident Response |
| Asset            | Transformer T-015 |
| Domain tags      | IoT · FMSR · TSFM · WO |

### Invocation command

```cmd
cd /d "C:\Users\aksha\Documents\COLUMBIA\HPML\Final Project\AssetOpsBench"
uv run plan-execute ^
  --verbose --show-plan --show-trajectory ^
  --model-id watsonx/meta-llama/llama-3-3-70b-instruct ^
  "Transformer T-015 shows rising load and intermittent over-temperature alerts. ^
   Investigate recent sensor behavior, infer probable fault mode, estimate ^
   short-term risk over 30 days, and issue a maintenance work order recommendation."
```

### Key terminal output (success signals)

```
00:39:16  INFO  agent.plan_execute.runner  Planning...
00:39:34  INFO  agent.plan_execute.runner  Plan has 8 step(s).
00:39:38  INFO  agent.plan_execute.executor  Step 1 OK.
00:39:40  INFO  agent.plan_execute.executor  Step 2 OK.
00:39:49  INFO  agent.plan_execute.executor  Step 3 OK.
00:39:58  INFO  agent.plan_execute.executor  Step 4 OK.
00:40:07  INFO  agent.plan_execute.executor  Step 5 OK.
00:40:17  INFO  agent.plan_execute.executor  Step 6 OK.
00:40:37  INFO  agent.plan_execute.executor  Step 7 OK.
00:40:47  INFO  agent.plan_execute.executor  Step 8 OK.
```

- 8-step plan generated, all steps completed with `[OK]`
- `run_status: "success"`, `pass: 1`, `fail: 0`
- Wall clock: 93.6 s (LLM latency included)

### Committed artifacts

| File | Description |
|------|-------------|
| `benchmarks/cell_Y_plan_execute/raw/local-20260413-003914_pe_mcp_baseline_watsonx_smoke/meta.json` | Run metadata (`run_status: "success"`) |
| `benchmarks/cell_Y_plan_execute/raw/local-20260413-003914_pe_mcp_baseline_watsonx_smoke/harness.log` | Full step-by-step execution log |
| `benchmarks/cell_Y_plan_execute/raw/local-20260413-003914_pe_mcp_baseline_watsonx_smoke/latencies.jsonl` | Per-trial latency record |
| `benchmarks/cell_Y_plan_execute/raw/local-20260413-003914_pe_mcp_baseline_watsonx_smoke/2026-04-13_Y_llama-3-3-70b-instruct_plan_execute_baseline_multi_01_end_to_end_fault_response_run01.json` | Full 8-step trajectory |
| `benchmarks/cell_Y_plan_execute/config.json` | Run configuration (model, cell, experiment family) |
| `benchmarks/cell_Y_plan_execute/summary.json` | Aggregated summary for this cell |

---

## Run 2 — Local MCP direct smoke (2026-04-14)

This run is **fully reproducible from canonical history without any credentials**
and serves as the primary CI/onboarding verification path.

### What it tests

Exercises all four MCP server modules (`iot`, `fmsr`, `tsfm`, `wo`) through the
same 8-tool-call sequence as the Watsonx plan-execute run, calling Python tool
functions directly — no LLM, no network, no Docker required.

### Invocation command

```bash
# From repo root:
python scripts/run_mcp_smoke_local.py
```

Requires only: `pip install mcp pandas numpy` (or `pip install -r requirements.txt`).

### Terminal output (abridged)

```
00:55:23  INFO  mcp_smoke  run_name=local-20260414-005523_mcp_direct_smoke
00:55:23  INFO  mcp_smoke  scenario=data/scenarios/multi_01_end_to_end_fault_response.json  transformer=T-015
00:55:23  INFO  mcp_smoke  Step 1/8 [iot]: Retrieve the list of sensors for transformer T-015
00:55:23  INFO  mcp_smoke  Step 1 OK.  (0.075s)
00:55:23  INFO  mcp_smoke  Step 2/8 [iot]: Get recent sensor readings for the over-temperature and load sensors
00:55:23  INFO  mcp_smoke  Step 2 OK.  (0.011s)
00:55:23  INFO  mcp_smoke  Step 3/8 [tsfm]: Trend analysis on the over-temperature sensor
00:55:23  INFO  mcp_smoke  Step 3 OK.  (0.076s)
00:55:23  INFO  mcp_smoke  Step 4/8 [tsfm]: Detect anomalies in the load sensor readings
00:55:23  INFO  mcp_smoke  Step 4 OK.  (0.012s)
00:55:23  INFO  mcp_smoke  Step 5/8 [fmsr]: Retrieve the most recent DGA record for T-015
00:55:23  INFO  mcp_smoke  Step 5 OK.  (0.002s)
00:55:23  INFO  mcp_smoke  Step 6/8 [fmsr]: Analyze DGA record with IEC 60599 Rogers Ratio method
00:55:23  INFO  mcp_smoke  Step 6 OK.  (0.000s)
00:55:23  INFO  mcp_smoke  Step 7/8 [tsfm]: Forecast remaining useful life over 30 days
00:55:23  INFO  mcp_smoke  Step 7 OK.  (0.003s)
00:55:23  INFO  mcp_smoke  Step 8/8 [wo]: Create maintenance work order based on findings
00:55:23  INFO  mcp_smoke  Step 8 OK.  (0.001s)
00:55:23  INFO  mcp_smoke  Run complete: status=success  total_steps=8  wall=0.20s

============================================================
  Smoke run complete — SUCCESS
  Scenario : data/scenarios/multi_01_end_to_end_fault_response.json  (SGT-009)
  Steps    : 8 OK / 0 FAIL / 8 total
  Wall time: 0.20s
  Artifacts: benchmarks/cell_Y_plan_execute/raw/local-20260414-005523_mcp_direct_smoke/
============================================================
```

Exit status: `0`

### Key results from trajectory

| Step | Server · Tool | Result |
|------|---------------|--------|
| 1 | `iot.list_sensors` | 6 sensors found for T-015 |
| 2 | `iot.get_sensor_readings` | 20 `winding_temp_top_c` readings |
| 3 | `tsfm.trend_analysis` | slope computed (increasing direction) |
| 4 | `tsfm.detect_anomalies` | anomaly scan complete on `load_current_a` |
| 5 | `fmsr.get_dga_record` | DGA snapshot retrieved (`fault_label: Low-temperature overheating`) |
| 6 | `fmsr.analyze_dga` | Rogers Ratio classification completed |
| 7 | `tsfm.forecast_rul` | `projected_rul_days: 517`, `health_index: 0.473` |
| 8 | `wo.create_work_order` | `WO-7CEA88C9` created, `status: open` |

### Committed artifacts

| File | Description |
|------|-------------|
| `benchmarks/cell_Y_plan_execute/raw/local-20260414-005523_mcp_direct_smoke/meta.json` | Run metadata (`run_status: "success"`) |
| `benchmarks/cell_Y_plan_execute/raw/local-20260414-005523_mcp_direct_smoke/harness.log` | Step-by-step log |
| `benchmarks/cell_Y_plan_execute/raw/local-20260414-005523_mcp_direct_smoke/latencies.jsonl` | Trial latency |
| `benchmarks/cell_Y_plan_execute/raw/local-20260414-005523_mcp_direct_smoke/2026-04-14_Y_mcp-direct_multi_01_end_to_end_fault_response_run01.json` | Full trajectory JSON |

---

## Scenario validation (baseline check)

The scenario schema is verified by `data/scenarios/validate_scenarios.py`:

```bash
$ python data/scenarios/validate_scenarios.py
Validation passed for 10 scenario files and 5 negative fixtures.
```

Exit status: `0`

---

## How to reproduce

Any teammate can reproduce Run 2 from a fresh clone:

```bash
git clone https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp
cd hpml-assetopsbench-smart-grid-mcp
pip install mcp pandas numpy          # or: pip install -r requirements.txt
python scripts/run_mcp_smoke_local.py
```

Expected output:
```
  Smoke run complete — SUCCESS
  Steps    : 8 OK / 0 FAIL / 8 total
```

For the full Watsonx plan-execute path (requires credentials and the upstream
`AssetOpsBench` repo), follow the runbook in `docs/eval_harness_readme.md`.

---

*Generated as part of issue #57 — "Run one existing benchmark scenario end-to-end on the canonical stack"*
