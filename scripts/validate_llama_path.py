"""
WatsonX in-process connectivity check for the four MCP server modules.

This is a development-time helper, not the canonical #58 benchmark proof.
The authoritative end-to-end proof (Insomnia A6000, self-hosted Llama-3.1-8B,
all four servers via the real AssetOpsBench plan-execute harness) is captured
in benchmarks/validation_8760652.log and benchmarks/validation_output.json.

What this script does
---------------------
1. Defines a representative subset of MCP tool schemas in WatsonX
   function-calling format.
2. Sends a diagnostic scenario to llama-3-3-70b-instruct on WatsonX and
   drives a tool-call loop until the model produces a final answer.
3. Routes each tool call to the local MCP server Python functions (in-process).
4. Prints a full annotated trace confirming import and call-path connectivity.

Scenario
--------
"Diagnose transformer T-018. Retrieve its asset metadata, get its DGA record,
analyse the gas concentrations, and check its remaining useful life. Summarise
the fault type and recommended next action."

Servers exercised:
  IoT    → get_asset_metadata
  FMSR   → get_dga_record, analyze_dga
  TSFM   → get_rul
  WO     → (deliberately not auto-invoked; benchmark can extend this)

Usage
-----
  .venv/bin/python scripts/validate_llama_path.py
  .venv/bin/python scripts/validate_llama_path.py --model meta-llama/llama-3-3-70b-instruct
  .venv/bin/python scripts/validate_llama_path.py --transformer T-007
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap repo root so MCP server imports work from any CWD
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

# ---------------------------------------------------------------------------
# Load .env
# ---------------------------------------------------------------------------
_env = REPO_ROOT / ".env"
if _env.exists():
    for line in _env.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())

# ---------------------------------------------------------------------------
# MCP server function imports (in-process, no subprocess required)
# ---------------------------------------------------------------------------
from mcp_servers.iot_server.server import get_asset_metadata, list_assets
from mcp_servers.fmsr_server.server import get_dga_record, analyze_dga
from mcp_servers.tsfm_server.server import get_rul, trend_analysis
from mcp_servers.wo_server.server import create_work_order, estimate_downtime

# ---------------------------------------------------------------------------
# Tool registry — maps tool name → callable
# ---------------------------------------------------------------------------
_TOOL_REGISTRY: dict[str, callable] = {
    "get_asset_metadata": get_asset_metadata,
    "list_assets": list_assets,
    "get_dga_record": get_dga_record,
    "analyze_dga": analyze_dga,
    "get_rul": get_rul,
    "trend_analysis": trend_analysis,
    "create_work_order": create_work_order,
    "estimate_downtime": estimate_downtime,
}

# ---------------------------------------------------------------------------
# WatsonX tool schemas (OpenAI-compatible function-calling format)
# ---------------------------------------------------------------------------
MCP_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_asset_metadata",
            "description": (
                "Return full nameplate and status metadata for a single transformer. "
                "Returns transformer_id, name, manufacturer, location, voltage_class, "
                "rating_kva, install_date, age_years, health_status, fdd_category, "
                "rul_days, in_service."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "transformer_id": {
                        "type": "string",
                        "description": "Asset identifier, e.g. 'T-018'.",
                    }
                },
                "required": ["transformer_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_dga_record",
            "description": (
                "Retrieve the most recent dissolved gas analysis (DGA) record for a "
                "transformer. Returns gas concentrations in ppm: dissolved_h2_ppm, "
                "dissolved_ch4_ppm, dissolved_c2h2_ppm, dissolved_c2h4_ppm, "
                "dissolved_c2h6_ppm, dissolved_co_ppm, dissolved_co2_ppm, and fault_label."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "transformer_id": {
                        "type": "string",
                        "description": "Asset identifier, e.g. 'T-018'.",
                    }
                },
                "required": ["transformer_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_dga",
            "description": (
                "Classify dissolved gas concentrations into a fault type using the "
                "IEC 60599 Rogers Ratio method. Returns iec_code, diagnosis, and the "
                "three diagnostic ratios (R1=CH4/H2, R2=C2H2/C2H4, R3=C2H4/C2H6)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "h2": {"type": "number", "description": "Hydrogen (ppm)."},
                    "ch4": {"type": "number", "description": "Methane (ppm)."},
                    "c2h2": {"type": "number", "description": "Acetylene (ppm)."},
                    "c2h4": {"type": "number", "description": "Ethylene (ppm)."},
                    "c2h6": {"type": "number", "description": "Ethane (ppm)."},
                    "transformer_id": {
                        "type": "string",
                        "description": "Optional — included in result for traceability.",
                    },
                },
                "required": ["h2", "ch4", "c2h2", "c2h4", "c2h6"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_rul",
            "description": (
                "Return the most recent remaining useful life (RUL) estimate for a "
                "transformer. Returns rul_days, health_index, fdd_category, and a "
                "plain-language interpretation."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "transformer_id": {
                        "type": "string",
                        "description": "Asset identifier, e.g. 'T-018'.",
                    }
                },
                "required": ["transformer_id"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Tool execution
# ---------------------------------------------------------------------------


def execute_tool(name: str, arguments: dict) -> str:
    """Call the registered MCP function and return its result as a JSON string."""
    fn = _TOOL_REGISTRY.get(name)
    if fn is None:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        result = fn(**arguments)
        return json.dumps(result, default=str)
    except Exception as exc:
        return json.dumps({"error": str(exc)})


# ---------------------------------------------------------------------------
# Main validation loop
# ---------------------------------------------------------------------------


def run_validation(transformer_id: str, model_id: str, max_rounds: int = 6) -> bool:
    """
    Drive a tool-call loop against WatsonX Llama.

    Returns True if the model produced a final text answer (success), False otherwise.
    """
    try:
        from ibm_watsonx_ai import Credentials
        from ibm_watsonx_ai.foundation_models import ModelInference
    except ImportError:
        print("ERROR: ibm-watsonx-ai not installed. Run: pip install ibm-watsonx-ai")
        return False

    api_key = os.environ.get("WATSONX_API_KEY")
    project_id = os.environ.get("WATSONX_PROJECT_ID")
    url = os.environ.get("WATSONX_URL")

    missing = [
        k
        for k, v in [
            ("WATSONX_API_KEY", api_key),
            ("WATSONX_PROJECT_ID", project_id),
            ("WATSONX_URL", url),
        ]
        if not v
    ]
    if missing:
        print(f"ERROR: missing env vars: {missing}")
        return False

    print(f"[setup] model        = {model_id}")
    print(f"[setup] transformer  = {transformer_id}")
    print(f"[setup] WatsonX URL  = {url}")
    print()

    creds = Credentials(url=url, api_key=api_key)
    model = ModelInference(
        model_id=model_id,
        credentials=creds,
        project_id=project_id,
    )

    system_prompt = (
        "You are an expert power-grid asset health analyst. "
        "Use the provided tools to gather data, then give a concise diagnosis "
        "and recommended next action. Be factual and cite the tool results."
    )
    user_prompt = (
        f"Diagnose transformer {transformer_id}. "
        "Retrieve its asset metadata, get its most recent DGA record, "
        "run an IEC Rogers Ratio analysis on the gas values, and check its "
        "remaining useful life. Summarise the fault type and recommended next action."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    print(f"[prompt] {user_prompt}")
    print("-" * 70)

    for round_num in range(1, max_rounds + 1):
        t0 = time.perf_counter()
        response = model.chat(
            messages=messages,
            tools=MCP_TOOLS,
            tool_choice="auto",
        )
        elapsed = time.perf_counter() - t0

        choice = response["choices"][0]
        message = choice["message"]
        finish = choice.get("finish_reason", "")

        # ---- Tool calls ----
        tool_calls = message.get("tool_calls") or []
        if tool_calls:
            print(
                f"[round {round_num}] model requested {len(tool_calls)} tool call(s)  "
                f"({elapsed:.2f}s)"
            )
            # Append the assistant turn with tool_calls
            messages.append(message)

            for tc in tool_calls:
                fn_name = tc["function"]["name"]
                fn_args_raw = tc["function"].get("arguments", "{}")
                try:
                    fn_args = json.loads(fn_args_raw)
                except json.JSONDecodeError:
                    fn_args = {}

                print(f"  → {fn_name}({json.dumps(fn_args)})")
                tool_result = execute_tool(fn_name, fn_args)
                result_obj = json.loads(tool_result)

                # Pretty-print a summary
                if "error" in result_obj:
                    print(f"    ✗ ERROR: {result_obj['error']}")
                else:
                    # Print first few keys as a preview
                    preview = {
                        k: v for i, (k, v) in enumerate(result_obj.items()) if i < 4
                    }
                    print(f"    ✓ {preview}")

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": tool_result,
                    }
                )
            continue

        # ---- Final answer ----
        final_text = message.get("content", "").strip()
        if final_text:
            print(f"\n[round {round_num}] final answer  ({elapsed:.2f}s)\n")
            print(final_text)
            print()
            return True

        # Unexpected finish reason
        print(f"[round {round_num}] unexpected finish_reason={finish!r}, stopping.")
        break

    print("WARNING: reached max_rounds without a final answer.")
    return False


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate MCP servers via WatsonX Llama"
    )
    parser.add_argument(
        "--transformer",
        default="T-018",
        help="Transformer ID to diagnose (default: T-018)",
    )
    parser.add_argument(
        "--model",
        default="meta-llama/llama-3-3-70b-instruct",
        help="WatsonX model ID to use",
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=6,
        help="Maximum tool-call rounds before giving up (default: 6)",
    )
    args = parser.parse_args()

    success = run_validation(
        transformer_id=args.transformer,
        model_id=args.model,
        max_rounds=args.max_rounds,
    )
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
