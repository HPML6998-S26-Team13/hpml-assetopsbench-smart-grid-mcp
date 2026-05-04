"""Cross-call-site WatsonX env-var alias helper.

The team's `.env` and `docs/reference/watsonx_access.md` document
`WATSONX_API_KEY` / `WATSONX_PROJECT_ID` / `WATSONX_URL`, but newer
litellm WatsonX provider versions (≥ 1.81.x as observed in the team
`.venv-insomnia`) read `WX_API_KEY` / `WX_PROJECT_ID` / `WX_URL` and
fail with `"Watsonx project_id and space_id not set"` if only the
`WATSONX_*` names are set.

This helper copies `WATSONX_<NAME>` into `WX_<NAME>` when `WX_<NAME>`
is unset. Caller-provided `WX_*` values win (no clobber). It mirrors
the long-standing `WATSONX_API_KEY` ↔ `WATSONX_APIKEY` bridge in
`scripts/run_experiment.sh:290`.

Used by every Python entry point in this repo that drives a
`watsonx/...` LiteLLM model:

  - scripts/generate_scenarios.py (PS B generator → litellm.completion)
  - scripts/aat_runner.py         (AaT runner → Agents SDK LitellmModel)
  - scripts/judge_trajectory.py   (judge → litellm.completion)

The bash wrapper `scripts/run_experiment.sh` does the same alias inline
so subprocess paths (replay loop, batch mode, etc.) inherit the WX_*
names without going through Python.
"""

from __future__ import annotations

import os

# Source / destination env-var pairs. Order is irrelevant; absent sources
# are skipped, present-destination overrides win.
_WATSONX_ENV_ALIASES: tuple[tuple[str, str], ...] = (
    ("WATSONX_API_KEY", "WX_API_KEY"),
    ("WATSONX_PROJECT_ID", "WX_PROJECT_ID"),
    ("WATSONX_URL", "WX_URL"),
)


def propagate_watsonx_env() -> None:
    """Mirror `WATSONX_<NAME>` → `WX_<NAME>` for litellm WatsonX provider.

    No-clobber: a pre-set `WX_*` value wins. Missing source values are
    silently skipped (i.e. the function is safe to call even when no
    WatsonX env vars are present).
    """
    for src, dst in _WATSONX_ENV_ALIASES:
        if dst not in os.environ and os.environ.get(src):
            os.environ[dst] = os.environ[src]
