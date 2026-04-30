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
        ],
        check=True,
    )

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    assert summary["wall_clock_seconds_total"] == 2.0
    assert summary["mcp_setup_seconds"] is None
    assert meta["mcp_setup_seconds"] is None
