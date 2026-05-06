"""Text guardrails for shell-runner wiring that is awkward to unit-test live."""

from __future__ import annotations

from pathlib import Path


def _function_body(script: str, start_marker: str, end_marker: str) -> str:
    start = script.index(start_marker)
    end = script.index(end_marker, start)
    return script[start:end]


def test_per_trial_aat_exports_mcp_server_environment() -> None:
    script = Path("scripts/run_experiment.sh").read_text(encoding="utf-8")
    body = _function_body(
        script,
        "run_agent_as_tool_trial()",
        "run_agent_as_tool_batch()",
    )

    export_line = (
        "export AAT_MCP_SERVER_PYTHON AAT_MCP_SERVER_LAUNCH_MODE "
        "AAT_MCP_CLIENT_TIMEOUT_SECONDS"
    )
    invocation = '(cd "$REPO_ROOT" && "${cmd[@]}")'
    assert export_line in body
    assert body.index(export_line) < body.index(invocation)


def test_aat_batch_infrastructure_failures_are_not_masked() -> None:
    script = Path("scripts/run_experiment.sh").read_text(encoding="utf-8")
    body = _function_body(
        script,
        'if [ "$ORCHESTRATION" = "agent_as_tool" ]',
        "else\n\nfor SCENARIO_FILE",
    )

    assert 'run_agent_as_tool_batch "$RUN_DIR" || true' not in body
    assert "BATCH_RC=0" in body
    assert "BATCH_RC=$?" in body
    assert "INFRA_FAIL=1" in body
    assert "Infrastructure failure detected; exiting nonzero." in script


def test_gcp_batch_driver_hard_fails_incomplete_artifacts() -> None:
    script = Path("scripts/run_gcp_context_batch.sh").read_text(encoding="utf-8")

    assert "validate-run-shell" in script
    assert "incomplete trajectory artifacts" in script
    assert 'status="artifact_failed"' in script
    assert 'existing_status" = "complete"' in script
    assert "SMARTGRID_SKIP_LOCAL_MODEL_PREFLIGHT" in script


def test_plan_execute_repo_local_keeps_smartgrid_server_overrides() -> None:
    script = Path("scripts/run_experiment.sh").read_text(encoding="utf-8")
    body = _function_body(
        script,
        "run_plan_execute_trial()",
        "run_json_stdout_trial()",
    )

    assert 'PLAN_EXECUTE_REPO_LOCAL="${PLAN_EXECUTE_REPO_LOCAL:-}"' in script
    assert '[ "$ORCHESTRATION" = "plan_execute" ]' in script
    assert '[ "$ENABLE_SMARTGRID_SERVERS" = "1" ]' in script
    assert "PLAN_EXECUTE_REPO_LOCAL=1" in script
    assert '[ "${PLAN_EXECUTE_REPO_LOCAL:-0}" = "1" ]' in body
    assert "wrapper_cmd+=(--disable-self-ask)" in body
    assert 'wrapper_cmd+=("${SERVER_ARGS[@]}")' in body

    upstream_cli = body.split("local -a cmd=(uv run plan-execute", 1)[1]
    assert 'cmd+=("${SERVER_ARGS[@]}")' not in upstream_cli


def test_repo_local_pe_runner_can_disable_self_ask() -> None:
    runner = Path("scripts/plan_execute_self_ask_runner.py").read_text(encoding="utf-8")

    assert '"--disable-self-ask"' in runner
    assert "if args.disable_self_ask" in runner
    assert "augmented_question=args.question" in runner
