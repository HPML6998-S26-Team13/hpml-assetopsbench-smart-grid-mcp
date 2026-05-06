"""PS B scenario generation prototype (#2).

Consumes ``docs/knowledge/scenario_generation_support.json`` (the family matrix
+ DGA / event / WO templates from #83/#90) and produces candidate Smart Grid
scenarios into ``data/scenarios/generated/<batch_id>/``. Each generated
scenario carries the full provenance + nearest-comparator metadata required
by ``docs/knowledge/generated_scenario_authoring_and_ground_truth.md``.

Default invocation (no LLM call, dry-run):

    python scripts/generate_scenarios.py --dry-run --family FMSR_DGA_DIAGNOSIS

Live generation (calls WatsonX via LiteLLM):

    export WATSONX_API_KEY=... WATSONX_PROJECT_ID=... WATSONX_URL=...
    python scripts/generate_scenarios.py \\
        --family FMSR_DGA_DIAGNOSIS \\
        --n 1 \\
        --model watsonx/meta-llama/llama-3-3-70b-instruct \\
        --batch-id smoke

Output layout:

    data/scenarios/generated/<batch_id>/
        SGT-GEN-001.json            # one scenario per file, schema-valid
        SGT-GEN-002.json
        ...
        batch_manifest.json         # provenance roll-up for the batch
        prompts/                    # exact prompts sent (for reproducibility)
            family_<FAMILY>_001.txt
            ...
        raw_responses/              # raw LLM outputs before parsing
            family_<FAMILY>_001.json
            ...

Scope (#2 prototype, per Alex's coordination note):
    - Generator path runnable end-to-end against WatsonX
    - First candidate batch can be inspected
    - Provenance + nearest-comparator metadata explicit
    - Validator-clean output (`data/scenarios/validate_scenarios.py` schema)

Out of scope here (deferred to #68 scale-up):
    - Full 18-scenario target across all 5 families
    - Akshat's PS B validation pass (#53)
    - Tighter prompt engineering past the first reviewable batch
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import logging
import os
import pathlib
import random
import re
import sys
from typing import Any, Optional

# Allow running as `python scripts/generate_scenarios.py` from repo root.
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "data" / "scenarios"))

# Reuse the canonical validator. Same module the team's CI uses; gives us a
# single source of truth for "is this scenario shape valid".
import validate_scenarios as _validator  # type: ignore  # noqa: E402

log = logging.getLogger("generate_scenarios")

SUPPORT_PATH = _REPO_ROOT / "docs" / "knowledge" / "scenario_generation_support.json"
TEMPLATE_PATH = _REPO_ROOT / "docs" / "knowledge" / "generated_scenario_template.json"
AUTHORING_DOC = (
    _REPO_ROOT
    / "docs"
    / "knowledge"
    / "generated_scenario_authoring_and_ground_truth.md"
)
HANDCRAFTED_DIR = _REPO_ROOT / "data" / "scenarios"
GENERATED_ROOT = _REPO_ROOT / "data" / "scenarios" / "generated"
ASSET_CSV = _REPO_ROOT / "data" / "processed" / "asset_metadata.csv"

PROMPT_VERSION = "v0.2"  # bump on any prompt-template change
# v0.1 (2026-05-03) → v0.2 (2026-05-05) changelog:
# - Asset rotation: build_prompt() now takes an explicit asset_id and pins it
#   in the prompt instead of letting the model pick. Caller passes a
#   deterministic rotation across T-001..T-020 so a single seed doesn't
#   collapse every scenario in the batch onto the same transformer (the
#   v0.1 first batch landed all 5 scenarios on T-005 because temperature=0.7
#   has a strong bias toward common IDs). Addresses PR #178 inspection issue
#   "all five use T-005".
# - NO_HINT_RULES: ban naming gases by chemical formula or common name in the
#   user-facing text. v0.1 SGT-GEN-005 named "methane and ethylene" which
#   narrowed the fault class (CH4+C2H4 → thermal pattern) and contradicted
#   the labeled D2 fault. Addresses PR #178 inspection issue "gas-fault
#   mismatch in SGT-GEN-005" + "borderline no-hint" finding.
# - CONSISTENCY_CONSTRAINTS (new section): three explicit checks the model
#   must satisfy before emitting JSON:
#     1. text-evidence ↔ ground_truth.final_value consistency
#     2. expected_tools callability from prompt context (every tool's
#        required arguments must be derivable from the text, OR a discovery
#        tool must precede it in ideal_tool_sequence)
#     3. asset_id pinning: the rotated asset_id must appear in both the
#        user-facing text and ground_truth, and not be replaced by the model.
#   Addresses PR #178 inspection issues SGT-GEN-001 / 003 / 005 / Medium 4.
# - SCHEMA_REMINDER: tightened ground_truth.final_value example to discourage
#   the v0.1 SGT-GEN-002 case (decisive_intermediate_values.rul_range_days
#   said 360 but final_value.rul_estimate_days said 540 — out of range).
#
# Out of scope for v0.2 (deferred to a real data-grounding pass): inlining
# actual MCP tool outputs into the prompt at generation time. The model
# still has no way to know what get_dga_record('T-NNN') actually returns,
# so ground_truth.decisive_intermediate_values + final_value remain
# model-asserted. The right structural fix is either prompt-time MCP tool
# calls or a post-generation grounding pass that overwrites those fields
# with what the live tools return; tracked under the PS B scale-up backlog
# in #68. v0.2 is the prompt-side improvements that don't need MCP runtime.


def _load_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _stable_hash(path: pathlib.Path) -> str:
    """Short content hash for provenance — version pin without touching git."""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def _display_path(path: pathlib.Path) -> str:
    """Path for log output. Repo-relative when inside the repo, absolute otherwise."""
    try:
        return str(path.relative_to(_REPO_ROOT))
    except ValueError:
        return str(path)


def _load_handcrafted() -> list[dict[str, Any]]:
    """Load every existing canonical scenario (non-recursive). Used for the
    nearest-comparator field in generated scenarios."""
    out: list[dict[str, Any]] = []
    for path in sorted(HANDCRAFTED_DIR.glob("*.json")):
        if path.name.lower() == "schema.json":
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        payload["_file"] = path.name
        out.append(payload)
    return out


def _nearest_handcrafted_comparator(
    generated: dict[str, Any], corpus: list[dict[str, Any]]
) -> dict[str, Any]:
    """Build the `nearest_handcrafted_comparator` block for the generated scenario.

    Field shape matches `docs/knowledge/generated_scenario_template.json` —
    `scenario_id`, `scenario_file`, `similarity_basis`, `novelty_note`, plus
    optional `nearest_match_weak`. Similarity is rough on purpose: same
    `type`, then largest overlap of expected tools. Path is repo-relative
    (`data/scenarios/<file>`) so reviewers can open the comparator directly.
    """
    same_type = [s for s in corpus if s.get("type") == generated.get("type")]
    if not same_type:
        return {
            "scenario_id": None,
            "scenario_file": None,
            "similarity_basis": "no canonical scenario shares this scenario's type",
            "novelty_note": "no comparator basis available; treat as fully novel",
            "nearest_match_weak": True,
        }

    gen_tools = set(generated.get("expected_tools") or [])

    def _overlap(s: dict[str, Any]) -> int:
        return len(gen_tools.intersection(set(s.get("expected_tools") or [])))

    best = max(same_type, key=_overlap)
    overlap_count = _overlap(best)
    file_name = best.get("_file") or ""
    return {
        "scenario_id": best.get("id"),
        "scenario_file": f"data/scenarios/{file_name}" if file_name else None,
        "similarity_basis": (
            f"shares type={best.get('type')!r} and {overlap_count} expected_tools entr"
            f"{'y' if overlap_count == 1 else 'ies'}"
            if overlap_count
            else f"shares type={best.get('type')!r}; no expected_tools overlap"
        ),
        "novelty_note": (
            "different generated context / templates; manual review should confirm "
            "the generated scenario is materially distinct from the comparator"
        ),
        "nearest_match_weak": overlap_count == 0,
    }


# ---------------------------------------------------------------------------
# Prompt assembly
# ---------------------------------------------------------------------------

# The no-hint rules are inlined here verbatim (they're ~1 KB and we want the
# generator self-contained for review). The authoring doc remains the source
# of truth — bump PROMPT_VERSION when this list changes.
NO_HINT_RULES = """
NO-HINT RULES — banned in the user-facing `text` field:
- Tool names (e.g. `fmsr.analyze_dga`, `wo.create_work_order`)
- Method names or analytic technique names (e.g. "Duval triangle", "Rogers ratio")
- IEC fault codes (PD, D1, D2, T1, T2, T3) in the prompt itself — they may appear in `decisive_intermediate_values` only
- Specific gas concentrations or ratio thresholds
- Names of dissolved gases by chemical formula OR common name (H2 / hydrogen,
  CH4 / methane, C2H2 / acetylene, C2H4 / ethylene, C2H6 / ethane, CO,
  CO2). Naming WHICH gases are rising effectively narrows the fault class
  to the model and is a closet-form hint. Use a generic phrasing like
  "recent dissolved-gas analysis shows elevated activity" or "DGA values
  are within normal range" — neither names the gases nor reveals the
  fault. (Added v0.2 after SGT-GEN-005 violated this in the v0.1 batch.)
- Pre-framed decisions ("you should create a work order")
- Step-by-step instructions
- Paraphrases of any canonical hand-crafted scenario under data/scenarios/

PREFERRED:
- Describe an operational event or condition naturally
- Ask for a decision (diagnosis / RUL / work order / sensor anomaly), not a tool call
- Ground in the supplied transformer ID and one or two context details (criticality, alarm, recent reading)
- One task per scenario
- Under 80 words
"""


CONSISTENCY_CONSTRAINTS = """
CONSISTENCY CONSTRAINTS — the model MUST satisfy these before emitting JSON.
Most v0.1 batch failures were here:

1. TEXT EVIDENCE ↔ GROUND TRUTH consistency
   Whatever evidence appears in `text` (alarm type, sensor reading, gas
   trend description, load condition) MUST be consistent with the labeled
   answer in `ground_truth.final_value`. If `ground_truth.final_value`
   says fault label D2 (low-energy discharge → C2H2-driven), then the
   `text` cannot describe a thermal pattern. If `ground_truth.final_value`
   says rul_estimate_days=540, then any range/window the text or
   `decisive_intermediate_values` mentions MUST contain 540. Do NOT
   describe stable conditions and then label a fault, or describe rising
   thermal indicators and then label an arc fault. Pick the answer
   first; then write text consistent with that answer.

2. EXPECTED_TOOLS CALLABILITY from prompt context
   For every tool in `expected_tools`, ALL its required arguments must be
   derivable from the text — OR a prerequisite tool that returns those
   arguments must precede it in `ideal_tool_sequence`. Rules of thumb:
     - `iot.get_sensor_readings(transformer_id, sensor_id)` requires a
       specific sensor_id. Either name the sensor in the text, OR
       precede this tool with `iot.list_sensors` in ideal_tool_sequence.
     - `fmsr.analyze_dga(...)` requires all five gas values
       (H2/CH4/C2H2/C2H4/C2H6). It MUST be preceded by
       `fmsr.get_dga_record` in ideal_tool_sequence.
     - `wo.estimate_downtime(transformer_id, severity, ...)` requires a
       severity. Either describe an unambiguous severity-suggesting
       event in the text (e.g. "complete loss of function"), OR precede
       with a fault-classification tool that produces severity.
     - `wo.create_work_order(...)` requires fault context. It MUST be
       preceded by something that classifies or identifies the fault
       (e.g. `fmsr.analyze_dga` or a sensor-threshold check).

3. ASSET ID is supplied to you (see ASSIGNED ASSET below). Use exactly
   that asset_id. Do not pick a different one, do not vary it across
   the scenario.
"""


SCHEMA_REMINDER = """
OUTPUT FORMAT (return one JSON object, no markdown fence):
{
  "id": "SGT-GEN-XXX",                                  // caller fills XXX
  "type": "FMSR" | "TSFM" | "WO" | "IoT" | "Multi",
  "text": "<the user-facing prompt, follows NO-HINT RULES>",
  "category": "<one of: Fault Diagnosis | Root Cause Analysis | Remaining Useful Life | Anomaly Detection | Trend Analysis | Maintenance Decision | Work Order Creation | Sensor Analysis | End-to-End Incident Response | Cross-Domain Planning>",
  "characteristic_form": "<one-sentence description of the answer's structure>",
  "asset_id": "T-NNN",                                  // T-001 .. T-020
  "expected_tools": ["domain.tool", ...],               // every tool the ideal agent calls
  "domain_tags": ["FMSR", ...],                         // matches the type for single-domain; >=2 for Multi
  "difficulty": "easy" | "medium" | "hard",
  "ground_truth": {
    "ideal_tool_sequence": ["domain.tool", ...],        // ordered, same entries as expected_tools
    "decisive_intermediate_values": { "<key>": "<value>", ... },
    "final_value": { "<key>": "<value>", ... },         // concrete output (e.g. fault_label, rul_days)
    "acceptance_criteria": ["agent <does X>", ...],     // 2-5 checks, each starting with "agent "
    "must_include": ["<element>", ...]                  // coarse high-level answer elements
  }
}

DO NOT include `provenance` or `nearest_handcrafted_comparator` blocks in
your output — the caller fills those after generation. DO NOT emit
`source_type`, `generator_prompt_version`, `generation_model`, or any
other generator-metadata field at the top level. The scenario JSON should
contain ONLY the canonical scenario contract (id, type, text, category,
characteristic_form, asset_id, expected_tools, domain_tags, difficulty,
ground_truth).

Return ONLY the JSON object. No commentary, no markdown fences, no explanation.
""".strip()


# Each family in scenario_generation_support.json maps to one or more
# template subsections. Routing them into the prompt by family avoids
# bloating non-FMSR prompts with DGA tables they don't need, and avoids
# starving non-FMSR families of the templates they DO need (the v0.1 prompt
# only injected DGA which silently broke WO / TSFM / IoT / Multi grounding).
#
# Sources are top-level keys in scenario_generation_support.json:
#   dga_trend_templates           → templates: {name -> step list}
#   event_alarm_templates          → templates: {name -> alarm pattern}
#   work_order_playbook            → entries:   {name -> WO playbook entry}
#   rul_health_context_templates   → templates: {name -> RUL context}
FAMILY_TEMPLATE_ROUTES: dict[str, list[tuple[str, str, str]]] = {
    # family                       (label                            , support_key                       , subkey)
    "FMSR_DGA_DIAGNOSIS": [
        ("DGA TREND TEMPLATE", "dga_trend_templates", "templates"),
    ],
    "TSFM_RUL_FORECAST": [
        ("RUL/HEALTH CONTEXT TEMPLATE", "rul_health_context_templates", "templates"),
    ],
    "WO_CREATION": [
        ("WORK-ORDER PLAYBOOK ENTRY", "work_order_playbook", "entries"),
    ],
    "IOT_SENSOR_ANALYSIS": [
        ("EVENT/ALARM TEMPLATE", "event_alarm_templates", "templates"),
    ],
    "MULTI_DOMAIN_INCIDENT": [
        # Multi-domain scenarios chain a triggering alarm → a DGA finding →
        # a WO action, so all three template families are relevant.
        ("EVENT/ALARM TEMPLATE", "event_alarm_templates", "templates"),
        ("DGA TREND TEMPLATE", "dga_trend_templates", "templates"),
        ("WORK-ORDER PLAYBOOK ENTRY", "work_order_playbook", "entries"),
    ],
}


def _select_family_templates(
    family_name: str,
    support: dict[str, Any],
    rng: random.Random,
) -> str:
    """Build the per-family template block for the prompt.

    Returns one or more "LABEL (name):\\n<json>" sections separated by blank
    lines, or an empty string if the family has no template route. Each section
    is one randomly-picked entry from the relevant subsection of the support
    data (e.g. one DGA trend template, one work-order playbook entry).
    """
    routes = FAMILY_TEMPLATE_ROUTES.get(family_name, [])
    sections: list[str] = []
    for label, support_key, subkey in routes:
        block = support.get(support_key, {})
        entries = block.get(subkey, {}) if isinstance(block, dict) else {}
        if not entries:
            continue
        chosen = rng.choice(list(entries.keys()))
        sections.append(
            f"{label} (`{chosen}`):\n" + json.dumps(entries[chosen], indent=2)
        )
    return "\n\n".join(sections)


def build_prompt(
    family_name: str,
    family_spec: dict[str, Any],
    operational_contexts: dict[str, Any],
    support: dict[str, Any],
    rng: random.Random,
    asset_id: str | None = None,
) -> str:
    """Assemble the per-scenario LLM prompt from the support data.

    Picks one operational context and the family-specific template
    block(s) per `FAMILY_TEMPLATE_ROUTES`. The model is given the family
    spec, operational context, routed templates, no-hint rules,
    consistency constraints, and the schema reminder.

    If `asset_id` is None, the model picks (v0.1 behavior — kept for
    backward-compat with any caller that wants the old shape). The
    canonical generator path in `main()` always passes an explicit
    asset_id from a deterministic per-batch rotation; that's the v0.2
    behavior fix for the "all five scenarios on T-005" failure.
    """
    ctx_name = rng.choice(list(operational_contexts.keys()))
    ctx = operational_contexts[ctx_name]
    template_block = _select_family_templates(family_name, support, rng)
    template_section = f"\n\n{template_block}" if template_block else ""
    asset_section = (
        f"\n\nASSIGNED ASSET: {asset_id}\n"
        f"You MUST use exactly this asset_id (do not pick a different "
        f"transformer ID, do not vary it across the scenario)."
        if asset_id
        else ""
    )

    return f"""You are generating a single Smart Grid maintenance scenario for the SmartGridBench benchmark suite. The scenario will be evaluated against an LLM agent with access to four MCP servers (IoT, FMSR, TSFM, WO).

FAMILY: {family_name}
FAMILY SPEC:
{json.dumps(family_spec, indent=2)}

OPERATIONAL CONTEXT (`{ctx_name}`):
{json.dumps(ctx, indent=2)}{template_section}{asset_section}

{NO_HINT_RULES}

{CONSISTENCY_CONSTRAINTS}

{SCHEMA_REMINDER}
""".strip()


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------


def call_llm(
    prompt: str, model: str, *, temperature: float = 0.7, max_tokens: int = 1500
) -> str:
    """Single round-trip to the LLM via LiteLLM. Returns raw assistant text."""
    try:
        import litellm  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "litellm not installed; install via `uv pip install -r requirements-insomnia.txt` "
            "or run with --dry-run."
        ) from exc

    if model.startswith("watsonx/"):
        # Bridge documented WATSONX_* env vars to the WX_* names litellm's
        # newer WatsonX provider expects. Shared helper covers every Python
        # call site (generator + aat_runner + judge_trajectory).
        from scripts.watsonx_env import propagate_watsonx_env

        propagate_watsonx_env()

    log.info(
        "calling %s (temperature=%.2f, max_tokens=%d, prompt_chars=%d)",
        model,
        temperature,
        max_tokens,
        len(prompt),
    )
    response = litellm.completion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response["choices"][0]["message"]["content"]


def parse_response(raw: str) -> dict[str, Any]:
    """Strip optional markdown fences and parse JSON. Raises on malformed."""
    cleaned = raw.strip()
    # Some Llama responses wrap in ```json ... ``` despite the schema reminder.
    fence = re.match(r"^```(?:json)?\s*\n(.*?)\n```\s*$", cleaned, re.DOTALL)
    if fence:
        cleaned = fence.group(1).strip()
    return json.loads(cleaned)


# ---------------------------------------------------------------------------
# Provenance + validation
# ---------------------------------------------------------------------------


# Field set required inside the nested `provenance` block, per
# docs/knowledge/generated_scenario_template.json. `cleanup_notes` is
# conditional (only emitted if manual_cleanup=true) and is not in this set.
REQUIRED_PROVENANCE_FIELDS = frozenset(
    {
        "source_type",
        "generator_prompt_version",
        "knowledge_plugin_version",
        "generation_model",
        "generation_date",
        "batch_id",
        "manual_cleanup",
    }
)

# Field set required inside the nested `nearest_handcrafted_comparator`
# block, per the same template. `nearest_match_weak` is optional (only set
# when no natural comparator exists).
REQUIRED_COMPARATOR_FIELDS = frozenset(
    {"scenario_id", "scenario_file", "similarity_basis", "novelty_note"}
)


def attach_provenance(
    scenario: dict[str, Any],
    *,
    scenario_id: str,
    family: str,
    model: str,
    batch_id: str,
    knowledge_plugin_hash: str,
) -> dict[str, Any]:
    """Stamp the SGT-GEN id and emit the nested `provenance` block.

    Field shape matches the contract in
    `docs/knowledge/generated_scenario_template.json` — provenance fields go
    inside a single nested object, NOT at the scenario top level. The model
    sometimes emits a partial top-level provenance from the prompt; this
    function strips those so they don't shadow the canonical nested block.

    `family` is also written at the top level (not in the template) because
    the team's generation pipeline uses it as a routing key downstream; it
    is not a contract field for the canonical scenario schema.
    """
    scenario["id"] = scenario_id
    # Strip any stray top-level provenance fields the model may have emitted
    # (some Llama responses copy fields into both top-level and the nested
    # provenance block; the template only allows the nested form).
    for stray in REQUIRED_PROVENANCE_FIELDS:
        scenario.pop(stray, None)

    provenance = scenario.setdefault("provenance", {})
    provenance["source_type"] = "generated"
    provenance["generator_prompt_version"] = PROMPT_VERSION
    provenance["knowledge_plugin_version"] = knowledge_plugin_hash
    provenance["generation_model"] = model
    provenance["generation_date"] = dt.datetime.now(dt.timezone.utc).isoformat()
    provenance["batch_id"] = batch_id
    # Manual cleanup defaults to false; humans flip it (and add cleanup_notes)
    # when editing the scenario before promoting it to the canonical set.
    provenance.setdefault("manual_cleanup", False)
    if not provenance.get("manual_cleanup"):
        # `cleanup_notes` is conditional on manual_cleanup=true; don't emit
        # an empty/null value when no cleanup occurred.
        provenance.pop("cleanup_notes", None)

    # `family` is a generation-pipeline routing key, separate from the
    # template's nested provenance contract. Keep it visible at top level.
    scenario["family"] = family
    return scenario


def _validate_generated_contract(scenario: dict[str, Any]) -> list[str]:
    """Generator-only checks: enforce the PS B nested-provenance contract.

    The team validator (`data/scenarios/validate_scenarios.py`) covers the
    canonical scenario schema (id / type / tools / etc.) but predates PS B,
    so it does NOT know about the nested `provenance` and
    `nearest_handcrafted_comparator` blocks introduced for generated
    scenarios. Without this check, a malformed generated output (provenance
    fields at the top level, comparator field renamed) would land in the
    `valid` output path while silently violating the contract Akshat's #53
    rubric will read against. Returns a list of human-readable error
    strings; empty list means contract-clean.
    """
    errors: list[str] = []

    provenance = scenario.get("provenance")
    if not isinstance(provenance, dict):
        errors.append(
            "missing required nested `provenance` block (must be an object, not "
            "top-level fields)"
        )
    else:
        missing = REQUIRED_PROVENANCE_FIELDS.difference(provenance.keys())
        if missing:
            errors.append(
                f"`provenance` block missing required fields: {sorted(missing)}"
            )
        if provenance.get("source_type") != "generated":
            errors.append(
                f"`provenance.source_type` must be 'generated', got "
                f"{provenance.get('source_type')!r}"
            )
        if provenance.get("manual_cleanup") is True and not provenance.get(
            "cleanup_notes"
        ):
            errors.append(
                "`provenance.manual_cleanup=true` requires a non-empty "
                "`cleanup_notes` field"
            )

    comparator = scenario.get("nearest_handcrafted_comparator")
    if not isinstance(comparator, dict):
        errors.append(
            "missing required `nearest_handcrafted_comparator` block (must be an "
            "object). The earlier `nearest_handcrafted` field name is wrong; rename "
            "to `nearest_handcrafted_comparator` per the template."
        )
    else:
        missing = REQUIRED_COMPARATOR_FIELDS.difference(comparator.keys())
        if missing:
            errors.append(
                f"`nearest_handcrafted_comparator` missing required fields: "
                f"{sorted(missing)}"
            )

    # Reject the legacy/wrong keys explicitly so a future code regression
    # doesn't silently re-introduce them.
    for stray in REQUIRED_PROVENANCE_FIELDS:
        if stray in scenario:
            errors.append(
                f"top-level `{stray}` is not allowed; provenance fields belong inside "
                f"the nested `provenance` block"
            )
    if "nearest_handcrafted" in scenario:
        errors.append(
            "`nearest_handcrafted` is the wrong field name; use "
            "`nearest_handcrafted_comparator` per the template"
        )

    return errors


def validate_scenario(scenario: dict[str, Any], valid_asset_ids: set[str]) -> list[str]:
    """Run the canonical validator + generated-scenario contract check.

    Combines the team's `validate_scenarios.py:validate_file` (canonical
    schema, asset-id, tool / domain coherence) with the PS-B-specific
    `_validate_generated_contract` (nested provenance + comparator). A
    scenario is contract-clean only if BOTH return empty error lists.
    """
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = pathlib.Path(tmp) / f"{scenario.get('id', 'unknown')}.json"
        tmp_path.write_text(json.dumps(scenario, indent=2), encoding="utf-8")
        canonical_errors = _validator.validate_file(tmp_path, valid_asset_ids)

    return canonical_errors + _validate_generated_contract(scenario)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument(
        "--family",
        action="append",
        choices=[
            "FMSR_DGA_DIAGNOSIS",
            "TSFM_RUL_FORECAST",
            "WO_CREATION",
            "IOT_SENSOR_ANALYSIS",
            "MULTI_DOMAIN_INCIDENT",
        ],
        help="Which family to generate from. Pass multiple times for multiple families.",
    )
    p.add_argument(
        "--n",
        type=int,
        default=1,
        help="Number of scenarios per family. Default 1 (smoke).",
    )
    p.add_argument(
        "--model",
        default="watsonx/meta-llama/llama-3-3-70b-instruct",
        help="LiteLLM model string. Default WatsonX Llama-3.3-70B-instruct (no GPU contention with W5 captures).",
    )
    p.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Sampling temperature for generation. 0.7 balances variety with coherence.",
    )
    p.add_argument(
        "--batch-id",
        default=None,
        help="Batch identifier. Defaults to ISO date + random suffix.",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=None,
        help="RNG seed for reproducible context / template selection.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Build prompts and write them to stdout, but do NOT call the LLM. Use to inspect prompts before burning credits.",
    )
    p.add_argument(
        "--out-dir",
        type=pathlib.Path,
        default=None,
        help="Override the output directory. Default: data/scenarios/generated/<batch_id>/",
    )
    p.add_argument(
        "--append",
        action="store_true",
        help="Allow writing into a batch directory that already contains scenarios. "
        "Without this flag, the script refuses to run if SGT-GEN-NNN.json files "
        "already exist in the target dir, to prevent silent overwrite when the "
        "same --batch-id is used across separate invocations. With --append, "
        "next_id continues from max(existing SGT-GEN-NNN)+1 and the manifest is "
        "merged.",
    )
    p.add_argument("--verbose", action="store_true")
    return p.parse_args()


def _scan_existing_batch(out_dir: pathlib.Path) -> tuple[int, list[str]]:
    """Inspect an existing batch dir for SGT-GEN-NNN.json files.

    Returns (next_id, existing_ids) where next_id is one past the highest
    NNN found (so a fresh dir gives next_id=1 and an empty list). The
    caller uses this to continue numbering across `--append` invocations.
    """
    existing: list[str] = []
    max_n = 0
    pattern = re.compile(r"^SGT-GEN-(\d{3,})\.json$")
    if out_dir.is_dir():
        for path in out_dir.iterdir():
            m = pattern.match(path.name)
            if m:
                existing.append(path.stem)
                max_n = max(max_n, int(m.group(1)))
    return max_n + 1, sorted(existing)


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # Load support data + template + handcrafted corpus.
    support = _load_json(SUPPORT_PATH)
    handcrafted = _load_handcrafted()
    valid_asset_ids = _validator.load_valid_asset_ids(ASSET_CSV)

    family_matrix = support["scenario_family_matrix"]["families"]
    op_contexts = support["operational_context_profiles"]["profiles"]

    families = args.family or list(family_matrix.keys())
    rng = random.Random(args.seed) if args.seed is not None else random.Random()

    knowledge_plugin_hash = _stable_hash(SUPPORT_PATH)

    batch_id = args.batch_id or (
        f"{dt.date.today().isoformat()}_{rng.randint(1000, 9999)}"
    )
    out_dir = args.out_dir or (GENERATED_ROOT / batch_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "prompts").mkdir(exist_ok=True)
    (out_dir / "raw_responses").mkdir(exist_ok=True)

    # Refuse to silently overwrite an existing batch. Without this guard, the
    # documented "loop one --batch-id across families" pattern would reset
    # next_id=1 every iteration and rewrite SGT-GEN-001.json once per family.
    next_id, existing_ids = _scan_existing_batch(out_dir)
    if existing_ids and not args.append:
        log.error(
            "batch dir %s already contains %d scenario file(s) (%s..%s). "
            "Pass --append to continue numbering from SGT-GEN-%03d, or pick a "
            "different --batch-id.",
            _display_path(out_dir),
            len(existing_ids),
            existing_ids[0],
            existing_ids[-1],
            next_id,
        )
        return 1

    log.info("batch_id=%s out_dir=%s dry_run=%s", batch_id, out_dir, args.dry_run)
    log.info("families=%s n=%d model=%s", families, args.n, args.model)
    log.info("knowledge_plugin_version=%s", knowledge_plugin_hash)
    if args.append and existing_ids:
        log.info(
            "append mode: continuing from SGT-GEN-%03d (existing: %d scenario(s))",
            next_id,
            len(existing_ids),
        )

    scenarios_emitted: list[dict[str, Any]] = []
    invocation_starting_id = next_id

    # Asset rotation: deterministically walk through T-001..T-020 across the
    # batch (ordered by next_id) so a single seed doesn't collapse every
    # scenario onto the same transformer. The v0.1 first batch landed all 5
    # scenarios on T-005 because the model has a strong asset bias at
    # temperature=0.7. PROMPT_VERSION v0.2 fix.
    asset_pool: list[str] = sorted(valid_asset_ids)
    if not asset_pool:
        log.error("no valid asset IDs available; cannot pin asset_id in prompts")
        return 1

    for family in families:
        family_spec = family_matrix[family]
        for i in range(args.n):
            scenario_id = f"SGT-GEN-{next_id:03d}"
            prompt_label = f"{family}_{scenario_id}"
            # Walk asset_pool by scenario index (next_id-1) modulo pool size.
            # Across an N-scenario batch this gives N different assets when
            # N <= 20; wraps cleanly for larger batches.
            assigned_asset = asset_pool[(next_id - 1) % len(asset_pool)]
            prompt = build_prompt(
                family,
                family_spec,
                op_contexts,
                support,
                rng,
                asset_id=assigned_asset,
            )
            (out_dir / "prompts" / f"{prompt_label}.txt").write_text(
                prompt, encoding="utf-8"
            )
            log.info(
                "[%s] built prompt (chars=%d) -> %s",
                scenario_id,
                len(prompt),
                prompt_label,
            )

            if args.dry_run:
                log.info("[%s] dry-run: skipping LLM call", scenario_id)
                next_id += 1
                continue

            try:
                raw = call_llm(prompt, model=args.model, temperature=args.temperature)
            except Exception as exc:
                log.error("[%s] LLM call failed: %s", scenario_id, exc)
                next_id += 1
                continue
            (out_dir / "raw_responses" / f"{prompt_label}.json").write_text(
                raw, encoding="utf-8"
            )

            try:
                scenario = parse_response(raw)
            except json.JSONDecodeError as exc:
                log.error("[%s] response was not valid JSON: %s", scenario_id, exc)
                next_id += 1
                continue

            scenario = attach_provenance(
                scenario,
                scenario_id=scenario_id,
                family=family,
                model=args.model,
                batch_id=batch_id,
                knowledge_plugin_hash=knowledge_plugin_hash,
            )
            scenario["nearest_handcrafted_comparator"] = (
                _nearest_handcrafted_comparator(scenario, handcrafted)
            )

            errors = validate_scenario(scenario, valid_asset_ids)
            if errors:
                log.warning(
                    "[%s] validation failed (%d errors); writing to invalid/ for inspection",
                    scenario_id,
                    len(errors),
                )
                for err in errors:
                    log.warning("[%s]   %s", scenario_id, err)
                invalid_dir = out_dir / "invalid"
                invalid_dir.mkdir(exist_ok=True)
                (invalid_dir / f"{scenario_id}.json").write_text(
                    json.dumps({"scenario": scenario, "errors": errors}, indent=2),
                    encoding="utf-8",
                )
            else:
                target = out_dir / f"{scenario_id}.json"
                target.write_text(
                    json.dumps(scenario, indent=2) + "\n", encoding="utf-8"
                )
                scenarios_emitted.append(scenario)
                log.info("[%s] OK -> %s", scenario_id, _display_path(target))

            next_id += 1

    # Batch manifest summarises the run for reviewer + reproducibility.
    # On --append, we LOAD any existing manifest and append a new
    # `invocations` entry rather than rewriting top-level fields, so the
    # batch keeps a faithful record of every generator pass that contributed
    # to it (model / seed / families / count for each invocation).
    manifest_path = out_dir / "batch_manifest.json"
    invocation_record = {
        "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "model": args.model,
        "temperature": args.temperature,
        "seed": args.seed,
        "families_requested": families,
        "n_per_family": args.n,
        "scenarios_emitted": [s["id"] for s in scenarios_emitted],
        "starting_scenario_id": f"SGT-GEN-{invocation_starting_id:03d}",
        "dry_run": args.dry_run,
        "append": args.append,
    }

    if args.append and manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest.setdefault("invocations", []).append(invocation_record)
        # Keep the cumulative scenarios_emitted list in sync so consumers
        # don't have to walk every invocation block.
        cumulative = list(manifest.get("scenarios_emitted", []))
        cumulative.extend(invocation_record["scenarios_emitted"])
        # Deduplicate while preserving order in case an earlier append
        # rewrote a scenario id (it shouldn't, but defensive).
        seen: set[str] = set()
        manifest["scenarios_emitted"] = [
            i for i in cumulative if not (i in seen or seen.add(i))
        ]
        manifest["last_updated_at"] = invocation_record["started_at"]
    else:
        manifest = {
            "batch_id": batch_id,
            "created_at": invocation_record["started_at"],
            "last_updated_at": invocation_record["started_at"],
            "prompt_version": PROMPT_VERSION,
            "knowledge_plugin_version": knowledge_plugin_hash,
            "generator_script": "scripts/generate_scenarios.py",
            "support_data": SUPPORT_PATH.relative_to(_REPO_ROOT).as_posix(),
            "handcrafted_corpus_size": len(handcrafted),
            "scenarios_emitted": list(invocation_record["scenarios_emitted"]),
            "invocations": [invocation_record],
        }

    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    log.info("batch manifest written to %s", _display_path(manifest_path))
    log.info(
        "emitted %d scenario(s) this invocation; batch total: %d",
        len(scenarios_emitted),
        len(manifest["scenarios_emitted"]),
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
