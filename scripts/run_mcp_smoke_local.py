#!/usr/bin/env python3
"""
Local MCP Smoke Runner — canonical benchmark scenario end-to-end without Watsonx.

Exercises the Smart Grid MCP server layer (IoT → FMSR → TSFM → WO) for the
scenario defined in data/scenarios/multi_01_end_to_end_fault_response.json,
exactly mirroring the eight tool-call steps produced by the Watsonx plan-execute
run on 2026-04-13.

No LLM or network access is required; all calls go directly to the Python tool
functions exposed by each MCP server module.

Usage
-----
    # From repo root:
    python scripts/run_mcp_smoke_local.py

Output
------
    benchmarks/cell_Y_plan_execute/raw/<run-id>/
        harness.log            — step-by-step log identical in structure to a
                                 live plan-execute run
        latencies.jsonl        — per-step timing in the canonical schema
        meta.json              — run metadata (matches wandb_schema.md fields)
        <scenario-result>.json — full trajectory for the scenario trial

Exit codes
----------
    0  all steps succeeded
    1  one or more steps returned an error
"""

from __future__ import annotations

import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Repo-root setup — allows running from any working directory
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from mcp_servers.fmsr_server.server import analyze_dga, get_dga_record  # noqa: E402
from mcp_servers.iot_server.server import get_sensor_readings, list_sensors  # noqa: E402
from mcp_servers.tsfm_server.server import (  # noqa: E402
    detect_anomalies,
    forecast_rul,
    trend_analysis,
)
from mcp_servers.wo_server.server import create_work_order  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SCENARIO_FILE = "data/scenarios/multi_01_end_to_end_fault_response.json"
SCENARIO_ID = "SGT-009"
TRANSFORMER_ID = "T-015"
CELL_DIR = REPO_ROOT / "benchmarks" / "cell_Y_plan_execute"

RUN_TIMESTAMP = datetime.now(timezone.utc)
RUN_NAME = f"local-{RUN_TIMESTAMP.strftime('%Y%m%d-%H%M%S')}_mcp_direct_smoke"


# ---------------------------------------------------------------------------
# Step definitions — mirror the 8-step plan from the Watsonx run
# ---------------------------------------------------------------------------
def _build_steps():
    """Return a list of (label, server, tool_name, callable, kwargs) tuples."""
    return [
        (
            "Retrieve the list of sensors for transformer T-015",
            "iot",
            "list_sensors",
            lambda: list_sensors(transformer_id=TRANSFORMER_ID),
            {"transformer_id": TRANSFORMER_ID},
        ),
        (
            "Get recent sensor readings for the over-temperature and load sensors",
            "iot",
            "get_sensor_readings",
            lambda: get_sensor_readings(
                transformer_id=TRANSFORMER_ID,
                sensor_id="winding_temp_top_c",
                limit=20,
            ),
            {"transformer_id": TRANSFORMER_ID, "sensor_id": "winding_temp_top_c", "limit": 20},
        ),
        (
            "Trend analysis on the over-temperature sensor",
            "tsfm",
            "trend_analysis",
            lambda: trend_analysis(
                transformer_id=TRANSFORMER_ID,
                sensor_id="winding_temp_top_c",
            ),
            {"transformer_id": TRANSFORMER_ID, "sensor_id": "winding_temp_top_c"},
        ),
        (
            "Detect anomalies in the load sensor readings",
            "tsfm",
            "detect_anomalies",
            lambda: detect_anomalies(
                transformer_id=TRANSFORMER_ID,
                sensor_id="load_current_a",
            ),
            {"transformer_id": TRANSFORMER_ID, "sensor_id": "load_current_a"},
        ),
        (
            "Retrieve the most recent DGA record for T-015",
            "fmsr",
            "get_dga_record",
            lambda: get_dga_record(transformer_id=TRANSFORMER_ID),
            {"transformer_id": TRANSFORMER_ID},
        ),
        (
            "Analyze DGA record with IEC 60599 Rogers Ratio method",
            "fmsr",
            "analyze_dga",
            lambda: _run_analyze_dga(),
            None,  # args resolved dynamically after step 5
        ),
        (
            "Forecast remaining useful life over 30 days",
            "tsfm",
            "forecast_rul",
            lambda: forecast_rul(transformer_id=TRANSFORMER_ID, horizon_days=30),
            {"transformer_id": TRANSFORMER_ID, "horizon_days": 30},
        ),
        (
            "Create maintenance work order based on findings",
            "wo",
            "create_work_order",
            lambda: create_work_order(
                transformer_id=TRANSFORMER_ID,
                issue_description="Rising load and intermittent over-temperature alerts",
                priority="high",
                fault_type="Low-temperature overheating",
                estimated_downtime_hours=48,
            ),
            {
                "transformer_id": TRANSFORMER_ID,
                "issue_description": "Rising load and intermittent over-temperature alerts",
                "priority": "high",
                "fault_type": "Low-temperature overheating",
                "estimated_downtime_hours": 48,
            },
        ),
    ]


# DGA step needs the record fetched in step 5 — resolved at runtime
_dga_record: dict = {}


def _run_analyze_dga() -> dict:
    return analyze_dga(
        h2=_dga_record.get("dissolved_h2_ppm", 0),
        ch4=_dga_record.get("dissolved_ch4_ppm", 0),
        c2h2=_dga_record.get("dissolved_c2h2_ppm", 0),
        c2h4=_dga_record.get("dissolved_c2h4_ppm", 0),
        c2h6=_dga_record.get("dissolved_c2h6_ppm", 0),
        transformer_id=TRANSFORMER_ID,
    )


# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------
def _setup_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("mcp_smoke")
    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s %(levelname)-8s %(name)s %(message)s",
                            datefmt="%H:%M:%S")
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(sh)
    logger.addHandler(fh)
    return logger


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------
def main() -> int:
    out_dir = CELL_DIR / "raw" / RUN_NAME
    out_dir.mkdir(parents=True, exist_ok=True)

    log = _setup_logger(out_dir / "harness.log")
    log.info("run_name=%s", RUN_NAME)
    log.info("scenario=%s  transformer=%s", SCENARIO_FILE, TRANSFORMER_ID)
    log.info("output_dir=%s", out_dir)

    steps = _build_steps()
    trajectory: list[dict] = []
    latencies: list[dict] = []
    wall_start = time.monotonic()
    all_ok = True

    for idx, (task, server, tool_name, fn, tool_args) in enumerate(steps, start=1):
        log.info("Step %d/%d [%s]: %s", idx, len(steps), server, task)
        t0 = time.monotonic()
        error = None
        response = None
        success = False
        try:
            response = fn()
            # Cache DGA record for the analyze_dga step
            if tool_name == "get_dga_record" and isinstance(response, dict):
                _dga_record.update(response)
            if isinstance(response, dict) and "error" in response:
                error = response["error"]
                all_ok = False
            elif isinstance(response, list) and response and "error" in response[0]:
                error = response[0]["error"]
                all_ok = False
            else:
                success = True
        except Exception as exc:
            error = str(exc)
            all_ok = False

        elapsed = time.monotonic() - t0

        if success:
            log.info("Step %d OK.  (%.3fs)", idx, elapsed)
        else:
            log.error("Step %d FAILED: %s  (%.3fs)", idx, error, elapsed)

        # Resolve dynamic args for the analyze_dga step
        if tool_name == "analyze_dga" and tool_args is None:
            tool_args = {
                "h2": _dga_record.get("dissolved_h2_ppm"),
                "ch4": _dga_record.get("dissolved_ch4_ppm"),
                "c2h2": _dga_record.get("dissolved_c2h2_ppm"),
                "c2h4": _dga_record.get("dissolved_c2h4_ppm"),
                "c2h6": _dga_record.get("dissolved_c2h6_ppm"),
                "transformer_id": TRANSFORMER_ID,
            }

        trajectory.append({
            "step": idx,
            "task": task,
            "server": server,
            "tool": tool_name,
            "tool_args": tool_args,
            "response": json.dumps(response, default=str) if response is not None else None,
            "error": error,
            "success": success,
            "latency_seconds": round(elapsed, 6),
        })
        latencies.append({
            "step": idx,
            "server": server,
            "tool": tool_name,
            "latency_seconds": round(elapsed, 6),
            "success": success,
        })

    wall_elapsed = time.monotonic() - wall_start
    run_status = "success" if all_ok else "failure"
    finished_at = datetime.now(timezone.utc).isoformat()

    log.info(
        "Run complete: status=%s  total_steps=%d  wall=%.2fs",
        run_status, len(steps), wall_elapsed,
    )

    # ------------------------------------------------------------------ #
    # Write latencies.jsonl
    # ------------------------------------------------------------------ #
    scenario_label = "multi_01_end_to_end_fault_response"
    result_filename = (
        f"{RUN_TIMESTAMP.strftime('%Y-%m-%d')}_Y_mcp-direct_"
        f"{scenario_label}_run01.json"
    )
    latencies_path = out_dir / "latencies.jsonl"
    with latencies_path.open("w", encoding="utf-8") as f:
        entry = {
            "scenario_file": SCENARIO_FILE,
            "trial_index": 1,
            "latency_seconds": round(wall_elapsed, 6),
            "output_path": str(
                (out_dir / result_filename).relative_to(REPO_ROOT)
            ),
        }
        f.write(json.dumps(entry) + "\n")

    # ------------------------------------------------------------------ #
    # Write scenario result JSON
    # ------------------------------------------------------------------ #
    result = {
        "scenario_id": SCENARIO_ID,
        "scenario_file": SCENARIO_FILE,
        "run_name": RUN_NAME,
        "run_mode": "mcp_direct",
        "transformer_id": TRANSFORMER_ID,
        "status": run_status,
        "wall_clock_seconds": round(wall_elapsed, 6),
        "tool_call_count": len(steps),
        "tool_error_count": sum(1 for s in trajectory if not s["success"]),
        "trajectory": trajectory,
    }
    result_path = out_dir / result_filename
    with result_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)

    # ------------------------------------------------------------------ #
    # Write meta.json
    # ------------------------------------------------------------------ #
    meta = {
        "started_at": RUN_TIMESTAMP.isoformat(),
        "run_name": RUN_NAME,
        "run_mode": "mcp_direct_smoke",
        "scenario_file": SCENARIO_FILE,
        "scenario_id": SCENARIO_ID,
        "benchmark_summary_path": str(
            (CELL_DIR / "summary.json").relative_to(REPO_ROOT)
        ),
        "finished_at": finished_at,
        "pass": 1 if all_ok else 0,
        "fail": 0 if all_ok else 1,
        "total_runs": 1,
        "run_status": run_status,
    }
    with (out_dir / "meta.json").open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    # ------------------------------------------------------------------ #
    # Update cell summary.json
    # ------------------------------------------------------------------ #
    import hashlib
    scenario_text = (REPO_ROOT / SCENARIO_FILE).read_text(encoding="utf-8")
    scenario_hash = hashlib.sha256(scenario_text.encode()).hexdigest()

    summary = {
        "schema_version": "v1",
        "run_name": RUN_NAME,
        "run_mode": "mcp_direct_smoke",
        "experiment_family": "exp2_orchestration",
        "experiment_cell": "Y",
        "orchestration_mode": "mcp_direct",
        "mcp_mode": "baseline",
        "scenario_set_name": "smartgrid_single_scenario_smoke",
        "scenario_set_hash": scenario_hash,
        "model_id": "n/a (direct tool call — no LLM)",
        "run_status": run_status,
        "scenarios_attempted": 1,
        "scenarios_completed": 1 if all_ok else 0,
        "success_rate": 1.0 if all_ok else 0.0,
        "failure_count": 0 if all_ok else 1,
        "wall_clock_seconds_total": round(wall_elapsed, 6),
        "latency_seconds_mean": round(wall_elapsed, 6),
        "tool_call_count_total": len(steps),
        "tool_call_count_mean": float(len(steps)),
        "tool_error_count": sum(1 for s in trajectory if not s["success"]),
        "finished_at": finished_at,
    }
    # Merge into existing summary if present (keep watsonx run fields)
    summary_path = CELL_DIR / "summary.json"
    if summary_path.exists():
        with summary_path.open(encoding="utf-8") as f:
            existing = json.load(f)
        existing["mcp_direct_smoke_run"] = summary
        with summary_path.open("w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
    else:
        with summary_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

    # ------------------------------------------------------------------ #
    # Final summary to stdout
    # ------------------------------------------------------------------ #
    step_ok = sum(1 for s in trajectory if s["success"])
    step_fail = len(trajectory) - step_ok
    print()
    print("=" * 60)
    print(f"  Smoke run complete — {run_status.upper()}")
    print(f"  Scenario : {SCENARIO_FILE}  ({SCENARIO_ID})")
    print(f"  Steps    : {step_ok} OK / {step_fail} FAIL / {len(steps)} total")
    print(f"  Wall time: {wall_elapsed:.2f}s")
    print(f"  Artifacts: {out_dir.relative_to(REPO_ROOT)}/")
    print("=" * 60)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
