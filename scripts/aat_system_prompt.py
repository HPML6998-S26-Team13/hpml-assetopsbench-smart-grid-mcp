"""Vendored AOB Agent-as-Tool system prompt.

The string in AOB_SYSTEM_PROMPT is copied VERBATIM from IBM/AssetOpsBench
at commit `2a9b15e`, source file `src/agent/openai_agent/runner.py`
(the `_SYSTEM_PROMPT` constant defined at line 86).

DO NOT MODIFY the prompt text in isolation. To resync:
  1. Update AOB_SOURCE_SHA to the new AOB commit SHA (7 chars).
  2. Paste the new prompt text into AOB_SYSTEM_PROMPT.
  3. Update AOB_PROMPT_SHA to sha1(AOB_SYSTEM_PROMPT.encode())[:7]. Compute
     with: `python -c "from scripts.aat_system_prompt import _compute_prompt_sha; print(_compute_prompt_sha())"`
     (first 7 hex chars of sha1 over the prompt string only, NOT the whole file).
  4. Commit with a message that names the AOB commit you pulled from.

The test_aob_prompt_sha_matches_constant unit test enforces this by
failing CI if the prompt and SHA drift apart.
"""

from __future__ import annotations

AOB_SOURCE_SHA = "2a9b15e"
AOB_SOURCE_PATH = "src/agent/openai_agent/runner.py"

AOB_SYSTEM_PROMPT = """You are an industrial asset operations assistant with access to MCP tools for
querying IoT sensor data, failure mode and symptom records, time-series
forecasting models, and work order management.

Answer the user's question concisely and accurately using the available tools.
When you retrieve data, include the key numbers or names in your answer.
"""


def _compute_prompt_sha() -> str:
    """Utility for resync; not used by the runner."""
    import hashlib

    return hashlib.sha1(AOB_SYSTEM_PROMPT.encode("utf-8")).hexdigest()[:7]


# Computed sha1(AOB_SYSTEM_PROMPT.encode())[:7]. Keep in sync with the prompt.
AOB_PROMPT_SHA = "933d2c8"
