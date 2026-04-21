"""
Tests for the IoT MCP server (issue #9).

Covers:
  - list_assets: happy path and health_status filter
  - get_asset_metadata: known ID, missing ID
  - list_sensors: known transformer, missing transformer (error dict, not list)
  - get_sensor_readings: known sensor, missing transformer, missing sensor,
    time-window filtering, limit clamping
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mcp_servers.iot_server.server import (
    get_asset_metadata,
    get_sensor_readings,
    list_assets,
    list_sensors,
)

# ---------------------------------------------------------------------------
# list_assets
# ---------------------------------------------------------------------------


def test_list_assets_returns_list():
    result = list_assets()
    assert isinstance(result, list)
    assert len(result) > 0


def test_list_assets_fields():
    result = list_assets()
    row = result[0]
    for key in (
        "transformer_id",
        "name",
        "location",
        "health_status",
        "rul_days",
        "in_service",
    ):
        assert key in row, f"Missing field: {key}"


def test_list_assets_filter_health_status():
    all_assets = list_assets()
    filtered = list_assets(health_status=0)
    assert isinstance(filtered, list)
    assert all(r["health_status"] == 0 for r in filtered)
    # Filtered set must be a subset of all assets
    all_ids = {r["transformer_id"] for r in all_assets}
    assert all(r["transformer_id"] in all_ids for r in filtered)


def test_list_assets_filter_nonexistent_status_returns_empty():
    result = list_assets(health_status=999)
    assert result == []


# ---------------------------------------------------------------------------
# get_asset_metadata
# ---------------------------------------------------------------------------


def test_get_asset_metadata_known():
    result = get_asset_metadata("T-001")
    assert "error" not in result
    assert result["transformer_id"] == "T-001"
    for key in (
        "name",
        "manufacturer",
        "location",
        "voltage_class",
        "rating_kva",
        "install_date",
        "age_years",
        "health_status",
        "fdd_category",
        "rul_days",
        "in_service",
    ):
        assert key in result, f"Missing field: {key}"


def test_get_asset_metadata_missing():
    result = get_asset_metadata("T-NONEXISTENT")
    assert "error" in result
    assert "T-NONEXISTENT" in result["error"]


# ---------------------------------------------------------------------------
# list_sensors
# ---------------------------------------------------------------------------


def test_list_sensors_known():
    result = list_sensors("T-001")
    assert isinstance(result, list)
    assert len(result) > 0
    for row in result:
        assert "sensor_id" in row
        assert "unit" in row
        assert "num_readings" in row


def test_list_sensors_missing_returns_error_dict():
    # Error must be a dict, not a list — harness checks result["error"]
    result = list_sensors("T-NONEXISTENT")
    assert isinstance(
        result, dict
    ), "list_sensors error case must return a dict, not a list"
    assert "error" in result


# ---------------------------------------------------------------------------
# get_sensor_readings
# ---------------------------------------------------------------------------


def _get_first_sensor(transformer_id: str) -> str:
    sensors = list_sensors(transformer_id)
    assert isinstance(sensors, list) and len(sensors) > 0
    return sensors[0]["sensor_id"]


def test_get_sensor_readings_happy_path():
    sensor_id = _get_first_sensor("T-001")
    result = get_sensor_readings("T-001", sensor_id)
    assert isinstance(result, list)
    assert len(result) > 0
    for row in result:
        assert "timestamp" in row
        assert "value" in row
        assert "unit" in row
        # Timestamp must be a plain string, not a pandas Timestamp
        assert isinstance(row["timestamp"], str), "timestamp must be a string"


def test_get_sensor_readings_missing_transformer():
    result = get_sensor_readings("T-NONEXISTENT", "dga_h2_ppm")
    assert isinstance(result, list)
    assert len(result) == 1
    assert "error" in result[0]


def test_get_sensor_readings_missing_sensor():
    result = get_sensor_readings("T-001", "nonexistent_sensor_xyz")
    assert isinstance(result, list)
    assert len(result) == 1
    assert "error" in result[0]


def test_get_sensor_readings_limit():
    sensor_id = _get_first_sensor("T-001")
    result = get_sensor_readings("T-001", sensor_id, limit=5)
    assert len(result) <= 5


def test_get_sensor_readings_limit_capped_at_1000():
    sensor_id = _get_first_sensor("T-001")
    result = get_sensor_readings("T-001", sensor_id, limit=9999)
    assert len(result) <= 1000


def test_get_sensor_readings_time_window():
    sensor_id = _get_first_sensor("T-001")
    all_readings = get_sensor_readings("T-001", sensor_id, limit=1000)
    assert len(all_readings) >= 2
    # Use the second and third timestamps as window bounds
    start = all_readings[1]["timestamp"]
    end = all_readings[2]["timestamp"]
    windowed = get_sensor_readings("T-001", sensor_id, start_time=start, end_time=end)
    assert isinstance(windowed, list)
    assert all(start <= r["timestamp"] <= end for r in windowed)
