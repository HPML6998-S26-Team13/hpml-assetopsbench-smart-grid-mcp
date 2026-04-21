from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from orchestration_utils import (  # noqa: E402
    available_sensor_ids,
    build_planner_descriptions,
    build_planning_question,
    canonicalize_step_result,
    compact_step_for_context,
    compact_verifier_result,
    SelfAskDecision,
    VerificationDecision,
    build_retry_question,
    build_suffix_replan_question,
    effective_server_paths,
    generate_suffix_plan,
    maybe_self_ask,
    normalize_plan_steps,
    normalize_response_text,
    parse_json_object,
    preflight_aob_runtime_dependencies,
    repair_sensor_task_text,
    response_error_payload,
    serialize_step_result,
    should_skip_invalid_sensor_step,
    summarize_answer,
    summarize_terminal_failures,
    tool_schema_for_step,
    verify_step,
)


class DummyLLM:
    def __init__(self, responses):
        self._responses = list(responses)
        self.prompts = []

    def generate(self, prompt: str, **_kwargs) -> str:
        self.prompts.append(prompt)
        if not self._responses:
            raise AssertionError(f"No response left for prompt: {prompt[:120]}")
        return self._responses.pop(0)


class OrchestrationUtilsTests(unittest.TestCase):
    def test_build_planning_question_appends_guardrails(self):
        question = build_planning_question("Investigate transformer T-015.")
        self.assertIn("Use only these real servers", question)
        self.assertIn("get_dga_record and analyze_dga are FMSR tools", question)

    def test_build_planner_descriptions_adds_repo_specific_notes(self):
        descriptions = {
            "fmsr": "  - get_dga_record(transformer_id: string): Retrieve DGA"
        }
        tool_catalog = {
            "fmsr": {
                "get_dga_record": {
                    "description": "Retrieve DGA",
                    "schema": "transformer_id: string (transformer id like T-015)",
                }
            }
        }
        rendered = build_planner_descriptions(descriptions, tool_catalog)["fmsr"]
        self.assertIn("Planner notes:", rendered)
        self.assertIn("get_sensor_correlation only", rendered)
        self.assertIn("Canonical tool signatures:", rendered)

    def test_normalize_plan_steps_reroutes_unique_tool_server(self):
        class Step:
            def __init__(self, step_number, task, server, tool, dependencies=None):
                self.step_number = step_number
                self.task = task
                self.server = server
                self.tool = tool
                self.tool_args = {}
                self.dependencies = dependencies or []
                self.expected_output = ""

        class Plan:
            def __init__(self, steps):
                self.steps = steps

        plan = Plan(
            [
                Step(1, "Fetch the latest DGA record", "iot", "get_dga_record"),
                Step(2, "Analyze the gases", "iot", "analyze_dga", [1]),
            ]
        )
        tool_catalog = {
            "iot": {"get_asset_metadata": {"description": "", "schema": ""}},
            "fmsr": {
                "get_dga_record": {"description": "", "schema": ""},
                "analyze_dga": {"description": "", "schema": ""},
            },
        }
        warnings = normalize_plan_steps(plan, tool_catalog)
        self.assertEqual(plan.steps[0].server, "fmsr")
        self.assertEqual(plan.steps[1].server, "fmsr")
        self.assertEqual(plan.steps[1].dependencies, [1])
        self.assertTrue(any("Rerouted step 1" in warning for warning in warnings))

    def test_normalize_plan_steps_drops_terminal_none_step(self):
        class Step:
            def __init__(self, step_number, task, server, tool, dependencies=None):
                self.step_number = step_number
                self.task = task
                self.server = server
                self.tool = tool
                self.tool_args = {}
                self.dependencies = dependencies or []
                self.expected_output = ""

        class Plan:
            def __init__(self, steps):
                self.steps = steps

        plan = Plan(
            [
                Step(1, "Fetch DGA record", "fmsr", "get_dga_record"),
                Step(2, "Summarize findings", "none", "none", [1]),
            ]
        )
        tool_catalog = {"fmsr": {"get_dga_record": {"description": "", "schema": ""}}}
        warnings = normalize_plan_steps(plan, tool_catalog)
        self.assertEqual(len(plan.steps), 1)
        self.assertEqual(plan.steps[0].step_number, 1)
        self.assertTrue(
            any(
                "Dropped terminal synthesis-only step" in warning
                for warning in warnings
            )
        )

    def test_tool_schema_for_step_uses_hintful_schema(self):
        tool_catalog = {
            "fmsr": {
                "get_sensor_correlation": {
                    "description": "",
                    "schema": "failure_mode_id: string (failure mode id like FM-006; not a transformer id)",
                }
            }
        }
        schema = tool_schema_for_step(tool_catalog, "fmsr", "get_sensor_correlation")
        self.assertIn("FM-006", schema)
        self.assertIn("not a transformer id", schema)

    def test_normalize_response_text_wraps_newline_json_objects_into_list(self):
        response = '{"sensor_id":"load_current_a"}\n{"sensor_id":"winding_temp_top_c"}'
        normalized = normalize_response_text(response)
        self.assertIn("[", normalized)
        self.assertIn("winding_temp_top_c", normalized)

    def test_available_sensor_ids_reads_list_sensors_context(self):
        class Result:
            tool = "list_sensors"
            response = (
                '[{"sensor_id":"load_current_a"},{"sensor_id":"winding_temp_top_c"}]'
            )

        sensors = available_sensor_ids({3: Result()})
        self.assertEqual(sensors, {"load_current_a", "winding_temp_top_c"})

    def test_repair_sensor_task_text_rewrites_known_alias(self):
        task, warning = repair_sensor_task_text(
            "Compute the trend of the winding_temp_c sensor readings.",
            {"winding_temp_top_c", "oil_temp_c"},
        )
        self.assertIn("winding_temp_top_c", task)
        self.assertIn("winding_temp_c -> winding_temp_top_c", warning)

    def test_should_skip_invalid_sensor_step_for_iot_dga_lookup(self):
        class Step:
            tool = "get_sensor_readings"
            task = "Get time-series readings for sensor dga_h2_ppm on transformer T-015"

        should_skip, reason = should_skip_invalid_sensor_step(
            Step(), {"load_current_a", "winding_temp_top_c"}
        )
        self.assertTrue(should_skip)
        self.assertIn("DGA data in this repo comes from FMSR", reason)

    def test_canonicalize_step_result_normalizes_response(self):
        class Result:
            response = (
                '{"sensor_id":"load_current_a"}\n{"sensor_id":"winding_temp_top_c"}'
            )

        result = Result()
        canonicalize_step_result(result)
        self.assertIn("[", result.response)
        self.assertIn("winding_temp_top_c", result.response)

    def test_compact_step_for_context_truncates_large_response_and_error(self):
        class Result:
            response = "A" * 3000
            error = "B" * 1200

        result = Result()
        compact_step_for_context(result)
        self.assertIn("[truncated", result.response)
        self.assertIn("[truncated", result.error)
        self.assertLess(len(result.response), 1400)
        self.assertLess(len(result.error), 800)

    def test_compact_verifier_result_truncates_large_response(self):
        compacted = compact_verifier_result(
            {
                "step": 4,
                "task": "Get sensor readings",
                "server": "iot",
                "tool": "get_sensor_readings",
                "success": True,
                "response": "A" * 3000,
                "error": None,
            }
        )
        self.assertIn("[truncated", compacted["response"])
        self.assertLess(len(compacted["response"]), 1400)

    def test_parse_json_object_handles_markdown_fence(self):
        raw = '```json\n{"decision": "continue", "reason": "looks good"}\n```'
        payload = parse_json_object(raw)
        self.assertEqual(payload["decision"], "continue")

    def test_parse_json_object_preserves_json_substring_in_payload(self):
        raw = '```json\n{"name": "json_value"}\n```'
        payload = parse_json_object(raw)
        self.assertEqual(payload["name"], "json_value")

    def test_response_error_payload_detects_top_level_json_error(self):
        self.assertEqual(
            response_error_payload('{"error": "Failure mode not found."}'),
            "Failure mode not found.",
        )
        self.assertIsNone(response_error_payload('{"result": "ok"}'))

    def test_response_error_payload_detects_list_wrapped_error(self):
        self.assertEqual(
            response_error_payload([{"error": "No sensor data found for 'T-020'."}]),
            "No sensor data found for 'T-020'.",
        )

    def test_response_error_payload_detects_unknown_tool_string(self):
        self.assertEqual(
            response_error_payload("Unknown tool: get_dga_record"),
            "Unknown tool: get_dga_record",
        )

    def test_serialize_step_result_marks_json_error_payload_as_failure(self):
        class Result:
            step_number = 4
            task = "Infer probable fault mode"
            server = "fmsr"
            tool = "get_sensor_correlation"
            tool_args = {"failure_mode_id": "T-015"}
            response = '{"error": "Failure mode \\"T-015\\" not found."}'
            error = None
            success = True

        payload = serialize_step_result(Result())
        self.assertFalse(payload["success"])
        self.assertTrue(payload["executor_success"])
        self.assertEqual(payload["error"], 'Failure mode "T-015" not found.')

    def test_serialize_step_result_marks_unknown_tool_string_as_failure(self):
        class Result:
            step_number = 1
            task = "Get DGA record"
            server = "iot"
            tool = "get_dga_record"
            tool_args = {"transformer_id": "T-020"}
            response = "Unknown tool: get_dga_record"
            error = None
            success = True

        payload = serialize_step_result(Result())
        self.assertFalse(payload["success"])
        self.assertTrue(payload["executor_success"])
        self.assertEqual(payload["error"], "Unknown tool: get_dga_record")

    def test_serialize_step_result_carries_runner_repair_metadata(self):
        class Result:
            step_number = 2
            task = "Inspect DGA sensor"
            server = "iot"
            tool = "get_sensor_readings"
            tool_args = {"sensor_id": "dga_h2_ppm"}
            response = "Skipped invalid IoT DGA lookup."
            error = None
            success = True
            runner_repair = "invalid_iot_dga_sensor_lookup"
            runner_repair_reason = "Use FMSR DGA tools instead."

        payload = serialize_step_result(Result())
        self.assertTrue(payload["success"])
        self.assertEqual(payload["runner_repair"], "invalid_iot_dga_sensor_lookup")
        self.assertEqual(payload["runner_repair_reason"], "Use FMSR DGA tools instead.")

    def test_maybe_self_ask_defaults_to_original_question_when_false(self):
        llm = DummyLLM(
            [
                '{"needs_self_ask": false, "clarifying_questions": [], "assumptions": [], "augmented_question": "ignored"}'
            ]
        )
        decision = maybe_self_ask("What failed at site MAIN?", llm)
        self.assertEqual(
            decision,
            SelfAskDecision(
                needs_self_ask=False,
                clarifying_questions=[],
                assumptions=[],
                augmented_question="What failed at site MAIN?",
            ),
        )

    def test_maybe_self_ask_constructs_augmented_question_when_missing(self):
        llm = DummyLLM(
            [
                '{"needs_self_ask": true, "clarifying_questions": ["Which transformer?"], "assumptions": ["Use the most recent incident"], "augmented_question": ""}'
            ]
        )
        decision = maybe_self_ask("Investigate the overheating alert.", llm)
        self.assertTrue(decision.needs_self_ask)
        self.assertIn("Which transformer?", decision.augmented_question)
        self.assertIn("Use the most recent incident", decision.augmented_question)

    def test_build_suffix_replan_question_includes_focus_and_remaining_steps(self):
        class Step:
            def __init__(self, step_number, task, server, tool):
                self.step_number = step_number
                self.task = task
                self.server = server
                self.tool = tool

        history = [
            {
                "step": 1,
                "task": "Find the transformer",
                "server": "iot",
                "tool": "get_asset_metadata",
                "response": "Transformer is T-015.",
                "error": None,
                "success": True,
            }
        ]
        remaining = [Step(2, "Fetch DGA record", "fmsr", "get_dga_record")]
        question = build_suffix_replan_question(
            "Investigate T-015.",
            "Investigate T-015.",
            history,
            remaining,
            VerificationDecision(
                decision="replan_suffix",
                reason="The investigation should pivot to thermal fault confirmation.",
                updated_focus="Confirm the thermal fault before creating the work order.",
            ),
        )
        self.assertIn("thermal fault", question)
        self.assertIn("Fetch DGA record", question)
        self.assertIn("Dependency1: None", question)
        self.assertIn("never on completed steps", question)

    def test_build_retry_question_includes_previous_attempt_and_reason(self):
        class Step:
            def __init__(self, step_number, task):
                self.step_number = step_number
                self.task = task

        question = build_retry_question(
            "Investigate T-015.",
            "Investigate T-015 with internal clarifications.",
            Step(2, "Fetch DGA record"),
            {"response": "Returned the wrong asset record."},
            VerificationDecision(
                decision="retry",
                reason="The tool arguments targeted the wrong asset.",
                updated_focus="Use the transformer identified in step 1.",
            ),
            retries_used=1,
        )
        self.assertIn("wrong asset", question)
        self.assertIn("Retry attempt number: 1", question)
        self.assertIn("step 1", question.lower())

    def test_summarize_answer_uses_only_terminal_history_entries(self):
        llm = DummyLLM(["Final answer."])
        answer = summarize_answer(
            "What happened?",
            [
                {
                    "step": 1,
                    "task": "Lookup alert",
                    "server": "iot",
                    "response": "Old retry response",
                    "error": None,
                    "success": True,
                },
                {
                    "step": 1,
                    "task": "Lookup alert",
                    "server": "iot",
                    "response": "Final step 1 response",
                    "error": None,
                    "success": True,
                },
                {
                    "step": 2,
                    "task": "Create WO",
                    "server": "wo",
                    "response": "WO created",
                    "error": None,
                    "success": True,
                },
            ],
            llm,
        )
        self.assertEqual(answer, "Final answer.")
        self.assertIn("Final step 1 response", llm.prompts[0])
        self.assertNotIn("Old retry response", llm.prompts[0])

    def test_summarize_answer_falls_back_when_llm_raises(self):
        class BrokenLLM:
            def generate(self, _prompt: str, **_kwargs) -> str:
                raise RuntimeError("context window exceeded")

        with self.assertLogs("orchestration_utils", level="WARNING") as logs:
            answer = summarize_answer(
                "What happened?",
                [
                    {
                        "step": 1,
                        "task": "Get readings",
                        "server": "iot",
                        "tool": "get_sensor_readings",
                        "response": "A" * 2000,
                        "error": None,
                        "success": True,
                    },
                    {
                        "step": 2,
                        "task": "Create WO",
                        "server": "wo",
                        "tool": "create_work_order",
                        "response": None,
                        "error": "could not create",
                        "success": False,
                    },
                ],
                BrokenLLM(),
            )
        self.assertIn("Compact terminal results", answer)
        self.assertIn("create_work_order", answer)
        self.assertTrue(any("summarization failed" in line for line in logs.output))

    def test_summarize_terminal_failures_only_keeps_terminal_failed_steps(self):
        failures = summarize_terminal_failures(
            [
                {
                    "step": 1,
                    "task": "Lookup alert",
                    "server": "iot",
                    "tool": "get_alert",
                    "error": "transient failure",
                    "success": False,
                },
                {
                    "step": 1,
                    "task": "Lookup alert",
                    "server": "iot",
                    "tool": "get_alert",
                    "error": None,
                    "success": True,
                },
                {
                    "step": 2,
                    "task": "Create WO",
                    "server": "wo",
                    "tool": "create_work_order",
                    "error": "Unknown server",
                    "success": False,
                    "verifier_decision": "error",
                },
            ]
        )
        self.assertEqual(
            failures,
            [
                {
                    "step": 2,
                    "task": "Create WO",
                    "server": "wo",
                    "tool": "create_work_order",
                    "error": "Unknown server",
                    "verifier_decision": "error",
                }
            ],
        )

    def test_generate_suffix_plan_returns_warning_payload_on_invalid_plan(self):
        class DummyPlanner:
            def generate_plan(self, _question, _descriptions):
                raise ValueError("Invalid dependency reference for step 1: #S1")

        with self.assertLogs("orchestration_utils", level="WARNING") as logs:
            plan, error = generate_suffix_plan(
                DummyPlanner(),
                "Replan only the suffix.",
                {"iot": "list_sensors"},
            )
        self.assertIsNone(plan)
        self.assertEqual(error, "Invalid dependency reference for step 1: #S1")
        self.assertIn(
            "continuing with the original remaining plan", "\n".join(logs.output)
        )

    def test_verify_step_warns_and_falls_back_when_json_missing(self):
        class Step:
            def __init__(self):
                self.step_number = 2
                self.task = "Fetch DGA record"
                self.server = "fmsr"
                self.tool = "get_dga_record"

        llm = DummyLLM(["not json at all"])
        with self.assertLogs("orchestration_utils", level="WARNING") as logs:
            decision = verify_step(
                "Investigate T-015.",
                "Investigate T-015.",
                Step(),
                {"response": "Some result", "success": True},
                [],
                [],
                llm,
            )
        self.assertEqual(decision.decision, "continue")
        self.assertTrue(any("no parseable JSON" in line for line in logs.output))

    def test_verify_step_warns_and_falls_back_when_decision_unknown(self):
        class Step:
            def __init__(self):
                self.step_number = 2
                self.task = "Fetch DGA record"
                self.server = "fmsr"
                self.tool = "get_dga_record"

        llm = DummyLLM(
            [
                '{"decision": "repair_everything", "reason": "nonsense", "updated_focus": ""}'
            ]
        )
        with self.assertLogs("orchestration_utils", level="WARNING") as logs:
            decision = verify_step(
                "Investigate T-015.",
                "Investigate T-015.",
                Step(),
                {"response": "Some result", "success": True},
                [],
                [],
                llm,
            )
        self.assertEqual(decision.decision, "continue")
        self.assertTrue(any("unknown decision" in line for line in logs.output))

    def test_verify_step_warns_and_falls_back_when_llm_raises(self):
        class Step:
            def __init__(self):
                self.step_number = 4
                self.task = "Get sensor readings"
                self.server = "iot"
                self.tool = "get_sensor_readings"

        class BrokenLLM:
            def generate(self, _prompt: str, **_kwargs) -> str:
                raise RuntimeError("context window exceeded")

        with self.assertLogs("orchestration_utils", level="WARNING") as logs:
            decision = verify_step(
                "Investigate T-015.",
                "Investigate T-015.",
                Step(),
                {"response": "A" * 5000, "success": True},
                [],
                [],
                BrokenLLM(),
            )
        self.assertEqual(decision.decision, "continue")
        self.assertTrue(any("Verifier failed" in line for line in logs.output))

    def test_effective_server_paths_exits_cleanly_on_bad_override(self):
        with self.assertRaises(SystemExit) as exc:
            effective_server_paths(["bad-entry"], REPO_ROOT)
        self.assertIn("Invalid --server entry", str(exc.exception))

    def test_preflight_aob_runtime_dependencies_reports_missing_modules(self):
        def fake_import_module(name: str):
            if name == "litellm":
                raise ModuleNotFoundError("No module named 'litellm'")
            return object()

        with patch(
            "orchestration_utils.importlib.import_module",
            side_effect=fake_import_module,
        ):
            with self.assertRaises(RuntimeError) as exc:
                preflight_aob_runtime_dependencies()
        self.assertIn("litellm", str(exc.exception))
        self.assertIn("requirements-insomnia.txt", str(exc.exception))


if __name__ == "__main__":
    unittest.main()
