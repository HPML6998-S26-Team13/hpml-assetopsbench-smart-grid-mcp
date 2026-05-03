from __future__ import annotations

import json
from pathlib import Path

from scripts import gcp_resume_state


def _scenario(path: Path, scenario_id: str = "SGT-001") -> Path:
    path.write_text(
        json.dumps({"id": scenario_id, "text": "test prompt"}) + "\n",
        encoding="utf-8",
    )
    return path


def _trial(path: Path, *, success: bool | None = True, answer: str = "done") -> Path:
    payload = {"answer": answer, "history": []}
    if success is not None:
        payload["success"] = success
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    return path


def _latency(
    path: Path, scenario_file: Path, trial_index: int, output_path: Path
) -> None:
    path.write_text(
        json.dumps(
            {
                "scenario_file": scenario_file.as_posix(),
                "trial_index": trial_index,
                "latency_seconds": 1.25,
                "output_path": output_path.as_posix(),
            }
        )
        + "\n",
        encoding="utf-8",
    )


def _classify(
    tmp_path: Path,
    scenario_file: Path,
    output_path: Path,
    *,
    require_latency: bool = True,
) -> dict:
    return gcp_resume_state.classify_trial(
        run_dir=tmp_path,
        scenario_file=scenario_file,
        trial_index=1,
        output_path=output_path,
        latency_file=tmp_path / "latencies.jsonl",
        require_latency=require_latency,
    )


def test_completed_success_is_terminal_with_latency(tmp_path: Path) -> None:
    scenario_file = _scenario(tmp_path / "multi_01.json")
    output = _trial(tmp_path / "2026-05-03_Y_multi_01_run01.json", success=True)
    _latency(tmp_path / "latencies.jsonl", scenario_file, 1, output)

    result = _classify(tmp_path, scenario_file, output)

    assert result["state"] == "complete_success"
    assert result["complete"] is True
    assert result["success"] is True


def test_completed_failure_is_terminal_and_skippable(tmp_path: Path) -> None:
    scenario_file = _scenario(tmp_path / "multi_01.json")
    output = _trial(tmp_path / "2026-05-03_Y_multi_01_run01.json", success=False)
    _latency(tmp_path / "latencies.jsonl", scenario_file, 1, output)

    result = _classify(tmp_path, scenario_file, output)

    assert result["state"] == "complete_failure"
    assert result["complete"] is True
    assert result["success"] is False


def test_missing_latency_keeps_valid_json_incomplete_by_default(tmp_path: Path) -> None:
    scenario_file = _scenario(tmp_path / "multi_01.json")
    output = _trial(tmp_path / "2026-05-03_Y_multi_01_run01.json", success=True)

    result = _classify(tmp_path, scenario_file, output)

    assert result["state"] == "incomplete"
    assert "missing_latency" in result["reason"]


def test_invalid_json_is_incomplete(tmp_path: Path) -> None:
    scenario_file = _scenario(tmp_path / "multi_01.json")
    output = tmp_path / "2026-05-03_Y_multi_01_run01.json"
    output.write_text("{not-json", encoding="utf-8")

    result = _classify(tmp_path, scenario_file, output, require_latency=False)

    assert result["state"] == "incomplete"
    assert "invalid_json" in result["reason"]


def test_legacy_stdout_next_to_terminal_json_is_not_dangling(tmp_path: Path) -> None:
    scenario_file = _scenario(tmp_path / "multi_01.json")
    output = _trial(tmp_path / "legacy_multi_01_run01.json", success=True)
    output.with_suffix(output.suffix + ".stdout").write_text(
        "legacy log\n", encoding="utf-8"
    )
    _latency(tmp_path / "latencies.jsonl", scenario_file, 1, output)
    newer_name = tmp_path / "2026-05-04_Y_multi_01_run01.json"

    result = _classify(tmp_path, scenario_file, newer_name)

    assert result["state"] == "complete_success"
    assert result["output_path"] == output.as_posix()


def test_conflicting_duplicate_latency_rows_are_incomplete(tmp_path: Path) -> None:
    scenario_file = _scenario(tmp_path / "multi_01.json")
    output = _trial(tmp_path / "2026-05-03_Y_multi_01_run01.json", success=True)
    rows = [
        {
            "scenario_file": scenario_file.as_posix(),
            "trial_index": 1,
            "latency_seconds": 1.0,
            "output_path": output.as_posix(),
        },
        {
            "scenario_file": scenario_file.as_posix(),
            "trial_index": 1,
            "latency_seconds": 2.0,
            "output_path": output.as_posix(),
        },
    ]
    (tmp_path / "latencies.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )

    result = _classify(tmp_path, scenario_file, output)

    assert result["state"] == "incomplete"
    assert "duplicate_conflicting_latency" in result["reason"]


def test_finalize_trial_writes_atomic_output_latency_and_manifest(
    tmp_path: Path,
) -> None:
    scenario_file = _scenario(tmp_path / "multi_01.json")
    temp_output = _trial(tmp_path / "run" / "trial.json.tmp", success=None)
    output = tmp_path / "run" / "trial.json"
    latency_file = tmp_path / "run" / "latencies.jsonl"
    manifest_file = tmp_path / "run" / "resume_manifest.jsonl"

    result = gcp_resume_state.finalize_trial(
        scenario_file=scenario_file,
        trial_index=1,
        temp_output=temp_output,
        output_path=output,
        latency_file=latency_file,
        manifest_file=manifest_file,
        run_name="resume-smoke",
        batch_id="batch-1",
        start_epoch=10.0,
        end_epoch=12.5,
        return_code=0,
    )

    assert result["state"] == "complete_success"
    assert output.exists()
    assert not temp_output.exists()
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["scenario"]["id"] == "SGT-001"
    assert payload["success"] is True
    latency_rows = [json.loads(line) for line in latency_file.read_text().splitlines()]
    assert latency_rows == [
        {
            "latency_seconds": 2.5,
            "output_path": output.as_posix(),
            "scenario_file": scenario_file.as_posix(),
            "trial_index": 1,
        }
    ]
    manifest_rows = [
        json.loads(line)
        for line in manifest_file.read_text(encoding="utf-8").splitlines()
    ]
    assert manifest_rows[-1]["state"] == "complete_success"
    assert manifest_rows[-1]["batch_id"] == "batch-1"
    assert "runtime_versions" in manifest_rows[-1]


def test_finalize_trial_marks_divergent_rerun(tmp_path: Path) -> None:
    scenario_file = _scenario(tmp_path / "multi_01.json")
    output = tmp_path / "run" / "trial.json"
    latency_file = tmp_path / "run" / "latencies.jsonl"
    manifest_file = tmp_path / "run" / "resume_manifest.jsonl"
    first_temp = _trial(tmp_path / "run" / "trial-first.json.tmp", answer="first")
    second_temp = _trial(tmp_path / "run" / "trial-second.json.tmp", answer="second")

    gcp_resume_state.finalize_trial(
        scenario_file=scenario_file,
        trial_index=1,
        temp_output=first_temp,
        output_path=output,
        latency_file=latency_file,
        manifest_file=manifest_file,
        run_name="resume-smoke",
        batch_id="batch-1",
        start_epoch=10.0,
        end_epoch=12.5,
        return_code=0,
    )

    gcp_resume_state.finalize_trial(
        scenario_file=scenario_file,
        trial_index=1,
        temp_output=second_temp,
        output_path=output,
        latency_file=latency_file,
        manifest_file=manifest_file,
        run_name="resume-smoke",
        batch_id="batch-1",
        start_epoch=20.0,
        end_epoch=23.0,
        return_code=0,
    )

    manifest_rows = [
        json.loads(line)
        for line in manifest_file.read_text(encoding="utf-8").splitlines()
    ]
    rerun = manifest_rows[-1]
    assert rerun["divergent"] is True
    assert rerun["original_output_sha256"] != rerun["final_output_sha256"]
