"""Unit tests for scripts/generate_scenarios.py prompt assembly (#68 v0.2).

Focused on the v0.1 → v0.2 prompt-template changes that landed for the PR
#178 inspection-only batch's findings:

  - asset_id pinning (`build_prompt(..., asset_id="T-NNN")` injects an
    ASSIGNED ASSET section the model must use exactly)
  - NO_HINT_RULES expansion (gas-name ban added)
  - CONSISTENCY_CONSTRAINTS injection (text↔ground_truth + tool callability)
  - PROMPT_VERSION bumped to v0.2

Pure prompt-string inspection — no LLM call, no MCP runtime. The prompt
template is the contract; these tests assert it stays a contract.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


@pytest.fixture
def support():
    """Real support data so route + template selection match production."""
    from scripts import generate_scenarios

    return generate_scenarios._load_json(generate_scenarios.SUPPORT_PATH)


@pytest.fixture
def family_spec(support):
    return support["scenario_family_matrix"]["families"]["FMSR_DGA_DIAGNOSIS"]


@pytest.fixture
def op_contexts(support):
    return support["operational_context_profiles"]["profiles"]


def _rng(seed=42):
    import random

    return random.Random(seed)


# ---------------------------------------------------------------------------
# PROMPT_VERSION
# ---------------------------------------------------------------------------


def test_prompt_version_is_v0_2():
    """The version pinned in provenance must reflect the v0.2 prompt set."""
    from scripts import generate_scenarios

    assert generate_scenarios.PROMPT_VERSION == "v0.2"


# ---------------------------------------------------------------------------
# Asset pinning (v0.2 fix for "all five used T-005" in the v0.1 batch)
# ---------------------------------------------------------------------------


def test_build_prompt_pins_asset_id(family_spec, op_contexts, support):
    """An explicit asset_id must appear in the rendered prompt verbatim."""
    from scripts.generate_scenarios import build_prompt

    prompt = build_prompt(
        "FMSR_DGA_DIAGNOSIS",
        family_spec,
        op_contexts,
        support,
        _rng(),
        asset_id="T-013",
    )
    assert "ASSIGNED ASSET: T-013" in prompt
    assert "MUST use exactly this asset_id" in prompt


def test_build_prompt_omits_asset_section_when_unset(family_spec, op_contexts, support):
    """Backward-compat: if no asset_id is passed, the ASSIGNED-ASSET injection
    block is omitted entirely. (The CONSISTENCY_CONSTRAINTS body still mentions
    'ASSIGNED ASSET below' as a forward-reference, so we look for the actual
    injected pattern `ASSIGNED ASSET: T-NNN` rather than the substring alone.)"""
    import re

    from scripts.generate_scenarios import build_prompt

    prompt = build_prompt(
        "FMSR_DGA_DIAGNOSIS",
        family_spec,
        op_contexts,
        support,
        _rng(),
        asset_id=None,
    )
    # The injected section always has the literal `ASSIGNED ASSET: T-NNN` line.
    # Without an asset, that line must NOT appear.
    assert not re.search(r"ASSIGNED ASSET:\s*T-\d{3}", prompt)
    # And the imperative line that only appears in the injection.
    assert "MUST use exactly this asset_id" not in prompt


def test_build_prompt_asset_id_is_pinned_per_call(family_spec, op_contexts, support):
    """Different asset_ids produce different ASSIGNED ASSET sections."""
    from scripts.generate_scenarios import build_prompt

    p1 = build_prompt(
        "FMSR_DGA_DIAGNOSIS",
        family_spec,
        op_contexts,
        support,
        _rng(),
        asset_id="T-001",
    )
    p2 = build_prompt(
        "FMSR_DGA_DIAGNOSIS",
        family_spec,
        op_contexts,
        support,
        _rng(),
        asset_id="T-002",
    )
    assert "ASSIGNED ASSET: T-001" in p1
    assert "ASSIGNED ASSET: T-002" in p2
    assert "ASSIGNED ASSET: T-001" not in p2


# ---------------------------------------------------------------------------
# NO_HINT_RULES expansion: gas-name ban
# ---------------------------------------------------------------------------


def test_no_hint_rules_ban_gas_names_by_formula_and_common_name(
    family_spec, op_contexts, support
):
    """The prompt must explicitly ban naming gases (per PR #178 SGT-GEN-005)."""
    from scripts.generate_scenarios import build_prompt

    prompt = build_prompt(
        "FMSR_DGA_DIAGNOSIS",
        family_spec,
        op_contexts,
        support,
        _rng(),
        asset_id="T-001",
    )
    # The ban appears in NO_HINT_RULES.
    assert "Names of dissolved gases" in prompt
    # Both representations are explicitly named so the model can't argue
    # the formula vs common-name path is allowed.
    for token in (
        "H2",
        "hydrogen",
        "CH4",
        "methane",
        "C2H2",
        "acetylene",
        "C2H4",
        "ethylene",
    ):
        assert token in prompt, f"expected gas token {token!r} in NO_HINT_RULES ban"


# ---------------------------------------------------------------------------
# CONSISTENCY_CONSTRAINTS injection
# ---------------------------------------------------------------------------


def test_consistency_constraints_injected(family_spec, op_contexts, support):
    """The 3-rule CONSISTENCY CONSTRAINTS section must appear in every prompt."""
    from scripts.generate_scenarios import build_prompt

    prompt = build_prompt(
        "FMSR_DGA_DIAGNOSIS",
        family_spec,
        op_contexts,
        support,
        _rng(),
        asset_id="T-001",
    )
    assert "CONSISTENCY CONSTRAINTS" in prompt
    # Rule 1: text ↔ ground_truth
    assert "TEXT EVIDENCE" in prompt
    assert "ground_truth.final_value" in prompt
    # Rule 2: tool callability + concrete tool examples
    assert "EXPECTED_TOOLS CALLABILITY" in prompt
    assert "iot.get_sensor_readings" in prompt
    assert "fmsr.analyze_dga" in prompt
    assert "wo.estimate_downtime" in prompt
    assert "wo.create_work_order" in prompt
    # Rule 3: asset id usage
    assert "ASSET ID is supplied to you" in prompt


def test_consistency_block_appears_before_schema_reminder(
    family_spec, op_contexts, support
):
    """Order matters: model should read constraints before the schema."""
    from scripts.generate_scenarios import build_prompt

    prompt = build_prompt(
        "FMSR_DGA_DIAGNOSIS",
        family_spec,
        op_contexts,
        support,
        _rng(),
        asset_id="T-001",
    )
    consistency_idx = prompt.index("CONSISTENCY CONSTRAINTS")
    schema_idx = prompt.index("OUTPUT FORMAT")
    assert consistency_idx < schema_idx


# ---------------------------------------------------------------------------
# Asset rotation order (the algorithm main() uses)
# ---------------------------------------------------------------------------


def test_asset_rotation_walks_pool_modulo_size():
    """`asset_pool[(next_id - 1) % len(asset_pool)]` produces N distinct
    assets for N <= 20 then wraps. This is the rotation algorithm in main().
    """
    asset_pool = sorted(f"T-{i:03d}" for i in range(1, 21))
    assert len(asset_pool) == 20

    # First 5 scenarios get 5 different assets.
    picks = [asset_pool[(next_id - 1) % len(asset_pool)] for next_id in range(1, 6)]
    assert picks == ["T-001", "T-002", "T-003", "T-004", "T-005"]
    assert len(set(picks)) == 5  # no v0.1 collapse onto T-005

    # Wrap at 21.
    pick_21 = asset_pool[(21 - 1) % len(asset_pool)]
    assert pick_21 == "T-001"


# ---------------------------------------------------------------------------
# v0.2 prompt is non-trivially larger than v0.1 (regression guard)
# ---------------------------------------------------------------------------


def test_v0_2_prompt_includes_all_required_sections(family_spec, op_contexts, support):
    """A spot-check that the v0.2 prompt has every section we promised in
    PROMPT_VERSION's changelog comment."""
    from scripts.generate_scenarios import build_prompt

    prompt = build_prompt(
        "MULTI_DOMAIN_INCIDENT",
        support["scenario_family_matrix"]["families"]["MULTI_DOMAIN_INCIDENT"],
        op_contexts,
        support,
        _rng(),
        asset_id="T-007",
    )
    required_section_markers = [
        "FAMILY: MULTI_DOMAIN_INCIDENT",
        "FAMILY SPEC:",
        "OPERATIONAL CONTEXT",
        # Multi-domain pulls all three template families.
        "EVENT/ALARM TEMPLATE",
        "DGA TREND TEMPLATE",
        "WORK-ORDER PLAYBOOK ENTRY",
        # v0.2 additions.
        "ASSIGNED ASSET: T-007",
        "NO-HINT RULES",
        "Names of dissolved gases",
        "CONSISTENCY CONSTRAINTS",
        "TEXT EVIDENCE",
        "EXPECTED_TOOLS CALLABILITY",
        # Schema reminder closes the prompt.
        "OUTPUT FORMAT",
    ]
    for marker in required_section_markers:
        assert marker in prompt, f"missing prompt section marker: {marker!r}"
