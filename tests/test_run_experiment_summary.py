"""Regression tests for run_experiment.sh summary generation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _extract_summary_python(repo_root: Path) -> str:
    script = repo_root.joinpath("scripts/run_experiment.sh").read_text(encoding="utf-8")
    marker = '"$PYTHON_BIN" - "$SUMMARY_FILE"'
    start = script.index(marker)
    heredoc_start = script.index("<<'PY'\n", start) + len("<<'PY'\n")
    heredoc_end = script.index("\nPY\n", heredoc_start)
    return script[heredoc_start:heredoc_end]


def _base_config(summary_path: Path) -> dict:
    return {
        "schema_version": "v1",
        "wandb_entity": "assetopsbench-smartgrid",
        "project_name": "assetopsbench-smartgrid",
        "run_name": "test-run",
        "git_sha": "test-sha",
        "benchmark_config_path": "configs/aat_mcp_optimized.env",
        "benchmark_summary_path": summary_path.as_posix(),
        "wandb_run_url": None,
        "experiment_family": "exp1_mcp_overhead",
        "contributing_experiments": ["exp1_mcp_overhead"],
        "experiment_cell": "C",
        "orchestration_mode": "agent_as_tool",
        "mcp_mode": "optimized",
        "scenario_set_name": "test-set",
        "scenario_set_hash": "test-hash",
        "model_id": "openai/Llama-3.1-8B-Instruct",
        "host_name": "test-host",
        "compute_env": "local",
        "compute_provider": None,
        "compute_zone": None,
        "compute_instance": None,
        "gpu_type": "test-gpu",
        "slurm_job_id": "test-job",
    }


def test_summary_includes_batch_mcp_setup_once(tmp_path):
    """Cell C batch summaries include one-time MCP setup without skewing p50/p95."""
    repo_root = Path(__file__).resolve().parent.parent
    summary_py = _extract_summary_python(repo_root)

    summary_path = tmp_path / "summary.json"
    config_path = tmp_path / "config.json"
    meta_path = tmp_path / "meta.json"
    latency_path = tmp_path / "latencies.jsonl"
    run_dir = tmp_path / "raw" / "test-run"
    run_dir.mkdir(parents=True)

    config_path.write_text(
        json.dumps(_base_config(summary_path), indent=2) + "\n",
        encoding="utf-8",
    )
    meta_path.write_text(json.dumps({"started_at": "now"}) + "\n", encoding="utf-8")
    latency_path.write_text(
        "\n".join(
            [
                json.dumps({"latency_seconds": 2.0, "mcp_setup_seconds": 5.0}),
                json.dumps({"latency_seconds": 3.0, "mcp_setup_seconds": 5.0}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    subprocess.run(
        [
            sys.executable,
            "-c",
            summary_py,
            str(summary_path),
            str(config_path),
            str(meta_path),
            str(latency_path),
            str(run_dir),
            "2",
            "0",
            "2",
            "0",
            "0",
        ],
        check=True,
    )

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    assert summary["wall_clock_seconds_total"] == 10.0
    assert summary["latency_seconds_mean"] == 2.5
    assert summary["latency_seconds_p50"] == 2.0
    assert summary["latency_seconds_p95"] == 3.0
    assert summary["mcp_setup_seconds"] == 5.0
    assert meta["mcp_setup_seconds"] == 5.0


def test_summary_records_null_mcp_setup_when_absent(tmp_path):
    """Non-batch summaries keep the setup field present with a null value."""
    repo_root = Path(__file__).resolve().parent.parent
    summary_py = _extract_summary_python(repo_root)

    summary_path = tmp_path / "summary.json"
    config_path = tmp_path / "config.json"
    meta_path = tmp_path / "meta.json"
    latency_path = tmp_path / "latencies.jsonl"
    run_dir = tmp_path / "raw" / "test-run"
    run_dir.mkdir(parents=True)

    config_path.write_text(
        json.dumps(_base_config(summary_path), indent=2) + "\n",
        encoding="utf-8",
    )
    meta_path.write_text(json.dumps({"started_at": "now"}) + "\n", encoding="utf-8")
    latency_path.write_text(
        json.dumps({"latency_seconds": 2.0}) + "\n",
        encoding="utf-8",
    )

    subprocess.run(
        [
            sys.executable,
            "-c",
            summary_py,
            str(summary_path),
            str(config_path),
            str(meta_path),
            str(latency_path),
            str(run_dir),
            "1",
            "0",
            "1",
            "0",
            "0",
        ],
        check=True,
    )

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    assert summary["wall_clock_seconds_total"] == 2.0
    assert summary["mcp_setup_seconds"] is None
    assert meta["mcp_setup_seconds"] is None


def _write_trial(
    run_dir: Path,
    *,
    name: str,
    success: bool = True,
    tool_call_count: int = 1,
    usage: dict | None = None,
) -> None:
    """Write a per-trial JSON shaped like the aat_runner output."""
    payload = {
        "question": "test",
        "answer": "ok",
        "success": success,
        "max_turns_exhausted": False,
        "turn_count": 1,
        "tool_call_count": tool_call_count,
        "usage": usage if usage is not None else {},
        "history": [
            {"turn": 1, "role": "assistant", "content": "ok", "tool_calls": []}
        ],
        "runner_meta": {"duration_seconds": 1.0},
    }
    (run_dir / name).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_summary_aggregates_token_usage_when_trials_report_it(tmp_path):
    """#133: per-trial usage blocks roll up into summary token totals + tok/s."""
    repo_root = Path(__file__).resolve().parent.parent
    summary_py = _extract_summary_python(repo_root)

    summary_path = tmp_path / "summary.json"
    config_path = tmp_path / "config.json"
    meta_path = tmp_path / "meta.json"
    latency_path = tmp_path / "latencies.jsonl"
    run_dir = tmp_path / "raw" / "test-run"
    run_dir.mkdir(parents=True)

    config_path.write_text(
        json.dumps(_base_config(summary_path), indent=2) + "\n", encoding="utf-8"
    )
    meta_path.write_text(json.dumps({"started_at": "now"}) + "\n", encoding="utf-8")
    # Two trials, 5s wall-clock each → 10s total in the throughput denominator.
    latency_path.write_text(
        "\n".join(
            [
                json.dumps({"latency_seconds": 5.0}),
                json.dumps({"latency_seconds": 5.0}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    _write_trial(
        run_dir,
        name="2026-04-28_C_llama_agent_as_tool_optimized_scenA_run01.json",
        usage={
            "input_tokens": 100,
            "output_tokens": 200,
            "total_tokens": 300,
            "requests": 3,
        },
    )
    _write_trial(
        run_dir,
        name="2026-04-28_C_llama_agent_as_tool_optimized_scenA_run02.json",
        usage={
            "input_tokens": 150,
            "output_tokens": 250,
            "total_tokens": 400,
            "requests": 4,
        },
    )

    subprocess.run(
        [
            sys.executable,
            "-c",
            summary_py,
            str(summary_path),
            str(config_path),
            str(meta_path),
            str(latency_path),
            str(run_dir),
            "2",
            "0",
            "2",
            "0",
            "0",
        ],
        check=True,
    )

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["input_tokens_total"] == 250
    assert summary["output_tokens_total"] == 450
    assert summary["total_tokens_total"] == 700
    assert summary["tokens_usage_trial_count"] == 2
    # End-to-end agent throughput = output_tokens_total / wall_clock_seconds_total
    # = 450 / 10.0 = 45.0 tok/s. (Includes tool-call + MCP time in denominator
    # per Alex's review note — this is NOT pure model-decode tok/s.)
    assert summary["tokens_per_second_mean"] == 45.0


def test_summary_token_fields_null_when_no_trial_reports_usage(tmp_path):
    """Older trials predating the usage capture stay null in summary."""
    repo_root = Path(__file__).resolve().parent.parent
    summary_py = _extract_summary_python(repo_root)

    summary_path = tmp_path / "summary.json"
    config_path = tmp_path / "config.json"
    meta_path = tmp_path / "meta.json"
    latency_path = tmp_path / "latencies.jsonl"
    run_dir = tmp_path / "raw" / "test-run"
    run_dir.mkdir(parents=True)

    config_path.write_text(
        json.dumps(_base_config(summary_path), indent=2) + "\n", encoding="utf-8"
    )
    meta_path.write_text(json.dumps({"started_at": "now"}) + "\n", encoding="utf-8")
    latency_path.write_text(
        json.dumps({"latency_seconds": 1.0}) + "\n", encoding="utf-8"
    )
    # Trial omits usage entirely (older artifact shape).
    payload = {
        "question": "p",
        "answer": "a",
        "success": True,
        "max_turns_exhausted": False,
        "turn_count": 1,
        "tool_call_count": 0,
        "history": [],
        "runner_meta": {},
    }
    (run_dir / "2026-04-28_legacy_run01.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )

    subprocess.run(
        [
            sys.executable,
            "-c",
            summary_py,
            str(summary_path),
            str(config_path),
            str(meta_path),
            str(latency_path),
            str(run_dir),
            "1",
            "0",
            "1",
            "0",
            "0",
        ],
        check=True,
    )

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["input_tokens_total"] is None
    assert summary["output_tokens_total"] is None
    assert summary["total_tokens_total"] is None
    assert summary["tokens_per_second_mean"] is None
    assert summary["tokens_usage_trial_count"] == 0


def test_summary_records_resume_skip_and_rerun_counts(tmp_path):
    """Resume summaries expose skipped/rerun counts without changing pass math."""
    repo_root = Path(__file__).resolve().parent.parent
    summary_py = _extract_summary_python(repo_root)

    summary_path = tmp_path / "summary.json"
    config_path = tmp_path / "config.json"
    meta_path = tmp_path / "meta.json"
    latency_path = tmp_path / "latencies.jsonl"
    run_dir = tmp_path / "raw" / "test-run"
    run_dir.mkdir(parents=True)

    config_path.write_text(
        json.dumps(_base_config(summary_path), indent=2) + "\n",
        encoding="utf-8",
    )
    meta_path.write_text(json.dumps({"started_at": "now"}) + "\n", encoding="utf-8")
    latency_path.write_text("", encoding="utf-8")

    subprocess.run(
        [
            sys.executable,
            "-c",
            summary_py,
            str(summary_path),
            str(config_path),
            str(meta_path),
            str(latency_path),
            str(run_dir),
            "1",
            "2",
            "3",
            "2",
            "1",
        ],
        check=True,
    )

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    assert summary["scenarios_attempted"] == 3
    assert summary["scenarios_completed"] == 1
    assert summary["failure_count"] == 2
    assert summary["resume_skipped_count"] == 2
    assert summary["resume_rerun_count"] == 1
    assert summary["run_status"] == "partial"
    assert meta["resume_skipped_count"] == 2
    assert meta["resume_rerun_count"] == 1
