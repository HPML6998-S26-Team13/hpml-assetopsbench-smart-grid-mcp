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
AUTHORING_DOC = _REPO_ROOT / "docs" / "knowledge" / "generated_scenario_authoring_and_ground_truth.md"
HANDCRAFTED_DIR = _REPO_ROOT / "data" / "scenarios"
GENERATED_ROOT = _REPO_ROOT / "data" / "scenarios" / "generated"
ASSET_CSV = _REPO_ROOT / "data" / "processed" / "asset_metadata.csv"

PROMPT_VERSION = "v0.1"  # bump on any prompt-template change


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


def _nearest_comparator(generated: dict[str, Any], corpus: list[dict[str, Any]]) -> dict[str, Any]:
    """Find the canonical scenario most similar to the generated one.

    Similarity is rough on purpose: same `type`, then largest overlap of
    expected tools. Returns the structure required by the authoring doc
    section 7. If nothing in the corpus shares the type, returns
    `nearest_match_weak: true` and leaves comparison fields null.
    """
    same_type = [s for s in corpus if s.get("type") == generated.get("type")]
    if not same_type:
        return {
            "scenario_id": None,
            "scenario_file": None,
            "similarity_basis": None,
            "novelty_note": "no canonical scenario with the same type exists",
            "nearest_match_weak": True,
        }

    gen_tools = set(generated.get("expected_tools") or [])

    def _overlap(s: dict[str, Any]) -> int:
        return len(gen_tools.intersection(set(s.get("expected_tools") or [])))

    best = max(same_type, key=_overlap)
    overlap_count = _overlap(best)
    return {
        "scenario_id": best.get("id"),
        "scenario_file": best.get("_file"),
        "similarity_basis": (
            f"shares type={best.get('type')!r} and {overlap_count} tool(s)"
            if overlap_count
            else f"shares type={best.get('type')!r}; no tool overlap"
        ),
        "novelty_note": None,
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
- Pre-framed decisions ("you should create a work order")
- Step-by-step instructions
- Paraphrases of any of the 10 hand-crafted scenarios under data/scenarios/

PREFERRED:
- Describe an operational event or condition naturally
- Ask for a decision (diagnosis / RUL / work order / sensor anomaly), not a tool call
- Ground in one transformer ID and one or two context details (criticality, alarm, recent reading)
- One task per scenario
- Under 80 words
"""


SCHEMA_REMINDER = """
OUTPUT FORMAT (return one JSON object, no markdown fence):
{
  "id": "SGT-GEN-XXX",                                  // caller fills XXX
  "type": "FMSR" | "TSFM" | "WO" | "IoT" | "Multi",
  "text": "<the user-facing prompt, follows NO-HINT RULES>",
  "category": "<one of: Fault Diagnosis | Root Cause Analysis | Remaining Useful Life | Anomaly Detection | Trend Analysis | Maintenance Decision | Work Order Creation | Sensor Analysis | End-to-End Incident Response | Cross-Domain Planning>",
  "characteristic_form": "<one-sentence description of the answer's structure>",
  "asset_id": "T-NNN",
  "expected_tools": ["domain.tool", ...],               // every tool the ideal agent calls
  "domain_tags": ["FMSR", ...],                         // matches the type for single-domain; >=2 for Multi
  "difficulty": "easy" | "medium" | "hard",
  "ground_truth": {
    "ideal_tool_sequence": ["domain.tool", ...],
    "decisive_intermediate_values": { "<key>": "<value>", ... },
    "final_value": "<concrete answer>",
    "acceptance_criteria": ["<2-5 natural-language checks>"]
  }
}
Return ONLY the JSON object. No commentary, no markdown fences, no explanation.
""".strip()


def build_prompt(
    family_name: str,
    family_spec: dict[str, Any],
    operational_contexts: dict[str, Any],
    dga_templates: dict[str, Any],
    rng: random.Random,
) -> str:
    """Assemble the per-scenario LLM prompt from the support data.

    Picks one operational context and (if FMSR) one DGA template to ground the
    scenario. The model is given the support data verbatim plus the no-hint
    rules and schema reminder.
    """
    ctx_name = rng.choice(list(operational_contexts.keys()))
    ctx = operational_contexts[ctx_name]
    dga_block = ""
    if family_spec.get("primary_domain") == "FMSR" and dga_templates:
        dga_name = rng.choice(list(dga_templates.keys()))
        dga_block = (
            f"\n\nDGA TREND TEMPLATE (`{dga_name}`):\n"
            + json.dumps(dga_templates[dga_name], indent=2)
        )

    return f"""You are generating a single Smart Grid maintenance scenario for the SmartGridBench benchmark suite. The scenario will be evaluated against an LLM agent with access to four MCP servers (IoT, FMSR, TSFM, WO).

FAMILY: {family_name}
FAMILY SPEC:
{json.dumps(family_spec, indent=2)}

OPERATIONAL CONTEXT (`{ctx_name}`):
{json.dumps(ctx, indent=2)}{dga_block}

{NO_HINT_RULES}

{SCHEMA_REMINDER}
""".strip()


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------


def call_llm(prompt: str, model: str, *, temperature: float = 0.7, max_tokens: int = 1500) -> str:
    """Single round-trip to the LLM via LiteLLM. Returns raw assistant text."""
    try:
        import litellm  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "litellm not installed; install via `uv pip install -r requirements-insomnia.txt` "
            "or run with --dry-run."
        ) from exc

    log.info("calling %s (temperature=%.2f, max_tokens=%d, prompt_chars=%d)",
             model, temperature, max_tokens, len(prompt))
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


def attach_provenance(
    scenario: dict[str, Any],
    *,
    scenario_id: str,
    family: str,
    model: str,
    batch_id: str,
    knowledge_plugin_hash: str,
) -> dict[str, Any]:
    """Set the SGT-GEN id and stamp source_type / generator metadata."""
    scenario["id"] = scenario_id
    scenario["source_type"] = "generated"
    scenario["family"] = family
    scenario["generator_prompt_version"] = PROMPT_VERSION
    scenario["knowledge_plugin_version"] = knowledge_plugin_hash
    scenario["generation_model"] = model
    scenario["generation_date"] = dt.datetime.now(dt.timezone.utc).isoformat()
    scenario["batch_id"] = batch_id
    # Manual cleanup defaults to false; humans flip if they edit before commit.
    scenario.setdefault("manual_cleanup", False)
    return scenario


def validate_scenario(scenario: dict[str, Any], valid_asset_ids: set[str]) -> list[str]:
    """Run the canonical validator over a single scenario in-memory.

    The team's `data/scenarios/validate_scenarios.py:validate_file` reads from
    disk; we round-trip through a tempfile so we share its exact rule set.
    """
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = pathlib.Path(tmp) / f"{scenario.get('id', 'unknown')}.json"
        tmp_path.write_text(json.dumps(scenario, indent=2), encoding="utf-8")
        return _validator.validate_file(tmp_path, valid_asset_ids)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
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
    p.add_argument("--verbose", action="store_true")
    return p.parse_args()


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
    dga_templates = support.get("dga_trend_templates", {}).get("templates", {})

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

    log.info("batch_id=%s out_dir=%s dry_run=%s", batch_id, out_dir, args.dry_run)
    log.info("families=%s n=%d model=%s", families, args.n, args.model)
    log.info("knowledge_plugin_version=%s", knowledge_plugin_hash)

    scenarios_emitted: list[dict[str, Any]] = []
    next_id = 1

    for family in families:
        family_spec = family_matrix[family]
        for i in range(args.n):
            scenario_id = f"SGT-GEN-{next_id:03d}"
            prompt_label = f"family_{family}_{i + 1:03d}"
            prompt = build_prompt(family, family_spec, op_contexts, dga_templates, rng)
            (out_dir / "prompts" / f"{prompt_label}.txt").write_text(prompt, encoding="utf-8")
            log.info("[%s] built prompt (chars=%d) -> %s", scenario_id, len(prompt), prompt_label)

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
            (out_dir / "raw_responses" / f"{prompt_label}.json").write_text(raw, encoding="utf-8")

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
            scenario["nearest_handcrafted"] = _nearest_comparator(scenario, handcrafted)

            errors = validate_scenario(scenario, valid_asset_ids)
            if errors:
                log.warning("[%s] validation failed (%d errors); writing to invalid/ for inspection",
                            scenario_id, len(errors))
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
                target.write_text(json.dumps(scenario, indent=2) + "\n", encoding="utf-8")
                scenarios_emitted.append(scenario)
                log.info("[%s] OK -> %s", scenario_id, _display_path(target))

            next_id += 1

    # Batch manifest summarises the run for reviewer + reproducibility.
    manifest = {
        "batch_id": batch_id,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "model": args.model,
        "temperature": args.temperature,
        "seed": args.seed,
        "families_requested": families,
        "n_per_family": args.n,
        "prompt_version": PROMPT_VERSION,
        "knowledge_plugin_version": knowledge_plugin_hash,
        "scenarios_emitted": [s["id"] for s in scenarios_emitted],
        "dry_run": args.dry_run,
        "generator_script": "scripts/generate_scenarios.py",
        "support_data": SUPPORT_PATH.relative_to(_REPO_ROOT).as_posix(),
        "handcrafted_corpus_size": len(handcrafted),
    }
    (out_dir / "batch_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    log.info("batch manifest written to %s", _display_path(out_dir / "batch_manifest.json"))
    log.info("emitted %d scenario(s)", len(scenarios_emitted))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
