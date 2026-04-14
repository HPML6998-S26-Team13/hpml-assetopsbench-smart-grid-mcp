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
    "task_completion":               "judge_dim_task_completion_mean",
    "data_retrieval_accuracy":       "judge_dim_correctness_mean",
    "generalized_result_verification": "judge_dim_correctness_mean",  # contributes to same mean
    "agent_sequence_correct":        "judge_dim_tool_usage_mean",
    "clarity_and_justification":     "judge_dim_efficiency_mean",
    "hallucinations":                "judge_dim_grounding_mean",   # inverted: false=good
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

def _call_judge(prompt_user: str, judge_model: str, max_retries: int = 3) -> dict:
    """Call the judge model and parse the 6-dimension JSON response."""
    try:
        import litellm  # type: ignore
    except ImportError:
        sys.exit(
            "litellm is required. Run from the AssetOpsBench venv: "
            "source AssetOpsBench/.venv/bin/activate"
        )

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user",   "content": prompt_user},
    ]

    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            response = litellm.completion(
                model=judge_model,
                messages=messages,
                temperature=0.0,
                max_tokens=512,
            )
            raw = response.choices[0].message.content or ""
            parsed = _parse_judge_json(raw)
            if parsed is not None:
                return parsed
            print(
                f"  [judge] attempt {attempt + 1}: could not parse JSON, retrying...",
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
    """Extract and parse the JSON block from the judge response."""
    raw = raw.strip()
    # Try direct parse first
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    # Try extracting {...} block
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return None


# ---------------------------------------------------------------------------
# Score computation
# ---------------------------------------------------------------------------

def _compute_score(dims: dict) -> float:
    """
    Compute a scalar score in [0, 1] from the 6 boolean dimensions.

    Each dimension contributes 1/6 to the total. For 'hallucinations',
    the score contribution is inverted: False (no hallucinations) = good = 1/6.
    """
    total = 0.0
    for dim in _BOOLEAN_DIMS:
        val = dims.get(dim, False)
        if dim == "hallucinations":
            total += 0.0 if val else 1.0   # False hallucinations = good
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
        lines.append(f"  Step {step.get('step', '?')}: [{server}] {tool} — {task}{dep_str}")
    return "\n".join(lines) if lines else "(no plan)"


def _summarise_trajectory(trajectory: list[dict], max_chars: int = 800) -> str:
    lines = []
    for r in trajectory:
        status = "OK" if r.get("success") else "ERR"
        tool = r.get("tool") or "none"
        server = r.get("server", "")
        response = str(r.get("response", ""))[:200]
        lines.append(f"  [{status}] Step {r.get('step', '?')} [{server}] {tool}: {response}")
    full = "\n".join(lines)
    if len(full) > max_chars:
        full = full[:max_chars] + "...(truncated)"
    return full if full else "(no trajectory)"


# ---------------------------------------------------------------------------
# Main scoring logic
# ---------------------------------------------------------------------------

def score_trajectory(
    trajectory_path: Path,
    scenario_path: Path,
    meta_path: Path | None,
    judge_model: str,
    out_path: Path,
) -> dict:
    """Score one trajectory file. Appends a JSONL record to out_path."""
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
    dims = _call_judge(prompt_user, judge_model)

    score = _compute_score(dims)
    passed = score >= _PASS_THRESHOLD

    record = {
        "schema_version": "v1",
        "scored_at": datetime.now(timezone.utc).isoformat(),

        # Join keys (align with results/README.md conventions)
        "run_name":          meta_data.get("run_name", trajectory_path.parent.name),
        "wandb_run_url":     meta_data.get("wandb_run_url"),
        "scenario_id":       scenario_data.get("id", ""),
        "scenario_file":     str(scenario_path).replace("\\", "/"),
        "trial_index":       1,
        "experiment_cell":   meta_data.get("experiment_cell", "Y"),
        "orchestration_mode": meta_data.get("orchestration_mode", "plan_execute"),
        "mcp_mode":          meta_data.get("mcp_mode", "baseline"),
        "model_id":          meta_data.get("model_id", ""),
        "judge_model":       judge_model,

        # 6 rubric dimensions (from AssetOpsBench evaluation_agent)
        "dim_task_completion":              bool(dims.get("task_completion")),
        "dim_data_retrieval_accuracy":      bool(dims.get("data_retrieval_accuracy")),
        "dim_generalized_result_verification": bool(dims.get("generalized_result_verification")),
        "dim_agent_sequence_correct":       bool(dims.get("agent_sequence_correct")),
        "dim_clarity_and_justification":    bool(dims.get("clarity_and_justification")),
        "dim_hallucinations":               bool(dims.get("hallucinations")),

        # Derived aggregate
        "score_6d":       score,
        "pass_threshold": _PASS_THRESHOLD,
        "pass":           passed,

        "suggestions":          dims.get("suggestions", ""),
        "trajectory_file":      str(trajectory_path).replace("\\", "/"),
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")

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
        """),
    )
    p.add_argument("--trajectory",    type=Path, help="Path to a single trajectory JSON file.")
    p.add_argument("--scenario",      type=Path, help="Path to the scenario JSON file (for --trajectory mode).")
    p.add_argument("--run-meta",      type=Path, help="Path to meta.json for the run (optional, enriches output).")
    p.add_argument("--run-dir",       type=Path, help="Run directory; scores all *.json files that look like trajectories.")
    p.add_argument("--scenario-dir",  type=Path, default=Path("data/scenarios"),
                   help="Directory to search for scenario files when using --run-dir.")
    p.add_argument("--out",           type=Path, default=Path("results/metrics/scenario_scores.jsonl"),
                   help="Output JSONL file (appended). Default: results/metrics/scenario_scores.jsonl")
    p.add_argument("--judge-model",   default=_DEFAULT_JUDGE_MODEL,
                   help=f"LiteLLM model string for the judge. Default: {_DEFAULT_JUDGE_MODEL}")
    return p


def _find_scenario(scenario_dir: Path, trajectory_path: Path) -> Path | None:
    """
    Try to find the matching scenario file for a trajectory by scanning
    the trajectory JSON for a scenario_id or matching filename stem.
    """
    try:
        data = json.loads(trajectory_path.read_text(encoding="utf-8"))
    except Exception:
        return None

    # If trajectory has a scenario_file field (e.g., from run_experiment.sh latencies)
    sf = data.get("scenario_file")
    if sf:
        candidate = Path(sf)
        if candidate.exists():
            return candidate

    # Try matching by stem: trajectory stem may contain scenario slug
    for candidate in scenario_dir.glob("*.json"):
        if candidate.stem in trajectory_path.stem or trajectory_path.stem in candidate.stem:
            return candidate

    # Fall back: return all scenario files and let caller decide
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


def main() -> None:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()

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
            print(f"Scoring {traj_file.name} against {scenario_path.name}...", file=sys.stderr)
            record = score_trajectory(
                trajectory_path=traj_file,
                scenario_path=scenario_path,
                meta_path=meta_path,
                judge_model=args.judge_model,
                out_path=args.out,
            )
            print(f"  score_6d={record['score_6d']}  pass={record['pass']}")
            scored += 1

        print(f"\nScored {scored} trajectory file(s). Output: {args.out}")
        return

    _build_parser().print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
