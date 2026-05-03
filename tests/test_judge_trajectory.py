from __future__ import annotations

import json
from pathlib import Path

from scripts import judge_trajectory


def test_existing_score_keys_include_prompt_version_and_legacy_rows(
    tmp_path: Path,
) -> None:
    out = tmp_path / "scenario_scores.jsonl"
    out.write_text(
        json.dumps(
            {
                "run_name": "run-a",
                "scenario_id": "SGT-001",
                "trial_index": 1,
                "judge_model": "watsonx/test",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    keys = judge_trajectory._existing_score_keys(out)

    assert keys == {
        (
            "run-a",
            "SGT-001",
            1,
            "watsonx/test",
            judge_trajectory._JUDGE_PROMPT_VERSION,
        )
    }


def test_score_identity_matches_existing_row_shape(tmp_path: Path) -> None:
    run_dir = tmp_path / "raw" / "run-a"
    run_dir.mkdir(parents=True)
    trajectory = run_dir / "2026-05-03_Y_multi_01_run02.json"
    trajectory.write_text(
        json.dumps({"answer": "ok", "history": []}) + "\n",
        encoding="utf-8",
    )
    scenario = tmp_path / "multi_01.json"
    scenario.write_text(json.dumps({"id": "SGT-001", "text": "prompt"}) + "\n")
    meta = run_dir / "meta.json"
    meta.write_text(json.dumps({"run_name": "run-a"}) + "\n")

    identity = judge_trajectory._score_identity(
        trajectory,
        scenario,
        meta,
        "watsonx/test",
    )

    assert identity == (
        "run-a",
        "SGT-001",
        2,
        "watsonx/test",
        judge_trajectory._JUDGE_PROMPT_VERSION,
    )
