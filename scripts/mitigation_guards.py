"""Deterministic mitigation guards for benchmark trial artifacts."""

from __future__ import annotations

import json
import re
from typing import Any

MISSING_EVIDENCE_GUARD_NAME = "missing_evidence_final_answer_guard"

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
    "get_fault_history",
}

WORK_ORDER_TOOLS = {
    "create_work_order",
    "create_inspection_order",
    "update_work_order",
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

    hits = _missing_evidence_hits(payload)
    work_order_after_missing = _work_order_after_first_hit(payload, hits)
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


def _guard_reason(
    hits: list[dict[str, str]],
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
    hits: list[dict[str, str]],
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


def _missing_evidence_hits(payload: dict[str, Any]) -> list[dict[str, str]]:
    hits = []
    for record in _iter_tool_records(payload):
        tool = record["tool"].lower()
        if not tool or tool not in EVIDENCE_TOOLS:
            continue
        reason = _missing_evidence_reason(record)
        if not reason:
            continue
        hits.append(
            {
                "source": record["source"],
                "tool": record["tool"],
                "reason": reason,
                "excerpt": _excerpt(record.get("response") or record.get("error")),
            }
        )
    return hits


def _work_order_after_first_hit(
    payload: dict[str, Any],
    hits: list[dict[str, str]],
) -> bool:
    if not hits:
        return False
    first_order = _source_order(hits[0]["source"])
    for record in _iter_tool_records(payload):
        if record["tool"].lower() not in WORK_ORDER_TOOLS:
            continue
        if _source_order(record["source"]) > first_order:
            return True
    return False


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
                        "tool": str(call.get("name") or call.get("tool") or ""),
                        "response": call.get("output") or call.get("response"),
                        "error": call.get("error"),
                        "success": call.get("success", True),
                    }
                )
            continue
        records.append(
            {
                "source": source,
                "tool": str(step.get("tool") or ""),
                "response": step.get("response"),
                "error": step.get("error"),
                "success": step.get("success", True),
            }
        )
    return records


def _missing_evidence_reason(record: dict[str, Any]) -> str | None:
    if record.get("success") is False:
        return "tool step was marked unsuccessful"
    if record.get("error"):
        return "tool step recorded an error"

    response = record.get("response")
    parsed = _parse_json_like(response)
    if parsed == []:
        return "tool response was an empty list"
    if isinstance(parsed, dict):
        if parsed.get("error"):
            return "tool response carried an error field"
        empty_key = _first_empty_evidence_key(parsed)
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


def _first_empty_evidence_key(value: dict[str, Any]) -> str | None:
    for key, item in value.items():
        if key in EMPTY_EVIDENCE_KEYS and item in (None, "", [], {}):
            return key
        if isinstance(item, dict):
            nested = _first_empty_evidence_key(item)
            if nested:
                return f"{key}.{nested}"
    return None


def _is_evidence_limited_answer(answer: str) -> bool:
    if not answer:
        return False
    return any(pattern.search(answer) for pattern in EVIDENCE_LIMITED_ANSWER_PATTERNS)


def _parse_json_like(value: Any) -> Any:
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
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    return json.dumps(value, sort_keys=True, default=str)


def _excerpt(value: Any, *, limit: int = 240) -> str:
    text = _text(value).replace("\n", " ").strip()
    return text if len(text) <= limit else text[:limit] + "...[truncated]"


def _source_order(source: str) -> tuple[int, int]:
    numbers = [int(part) for part in re.findall(r"\[(\d+)\]", source)]
    if not numbers:
        return (10**9, 10**9)
    if len(numbers) == 1:
        return (numbers[0], -1)
    return (numbers[0], numbers[1])
