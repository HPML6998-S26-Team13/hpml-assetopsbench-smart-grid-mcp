"""Sanity checks on the vendored AOB system prompt.

Catches silent edits: if anyone modifies AOB_SYSTEM_PROMPT without
bumping AOB_PROMPT_SHA (and re-vendoring from a new AOB commit), this
test fails.
"""

from __future__ import annotations

import hashlib


def test_aob_prompt_sha_matches_constant() -> None:
    from scripts.aat_system_prompt import AOB_PROMPT_SHA, AOB_SYSTEM_PROMPT

    actual = hashlib.sha1(AOB_SYSTEM_PROMPT.encode("utf-8")).hexdigest()[:7]
    assert actual == AOB_PROMPT_SHA, (
        f"AOB_SYSTEM_PROMPT has been edited without updating AOB_PROMPT_SHA. "
        f"If intentional, resync from a new AOB commit and set AOB_PROMPT_SHA "
        f"to {actual!r}."
    )


def test_aob_prompt_nonempty() -> None:
    from scripts.aat_system_prompt import AOB_SYSTEM_PROMPT

    assert (
        len(AOB_SYSTEM_PROMPT) > 100
    ), "AOB system prompt unexpectedly short; re-vendor"
