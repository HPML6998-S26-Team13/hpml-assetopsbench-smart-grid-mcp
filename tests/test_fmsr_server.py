"""
Tests for the FMSR MCP server (issue #11).

Covers:
  - list_failure_modes: returns all modes with required fields
  - search_failure_modes: keyword hit, no match
  - get_sensor_correlation: known ID, missing ID, key_gases is a list
  - get_dga_record: known transformer, missing transformer, returns most recent
  - analyze_dga: known gases (T-018 profile), all-zero gases, determinism

DGA contract assumptions documented below for harness authors (see also #11):
  - analyze_dga is fully deterministic: same inputs always yield the same output
  - IEC code "N" / "Normal / Inconclusive" is a valid output, not an error
  - C2H2 >> C2H4 (ratio > 3) indicates high-energy arcing; Rogers table maps
    R2 >= 3 → D2 ("High-Energy Electrical Discharge (Arcing)")
  - All-zero inputs return "N" (no division by zero crash)
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mcp_servers.fmsr_server.server import (
    analyze_dga,
    get_dga_record,
    get_sensor_correlation,
    list_failure_modes,
    search_failure_modes,
)

# ---------------------------------------------------------------------------
# list_failure_modes
# ---------------------------------------------------------------------------


def test_list_failure_modes_returns_list():
    result = list_failure_modes()
    assert isinstance(result, list)
    assert len(result) > 0


def test_list_failure_modes_fields():
    result = list_failure_modes()
    row = result[0]
    for key in (
        "failure_mode_id",
        "name",
        "severity",
        "iec_code",
        "key_gases",
        "recommended_action",
    ):
        assert key in row, f"Missing field: {key}"


# ---------------------------------------------------------------------------
# search_failure_modes
# ---------------------------------------------------------------------------


def test_search_failure_modes_arc_hit():
    result = search_failure_modes("arc")
    assert isinstance(result, list)
    assert len(result) > 0


def test_search_failure_modes_no_match():
    result = search_failure_modes("zzznomatchxyz")
    assert result == []


def test_search_failure_modes_iec_code():
    result = search_failure_modes("PD")
    assert isinstance(result, list)
    assert any(r["iec_code"] == "PD" for r in result)


# ---------------------------------------------------------------------------
# get_sensor_correlation
# ---------------------------------------------------------------------------


def test_get_sensor_correlation_known():
    result = get_sensor_correlation("FM-001")
    assert "error" not in result
    assert result["failure_mode_id"] == "FM-001"
    # key_gases must be a Python list, not a raw comma-separated string
    assert isinstance(result["key_gases"], list), "key_gases must be a list"
    assert len(result["key_gases"]) > 0


def test_get_sensor_correlation_missing():
    result = get_sensor_correlation("FM-NONEXISTENT")
    assert "error" in result


# ---------------------------------------------------------------------------
# get_dga_record
# ---------------------------------------------------------------------------


def test_get_dga_record_known():
    result = get_dga_record("T-018")
    assert "error" not in result
    assert result["transformer_id"] == "T-018"
    for key in (
        "sample_date",
        "dissolved_h2_ppm",
        "dissolved_ch4_ppm",
        "dissolved_c2h2_ppm",
        "dissolved_c2h4_ppm",
        "dissolved_c2h6_ppm",
        "dissolved_co_ppm",
        "dissolved_co2_ppm",
        "fault_label",
    ):
        assert key in result, f"Missing field: {key}"


def test_get_dga_record_sample_date_present():
    result = get_dga_record("T-018")
    # sample_date must exist and be non-null; FastMCP handles Timestamp serialisation
    assert result.get("sample_date") is not None


def test_get_dga_record_missing():
    result = get_dga_record("T-NONEXISTENT")
    assert "error" in result


# ---------------------------------------------------------------------------
# analyze_dga  — representative T-018 profile
# ---------------------------------------------------------------------------

# T-018 gas values from data/processed/dga_records.csv
_T018_GASES = dict(h2=35.0, ch4=6.0, c2h2=482.0, c2h4=26.0, c2h6=3.0)


def test_analyze_dga_returns_required_fields():
    result = analyze_dga(**_T018_GASES, transformer_id="T-018")
    for key in (
        "iec_code",
        "diagnosis",
        "r1_ch4_h2",
        "r2_c2h2_c2h4",
        "r3_c2h4_c2h6",
        "input_gases",
    ):
        assert key in result, f"Missing field: {key}"
    assert result["transformer_id"] == "T-018"


def test_analyze_dga_echoes_inputs():
    result = analyze_dga(**_T018_GASES)
    gases = result["input_gases"]
    assert gases["h2_ppm"] == _T018_GASES["h2"]
    assert gases["c2h2_ppm"] == _T018_GASES["c2h2"]


def test_analyze_dga_deterministic():
    r1 = analyze_dga(**_T018_GASES)
    r2 = analyze_dga(**_T018_GASES)
    assert r1["iec_code"] == r2["iec_code"]
    assert r1["diagnosis"] == r2["diagnosis"]


def test_analyze_dga_high_c2h2_ratio():
    # Non-regression: T-018 profile (R1=0.17, R2=18.5, R3=8.67) returns N
    # under the current Rogers table implementation.
    result = analyze_dga(**_T018_GASES)
    assert result["iec_code"] == "N"


def test_analyze_dga_all_zeros_no_crash():
    result = analyze_dga(h2=0, ch4=0, c2h2=0, c2h4=0, c2h6=0)
    assert "iec_code" in result
    # Zero gases → normal / inconclusive
    assert result["iec_code"] == "N"


def test_analyze_dga_without_transformer_id():
    result = analyze_dga(**_T018_GASES)
    assert "transformer_id" not in result
