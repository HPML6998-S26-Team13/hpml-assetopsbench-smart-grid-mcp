# WandB Metrics Schema

*Created: 2026-04-10*
*Last updated: 2026-04-10*

*Owner: Alex (`#14`)*

Canonical schema for experiment tracking in the org repo. This doc defines what
`#61` should emit in code and what `#21` / `#28` should prove with the first
real logged runs.

## Scope

This schema covers the shared metadata and metrics for:
- benchmark cells in `benchmarks/`
- end-to-end scenario runs and trajectories
- LLM-as-Judge scoring outputs
- exported reproducibility artifacts in `results/`

The goal is not to log every raw token or event to WandB. The goal is to make
every run attributable, comparable, and reproducible across:
- orchestration condition
- MCP mode
- model / serving stack
- scenario set
- hardware / host
- git revision

## Canonical run structure

Each WandB run should represent one experiment execution under one config. That
execution may contain multiple scenarios and multiple trials.

One run should map cleanly back to:
- one benchmark config file
- one git SHA
- one model / serving stack
- one orchestration condition
- one MCP condition
- one hardware environment

## Initialization order

`wandb_run_url` cannot be populated until after `wandb.init()` returns. The
intended pattern for `#61` is:

1. build the pre-init config dict with every other required field, including `benchmark_summary_path` if the benchmark directory layout is already deterministic from the config
2. call `run = wandb.init(...)`
3. patch `wandb_run_url` into `wandb.config`
4. retroactively patch the benchmark `config.json` and later `summary.json` with
   that URL before committing reproducibility artifacts

This avoids the chicken-and-egg problem where the run URL is required for
artifact linkage but only exists after the WandB run is live.

## Required WandB config fields

These fields should be written into `wandb.config` for every tracked run.

### Identity and reproducibility

| Field | Type | Required | Notes |
|---|---|---|---|
| `schema_version` | string | yes | Start with `v1` so future notebook logic can branch cleanly if needed |
| `wandb_entity` | string | yes | Team / org slug used in the run URL; full run URL should follow `https://wandb.ai/<wandb_entity>/<project_name>/runs/<run_id>` |
| `project_name` | string | yes | Expected value: `assetopsbench-smartgrid` |
| `run_name` | string | yes | Human-readable unique run name |
| `git_sha` | string | yes | Full SHA preferred for reproducibility; short SHA is acceptable only for temporary smoke runs |
| `git_branch` | string | recommended | Helpful during active development |
| `run_timestamp` | string | yes | ISO 8601 timestamp |
| `benchmark_config_path` | string | yes | Repo-relative path to the config that launched the run |
| `benchmark_summary_path` | string | yes | Repo-relative path once generated; this should be populated before the run is treated as reproducible and committed |
| `wandb_run_url` | string | yes | Required, but only available after `wandb.init()` returns; write the rest of config first, then patch this field with `wandb.config.update(...)` |

### Experiment design

| Field | Type | Required | Notes |
|---|---|---|---|
| `experiment_family` | string | yes | Primary experiment family for the run: `exp1_mcp_overhead`, `exp2_orchestration`, `smoke`, or similar. For shared Cell B runs, use `exp1_mcp_overhead` here and record the dual-use explicitly in `contributing_experiments` and tags |
| `contributing_experiments` | list[string] | recommended | Use this when one run contributes to multiple analyses; Cell B should list both `exp1_mcp_overhead` and `exp2_orchestration` |
| `experiment_cell` | string | yes | Example: `A`, `B`, `C`, `Y`, `Z` |
| `orchestration_mode` | string | yes | `aat`, `plan_execute`, `hybrid`, or `none` for infrastructure-only smoke runs |
| `mcp_mode` | string | yes | `direct`, `baseline`, `optimized`, or `none` |
| `trial_count` | integer | yes | Number of repeated trials in the run |
| `scenario_count` | integer | yes | Number of scenarios attempted |
| `scenario_set_name` | string | yes | Example: `smartgrid_v1` |
| `scenario_set_hash` | string | yes | Compute as SHA-256 of the newline-joined lowercase hex-encoded per-file SHA-256 digests of the repo-relative scenario file paths sorted lexicographically, where each file is first canonicalized as UTF-8 JSON with sorted keys, no extra whitespace between elements, and normalized `\\n` line endings |
| `scenario_domain_scope` | string | recommended | `single_domain`, `multi_domain`, or mixed summary |
| `judge_model` | string | recommended | Example: `maverick-17b` when scoring is enabled |
| `judge_pass_threshold` | number | recommended | Required whenever `judge_pass_rate` is logged so pass/fail is comparable across runs |

### Model and serving stack

| Field | Type | Required | Notes |
|---|---|---|---|
| `model_id` | string | yes | Example: `meta-llama/Llama-3.1-8B-Instruct` |
| `model_provider` | string | yes | Example: `vllm`, `watsonx`, `openai` |
| `serving_stack` | string | yes | Example: `insomnia_vllm`, `watsonx_api` |
| `quantization_mode` | string | recommended | Example: `fp16`, `int8`, `none` |
| `context_window` | integer | recommended | Effective max context used for the run |
| `temperature` | number | recommended | Log explicit inference settings when controlled |
| `max_tokens` | integer | recommended | Output cap used for the run |

### Hardware and runtime environment

| Field | Type | Required | Notes |
|---|---|---|---|
| `host_name` | string | yes | Example: `insomnia-a6000-01` |
| `compute_env` | string | yes | Example: `insomnia`, `gcp`, `local` |
| `gpu_type` | string | yes | Example: `A6000`, `A100`, `none` |
| `gpu_count` | integer | yes | Usually `1` for current runs |
| `runtime_owner` | string | recommended | Who launched the run |
| `slurm_job_id` | string | recommended | Required when submitted through Slurm |

## Required WandB summary metrics

These fields should be written into `wandb.summary` once the run completes.

### Run outcome

| Field | Type | Required | Notes |
|---|---|---|---|
| `run_status` | string | yes | `success`, `partial`, `failed` |
| `scenarios_attempted` | integer | yes | Count attempted |
| `scenarios_completed` | integer | yes | Count completed without an unhandled exception; judge outcome does not affect this field |
| `success_rate` | number | yes | `scenarios_completed / scenarios_attempted`; this is operational completion rate, not judge pass rate |
| `failure_count` | integer | yes | Count of failed scenario executions |

### Latency and throughput

| Field | Type | Required | Notes |
|---|---|---|---|
| `wall_clock_seconds_total` | number | yes | Total runtime for the whole run |
| `latency_seconds_mean` | number | yes | Mean end-to-end latency per scenario-trial |
| `latency_seconds_p50` | number | yes | Median |
| `latency_seconds_p95` | number | yes | Tail latency |
| `tokens_per_second_mean` | number | recommended | For inference / throughput comparisons |

### Token usage

| Field | Type | Required | Notes |
|---|---|---|---|
| `input_tokens_total` | integer | recommended | Across the full run |
| `output_tokens_total` | integer | recommended | Across the full run |
| `tool_call_count_total` | integer | recommended | Across the full run |
| `tool_call_count_mean` | number | recommended | Per scenario-trial average |

### MCP / tool metrics

| Field | Type | Required | Notes |
|---|---|---|---|
| `mcp_latency_seconds_mean` | number | required for `mcp_mode=baseline` or `mcp_mode=optimized` runs | Mean end-to-end MCP call time from client dispatch to client receipt |
| `mcp_latency_seconds_p95` | number | required for `mcp_mode=baseline` or `mcp_mode=optimized` runs | Tail end-to-end MCP call latency |
| `tool_latency_seconds_mean` | number | required for `mcp_mode=baseline` or `mcp_mode=optimized` runs | Mean server-side tool handler execution time inside the MCP server |
| `tool_error_count` | integer | recommended | Contract / execution failures |

For Experiment 1 analysis:
- `mcp_latency_seconds_*` measures end-to-end MCP call time, including protocol and tool execution
- `tool_latency_seconds_mean` measures tool handler execution time only
- MCP protocol overhead can then be estimated as `mcp_latency_seconds_mean - tool_latency_seconds_mean`

### Judge metrics

| Field | Type | Required | Notes |
|---|---|---|---|
| `judge_score_mean` | number | required when scoring enabled | Aggregate average score |
| `judge_score_p50` | number | recommended | Median judge score |
| `judge_score_p95` | number | recommended | Upper tail of quality scores; useful but not the failure tail |
| `judge_score_p5` | number | recommended | Lower failure-tail summary for weak trajectories |
| `judge_pass_rate` | number | recommended | Fraction above `judge_pass_threshold`; only log when that threshold is explicitly set for the run |

### Dimension-level judge metrics

When the 6-dimension judge path is enabled, log the fields below. This path is
considered enabled when `judge_model` is set and the judge returns a structured
rubric response with per-dimension outputs.

| Field | Type | Required | Notes |
|---|---|---|---|
| `judge_dim_task_completion_mean` | number | recommended | |
| `judge_dim_correctness_mean` | number | recommended | |
| `judge_dim_tool_usage_mean` | number | recommended | |
| `judge_dim_grounding_mean` | number | recommended | |
| `judge_dim_efficiency_mean` | number | recommended | |
| `judge_dim_safety_mean` | number | recommended | |

## Required artifacts and file back-references

WandB should not be the only source of truth. Each run must still have durable
repo artifacts or exportable artifacts.

### Benchmark config linkage

Each benchmark `config.json` should include:
- `schema_version`
- `wandb_entity`
- `benchmark_summary_path`
- `model_id`
- `scenario_set_name`
- `scenario_set_hash`
- `experiment_family`
- `contributing_experiments` when applicable
- `experiment_cell`
- `orchestration_mode`
- `mcp_mode`
- `git_sha`
- `host_name`
- `gpu_type`
- `wandb_run_url`

`config.json` is typically written before the run starts, so the harness should
patch in `wandb_run_url` after `wandb.init()` succeeds.

### Benchmark summary linkage

Each benchmark `summary.json` should include:
- the same identifying config fields needed for reproducibility, especially `schema_version`, `wandb_entity`, `experiment_family`, `contributing_experiments` when applicable, `experiment_cell`, `scenario_set_name`, `scenario_set_hash`, `orchestration_mode`, `mcp_mode`, `git_sha`, `host_name`, and `gpu_type`
- aggregate latency metrics
- aggregate success metrics
- `wandb_run_url`

### Results linkage

`results/metrics/scenario_scores.jsonl` should include enough fields to join back
to WandB and benchmark artifacts:
- `run_name`
- `wandb_run_url`
- `scenario_id`
- `trial_index`
- `experiment_cell`
- `orchestration_mode`
- `mcp_mode`
- `judge_model`
- judge score outputs

### WandB exports

Long-lived reproducibility snapshots under `results/wandb_exports/` should retain:
- run config
- run summary
- tags
- artifact references if exported

## Required tags

Each WandB run should include tags that make filtering easy in the UI.

Required tags:
- `experiment:<family>`
- `cell:<cell>`
- `orchestration:<mode>`
- `mcp:<mode>`
- `model:<short-name>`
- `env:<compute-env>`

Special case:
- Cell B should carry both `experiment:exp1_mcp_overhead` and
  `experiment:exp2_orchestration`, even if `experiment_family` is recorded as a
  single primary family in config

Recommended tags:
- `gpu:<gpu-type>`
- `judge:<model>`
- `scenario-set:<name>`

## Run naming convention

Recommended run-name template:

`<date>_<experiment-family>_<cell>_<model-short>_<orchestration>_<mcp-mode>`

Example:

`2026-04-10_exp1_mcp_overhead_B_llama8b_aat_baseline`

The name should stay human-readable and stable enough to line up with:
- benchmark directory names
- notebook analysis outputs
- issue / PR discussion

Run names are for human-readable traceability, not for strict parsing. Notebook
joins should prefer explicit config fields and tags rather than parsing tokens
back out of `run_name`.

## Minimum viable first run for #21

The first run used to close `#21` does not need the entire final experiment stack.
It does need:
- a real WandB run in the shared project
- the required identity / experiment / model / hardware config fields above
- basic run outcome fields
- at least one latency metric
- a valid `wandb_run_url`

That first run is the proof point that the schema and instrumentation path are real.

## Dependencies

- `#14` defines the schema in this document
- `#61` should implement instrumentation against this schema
- `#21` should use the first real run emitted with this schema
- `#28` should only close once the shared-project logging path is visibly working
