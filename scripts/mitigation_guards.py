"""Deterministic mitigation guards for benchmark trial artifacts."""

from __future__ import annotations

import json
import re
from typing import Any

MISSING_EVIDENCE_GUARD_NAME = "missing_evidence_final_answer_guard"
MISSING_EVIDENCE_REPAIR_NAME = "missing_evidence_retry_replan_guard"
EXPLICIT_FAULT_RISK_ADJUDICATION_NAME = "explicit_fault_risk_adjudication_step"

EVIDENCE_TOOLS = {
    "get_asset_metadata",
    "list_sensors",
    "get_sensor_readings",
    "get_dga_record",
    "analyze_dga",
    "get_sensor_correlation",
    "detect_anomalies",
    "trend_analysis",
    "get_rul",
    "forecast_rul",
    "list_fault_records",
    "get_fault_record",
}

WORK_ORDER_TOOLS = {
    "create_work_order",
    "create_inspection_order",
    "update_work_order",
}

FAULT_RISK_EVIDENCE_TOOLS = {
    "analyze_dga",
    "get_dga_record",
    "get_sensor_correlation",
    "detect_anomalies",
    "trend_analysis",
    "get_rul",
    "forecast_rul",
    "list_fault_records",
    "get_fault_record",
}

FAULT_FIELD_KEYS = {
    "diagnosis",
    "diagnostic",
    "fault",
    "fault_id",
    "fault_label",
    "failure_mode",
    "failure_mode_id",
    "mode",
}

RISK_FIELD_KEYS = {
    "risk",
    "risk_level",
    "severity",
    "priority",
    "urgency",
    "rul",
    "rul_days",
    "remaining_useful_life",
}

MISSING_EVIDENCE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bno\s+(?:readings|records|data|evidence|sensor data)\s+found\b",
        r"\bnot\s+found\b",
        r"\bmissing\b",
        r"\bunavailable\b",
        r"\bunsupported\b",
        r"\bunknown tool\b",
        r"\berror executing tool\b",
        r"\bvalidation error\b",
        r"\bfield required\b",
        r"\bfailed to (?:retrieve|fetch|load|execute)\b",
        r"\bunable to (?:retrieve|fetch|load|determine)\b",
        r"\binsufficient (?:evidence|data)\b",
    )
]

EVIDENCE_LIMITED_ANSWER_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\binsufficient (?:evidence|data)\b",
        r"\bnot enough (?:evidence|data)\b",
        r"\bmissing (?:evidence|data|readings|records)\b",
        r"\bcannot (?:determine|conclude|verify|support)\b",
        r"\bunable to (?:determine|conclude|verify|support)\b",
    )
]

EMPTY_EVIDENCE_KEYS = {
    "readings",
    "records",
    "data",
    "values",
    "anomalies",
    "fault_records",
    "history",
    "results",
}

TARGET_FIELD_KEYS = {
    "transformer_id",
    "sensor_id",
    "fault_id",
    "failure_mode_id",
}

UNKNOWN_TARGET = (("*", "*"),)


def env_flag_enabled(value: Any) -> bool:
    """Return true for the standard bash/env truthy spellings."""
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def apply_missing_evidence_final_answer_guard(
    payload: dict[str, Any],
    *,
    enabled: bool,
) -> dict[str, Any]:
    """Block clean final answers that follow missing or untrusted evidence.

    The guard is intentionally post-processing only: it does not rewrite the
    model prompt or tool execution path. When enabled, it scans the emitted
    trajectory/history, records deterministic guard metadata, and marks the
    trial unsuccessful only when a substantive final answer or work order was
    emitted after required evidence looked missing, empty, or untrusted.
    """
    if not enabled:
        return payload

    hits, work_order_after_missing = _missing_evidence_scan(payload)
    answer = str(payload.get("answer") or "").strip()
    answer_already_limited = _is_evidence_limited_answer(answer)
    should_block = bool(hits) and (
        work_order_after_missing or (bool(answer) and not answer_already_limited)
    )

    guard = {
        "name": MISSING_EVIDENCE_GUARD_NAME,
        "enabled": True,
        "triggered": bool(hits),
        "blocked_final_answer": bool(should_block),
        "blocked_work_order": bool(work_order_after_missing),
        "evidence_limited_answer": bool(answer_already_limited),
        "hits": hits,
    }
    if hits:
        guard["reason"] = _guard_reason(hits, work_order_after_missing)
    else:
        guard["reason"] = "No missing or untrusted evidence signal detected."

    payload["mitigation_guard"] = guard

    if should_block:
        payload["answer"] = _blocked_answer(hits, work_order_after_missing)
        payload["success"] = False
        failed_steps = payload.get("failed_steps")
        if not isinstance(failed_steps, list):
            failed_steps = []
        failed_steps.append(
            {
                "step": 0,
                "task": "missing-evidence final-answer guard",
                "server": "runner",
                "tool": MISSING_EVIDENCE_GUARD_NAME,
                "error": guard["reason"],
                "verifier_decision": "mitigation_guard_block",
            }
        )
        payload["failed_steps"] = failed_steps

    return payload


def scan_missing_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    """Return deterministic missing-evidence hits without mutating payload."""
    hits, work_order_after_missing = _missing_evidence_scan(payload)
    return {
        "name": MISSING_EVIDENCE_GUARD_NAME,
        "triggered": bool(hits),
        "blocked_work_order": bool(work_order_after_missing),
        "hits": hits,
        "reason": (
            _guard_reason(hits, work_order_after_missing)
            if hits
            else "No missing or untrusted evidence signal detected."
        ),
    }


def build_explicit_fault_risk_adjudication(
    payload: dict[str, Any],
    *,
    enabled: bool,
) -> dict[str, Any]:
    """Build a structured fault/risk adjudication object without mutation."""
    if not enabled:
        return {
            "name": EXPLICIT_FAULT_RISK_ADJUDICATION_NAME,
            "enabled": False,
            "decision": "disabled",
        }

    missing_scan = scan_missing_evidence(payload)
    if missing_scan["triggered"]:
        return {
            "name": EXPLICIT_FAULT_RISK_ADJUDICATION_NAME,
            "enabled": True,
            "decision": "refuse_due_missing_evidence",
            "selected_fault_id": None,
            "selected_fault_label": None,
            "selected_risk_level": None,
            "deciding_evidence": [],
            "alternatives_considered": [],
            "missing_evidence": missing_scan["hits"],
            "reason": (
                "Fault/risk adjudication refused to finalize because deciding "
                "evidence is missing, empty, or untrusted."
            ),
        }

    deciding_evidence = _collect_fault_risk_evidence(payload)
    if not deciding_evidence:
        return {
            "name": EXPLICIT_FAULT_RISK_ADJUDICATION_NAME,
            "enabled": True,
            "decision": "refuse_due_missing_evidence",
            "selected_fault_id": None,
            "selected_fault_label": None,
            "selected_risk_level": None,
            "deciding_evidence": [],
            "alternatives_considered": [],
            "missing_evidence": [
                {
                    "source": "history",
                    "step": None,
                    "tool": None,
                    "reason": (
                        "No concrete DGA, fault-record, trend, anomaly, RUL, "
                        "or risk evidence was present to justify a fault/risk "
                        "choice."
                    ),
                    "target": {},
                    "excerpt": "",
                }
            ],
            "reason": (
                "Fault/risk adjudication refused to finalize because no "
                "concrete deciding evidence was present in the trajectory."
            ),
        }

    selected_fault_id = _first_evidence_value(
        deciding_evidence,
        {"fault_id", "failure_mode_id"},
    )
    selected_fault_label = _first_evidence_value(
        deciding_evidence,
        {"diagnosis", "diagnostic", "fault", "fault_label", "failure_mode", "mode"},
    )
    selected_risk_level = _first_evidence_value(deciding_evidence, RISK_FIELD_KEYS)
    alternatives = _collect_alternatives(
        payload, selected_fault_id, selected_fault_label
    )

    return {
        "name": EXPLICIT_FAULT_RISK_ADJUDICATION_NAME,
        "enabled": True,
        "decision": "finalize",
        "selected_fault_id": selected_fault_id,
        "selected_fault_label": selected_fault_label,
        "selected_risk_level": selected_risk_level,
        "deciding_evidence": deciding_evidence,
        "alternatives_considered": alternatives,
        "missing_evidence": [],
        "reason": (
            "Fault/risk adjudication found concrete deciding evidence in the "
            "trajectory; final answer should cite this evidence."
        ),
    }


def apply_explicit_fault_risk_adjudication(
    payload: dict[str, Any],
    *,
    enabled: bool,
) -> dict[str, Any]:
    """Attach adjudication metadata and block unsupported finalization."""
    if not enabled:
        return payload

    adjudication = build_explicit_fault_risk_adjudication(payload, enabled=True)
    payload["fault_risk_adjudication"] = adjudication
    if adjudication.get("decision") != "refuse_due_missing_evidence":
        return payload

    payload["answer"] = _adjudication_refusal_answer(adjudication)
    payload["success"] = False
    failed_steps = payload.get("failed_steps")
    if not isinstance(failed_steps, list):
        failed_steps = []
    failed_steps.append(adjudication_failed_step(adjudication))
    payload["failed_steps"] = failed_steps
    return payload


def adjudication_failed_step(adjudication: dict[str, Any]) -> dict[str, Any]:
    """Return a canonical failed-step entry for adjudication refusal."""
    return {
        "step": 0,
        "task": "explicit fault/risk adjudication",
        "server": "runner",
        "tool": EXPLICIT_FAULT_RISK_ADJUDICATION_NAME,
        "error": adjudication.get("reason")
        or "Fault/risk adjudication refused to finalize.",
        "verifier_decision": "fault_risk_adjudication_refusal",
    }


def adjudication_refusal_answer(adjudication: dict[str, Any]) -> str:
    """Public wrapper for deterministic refusal text."""
    return _adjudication_refusal_answer(adjudication)


def _guard_reason(
    hits: list[dict[str, Any]],
    work_order_after_missing: bool,
) -> str:
    first = hits[0]
    reason = (
        f"{MISSING_EVIDENCE_GUARD_NAME} saw missing or untrusted evidence at "
        f"{first['source']} ({first.get('tool') or 'unknown tool'}): {first['reason']}."
    )
    if work_order_after_missing:
        reason += " A work-order tool was emitted after that evidence gap."
    return reason


def _blocked_answer(
    hits: list[dict[str, Any]],
    work_order_after_missing: bool,
) -> str:
    first = hits[0]
    action = "final answer/work-order recommendation"
    if work_order_after_missing:
        action = "final answer or work order"
    return (
        "Mitigation guard blocked the "
        f"{action}: required evidence was missing, empty, or untrusted. "
        f"First blocking signal: {first.get('tool') or 'unknown tool'} at "
        f"{first['source']} ({first['reason']}). Rerun or repair the evidence "
        "retrieval step before making a maintenance recommendation."
    )


def _adjudication_refusal_answer(adjudication: dict[str, Any]) -> str:
    missing = adjudication.get("missing_evidence") or []
    if missing:
        first = missing[0]
        tool = first.get("tool") or "required evidence"
        reason = first.get("reason") or "missing deciding evidence"
        return (
            "Fault/risk adjudication refused to finalize the maintenance "
            f"recommendation: {tool} evidence is not sufficient ({reason}). "
            "Acquire or repair the deciding evidence before selecting a fault, "
            "risk level, or work-order action."
        )
    return (
        "Fault/risk adjudication refused to finalize the maintenance "
        "recommendation because no concrete deciding evidence was available."
    )


def _missing_evidence_scan(
    payload: dict[str, Any],
) -> tuple[list[dict[str, Any]], bool]:
    unresolved_hits = {}
    work_order_hits = []
    for record in _iter_tool_records(payload):
        tool = record["tool"].lower()
        if tool in WORK_ORDER_TOOLS and unresolved_hits and not work_order_hits:
            work_order_hits = list(unresolved_hits.values())
            continue

        if not tool or tool not in EVIDENCE_TOOLS:
            continue

        reason = _missing_evidence_reason(record)
        key = _evidence_key(record)
        if reason:
            unresolved_hits.setdefault(
                key,
                {
                    "source": record["source"],
                    "step": record.get("step"),
                    "tool": record["tool"],
                    "reason": reason,
                    "target": _target_dict(record),
                    "excerpt": _excerpt(
                        _effective_response(record.get("response"))
                        or record.get("error")
                    ),
                },
            )
            continue

        _clear_repaired_hit(unresolved_hits, record)

    final_hits = list(unresolved_hits.values())
    if work_order_hits:
        return _dedupe_hits(work_order_hits + final_hits), True
    return final_hits, False


def _collect_fault_risk_evidence(payload: dict[str, Any]) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for record in _iter_tool_records(payload):
        tool = str(record.get("tool") or "").lower()
        if tool not in FAULT_RISK_EVIDENCE_TOOLS:
            continue
        if _missing_evidence_reason(record):
            continue
        parsed = _parse_json_like(_effective_response(record.get("response")))
        for field, value in _iter_named_values(parsed):
            normalized = _leaf_field(field)
            if normalized not in FAULT_FIELD_KEYS and normalized not in RISK_FIELD_KEYS:
                continue
            if value in (None, "", [], {}):
                continue
            evidence.append(
                {
                    "tool": record["tool"],
                    "step": record.get("step"),
                    "field": field,
                    "value": _compact_value(value),
                    "source": record["source"],
                    "excerpt": _excerpt(record.get("response")),
                }
            )
    return _dedupe_evidence(evidence)[:8]


def _iter_named_values(value: Any, prefix: str = ""):
    parsed = _parse_json_like(_effective_response(value))
    if isinstance(parsed, dict):
        for key, item in parsed.items():
            field = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(item, dict):
                yield from _iter_named_values(item, field)
            elif isinstance(item, list):
                if _simple_list(item):
                    yield field, item
                else:
                    for index, child in enumerate(item):
                        yield from _iter_named_values(child, f"{field}[{index}]")
            else:
                yield field, item
    elif isinstance(parsed, list):
        for index, item in enumerate(parsed):
            yield from _iter_named_values(item, f"{prefix}[{index}]" if prefix else "")


def _simple_list(value: list[Any]) -> bool:
    return all(not isinstance(item, (dict, list)) for item in value)


def _compact_value(value: Any) -> str:
    if isinstance(value, str):
        return _excerpt(value, limit=160)
    return _excerpt(value, limit=160)


def _first_evidence_value(
    evidence: list[dict[str, Any]],
    fields: set[str],
) -> str | None:
    for item in evidence:
        normalized = _leaf_field(str(item.get("field") or ""))
        if normalized in fields:
            value = str(item.get("value") or "").strip()
            if value:
                return value
    return None


def _leaf_field(field: str) -> str:
    return re.sub(r"\[\d+\]", "", field).split(".")[-1].lower()


def _collect_alternatives(
    payload: dict[str, Any],
    selected_fault_id: str | None,
    selected_fault_label: str | None,
) -> list[dict[str, str]]:
    alternatives: list[dict[str, str]] = []
    selected = {item for item in (selected_fault_id, selected_fault_label) if item}
    for record in _iter_tool_records(payload):
        tool = str(record.get("tool") or "").lower()
        if tool not in {"list_fault_records", "get_fault_record"}:
            continue
        parsed = _parse_json_like(_effective_response(record.get("response")))
        for candidate in _iter_candidate_faults(parsed):
            label = candidate.get("fault_id") or candidate.get("failure_mode_id")
            label = (
                label or candidate.get("fault_label") or candidate.get("failure_mode")
            )
            if not label or label in selected:
                continue
            alternatives.append(
                {
                    "fault_id": str(label),
                    "reason_rejected": (
                        "Not selected by the deterministic adjudication pass; "
                        "the final answer must cite deciding evidence before "
                        "preferring this alternative."
                    ),
                }
            )
    return _dedupe_alternatives(alternatives)[:5]


def _iter_candidate_faults(value: Any):
    parsed = _parse_json_like(_effective_response(value))
    if isinstance(parsed, dict):
        if any(key in parsed for key in FAULT_FIELD_KEYS):
            yield {str(key): str(item) for key, item in parsed.items() if item}
        for item in parsed.values():
            yield from _iter_candidate_faults(item)
    elif isinstance(parsed, list):
        for item in parsed:
            yield from _iter_candidate_faults(item)


def _dedupe_evidence(evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped = []
    seen = set()
    for item in evidence:
        key = (
            item.get("tool"),
            item.get("step"),
            item.get("field"),
            item.get("value"),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _dedupe_alternatives(alternatives: list[dict[str, str]]) -> list[dict[str, str]]:
    deduped = []
    seen = set()
    for item in alternatives:
        key = item.get("fault_id")
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _iter_tool_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    history = payload.get("history") or payload.get("trajectory") or []
    if not isinstance(history, list):
        return records

    for step_index, step in enumerate(history):
        if not isinstance(step, dict):
            continue
        source = f"history[{step_index}]"
        tool_calls = step.get("tool_calls")
        if isinstance(tool_calls, list):
            for call_index, call in enumerate(tool_calls):
                if not isinstance(call, dict):
                    continue
                records.append(
                    {
                        "source": f"{source}.tool_calls[{call_index}]",
                        "step": step.get("step"),
                        "tool": str(call.get("name") or call.get("tool") or ""),
                        "args": call.get("arguments") or call.get("tool_args"),
                        "response": call.get("output") or call.get("response"),
                        "error": call.get("error"),
                        "success": call.get("success", True),
                    }
                )
            continue
        records.append(
            {
                "source": source,
                "step": step.get("step"),
                "tool": str(step.get("tool") or ""),
                "args": step.get("tool_args") or step.get("arguments"),
                "response": step.get("response"),
                "error": step.get("error"),
                "success": step.get("success", True),
            }
        )
    return records


def _missing_evidence_reason(record: dict[str, Any]) -> str | None:
    tool = str(record.get("tool") or "").lower()
    if record.get("success") is False:
        return "tool step was marked unsuccessful"
    if record.get("error"):
        return "tool step recorded an error"

    response = _effective_response(record.get("response"))
    parsed = _parse_json_like(response)
    if parsed == []:
        return "tool response was an empty list"
    if isinstance(parsed, dict):
        if parsed.get("error"):
            return "tool response carried an error field"
        empty_key = _first_empty_evidence_key(parsed, tool=tool)
        if empty_key:
            return f"tool response had empty evidence field {empty_key!r}"
    if isinstance(parsed, list) and not parsed:
        return "tool response was an empty list"

    text = _text(response)
    if not text.strip():
        return "tool response was empty"
    for pattern in MISSING_EVIDENCE_PATTERNS:
        if pattern.search(text):
            return f"tool response matched {pattern.pattern!r}"
    return None


def _first_empty_evidence_key(
    value: dict[str, Any],
    *,
    tool: str | None = None,
) -> str | None:
    for key, item in value.items():
        if _is_empty_evidence_value(tool, key, item, value):
            return key
        if isinstance(item, dict):
            nested = _first_empty_evidence_key(item, tool=tool)
            if nested:
                return f"{key}.{nested}"
    return None


def _is_empty_evidence_value(
    tool: str | None,
    key: str,
    item: Any,
    parent: dict[str, Any],
) -> bool:
    if key not in EMPTY_EVIDENCE_KEYS or item not in (None, "", [], {}):
        return False
    if (
        tool == "detect_anomalies"
        and key == "anomalies"
        and _positive_number(parent.get("total_readings"))
    ):
        return False
    return True


def _positive_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False


def _is_evidence_limited_answer(answer: str) -> bool:
    if not answer:
        return False
    return any(pattern.search(answer) for pattern in EVIDENCE_LIMITED_ANSWER_PATTERNS)


def _parse_json_like(value: Any) -> Any:
    value = _effective_response(value)
    if isinstance(value, (dict, list)):
        return value
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text:
        return value
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            return value
    return value


def _text(value: Any) -> str:
    value = _effective_response(value)
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    return json.dumps(value, sort_keys=True, default=str)


def _excerpt(value: Any, *, limit: int = 240) -> str:
    text = _text(value).replace("\n", " ").strip()
    return text if len(text) <= limit else text[:limit] + "...[truncated]"


def _evidence_key(record: dict[str, Any]) -> tuple[str, tuple[tuple[str, str], ...]]:
    tool = str(record.get("tool") or "").lower()
    parts = _target_parts(record.get("args"))
    if not parts:
        parts = _target_parts(_effective_response(record.get("response")))
    return (tool, parts or UNKNOWN_TARGET)


def _target_dict(record: dict[str, Any]) -> dict[str, str]:
    parts = _target_parts(record.get("args"))
    if not parts:
        parts = _target_parts(_effective_response(record.get("response")))
    return {key: value for key, value in parts if key != "*"}


def _target_parts(value: Any) -> tuple[tuple[str, str], ...]:
    parsed = _parse_json_like(_effective_response(value))
    found: dict[str, str] = {}

    def collect(candidate: Any) -> None:
        if not isinstance(candidate, dict):
            return
        for key, item in candidate.items():
            if key in TARGET_FIELD_KEYS and item not in (None, "", [], {}):
                found[key] = str(item)
            elif isinstance(item, dict):
                collect(item)

    collect(parsed)
    return tuple(sorted(found.items()))


def _effective_response(value: Any) -> Any:
    if isinstance(value, dict):
        if value.get("type") == "text" and "text" in value:
            return _effective_response(value.get("text"))
        if isinstance(value.get("content"), list):
            return _effective_response(value.get("content"))
        return value
    if isinstance(value, list):
        unwrapped = [_effective_response(item) for item in value]
        if unwrapped and all(isinstance(item, str) for item in unwrapped):
            return "\n".join(unwrapped)
        return unwrapped
    return value


def _clear_repaired_hit(
    unresolved_hits: dict[tuple[str, tuple[tuple[str, str], ...]], dict[str, str]],
    record: dict[str, Any],
) -> None:
    exact_key = _evidence_key(record)
    unresolved_hits.pop(exact_key, None)
    unresolved_hits.pop((exact_key[0], UNKNOWN_TARGET), None)


def _dedupe_hits(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped = []
    seen = set()
    for hit in hits:
        key = (hit["source"], hit.get("tool") or "", hit.get("reason") or "")
        if key in seen:
            continue
        seen.add(key)
        deduped.append(hit)
    return deduped
