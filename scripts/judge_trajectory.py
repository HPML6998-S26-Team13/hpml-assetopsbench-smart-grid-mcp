"""
LLM-as-Judge scorer for plan-execute trajectory artifacts.

Implements the 6-dimension rubric from the AssetOpsBench paper using
Llama-4-Maverick-17B-128E (or any WatsonX / LiteLLM model).

Usage
-----
Score a single trajectory file:
    python scripts/judge_trajectory.py \\
        --trajectory benchmarks/cell_Y_plan_execute/raw/<run>/foo.json \\
        --scenario   data/scenarios/aob_fmsr_01_list_failure_modes.json \\
        --run-meta   benchmarks/cell_Y_plan_execute/raw/<run>/meta.json \\
        --out        results/metrics/scenario_scores.jsonl

Score all trajectory files in a run directory automatically:
    python scripts/judge_trajectory.py \\
        --run-dir  benchmarks/cell_Y_plan_execute/raw/<run> \\
        --scenario-dir data/scenarios \\
        --out      results/metrics/scenario_scores.jsonl

Environment variables (same as the rest of the harness):
    WATSONX_APIKEY        IBM WatsonX API key
    WATSONX_PROJECT_ID    IBM WatsonX project ID
    WATSONX_URL           IBM WatsonX endpoint (optional)

    LITELLM_API_KEY       LiteLLM proxy key     (alternative backend)
    LITELLM_BASE_URL      LiteLLM proxy URL     (alternative backend)

    REPO_ROOT             Override the auto-detected repository root used to
                          produce repo-relative paths in JSONL and judge logs.

The default judge model is watsonx/meta-llama/llama-4-maverick-17b-128e-instruct-fp8.
Override with --judge-model.

Output format (scenario_scores.jsonl)
--------------------------------------
One JSON object per line (newline-delimited JSON / JSONL).
Schema version: v1.  See docs/judge_schema.md for field definitions.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Repo-root relative path helper
# ---------------------------------------------------------------------------

# Stable regardless of the caller's working directory.  Can be overridden via
# the REPO_ROOT env var for unusual checkout layouts.
_REPO_ROOT = Path(
    os.environ.get("REPO_ROOT", Path(__file__).resolve().parent.parent)
).resolve()


def _rel(p: Path) -> str:
    """Return a repo-root-relative POSIX path, falling back to absolute."""
    try:
        return p.resolve().relative_to(_REPO_ROOT).as_posix()
    except ValueError:
        return p.resolve().as_posix()


# ---------------------------------------------------------------------------
# Rubric prompt — adapted from AssetOpsBench evaluation_agent
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = textwrap.dedent("""\
    You are a critical reviewer evaluating an AI agent's response to an industrial
    asset operations task. Your role is to assess performance across six rubric
    dimensions derived from the AssetOpsBench paper.

    Respond ONLY with a valid JSON object — no markdown, no extra text.
""")

_USER_PROMPT_TEMPLATE = textwrap.dedent("""\
    ## Task
    {question}

    ## Expected Behaviour (Characteristic Answer)
    {characteristic_form}

    ## Agent Plan
    {plan_summary}

    ## Agent Trajectory (tool calls and results)
    {trajectory_summary}

    ## Agent Final Answer
    {answer}

    ---
    Evaluate across the six dimensions below. For each dimension output true (good) or false (bad).
    "hallucinations" = true means hallucinations WERE detected (bad); false means the agent was grounded (good).

    Output exactly this JSON object and nothing else:
    {{
        "task_completion": true_or_false,
        "data_retrieval_accuracy": true_or_false,
        "generalized_result_verification": true_or_false,
        "agent_sequence_correct": true_or_false,
        "clarity_and_justification": true_or_false,
        "hallucinations": true_or_false,
        "suggestions": "brief actionable note, or empty string if none"
    }}
""")

# ---------------------------------------------------------------------------
# Dimension → WandB field mapping (for downstream aggregation)
# ---------------------------------------------------------------------------

# Maps per-scenario boolean dimension names to the WandB run-level mean field names
# defined in docs/wandb_schema.md.
WANDB_DIM_MAP = {
    "task_completion": "judge_dim_task_completion_mean",
    "data_retrieval_accuracy": "judge_dim_correctness_mean",
    "generalized_result_verification": "judge_dim_correctness_mean",  # contributes to same mean
    "agent_sequence_correct": "judge_dim_tool_usage_mean",
    "clarity_and_justification": "judge_dim_efficiency_mean",
    "hallucinations": "judge_dim_grounding_mean",  # inverted: false=good
}

_BOOLEAN_DIMS = [
    "task_completion",
    "data_retrieval_accuracy",
    "generalized_result_verification",
    "agent_sequence_correct",
    "clarity_and_justification",
    "hallucinations",
]

_DEFAULT_JUDGE_MODEL = "watsonx/meta-llama/llama-4-maverick-17b-128e-instruct-fp8"
_PASS_THRESHOLD = 0.6  # 4 out of 6 dimensions


# ---------------------------------------------------------------------------
# LiteLLM helper
# ---------------------------------------------------------------------------


def _call_judge(
    prompt_user: str,
    judge_model: str,
    max_retries: int = 3,
) -> tuple[dict, str]:
    """Call the judge model and parse the 6-dimension JSON response.

    Returns
    -------
    (parsed_dims, raw_response)
        parsed_dims  — dict with the 6 boolean keys + suggestions
        raw_response — verbatim text returned by the model (for audit logging)
    """
    try:
        import litellm  # type: ignore
    except ImportError:
        sys.exit(
            "litellm is required. Run from the AssetOpsBench venv: "
            "source AssetOpsBench/.venv/bin/activate"
        )

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": prompt_user},
    ]

    last_error: Exception | None = None
    last_raw = ""
    for attempt in range(max_retries):
        try:
            response = litellm.completion(
                model=judge_model,
                messages=messages,
                temperature=0.0,
                max_tokens=512,
            )
            last_raw = response.choices[0].message.content or ""
            parsed = _parse_judge_json(last_raw)
            if parsed is not None:
                return parsed, last_raw
            print(
                f"  [judge] attempt {attempt + 1}: invalid/incomplete judge response,"
                " retrying...",
                file=sys.stderr,
            )
        except Exception as exc:
            last_error = exc
            print(
                f"  [judge] attempt {attempt + 1}: API error: {exc}",
                file=sys.stderr,
            )

    raise RuntimeError(
        f"Judge failed after {max_retries} attempts. Last error: {last_error}"
    )


def _parse_judge_json(raw: str) -> dict | None:
    """Extract, parse, and validate the JSON block from the judge response.

    Returns the parsed dict only if all six rubric keys are present and their
    values are actual JSON booleans.  Returns None otherwise so the caller can
    retry rather than silently persisting a corrupt score.
    """
    raw = raw.strip()

    # Try direct parse first, then extract {...} block as fallback
    candidate: dict | None = None
    try:
        candidate = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                candidate = json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

    if candidate is None:
        return None

    # Require all six rubric keys to be present
    missing = [dim for dim in _BOOLEAN_DIMS if dim not in candidate]
    if missing:
        print(
            f"  [judge] response missing rubric keys: {missing}",
            file=sys.stderr,
        )
        return None

    # Require rubric values to be real JSON booleans — reject string "true"/"false",
    # integers, etc. to prevent silent score corruption.
    non_bool = [dim for dim in _BOOLEAN_DIMS if not isinstance(candidate[dim], bool)]
    if non_bool:
        print(
            "  [judge] non-boolean rubric values: "
            + ", ".join(f"{d}={candidate[d]!r}" for d in non_bool),
            file=sys.stderr,
        )
        return None

    return candidate


# ---------------------------------------------------------------------------
# Score computation
# ---------------------------------------------------------------------------


def _compute_score(dims: dict) -> float:
    """Compute a scalar score in [0, 1] from the 6 boolean dimensions.

    Each dimension contributes 1/6 to the total. For 'hallucinations',
    the score contribution is inverted: False (no hallucinations) = good = 1/6.

    Raises ValueError if dims is missing any expected key or contains non-bool
    values — callers must validate before calling this function.
    """
    missing = [dim for dim in _BOOLEAN_DIMS if dim not in dims]
    if missing:
        raise ValueError(f"dims missing expected keys: {missing}")

    non_bool = [dim for dim in _BOOLEAN_DIMS if not isinstance(dims[dim], bool)]
    if non_bool:
        raise ValueError(
            "dims has non-boolean values: "
            + ", ".join(f"{d}={dims[d]!r}" for d in non_bool)
        )

    total = 0.0
    for dim in _BOOLEAN_DIMS:
        val = dims[dim]
        if dim == "hallucinations":
            total += 0.0 if val else 1.0  # False hallucinations = good
        else:
            total += 1.0 if val else 0.0
    return round(total / len(_BOOLEAN_DIMS), 4)


# ---------------------------------------------------------------------------
# Trajectory → prompt helpers
# ---------------------------------------------------------------------------


def _summarise_plan(plan: list[dict]) -> str:
    lines = []
    for step in plan:
        tool = step.get("tool") or "none"
        task = step.get("task", "")
        server = step.get("server", "")
        deps = step.get("dependencies", [])
        dep_str = f" (depends on steps {deps})" if deps else ""
        lines.append(
            f"  Step {step.get('step', '?')}: [{server}] {tool} — {task}{dep_str}"
        )
    return "\n".join(lines) if lines else "(no plan)"


def _summarise_trajectory(trajectory: list[dict], max_chars: int = 800) -> str:
    lines = []
    for r in trajectory:
        status = "OK" if r.get("success") else "ERR"
        tool = r.get("tool") or "none"
        server = r.get("server", "")
        response = str(r.get("response", ""))[:200]
        lines.append(
            f"  [{status}] Step {r.get('step', '?')} [{server}] {tool}: {response}"
        )
    full = "\n".join(lines)
    if len(full) > max_chars:
        full = full[:max_chars] + "...(truncated)"
    return full if full else "(no trajectory)"


def _extract_trial_index(trajectory_path: Path) -> int:
    """Derive trial index from filename pattern ``*_runNN*`` (1-indexed).

    Falls back to 1 if no match is found.
    """
    match = re.search(r"_run(\d+)", trajectory_path.stem)
    return int(match.group(1)) if match else 1


# ---------------------------------------------------------------------------
# Main scoring logic
# ---------------------------------------------------------------------------


def score_trajectory(
    trajectory_path: Path,
    scenario_path: Path,
    meta_path: Path | None,
    judge_model: str,
    out_path: Path,
    log_dir: Path | None = None,
) -> dict:
    """Score one trajectory file.

    Appends a JSONL record to out_path.  If log_dir is given, also writes a
    full judge audit log (prompt + raw Maverick response + parsed dims) to
    ``log_dir/<run_name>/<scenario_id>_judge_log.json``.
    """
    traj_data = json.loads(trajectory_path.read_text(encoding="utf-8"))
    scenario_data = json.loads(scenario_path.read_text(encoding="utf-8"))
    meta_data = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path else {}

    question = traj_data.get("question", "")
    answer = traj_data.get("answer", "")
    plan = traj_data.get("plan", [])
    trajectory = traj_data.get("trajectory", [])
    characteristic_form = scenario_data.get("characteristic_form", "")

    plan_summary = _summarise_plan(plan)
    traj_summary = _summarise_trajectory(trajectory)

    prompt_user = _USER_PROMPT_TEMPLATE.format(
        question=question,
        characteristic_form=characteristic_form,
        plan_summary=plan_summary,
        trajectory_summary=traj_summary,
        answer=answer,
    )

    print(f"  Calling judge ({judge_model})...", file=sys.stderr)
    scored_at = datetime.now(timezone.utc).isoformat()
    dims, raw_response = _call_judge(prompt_user, judge_model)

    score = _compute_score(dims)
    passed = score >= _PASS_THRESHOLD

    run_name = meta_data.get("run_name", trajectory_path.parent.name)
    scenario_id = scenario_data.get("id", "")

    record = {
        "schema_version": "v1",
        "scored_at": scored_at,
        # Join keys (align with results/README.md conventions)
        "run_name": run_name,
        "wandb_run_url": meta_data.get("wandb_run_url"),
        "scenario_id": scenario_id,
        "scenario_file": _rel(scenario_path),
        "trial_index": _extract_trial_index(trajectory_path),
        "experiment_cell": meta_data.get("experiment_cell", "Y"),
        "orchestration_mode": meta_data.get("orchestration_mode", "plan_execute"),
        "mcp_mode": meta_data.get("mcp_mode", "baseline"),
        "model_id": meta_data.get("model_id", ""),
        "judge_model": judge_model,
        # 6 rubric dimensions (from AssetOpsBench evaluation_agent)
        "dim_task_completion": dims["task_completion"],
        "dim_data_retrieval_accuracy": dims["data_retrieval_accuracy"],
        "dim_generalized_result_verification": dims["generalized_result_verification"],
        "dim_agent_sequence_correct": dims["agent_sequence_correct"],
        "dim_clarity_and_justification": dims["clarity_and_justification"],
        "dim_hallucinations": dims["hallucinations"],
        # Derived aggregate
        "score_6d": score,
        "pass_threshold": _PASS_THRESHOLD,
        "pass": passed,
        "suggestions": dims.get("suggestions", ""),
        "trajectory_file": _rel(trajectory_path),
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")

    # ------------------------------------------------------------------
    # Optional: save full judge audit log for reproducibility and analysis
    # ------------------------------------------------------------------
    if log_dir is not None:
        run_log_dir = log_dir / run_name
        run_log_dir.mkdir(parents=True, exist_ok=True)
        log_file = run_log_dir / f"{scenario_id}_judge_log.json"
        judge_log = {
            "schema_version": "v1",
            "scored_at": scored_at,
            "run_name": run_name,
            "scenario_id": scenario_id,
            "judge_model": judge_model,
            "trajectory_file": _rel(trajectory_path),
            "scenario_file": _rel(scenario_path),
            "prompt_system": _SYSTEM_PROMPT,
            "prompt_user": prompt_user,
            "raw_response": raw_response,
            "parsed_dims": dims,
            "score_6d": score,
            "pass": passed,
        }
        log_file.write_text(json.dumps(judge_log, indent=2), encoding="utf-8")
        print(f"  Judge log saved → {log_file}", file=sys.stderr)

    return record


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="judge_trajectory",
        description="Score plan-execute trajectories across the 6 AssetOpsBench rubric dimensions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              # Score a single trajectory
              python scripts/judge_trajectory.py \\
                  --trajectory benchmarks/cell_Y_plan_execute/raw/issue3-aob-harness-smoke/issue3_aob_fmsr_run01.json \\
                  --scenario   data/scenarios/aob_fmsr_01_list_failure_modes.json \\
                  --run-meta   benchmarks/cell_Y_plan_execute/raw/issue3-aob-harness-smoke/meta.json

              # Score all trajectories in a run directory
              python scripts/judge_trajectory.py \\
                  --run-dir    benchmarks/cell_Y_plan_execute/raw/issue3-aob-harness-smoke \\
                  --scenario-dir data/scenarios

              # Score with full audit log saved
              python scripts/judge_trajectory.py \\
                  --trajectory benchmarks/... \\
                  --scenario   data/scenarios/... \\
                  --log-dir    results/judge_logs
        """),
    )
    p.add_argument(
        "--trajectory", type=Path, help="Path to a single trajectory JSON file."
    )
    p.add_argument(
        "--scenario",
        type=Path,
        help="Path to the scenario JSON file (for --trajectory mode).",
    )
    p.add_argument(
        "--run-meta",
        type=Path,
        help="Path to meta.json for the run (optional, enriches output).",
    )
    p.add_argument(
        "--run-dir",
        type=Path,
        help="Run directory; scores all *.json files that look like trajectories.",
    )
    p.add_argument(
        "--scenario-dir",
        type=Path,
        default=Path("data/scenarios"),
        help="Directory to search for scenario files when using --run-dir.",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=Path("results/metrics/scenario_scores.jsonl"),
        help="Output JSONL file (appended). Default: results/metrics/scenario_scores.jsonl",
    )
    p.add_argument(
        "--judge-model",
        default=_DEFAULT_JUDGE_MODEL,
        help=f"LiteLLM model string for the judge. Default: {_DEFAULT_JUDGE_MODEL}",
    )
    p.add_argument(
        "--log-dir",
        type=Path,
        default=None,
        help=(
            "If set, save a full judge audit log (prompt + raw response + dims) to "
            "LOG_DIR/<run_name>/<scenario_id>_judge_log.json"
        ),
    )
    return p


def _find_scenario(scenario_dir: Path, trajectory_path: Path) -> Path | None:
    """Try to find the matching scenario file for a trajectory.

    Checks (in order):
    1. ``scenario_file`` field embedded in the trajectory JSON, resolved against
       multiple candidate bases (trajectory dir, scenario_dir parent, scenario_dir).
    2. Filename stem overlap between trajectory and scenario files.

    Returns None if no match is found.
    """
    try:
        data = json.loads(trajectory_path.read_text(encoding="utf-8"))
    except Exception:
        return None

    # If trajectory has a scenario_file field (e.g., from run_experiment.sh latencies),
    # resolve relative paths against several stable bases so the lookup works regardless
    # of the caller's working directory.
    sf = data.get("scenario_file")
    if sf:
        raw = Path(sf)
        bases = (
            [raw]
            if raw.is_absolute()
            else [
                trajectory_path.parent / raw,
                scenario_dir.parent / raw,
                scenario_dir / raw,
                _REPO_ROOT / raw,
            ]
        )
        for candidate in bases:
            if candidate.resolve().exists():
                return candidate.resolve()

    # Try matching by stem: trajectory stem may contain scenario slug
    for candidate in scenario_dir.glob("*.json"):
        if (
            candidate.stem in trajectory_path.stem
            or trajectory_path.stem in candidate.stem
        ):
            return candidate

    return None


def _is_trajectory_file(path: Path) -> bool:
    """Return True if the JSON file looks like a plan-execute trajectory output."""
    if path.name in ("meta.json", "config.json", "summary.json"):
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return "answer" in data and "trajectory" in data
    except Exception:
        return False


def _load_env() -> None:
    """Load .env when available; works with or without python-dotenv installed."""
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv()
        return
    except ImportError:
        pass

    env_path = Path(".env")
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key, val = key.strip(), val.strip().strip("'\"")
        if key:
            os.environ.setdefault(key, val)


def main() -> None:
    _load_env()

    args = _build_parser().parse_args()

    if args.trajectory:
        # Single-file mode
        if not args.scenario:
            sys.exit("--scenario is required when using --trajectory")
        record = score_trajectory(
            trajectory_path=args.trajectory,
            scenario_path=args.scenario,
            meta_path=args.run_meta,
            judge_model=args.judge_model,
            out_path=args.out,
            log_dir=args.log_dir,
        )
        print(json.dumps(record, indent=2))
        return

    if args.run_dir:
        # Run-directory mode: find all trajectory JSON files
        meta_path = args.run_dir / "meta.json"
        if not meta_path.exists():
            meta_path = None

        scored = 0
        for traj_file in sorted(args.run_dir.glob("*.json")):
            if not _is_trajectory_file(traj_file):
                continue
            scenario_path = _find_scenario(args.scenario_dir, traj_file)
            if scenario_path is None:
                print(
                    f"  [warn] could not find scenario for {traj_file.name}, skipping",
                    file=sys.stderr,
                )
                continue
            print(
                f"Scoring {traj_file.name} against {scenario_path.name}...",
                file=sys.stderr,
            )
            record = score_trajectory(
                trajectory_path=traj_file,
                scenario_path=scenario_path,
                meta_path=meta_path,
                judge_model=args.judge_model,
                out_path=args.out,
                log_dir=args.log_dir,
            )
            print(f"  score_6d={record['score_6d']}  pass={record['pass']}")
            scored += 1

        print(f"\nScored {scored} trajectory file(s). Output: {args.out}")
        return

    _build_parser().print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
