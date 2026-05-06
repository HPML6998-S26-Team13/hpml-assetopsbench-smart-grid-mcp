"""Unit tests for scripts/watsonx_env.py.

The helper bridges documented WATSONX_* env vars to the WX_* names that
litellm's newer WatsonX provider expects. (#177 / PR #130 review fall-out)
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Names this helper touches. Tests scrub them in setup/teardown so a stray
# value from the pytest invoker's shell can't leak between cases.
_NAMES = (
    "WATSONX_API_KEY",
    "WATSONX_PROJECT_ID",
    "WATSONX_URL",
    "WX_API_KEY",
    "WX_PROJECT_ID",
    "WX_URL",
)


@pytest.fixture(autouse=True)
def _scrub_env(monkeypatch):
    """Wipe every WATSONX/WX env var so each test starts clean."""
    for name in _NAMES:
        monkeypatch.delenv(name, raising=False)
    yield


def _propagate():
    """Fresh import + call so each test sees a fresh module."""
    from scripts import watsonx_env

    importlib.reload(watsonx_env)
    watsonx_env.propagate_watsonx_env()


def test_watsonx_to_wx_copy(monkeypatch):
    """All three documented WATSONX_* names land in their WX_* aliases."""
    monkeypatch.setenv("WATSONX_API_KEY", "key-abc")
    monkeypatch.setenv("WATSONX_PROJECT_ID", "proj-123")
    monkeypatch.setenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")

    _propagate()

    assert os.environ["WX_API_KEY"] == "key-abc"
    assert os.environ["WX_PROJECT_ID"] == "proj-123"
    assert os.environ["WX_URL"] == "https://us-south.ml.cloud.ibm.com"


def test_existing_wx_value_is_not_clobbered(monkeypatch):
    """Caller-set WX_* wins over the WATSONX_* source. (No-clobber contract.)"""
    monkeypatch.setenv("WATSONX_API_KEY", "from-watsonx")
    monkeypatch.setenv("WX_API_KEY", "preset-by-caller")
    monkeypatch.setenv("WATSONX_PROJECT_ID", "proj-from-watsonx")
    # WX_PROJECT_ID intentionally unset — should still get copied.

    _propagate()

    assert os.environ["WX_API_KEY"] == "preset-by-caller"  # not clobbered
    assert os.environ["WX_PROJECT_ID"] == "proj-from-watsonx"  # filled in


def test_no_op_when_nothing_set():
    """Helper is safe to call when no WatsonX env vars are present."""
    # Sanity: fixture left these absent.
    for name in _NAMES:
        assert name not in os.environ

    _propagate()

    for name in _NAMES:
        assert name not in os.environ


def test_partial_source_partial_destination(monkeypatch):
    """Only present source vars get copied; absent ones don't create empty WX_*."""
    monkeypatch.setenv("WATSONX_API_KEY", "key-only")
    # WATSONX_PROJECT_ID and WATSONX_URL deliberately absent.

    _propagate()

    assert os.environ["WX_API_KEY"] == "key-only"
    assert "WX_PROJECT_ID" not in os.environ
    assert "WX_URL" not in os.environ


def test_empty_string_source_is_treated_as_absent(monkeypatch):
    """A WATSONX_* set to '' should not produce an empty WX_* (avoids passing
    an empty string into litellm where None / unset would be the right shape)."""
    monkeypatch.setenv("WATSONX_API_KEY", "")
    monkeypatch.setenv("WATSONX_PROJECT_ID", "proj-real")

    _propagate()

    assert "WX_API_KEY" not in os.environ
    assert os.environ["WX_PROJECT_ID"] == "proj-real"


# ---------------------------------------------------------------------------
# Generator integration: call_llm() with a non-WatsonX model must NOT mutate
# WX_* env vars. Per Alex's review: the alias should only fire on watsonx/*.
# ---------------------------------------------------------------------------


def test_generator_call_llm_skips_alias_for_non_watsonx_models(monkeypatch):
    """call_llm() with model='openai/...' must not touch WX_* env vars.

    Stubs litellm so the test doesn't need network or the real package.
    """
    monkeypatch.setenv("WATSONX_API_KEY", "should-stay-in-WATSONX_only")

    # Pre-condition: WX_API_KEY absent.
    assert "WX_API_KEY" not in os.environ

    # Stub litellm to avoid the real network call.
    fake_litellm = type(sys)("litellm")
    fake_litellm.completion = lambda **kwargs: {
        "choices": [{"message": {"content": "stub"}}]
    }
    monkeypatch.setitem(sys.modules, "litellm", fake_litellm)

    from scripts import generate_scenarios

    importlib.reload(generate_scenarios)

    out = generate_scenarios.call_llm("hello", model="openai/gpt-4o-mini")
    assert out == "stub"
    # Critical: no leakage into WX_* for non-watsonx models.
    assert "WX_API_KEY" not in os.environ


def test_generator_call_llm_propagates_alias_for_watsonx_models(monkeypatch):
    """call_llm() with model='watsonx/...' triggers the WATSONX_* → WX_* copy."""
    monkeypatch.setenv("WATSONX_API_KEY", "key-real")
    monkeypatch.setenv("WATSONX_PROJECT_ID", "proj-real")
    monkeypatch.setenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")

    fake_litellm = type(sys)("litellm")
    fake_litellm.completion = lambda **kwargs: {
        "choices": [{"message": {"content": "stub"}}]
    }
    monkeypatch.setitem(sys.modules, "litellm", fake_litellm)

    from scripts import generate_scenarios

    importlib.reload(generate_scenarios)

    out = generate_scenarios.call_llm("hello", model="watsonx/meta-llama/llama-3-3")
    assert out == "stub"
    assert os.environ["WX_API_KEY"] == "key-real"
    assert os.environ["WX_PROJECT_ID"] == "proj-real"
    assert os.environ["WX_URL"] == "https://us-south.ml.cloud.ibm.com"
