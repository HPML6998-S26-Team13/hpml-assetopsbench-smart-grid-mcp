"""
Tests for the TSFM MCP server (issue #10).

Covers all four tools:
  - get_rul: known transformer, missing transformer, interpretation thresholds
  - forecast_rul: horizon capping at 365 days, known transformer, missing transformer
  - detect_anomalies: happy path, missing transformer/sensor
  - trend_analysis: happy path, time window, insufficient data window
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mcp_servers.tsfm_server.server import (
    detect_anomalies,
    forecast_rul,
    get_rul,
    trend_analysis,
)

# ---------------------------------------------------------------------------
# get_rul
# ---------------------------------------------------------------------------

def test_get_rul_known():
    result = get_rul("T-001")
    assert "error" not in result
    for key in ("transformer_id", "as_of_date", "rul_days", "health_index",
                "fdd_category", "interpretation"):
        assert key in result, f"Missing field: {key}"
    assert result["transformer_id"] == "T-001"
    assert isinstance(result["rul_days"], int)
    assert isinstance(result["health_index"], float)

def test_get_rul_missing():
    result = get_rul("T-NONEXISTENT")
    assert "error" in result

def test_get_rul_interpretation_healthy():
    result = get_rul("T-001")
    assert "error" not in result
    rul = result["rul_days"]
    interp = result["interpretation"]
    if rul >= 730:
        assert "Healthy" in interp
    elif rul >= 180:
        assert "Aging" in interp
    elif rul >= 30:
        assert "Degraded" in interp
    else:
        assert "Critical" in interp

# ---------------------------------------------------------------------------
# forecast_rul
# ---------------------------------------------------------------------------

def test_forecast_rul_known():
    result = forecast_rul("T-001", horizon_days=30)
    assert "error" not in result
    for key in ("transformer_id", "current_rul_days", "forecast_date",
                "projected_rul_days", "projected_health_index", "confidence", "method"):
        assert key in result, f"Missing field: {key}"
    assert result["projected_rul_days"] <= result["current_rul_days"]

def test_forecast_rul_missing():
    result = forecast_rul("T-NONEXISTENT", horizon_days=30)
    assert "error" in result

def test_forecast_rul_horizon_out_of_range_returns_error():
    # horizon_days > 365 must return an error (not silently clamp)
    result = forecast_rul("T-001", horizon_days=9999)
    assert "error" in result

def test_forecast_rul_zero_floor():
    # Projected RUL must never go below zero
    result = forecast_rul("T-001", horizon_days=365)
    assert result["projected_rul_days"] >= 0

# ---------------------------------------------------------------------------
# detect_anomalies
# ---------------------------------------------------------------------------

def test_detect_anomalies_happy_path():
    result = detect_anomalies("T-018", "winding_temp_top_c")
    assert "error" not in result
    for key in ("transformer_id", "sensor_id", "total_readings",
                "anomaly_count", "anomaly_rate_pct", "anomalies"):
        assert key in result, f"Missing field: {key}"
    assert isinstance(result["anomalies"], list)
    assert result["anomaly_count"] >= 0
    # Capped at 50
    assert len(result["anomalies"]) <= 50

def test_detect_anomalies_missing_transformer():
    result = detect_anomalies("T-NONEXISTENT", "winding_temp_top_c")
    assert "error" in result

def test_detect_anomalies_missing_sensor():
    result = detect_anomalies("T-001", "sensor_does_not_exist")
    assert "error" in result

def test_detect_anomalies_high_threshold_returns_fewer_anomalies():
    low_thresh  = detect_anomalies("T-018", "winding_temp_top_c", z_threshold=1.0)
    high_thresh = detect_anomalies("T-018", "winding_temp_top_c", z_threshold=10.0)
    assert "error" not in low_thresh
    assert "error" not in high_thresh
    assert low_thresh["anomaly_count"] >= high_thresh["anomaly_count"]

# ---------------------------------------------------------------------------
# trend_analysis
# ---------------------------------------------------------------------------

def test_trend_analysis_happy_path():
    result = trend_analysis("T-018", "winding_temp_top_c")
    assert "error" not in result
    for key in ("transformer_id", "sensor_id", "num_readings", "start_time",
                "end_time", "mean_value", "min_value", "max_value",
                "slope_per_day", "direction", "r_squared"):
        assert key in result, f"Missing field: {key}"
    assert result["direction"] in ("increasing", "decreasing", "stable")

def test_trend_analysis_missing_transformer():
    result = trend_analysis("T-NONEXISTENT", "winding_temp_top_c")
    assert "error" in result

def test_trend_analysis_missing_sensor():
    result = trend_analysis("T-001", "sensor_does_not_exist")
    assert "error" in result

def test_trend_analysis_with_tight_window_too_small():
    # A window so tight it contains < 2 readings should return an error
    result = trend_analysis(
        "T-018", "winding_temp_top_c",
        start_time="2099-01-01T00:00:00",
        end_time="2099-01-01T01:00:00",
    )
    assert "error" in result
