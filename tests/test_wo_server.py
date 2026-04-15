"""
Tests for the WO MCP server (issue #12).

Covers:
  - list_fault_records: happy path, transformer filter, status filter (with na=False guard)
  - get_fault_record: known ID, missing ID
  - create_work_order: happy path, invalid priority
  - list_work_orders: session filtering by transformer/status/priority
  - update_work_order: status, priority, assignee, notes; invalid WO ID, invalid status
  - estimate_downtime: all four severities, invalid severity

WO response contract for harness authors (see also #12):
  - work_order_id format: "WO-{8 hex chars uppercase}", e.g. "WO-A1B2C3D4"
  - created_at is UTC ISO-8601 with trailing "Z"
  - assigned_technician is null until explicitly set via update_work_order
  - notes is a list; each entry has "timestamp" and "text" keys
  - _work_orders is session-scoped (in-memory); each test run gets a fresh session
    only if the module is re-imported — tests within one run share state, so we
    use unique transformer IDs per test to avoid cross-contamination.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import mcp_servers.wo_server.server as wo_mod
from mcp_servers.wo_server.server import (
    create_work_order,
    estimate_downtime,
    get_fault_record,
    list_fault_records,
    list_work_orders,
    update_work_order,
)


@pytest.fixture(autouse=True)
def clear_work_orders():
    """Reset the in-memory WO store before each test."""
    wo_mod._work_orders.clear()
    yield
    wo_mod._work_orders.clear()


# ---------------------------------------------------------------------------
# list_fault_records
# ---------------------------------------------------------------------------

def test_list_fault_records_returns_list():
    result = list_fault_records()
    assert isinstance(result, list)
    assert len(result) > 0

def test_list_fault_records_default_limit():
    result = list_fault_records()
    assert len(result) <= 20

def test_list_fault_records_transformer_filter():
    result = list_fault_records(transformer_id="T-018")
    assert isinstance(result, list)
    assert all(r["transformer_id"] == "T-018" for r in result)

def test_list_fault_records_status_filter():
    result = list_fault_records(maintenance_status="Completed")
    assert isinstance(result, list)
    # All returned records should match (case-insensitive)
    assert all(r["maintenance_status"].lower() == "completed" for r in result)

def test_list_fault_records_status_filter_no_crash_on_na():
    # Should not raise even if maintenance_status has NaN values in real data
    result = list_fault_records(maintenance_status="Scheduled")
    assert isinstance(result, list)

def test_list_fault_records_limit():
    result = list_fault_records(limit=5)
    assert len(result) <= 5

def test_list_fault_records_limit_capped():
    result = list_fault_records(limit=9999)
    assert len(result) <= 100

# ---------------------------------------------------------------------------
# get_fault_record
# ---------------------------------------------------------------------------

def test_get_fault_record_known():
    records = list_fault_records(limit=1)
    assert len(records) > 0
    fault_id = records[0]["fault_id"]
    result = get_fault_record(fault_id)
    assert "error" not in result
    assert result["fault_id"] == fault_id

def test_get_fault_record_missing():
    result = get_fault_record("F-NONEXISTENT-999")
    assert "error" in result

# ---------------------------------------------------------------------------
# create_work_order
# ---------------------------------------------------------------------------

def test_create_work_order_happy_path():
    result = create_work_order("T-001", "Test fault description")
    assert "error" not in result
    for key in ("work_order_id", "transformer_id", "issue_description",
                "priority", "fault_type", "status", "estimated_downtime_hours",
                "created_at", "assigned_technician"):
        assert key in result, f"Missing field: {key}"
    assert result["transformer_id"] == "T-001"
    assert result["status"] == "open"
    assert result["assigned_technician"] is None
    assert result["work_order_id"].startswith("WO-")

def test_create_work_order_default_priority():
    result = create_work_order("T-002", "Default priority test")
    assert result["priority"] == "medium"

def test_create_work_order_critical_priority():
    result = create_work_order("T-003", "Critical fault", priority="critical")
    assert result["priority"] == "critical"
    # Typical downtime for critical is 72 hours
    assert result["estimated_downtime_hours"] == 72

def test_create_work_order_invalid_priority():
    result = create_work_order("T-004", "Bad priority", priority="urgent")
    assert "error" in result

def test_create_work_order_custom_downtime():
    result = create_work_order("T-005", "Custom downtime", estimated_downtime_hours=10)
    assert result["estimated_downtime_hours"] == 10

# ---------------------------------------------------------------------------
# list_work_orders
# ---------------------------------------------------------------------------

def test_list_work_orders_empty():
    result = list_work_orders()
    assert result == []

def test_list_work_orders_after_create():
    create_work_order("T-010", "WO list test")
    result = list_work_orders()
    assert len(result) == 1

def test_list_work_orders_filter_transformer():
    create_work_order("T-011", "WO A")
    create_work_order("T-012", "WO B")
    result = list_work_orders(transformer_id="T-011")
    assert len(result) == 1
    assert result[0]["transformer_id"] == "T-011"

def test_list_work_orders_filter_status():
    wo = create_work_order("T-013", "Status filter test")
    wo_id = wo["work_order_id"]
    update_work_order(wo_id, status="in_progress")
    open_wos      = list_work_orders(status="open")
    in_progress   = list_work_orders(status="in_progress")
    assert all(w["status"] == "open"        for w in open_wos)
    assert all(w["status"] == "in_progress" for w in in_progress)

# ---------------------------------------------------------------------------
# update_work_order
# ---------------------------------------------------------------------------

def test_update_work_order_status():
    wo = create_work_order("T-020", "Update status test")
    wo_id = wo["work_order_id"]
    result = update_work_order(wo_id, status="resolved")
    assert result["status"] == "resolved"

def test_update_work_order_assign_technician():
    wo = create_work_order("T-014", "Assign tech test")
    wo_id = wo["work_order_id"]
    result = update_work_order(wo_id, assigned_technician="TEC-02")
    assert result["assigned_technician"] == "TEC-02"

def test_update_work_order_add_note():
    wo = create_work_order("T-015", "Note test")
    wo_id = wo["work_order_id"]
    result = update_work_order(wo_id, note="Inspection completed")
    assert len(result["notes"]) == 1
    assert result["notes"][0]["text"] == "Inspection completed"
    assert "timestamp" in result["notes"][0]

def test_update_work_order_invalid_status():
    wo = create_work_order("T-016", "Invalid status test")
    result = update_work_order(wo["work_order_id"], status="in_flight")
    assert "error" in result

def test_update_work_order_missing_id():
    result = update_work_order("WO-DOESNOTEXIST", status="open")
    assert "error" in result

# ---------------------------------------------------------------------------
# estimate_downtime
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("severity,expected_typical", [
    ("low",      4),
    ("medium",   8),
    ("high",    24),
    ("critical", 72),
])
def test_estimate_downtime_severities(severity, expected_typical):
    result = estimate_downtime("T-018", severity=severity)
    assert "error" not in result
    assert result["estimated_typical_hours"] == expected_typical
    assert result["estimated_min_hours"] <= result["estimated_typical_hours"]
    assert result["estimated_typical_hours"] <= result["estimated_max_hours"]

def test_estimate_downtime_invalid_severity():
    result = estimate_downtime("T-018", severity="extreme")
    assert "error" in result

def test_estimate_downtime_records_fault_type():
    result = estimate_downtime("T-018", severity="high", fault_type="Arc Discharge")
    assert result["fault_type"] == "Arc Discharge"
