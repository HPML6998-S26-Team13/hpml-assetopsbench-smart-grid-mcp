# Judge Output Schema

*Schema version: v1. Owner: Akshat (issue #17).*

Defines the fields written to `results/metrics/scenario_scores.jsonl` by
`scripts/judge_trajectory.py`. Each line is one JSON object (newline-delimited
JSON / JSONL) representing one judge evaluation of one scenario-trial.

## Six Rubric Dimensions

From the AssetOpsBench paper (evaluation_agent rubric). All dimensions are
boolean. For `dim_hallucinations`, **False = good** (no hallucinations detected).

| Field | Type | Good value | Meaning |
|---|---|---|---|
| `dim_task_completion` | bool | `true` | Agent executed all required actions for the task |
| `dim_data_retrieval_accuracy` | bool | `true` | Correct asset, sensor, time window, and units used |
| `dim_generalized_result_verification` | bool | `true` | Task-type-specific output is correct (forecast / anomaly / classification) |
| `dim_agent_sequence_correct` | bool | `true` | Tools / agents invoked in the right order |
| `dim_clarity_and_justification` | bool | `true` | Answer is clear, reasoned, and internally consistent |
| `dim_hallucinations` | bool | `false` | No fabricated tool calls, data, or success claims detected |

### Mapping to WandB dimension-level fields

When aggregating across a run, map per-scenario booleans to the WandB
`judge_dim_*_mean` fields defined in `docs/wandb_schema.md`:

| Scenario field | WandB run-level field |
|---|---|
| `dim_task_completion` | `judge_dim_task_completion_mean` |
| `dim_data_retrieval_accuracy` | `judge_dim_correctness_mean` |
| `dim_generalized_result_verification` | `judge_dim_correctness_mean` (averaged together) |
| `dim_agent_sequence_correct` | `judge_dim_tool_usage_mean` |
| `dim_clarity_and_justification` | `judge_dim_efficiency_mean` |
| `dim_hallucinations` (inverted) | `judge_dim_grounding_mean` |

## Derived Score

```
score_6d = (task_completion + data_retrieval_accuracy + generalized_result_verification
            + agent_sequence_correct + clarity_and_justification + (NOT hallucinations)) / 6
```

Range: [0.0, 1.0]. Default pass threshold: 0.6 (4 out of 6 dimensions good).

## Full Field Reference

| Field | Type | Notes |
|---|---|---|
| `schema_version` | string | Always `"v1"` |
| `scored_at` | ISO 8601 string | UTC timestamp when judge was called |
| `run_name` | string | Join key — matches `benchmarks/<cell>/config.json` `run_name` |
| `wandb_run_url` | string or null | WandB run URL if available |
| `scenario_id` | string | `id` field from scenario JSON (e.g. `AOB-FMSR-001`) |
| `scenario_file` | string | Repo-relative path to scenario JSON |
| `trial_index` | integer | 1-indexed trial number within the run |
| `experiment_cell` | string | The experiment cell. Initial 5-cell vocabulary was `A`, `B`, `C`, `Y`, `Z`; post-PR175 evidence adds `D`, `YS`, `ZS`, `ZSD`, `Y/YS/Z/ZS-TP`, and the `*70B` hosted-WatsonX variants. See `results/metrics/evidence_registry.csv` for the authoritative list of paper-eligible cells. |
| `orchestration_mode` | string | `plan_execute`, `agent_as_tool`, `hybrid` |
| `mcp_mode` | string | `baseline`, `optimized`, `direct` |
| `model_id` | string | Model that produced the trajectory |
| `judge_model` | string | Model used to score (e.g. `watsonx/meta-llama/llama-4-maverick-17b-128e-instruct-fp8`) |
| `dim_task_completion` | bool | Rubric dimension 1 |
| `dim_data_retrieval_accuracy` | bool | Rubric dimension 2 |
| `dim_generalized_result_verification` | bool | Rubric dimension 3 |
| `dim_agent_sequence_correct` | bool | Rubric dimension 4 |
| `dim_clarity_and_justification` | bool | Rubric dimension 5 |
| `dim_hallucinations` | bool | Rubric dimension 6 (False = good) |
| `score_6d` | float [0,1] | Aggregate score across all 6 dimensions |
| `pass_threshold` | float | Threshold used to determine `pass` |
| `pass` | bool | `score_6d >= pass_threshold` |
| `suggestions` | string | Judge's actionable feedback, or empty string |
| `trajectory_file` | string | Path to the source trajectory JSON |

When `scripts/judge_trajectory.py` is run with `--log-dir`, full prompt /
response audit logs are written per scored trial at
`results/judge_logs/<run_name>/<scenario_id>_runNN_judge_log.json`. The JSONL
file remains the canonical aggregate table; the audit logs are reproducibility
evidence for individual calls.

## Judge Model

Default: `watsonx/meta-llama/llama-4-maverick-17b-128e-instruct-fp8`

Override with `--judge-model` flag. Must be accessible via LiteLLM with the
standard WatsonX environment variables (`WATSONX_APIKEY`, `WATSONX_PROJECT_ID`).

## Usage

```bash
# Score a single trajectory (from AssetOpsBench repo root or with AssetOpsBench venv active)
python ../hpml-assetopsbench-smart-grid-mcp/scripts/judge_trajectory.py \
    --trajectory benchmarks/cell_Y_plan_execute/raw/<run>/foo.json \
    --scenario   ../hpml-assetopsbench-smart-grid-mcp/data/scenarios/aob_fmsr_01_list_failure_modes.json \
    --run-meta   benchmarks/cell_Y_plan_execute/raw/<run>/meta.json \
    --out        ../hpml-assetopsbench-smart-grid-mcp/results/metrics/scenario_scores.jsonl
```
