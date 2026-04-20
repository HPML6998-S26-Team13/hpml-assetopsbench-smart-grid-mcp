from __future__ import annotations

import argparse
import importlib
import json
import logging
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

LOG_FORMAT = "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s"
LOG_DATE_FORMAT = "%H:%M:%S"
MAX_CONTEXT_RESPONSE_CHARS = 1200
MAX_CONTEXT_ERROR_CHARS = 600
_LOG = logging.getLogger(__name__)

SUMMARIZE_PROMPT = """\
You are summarizing the results of a multi-step task execution for an
industrial asset operations system.

Original question: {question}

If there was a self-ask clarification pass, use it only as internal guidance
and still answer the original question directly.

Step-by-step execution results:
{results}

Provide a concise, direct answer to the original question based on the results
above. Do not repeat the individual steps - just give the final answer.
"""

SELF_ASK_PROMPT = """\
You are deciding whether an industrial asset-operations question needs a brief
internal clarification pass before tool planning.

Return a single raw JSON object with exactly these keys:
- needs_self_ask: boolean
- clarifying_questions: list of at most 2 short strings
- assumptions: list of at most 3 short strings
- augmented_question: string

Rules:
- Use needs_self_ask=false when the original question is already specific enough.
- If needs_self_ask=false, set augmented_question to the original question.
- If needs_self_ask=true, augmented_question should keep the original question
  intact while appending the clarification points the planner should resolve
  internally before answering.
- Do not ask the human user for clarification. This is an internal planning aid.

Question:
{question}

JSON:
"""

VERIFIER_PROMPT = """\
You are verifying whether a completed plan-execute step actually advanced the
goal enough to continue without repair.

Return a single raw JSON object with exactly these keys:
- decision: one of "continue", "retry", "replan_suffix"
- reason: short string
- updated_focus: short string, or empty string if not needed

Rules:
- Prefer "continue" unless the current result clearly suggests the remaining
  plan should change.
- Use "retry" only when the same step should be attempted once more with the
  same overall intent.
- Use "replan_suffix" when the completed context changes what the remaining
  steps should be.
- Keep the answer benchmarkable: avoid open-ended or conversational behavior.

Original question:
{question}

Effective planning question:
{effective_question}

Current step:
{current_step}

Current step result:
{current_result}

Completed history so far:
{history}

Remaining planned steps:
{remaining_steps}

JSON:
"""


@dataclass
class SelfAskDecision:
    needs_self_ask: bool
    clarifying_questions: list[str]
    assumptions: list[str]
    augmented_question: str


@dataclass
class VerificationDecision:
    decision: str
    reason: str
    updated_focus: str


def setup_logging(verbose: bool) -> None:
    level = logging.INFO if verbose else logging.WARNING
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))
    logging.root.handlers.clear()
    logging.root.addHandler(handler)
    logging.root.setLevel(level)


def build_parser(prog: str, description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=prog, description=description)
    parser.add_argument("question", help="The question to answer.")
    parser.add_argument(
        "--model-id",
        default="watsonx/meta-llama/llama-4-maverick-17b-128e-instruct-fp8",
        metavar="MODEL_ID",
        help="litellm model string with provider prefix.",
    )
    parser.add_argument(
        "--server",
        action="append",
        metavar="NAME=PATH",
        dest="servers",
        default=[],
        help="Register an MCP server as NAME=PATH. Repeatable.",
    )
    parser.add_argument(
        "--aob-path",
        default="",
        metavar="PATH",
        help="Path to the sibling AssetOpsBench checkout.",
    )
    parser.add_argument(
        "--show-plan",
        action="store_true",
        help="Print the generated plan before execution.",
    )
    parser.add_argument(
        "--show-trajectory",
        action="store_true",
        help="Print each step result after execution.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Output the full result as JSON.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show INFO-level progress logs on stderr.",
    )
    return parser


def resolve_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_aob_path(repo_root: Path, raw_path: str = "") -> Path:
    if raw_path:
        return Path(raw_path).resolve()
    return (repo_root.parent / "AssetOpsBench").resolve()


def bootstrap_aob(aob_path: Path) -> None:
    src_path = aob_path / "src"
    agent_src_path = src_path / "agent"
    if not src_path.exists():
        raise FileNotFoundError(f"AssetOpsBench src path not found: {src_path}")
    if not agent_src_path.exists():
        raise FileNotFoundError(f"AssetOpsBench agent path not found: {agent_src_path}")
    for path in (src_path, agent_src_path):
        path_text = str(path)
        if path_text not in sys.path:
            sys.path.insert(0, path_text)


def preflight_aob_runtime_dependencies() -> None:
    failures = []
    checks = {
        "litellm": "AssetOpsBench LiteLLM backend",
        "mcp": "AssetOpsBench plan-execute MCP client helpers",
    }
    install_hint = (
        "Install the shared repo dependencies with `uv pip install -r requirements.txt` "
        "or, on Insomnia, `uv pip install -r requirements-insomnia.txt`."
    )
    for module_name, reason in checks.items():
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # noqa: BLE001
            failures.append(
                f"- {module_name}: {reason} failed to import "
                f"({exc.__class__.__name__}: {exc})"
            )
    if failures:
        raise RuntimeError(
            "Repo-local PE-family runners require a small AssetOpsBench runtime slice "
            "that is missing or incompatible in the active Python environment:\n"
            + "\n".join(failures)
            + "\n"
            + install_hint
        )
    if sys.version_info < (3, 12):
        _LOG.info(
            "AssetOpsBench declares Python >= 3.12, but the repo-local PE runners "
            "only import its plan-execute subset. Continuing under Python %s.",
            sys.version.split()[0],
        )


def build_llm(model_id: str):
    from llm.litellm import LiteLLMBackend

    return LiteLLMBackend(model_id=model_id)


PLANNING_GUARDRAILS = """\
Planning guardrails for this repo-local Smart Grid setup:
- Use only these real servers: iot, fmsr, tsfm, wo.
- Do not use a fake server like "none" or "null".
- If you only need a final natural-language answer, omit that final step. The
  runner will synthesize the final answer after tool execution.
- get_dga_record and analyze_dga are FMSR tools, not IoT tools.
- get_sensor_correlation expects a failure_mode_id like FM-006, not a
  transformer_id like T-015.
"""

PLANNER_NOTES = {
    "fmsr": [
        "Use get_dga_record(transformer_id=T-xxx) to retrieve the latest DGA snapshot for a transformer.",
        "Use analyze_dga(h2, ch4, c2h2, c2h4, c2h6[, transformer_id]) to diagnose a transformer from gas readings.",
        "Use get_sensor_correlation only when you already know a failure_mode_id like FM-006.",
    ],
    "iot": [
        "IoT tools expose asset metadata and raw sensor/time-series readings only.",
        "IoT does not provide DGA diagnosis tools.",
        "Valid Smart Grid sensor_ids in this repo are load_current_a, oil_temp_c, power_factor, voltage_hv_kv, voltage_lv_kv, and winding_temp_top_c.",
        "There are no DGA gas sensors exposed as IoT time-series sensor_ids.",
    ],
    "tsfm": [
        "TSFM operates on the same sensor_ids exposed by IoT list_sensors.",
        "Use winding_temp_top_c, not winding_temp_c.",
        "Do not use DGA gas names as TSFM sensor_ids.",
    ],
}

TOOL_SCHEMA_HINTS = {
    ("fmsr", "get_sensor_correlation", "failure_mode_id"): (
        "string (failure mode id like FM-006 from list_failure_modes/search_failure_modes; "
        "not a transformer id)"
    ),
    ("fmsr", "get_dga_record", "transformer_id"): "string (transformer id like T-015)",
    (
        "iot",
        "get_asset_metadata",
        "transformer_id",
    ): "string (transformer id like T-015)",
    ("iot", "list_sensors", "transformer_id"): "string (transformer id like T-015)",
    (
        "iot",
        "get_sensor_readings",
        "transformer_id",
    ): "string (transformer id like T-015)",
    ("tsfm", "get_rul", "transformer_id"): "string (transformer id like T-015)",
    ("tsfm", "forecast_rul", "transformer_id"): "string (transformer id like T-015)",
    (
        "tsfm",
        "detect_anomalies",
        "transformer_id",
    ): "string (transformer id like T-015)",
    ("tsfm", "trend_analysis", "transformer_id"): "string (transformer id like T-015)",
}

SENSOR_TOOLS = {"get_sensor_readings", "detect_anomalies", "trend_analysis"}
SENSOR_ALIAS_MAP = {
    "winding_temp_c": "winding_temp_top_c",
}


def parse_server_overrides(entries: list[str]) -> dict[str, Path] | None:
    if not entries:
        return None
    result: dict[str, Path] = {}
    for entry in entries:
        if "=" not in entry:
            raise ValueError(f"--server requires NAME=PATH format, got: {entry!r}")
        name, _, path = entry.partition("=")
        result[name.strip()] = Path(path.strip()).resolve()
    return result


def effective_server_paths(entries: list[str], repo_root: Path) -> dict[str, Path]:
    try:
        overrides = parse_server_overrides(entries)
    except ValueError as exc:
        raise SystemExit(f"Invalid --server entry: {exc}") from exc
    if overrides is not None:
        return overrides
    defaults = {
        "iot": repo_root / "mcp_servers/iot_server/server.py",
        "fmsr": repo_root / "mcp_servers/fmsr_server/server.py",
        "tsfm": repo_root / "mcp_servers/tsfm_server/server.py",
        "wo": repo_root / "mcp_servers/wo_server/server.py",
    }
    env_names = {
        "iot": "SERVER_IOT_PATH",
        "fmsr": "SERVER_FMSR_PATH",
        "tsfm": "SERVER_TSFM_PATH",
        "wo": "SERVER_WO_PATH",
    }
    resolved: dict[str, Path] = {}
    for name, default_path in defaults.items():
        raw = os.environ.get(env_names[name], str(default_path))
        resolved[name] = Path(raw).resolve()
    return resolved


def build_planning_question(question: str) -> str:
    return question.strip() + "\n\n" + PLANNING_GUARDRAILS.strip()


async def build_tool_catalog(
    server_paths: dict[str, Path],
) -> dict[str, dict[str, dict[str, str]]]:
    from plan_execute.executor import _list_tools

    catalog: dict[str, dict[str, dict[str, str]]] = {}
    for name, path in server_paths.items():
        try:
            tools = await _list_tools(path)
        except Exception:  # noqa: BLE001
            catalog[name] = {}
            continue
        server_catalog: dict[str, dict[str, str]] = {}
        for tool in tools:
            parameters = []
            for param in tool.get("parameters", []):
                hint = TOOL_SCHEMA_HINTS.get((name, tool["name"], param["name"]))
                rendered = hint or (
                    f"{param['type']}{'?' if not param['required'] else ''}"
                )
                parameters.append(f"{param['name']}: {rendered}")
            server_catalog[tool["name"]] = {
                "description": tool.get("description", "").strip(),
                "schema": ", ".join(parameters),
            }
        catalog[name] = server_catalog
    return catalog


def build_planner_descriptions(
    descriptions: dict[str, str],
    tool_catalog: dict[str, dict[str, dict[str, str]]],
) -> dict[str, str]:
    planner_descriptions: dict[str, str] = {}
    for server_name, description in descriptions.items():
        lines = [description.strip()] if description.strip() else []
        notes = PLANNER_NOTES.get(server_name, [])
        if notes:
            lines.append("Planner notes:")
            lines.extend(f"  - {note}" for note in notes)
        if server_name in tool_catalog and tool_catalog[server_name]:
            lines.append("Canonical tool signatures:")
            for tool_name, info in tool_catalog[server_name].items():
                schema = info.get("schema", "")
                desc = info.get("description", "")
                lines.append(f"  - {tool_name}({schema}): {desc}".rstrip())
        planner_descriptions[server_name] = "\n".join(line for line in lines if line)
    return planner_descriptions


def normalize_plan_steps(
    plan,
    tool_catalog: dict[str, dict[str, dict[str, str]]],
    *,
    default_server: str = "iot",
) -> list[str]:
    warnings: list[str] = []
    if not getattr(plan, "steps", None):
        return warnings

    tool_servers: dict[str, set[str]] = {}
    for server_name, tools in tool_catalog.items():
        for tool_name in tools:
            tool_servers.setdefault(tool_name, set()).add(server_name)

    ordered_steps = sorted(plan.steps, key=lambda step: int(step.step_number))
    kept_steps = []
    for index, step in enumerate(ordered_steps):
        server = str(getattr(step, "server", "") or "").strip()
        tool = str(getattr(step, "tool", "") or "").strip()
        server_key = server.lower()
        tool_key = tool
        is_terminal = index == len(ordered_steps) - 1

        if tool_key.lower() in {"", "none", "null"}:
            if server_key in {"", "none", "null"} and is_terminal:
                warnings.append(
                    f"Dropped terminal synthesis-only step {step.step_number}; final answer is summarized outside the plan."
                )
                continue
            if server_key in {"", "none", "null"}:
                setattr(step, "server", default_server)
                warnings.append(
                    f"Normalized server for no-tool step {step.step_number} to {default_server}."
                )
            kept_steps.append(step)
            continue

        if server_key in {"", "none", "null"} or server_key not in tool_catalog:
            candidates = sorted(tool_servers.get(tool_key, set()))
            if len(candidates) == 1:
                setattr(step, "server", candidates[0])
                warnings.append(
                    f"Rerouted step {step.step_number} tool {tool_key} to server {candidates[0]}."
                )
                kept_steps.append(step)
                continue

        elif tool_key not in tool_catalog.get(server_key, {}):
            candidates = sorted(tool_servers.get(tool_key, set()))
            if len(candidates) == 1:
                setattr(step, "server", candidates[0])
                warnings.append(
                    f"Rerouted step {step.step_number} tool {tool_key} from {server_key} to {candidates[0]}."
                )
                kept_steps.append(step)
                continue

        kept_steps.append(step)

    old_to_new: dict[int, int] = {}
    for new_step_number, step in enumerate(kept_steps, start=1):
        old_to_new[int(step.step_number)] = new_step_number
        setattr(step, "step_number", new_step_number)

    for step in kept_steps:
        dependencies = [
            old_to_new[dep]
            for dep in getattr(step, "dependencies", [])
            if dep in old_to_new
        ]
        setattr(step, "dependencies", dependencies)

    plan.steps = kept_steps
    return warnings


def tool_schema_for_step(
    tool_catalog: dict[str, dict[str, dict[str, str]]],
    server: str,
    tool: str,
) -> str:
    return tool_catalog.get(server, {}).get(tool, {}).get("schema", "")


def parse_json_object(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        inner = lines[1:-1] if lines and lines[-1].strip() == "```" else lines[1:]
        text = "\n".join(inner).strip()
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            try:
                value = json.loads(text[start:end])
                return value if isinstance(value, dict) else {}
            except json.JSONDecodeError:
                return {}
        return {}


def parse_json_like_value(raw: Any) -> Any:
    if not isinstance(raw, str):
        return raw

    text = raw.strip()
    if not text:
        return raw

    try:
        payload = json.loads(text)
        if isinstance(payload, (dict, list)):
            return payload
    except json.JSONDecodeError:
        pass

    payload = parse_json_object(text)
    if payload:
        return payload

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return raw

    parsed_items = []
    for line in lines:
        item = parse_json_object(line)
        if not item:
            return raw
        parsed_items.append(item)
    return parsed_items


def maybe_self_ask(question: str, llm) -> SelfAskDecision:
    raw = llm.generate(SELF_ASK_PROMPT.format(question=question))
    payload = parse_json_object(raw)
    needs_self_ask = bool(payload.get("needs_self_ask", False))
    clarifying_questions = [
        str(item).strip()
        for item in payload.get("clarifying_questions", [])
        if str(item).strip()
    ][:2]
    assumptions = [
        str(item).strip()
        for item in payload.get("assumptions", [])
        if str(item).strip()
    ][:3]
    augmented_question = str(payload.get("augmented_question", "")).strip()
    if not needs_self_ask:
        return SelfAskDecision(
            needs_self_ask=False,
            clarifying_questions=[],
            assumptions=[],
            augmented_question=question,
        )
    if not augmented_question:
        extra = []
        if clarifying_questions:
            extra.append(
                "Resolve these clarification questions internally before answering:\n- "
                + "\n- ".join(clarifying_questions)
            )
        if assumptions:
            extra.append(
                "Use these temporary assumptions if needed:\n- "
                + "\n- ".join(assumptions)
            )
        augmented_question = question + "\n\n" + "\n\n".join(extra)
    return SelfAskDecision(
        needs_self_ask=True,
        clarifying_questions=clarifying_questions,
        assumptions=assumptions,
        augmented_question=augmented_question,
    )


def terminal_history(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest_by_step: dict[int, dict[str, Any]] = {}
    for entry in history:
        latest_by_step[int(entry["step"])] = entry
    return [latest_by_step[step] for step in sorted(latest_by_step)]


def summarize_terminal_failures(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    failures = []
    for entry in terminal_history(history):
        if bool(entry.get("success", False)):
            continue
        failures.append(
            {
                "step": int(entry["step"]),
                "task": entry.get("task"),
                "server": entry.get("server"),
                "tool": entry.get("tool"),
                "error": entry.get("error"),
                "verifier_decision": entry.get("verifier_decision"),
            }
        )
    return failures


def summarize_answer(question: str, history: list[dict[str, Any]], llm) -> str:
    final_history = terminal_history(history)
    results_text = "\n\n".join(
        f"Step {entry['step']} - {entry['task']} (server: {entry['server']}):\n"
        + (
            compact_prompt_text(entry["response"], limit=600)
            if entry["success"]
            else f"ERROR: {compact_prompt_text(entry['error'], limit=240)}"
        )
        for entry in final_history
    )
    try:
        return llm.generate(
            SUMMARIZE_PROMPT.format(question=question, results=results_text)
        )
    except Exception as exc:
        _LOG.warning(
            "Final answer summarization failed (%s); using a compact fallback summary.",
            exc,
        )
        parts = []
        for entry in final_history:
            detail = (
                compact_prompt_text(entry["response"], limit=160)
                if entry["success"]
                else f"ERROR: {compact_prompt_text(entry['error'], limit=120)}"
            )
            parts.append(f"Step {entry['step']} ({entry['tool']}): {detail}")
        return (
            f"Question: {question}\n"
            "Execution completed, but the LLM summary step exceeded the prompt budget. "
            "Compact terminal results:\n- " + "\n- ".join(parts)
        )


def serialize_steps(steps: list[Any]) -> list[dict[str, Any]]:
    return [
        {
            "step": step.step_number,
            "task": step.task,
            "server": step.server,
            "tool": step.tool,
            "tool_args": step.tool_args,
            "dependencies": step.dependencies,
            "expected_output": step.expected_output,
        }
        for step in steps
    ]


def serialize_plan(plan) -> list[dict[str, Any]]:
    return serialize_steps(plan.steps)


def response_error_payload(response: Any) -> str | None:
    response = parse_json_like_value(response)
    if isinstance(response, dict):
        value = response.get("error")
        if value:
            return str(value).strip()
        return None

    if isinstance(response, list):
        for item in response:
            value = response_error_payload(item)
            if value:
                return value
        return None

    if not isinstance(response, str):
        return None

    text = response.strip()
    if not text:
        return None
    if text.lower().startswith("unknown tool:"):
        return text
    payload = parse_json_object(text)
    return response_error_payload(payload)


def serialize_step_result(result, **extra: Any) -> dict[str, Any]:
    normalized_response = normalize_response_text(result.response)
    payload_error = response_error_payload(normalized_response)
    payload = {
        "step": result.step_number,
        "task": result.task,
        "server": result.server,
        "tool": result.tool,
        "tool_args": result.tool_args,
        "response": normalized_response,
        "error": payload_error or result.error,
        "success": bool(result.success) and payload_error is None,
    }
    payload.update(extra)
    return payload


def normalize_response_text(response: Any) -> str:
    parsed = parse_json_like_value(response)
    if isinstance(parsed, (dict, list)):
        return json.dumps(parsed, indent=2)
    return str(response)


def canonicalize_step_result(result) -> None:
    result.response = normalize_response_text(result.response)


def compact_step_for_context(result) -> None:
    response = getattr(result, "response", None)
    if response is not None:
        result.response = compact_prompt_text(
            response, limit=MAX_CONTEXT_RESPONSE_CHARS
        )
    error = getattr(result, "error", None)
    if error:
        result.error = compact_prompt_text(error, limit=MAX_CONTEXT_ERROR_CHARS)


def available_sensor_ids(context: dict[int, Any]) -> set[str]:
    sensors: set[str] = set()
    for result in context.values():
        if getattr(result, "tool", "") != "list_sensors":
            continue
        payload = parse_json_like_value(getattr(result, "response", ""))
        if isinstance(payload, dict):
            sensor_id = payload.get("sensor_id")
            if sensor_id:
                sensors.add(str(sensor_id))
        elif isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict) and item.get("sensor_id"):
                    sensors.add(str(item["sensor_id"]))
    return sensors


def extract_requested_sensor(task: str) -> str | None:
    patterns = [
        r"([A-Za-z0-9_]+)\s+sensor(?:'s)?\s+readings",
        r"sensor\s+([A-Za-z0-9_]+)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, task)
        if match:
            return match.group(1)
    return None


def repair_sensor_task_text(task: str, sensors: set[str]) -> tuple[str, str | None]:
    requested = extract_requested_sensor(task)
    if not requested or requested in sensors:
        return task, None

    alias = SENSOR_ALIAS_MAP.get(requested)
    if alias and alias in sensors:
        return task.replace(requested, alias), (
            f"Rewrote sensor id {requested} -> {alias} from list_sensors context."
        )

    return task, None


def should_skip_invalid_sensor_step(step: Any, sensors: set[str]) -> tuple[bool, str]:
    if getattr(step, "tool", "") != "get_sensor_readings":
        return False, ""

    requested = extract_requested_sensor(getattr(step, "task", ""))
    if not requested or requested in sensors:
        return False, ""

    lowered = requested.lower()
    if lowered.startswith("dga_") or lowered.startswith("dissolved_"):
        return (
            True,
            (
                f"Skipped unsupported IoT sensor lookup for {requested}; "
                "DGA data in this repo comes from FMSR get_dga_record/analyze_dga, "
                "not IoT time-series sensors."
            ),
        )

    return False, ""


def compact_history(history: list[dict[str, Any]]) -> str:
    if not history:
        return "(none)"
    chunks = []
    for entry in history:
        status = "OK" if entry["success"] else "ERR"
        detail = entry["response"] if entry["success"] else entry["error"]
        detail = compact_prompt_text(detail, limit=240)
        chunks.append(
            f"Step {entry['step']} [{status}] {entry['task']} | tool={entry['tool']} | detail={detail}"
        )
    return "\n".join(chunks)


def compact_steps(steps: list[Any]) -> str:
    if not steps:
        return "(none)"
    return "\n".join(
        f"Step {step.step_number}: {step.task} | server={step.server} | tool={step.tool}"
        for step in steps
    )


def compact_prompt_text(value: Any, *, limit: int) -> str:
    text = normalize_response_text(value)
    if len(text) <= limit:
        return text
    truncated = len(text) - limit
    return f"{text[:limit]}\n...[truncated {truncated} chars]"


def compact_verifier_result(current_result: dict[str, Any]) -> dict[str, Any]:
    compacted = dict(current_result)
    if "response" in compacted:
        compacted["response"] = compact_prompt_text(compacted["response"], limit=1200)
    if "error" in compacted and compacted["error"]:
        compacted["error"] = compact_prompt_text(compacted["error"], limit=600)
    return compacted


def verify_step(
    question: str,
    effective_question: str,
    current_step: Any,
    current_result: dict[str, Any],
    history: list[dict[str, Any]],
    remaining_steps: list[Any],
    llm,
) -> VerificationDecision:
    verifier_payload = compact_verifier_result(current_result)
    try:
        raw = llm.generate(
            VERIFIER_PROMPT.format(
                question=question,
                effective_question=effective_question,
                current_step=(
                    f"Step {current_step.step_number}: {current_step.task} "
                    f"(server={current_step.server}, tool={current_step.tool})"
                ),
                current_result=json.dumps(verifier_payload, indent=2),
                history=compact_history(history),
                remaining_steps=compact_steps(remaining_steps),
            )
        )
    except Exception as exc:
        _LOG.warning(
            "Verifier failed (%s); falling back to decision='continue'.",
            exc,
        )
        return VerificationDecision(
            decision="continue",
            reason="Verifier unavailable; continuing with the current result.",
            updated_focus="",
        )
    payload = parse_json_object(raw)
    if not payload:
        _LOG.warning(
            "Verifier returned no parseable JSON; falling back to decision='continue'."
        )
    decision = str(payload.get("decision", "continue")).strip().lower()
    if decision not in {"continue", "retry", "replan_suffix"}:
        _LOG.warning(
            "Verifier returned unknown decision %r; falling back to 'continue'.",
            decision,
        )
        decision = "continue"
    return VerificationDecision(
        decision=decision,
        reason=str(payload.get("reason", "")).strip()
        or "No additional verifier reason recorded.",
        updated_focus=str(payload.get("updated_focus", "")).strip(),
    )


def build_retry_question(
    question: str,
    effective_question: str,
    current_step: Any,
    current_result: dict[str, Any],
    decision: VerificationDecision,
    retries_used: int,
) -> str:
    prompt = [
        effective_question,
        "",
        "Retry guidance for the current execution step:",
        f"- Original question: {question}",
        f"- Step: {current_step.step_number} / {current_step.task}",
        (
            "- Previous attempt result: "
            f"{compact_prompt_text(current_result.get('response') or current_result.get('error') or '(none)', limit=400)}"
        ),
        f"- Verifier reason: {decision.reason}",
        f"- Retry attempt number: {retries_used}",
        "- Keep the same overall intent, but correct the specific issue the verifier flagged.",
    ]
    if decision.updated_focus:
        prompt.append(f"- Updated focus: {decision.updated_focus}")
    return "\n".join(prompt)


def build_suffix_replan_question(
    question: str,
    effective_question: str,
    history: list[dict[str, Any]],
    remaining_steps: list[Any],
    decision: VerificationDecision,
) -> str:
    prompt = [
        "Replan only the remaining suffix of the task.",
        "",
        f"Original question:\n{question}",
        "",
        f"Effective planning question:\n{effective_question}",
        "",
        "Verified completed context:",
        compact_history(history),
        "",
        "Remaining plan that may need repair:",
        compact_steps(remaining_steps),
        "",
        f"Verifier reason: {decision.reason}",
    ]
    if decision.updated_focus:
        prompt.extend(["", f"Updated focus for the suffix: {decision.updated_focus}"])
    prompt.extend(
        [
            "",
            "Only plan the remaining work. Do not repeat already completed steps.",
            "Rules for this repaired suffix plan:",
            "- Start the repaired suffix at step 1.",
            "- Completed steps are already done and available as context, not as dependencies.",
            "- The first suffix step must use Dependency1: None.",
            "- Only reference dependencies on earlier suffix steps (#S1, #S2, ...) and never on completed steps.",
            "- If a suffix step needs prior completed context, mention it in the task text instead of as a dependency.",
        ]
    )
    return "\n".join(prompt)


def generate_suffix_plan(planner, replan_question: str, descriptions: dict[str, str]):
    try:
        return planner.generate_plan(replan_question, descriptions), None
    except Exception as exc:  # noqa: BLE001
        _LOG.warning(
            "Suffix replan generation failed; continuing with the original remaining plan: %s",
            exc,
        )
        return None, str(exc)


def renumber_plan(plan, offset: int):
    from plan_execute.models import Plan, PlanStep

    renumbered_steps = []
    for step in plan.steps:
        renumbered_steps.append(
            PlanStep(
                step_number=step.step_number + offset,
                task=step.task,
                server=step.server,
                tool=step.tool,
                tool_args=step.tool_args,
                dependencies=[dep + offset for dep in step.dependencies],
                expected_output=step.expected_output,
            )
        )
    return Plan(steps=renumbered_steps, raw=plan.raw)


def print_plan(plan: list[dict[str, Any]]) -> None:
    print("\n" + "─" * 60)
    print("  Plan")
    print("─" * 60)
    for step in plan:
        deps = ", ".join(f"#{dep}" for dep in step["dependencies"]) or "none"
        print(f"  [{step['step']}] {step['server']}: {step['task']}")
        print(f"       tool: {step['tool']}  args: {step['tool_args']}")
        print(f"       deps={deps} | expected: {step['expected_output']}")


def print_history(history: list[dict[str, Any]]) -> None:
    print("\n" + "─" * 60)
    print("  Trajectory")
    print("─" * 60)
    for entry in history:
        status = "OK " if entry["success"] else "ERR"
        print(f"  [{status}] Step {entry['step']} ({entry['server']}): {entry['task']}")
        if entry["tool"] and entry["tool"].lower() not in {"none", "null", ""}:
            print(f"       tool: {entry['tool']}  args: {entry['tool_args']}")
        if entry.get("verifier_decision"):
            print(
                "       verifier: "
                f"{entry['verifier_decision']} | {entry.get('verifier_reason', '')}"
            )
        detail = entry["response"] if entry["success"] else f"Error: {entry['error']}"
        snippet = detail[:200] + ("..." if len(detail) > 200 else "")
        print(f"        {snippet}")
