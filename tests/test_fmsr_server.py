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
  - The Rogers table follows IEC 60599:2022 Table 1 strictly. D2 ("Discharges
    of high energy / arcing") requires R2 = C2H2/C2H4 ∈ [0.6, 2.5) AND
    R3 ≥ 2.0 AND R1 ∈ [0.1, 1.0). Samples with R2 ≥ 2.5 fall outside D2 and
    (if R1 ∈ [0.1, 0.5) and R2 ≥ 1.0 and R3 ≥ 1.0) classify as D1 instead.
    This is per IEC's strict reading; some operational DGA tools relax D2's
    R2 upper bound, but this server matches the standard. Boundary phrasing
    here uses the encoded range convention: min-inclusive, max-exclusive.
  - All-zero inputs return "N" (no division by zero crash)
"""

import json as _json
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
    # T-018 profile (R1=0.17, R2=18.5, R3=8.67) classifies as D1 under
    # IEC 60599:2022 Table 1: R2=18.5 falls outside D2's [0.6, 2.5) cap,
    # so D1 (R1 ∈ [0.1, 0.5), R2 ≥ 1, R3 ≥ 1) wins.
    result = analyze_dga(**_T018_GASES)
    assert result["iec_code"] == "D1"


def test_analyze_dga_all_zeros_no_crash():
    result = analyze_dga(h2=0, ch4=0, c2h2=0, c2h4=0, c2h6=0)
    assert "iec_code" in result
    # Zero gases → normal / inconclusive
    assert result["iec_code"] == "N"


def test_analyze_dga_zero_c2h6_diverges_r3():
    # Regression: zero denominator must produce a divergent ratio internally
    # (so classification is correct), but the public output normalizes inf →
    # null + r3_divergent: True for JSON safety.
    result = analyze_dga(h2=500, ch4=200, c2h2=120, c2h4=100, c2h6=0)
    assert result["iec_code"] == "D2"
    assert result["r3_c2h4_c2h6"] is None
    assert result.get("r3_divergent") is True
    # Strict JSON serialization must succeed (allow_nan=False catches inf).
    _json.dumps(result, allow_nan=False)


def test_analyze_dga_zero_c2h4_diverges_r2():
    # Regression: c2h4=0, c2h2>0 → R2 diverges and R3 collapses to 0.
    # Public output: r2_c2h2_c2h4 → null + r2_divergent: True.
    result = analyze_dga(h2=500, ch4=200, c2h2=120, c2h4=0, c2h6=30)
    # R2 diverges, R3=0.0 (c2h4=0, c2h6>0). No fault row matches → N.
    assert result["iec_code"] == "N"
    assert result["r2_c2h2_c2h4"] is None
    assert result.get("r2_divergent") is True
    _json.dumps(result, allow_nan=False)


def test_analyze_dga_zero_h2_diverges_r1():
    # Regression: h2=0, ch4>0 → R1 diverges. Public r1_ch4_h2 → null + flag.
    result = analyze_dga(h2=0, ch4=200, c2h2=2, c2h4=80, c2h6=120)
    # R1 diverges, R2=0.025, R3=0.667 → T1 (R1>=1, R2 NS, R3<1).
    assert result["iec_code"] == "T1"
    assert result["r1_ch4_h2"] is None
    assert result.get("r1_divergent") is True
    _json.dumps(result, allow_nan=False)


def test_analyze_dga_finite_ratios_have_no_divergent_flags():
    # Non-regression: finite-ratio results must NOT carry r{1,2,3}_divergent
    # keys at all (avoid surprising consumers with always-false flags).
    result = analyze_dga(**_T018_GASES)
    assert "r1_divergent" not in result
    assert "r2_divergent" not in result
    assert "r3_divergent" not in result
    _json.dumps(result, allow_nan=False)


def test_analyze_dga_without_transformer_id():
    result = analyze_dga(**_T018_GASES)
    assert "transformer_id" not in result


# ---------------------------------------------------------------------------
# analyze_dga — knowledge plugin profile round-trip (issue #50)
# ---------------------------------------------------------------------------

_KNOWLEDGE_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "knowledge"
    / "transformer_standards.json"
)
_PROFILES = _json.loads(_KNOWLEDGE_PATH.read_text())["iec_60599"][
    "representative_gas_profiles"
]["profiles"]


@pytest.mark.parametrize("iec_code,profile", _PROFILES.items())
def test_knowledge_profile_round_trips(iec_code, profile):
    """Each representative_gas_profiles entry must produce its declared iec_code."""
    result = analyze_dga(
        h2=profile["H2"],
        ch4=profile["CH4"],
        c2h2=profile["C2H2"],
        c2h4=profile["C2H4"],
        c2h6=profile["C2H6"],
    )
    assert result["iec_code"] == profile["expected_iec_code"], (
        f"Profile {iec_code}: expected {profile['expected_iec_code']!r}, "
        f"got {result['iec_code']!r} (R1={result['r1_ch4_h2']:.3f}, "
        f"R2={result['r2_c2h2_c2h4']:.3f}, R3={result['r3_c2h4_c2h6']:.3f})"
    )
