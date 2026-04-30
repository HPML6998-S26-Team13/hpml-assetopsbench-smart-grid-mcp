# Validation Log

*Last updated: 2026-04-30*

Canonical log for live serve / benchmark / profiling proofs. Use this file for
concrete run records, not the runbooks.

## Convention

For each proof entry, record:

- date
- scope
- branch / git SHA
- config or command path
- run id / Slurm job id
- primary artifacts
- what the run proves
- caveats / follow-ups

## 2026-04-30 — Z + Self-Ask + D optimized PE-family ablation proof (`#85`, informs `#32`)

- **Scope:** Exploratory best-engineered PE-family ablation: Verified PE +
  Self-Ask with optimized MCP persistent sessions and the Cell D
  compressed-INT8 / BF16 / fp8-KV / prefix-cache serving profile.
- **Scenario set:** `data/scenarios/multi_*.json`, 2 scenarios × 3 trials = 6
  trial artifacts.
- **Model:** self-hosted `openai/Llama-3.1-8B-Instruct-int8` through local
  vLLM on Insomnia.
- **Branch / git SHA:** `team13/main@eb7019b3ebeb3e3b6848ab4b0c8b4bf0fa21ab44`
  in the shared Insomnia checkout.
- **Config:** `configs/experiment2/exp2_cell_ZSD_verified_pe_self_ask_mcp_model_optimized.env`.
- **Run id / Slurm job id:** `9074775_exp2_cell_ZSD_verified_pe_self_ask_mcp_model_optimized`.
- **Node / Slurm state:** `ins084`, `COMPLETED 0:0`, elapsed `00:12:38`.
- **W&B:** https://wandb.ai/assetopsbench-smartgrid/assetopsbench-smartgrid/runs/48nqpclw
- **Primary artifacts:**
  - `benchmarks/cell_ZSD/raw/9074775_exp2_cell_ZSD_verified_pe_self_ask_mcp_model_optimized/meta.json`
  - `benchmarks/cell_ZSD/raw/9074775_exp2_cell_ZSD_verified_pe_self_ask_mcp_model_optimized/harness.log`
  - `benchmarks/cell_ZSD/raw/9074775_exp2_cell_ZSD_verified_pe_self_ask_mcp_model_optimized/vllm.log`
  - `benchmarks/cell_ZSD/raw/9074775_exp2_cell_ZSD_verified_pe_self_ask_mcp_model_optimized/latencies.jsonl`
  - `benchmarks/cell_ZSD/config.json`, `benchmarks/cell_ZSD/summary.json`
  - `results/metrics/scenario_scores.jsonl`
  - `results/judge_logs/9074775_exp2_cell_ZSD_verified_pe_self_ask_mcp_model_optimized/SGT-009_run{01,02,03}_judge_log.json`
  - `results/judge_logs/9074775_exp2_cell_ZSD_verified_pe_self_ask_mcp_model_optimized/SGT-010_run{01,02,03}_judge_log.json`
  - W&B profiling artifact `profiling-48nqpclw`
- **Per-trial latencies:** `114.28`, `78.44`, `86.72`, `31.89`, `30.41`,
  `29.47` s.
- **Judge result:** Maverick-17B six-dimension judge scored all six ZSD trials
  with `score_6d` values `0.3333`, `0.5`, `0.0`, `0.8333`, `1.0`, `1.0`;
  mean `0.6111`, p50 `0.8333`, pass rate `3 / 6` at threshold `0.6`.

What this proves:

- The PE-family optimized MCP extension is real on Insomnia: the runner reused
  initialized MCP sessions, reached all four Smart Grid MCP servers, executed
  model/tool loops, and completed `6 / 6` with `tool_error_count=0`.
- The model-side stack was the intended Cell D serving profile. `vllm.log`
  records `dtype=torch.bfloat16`, `quantization=compressed-tensors`,
  `kv_cache_dtype=fp8`, `enable_prefix_caching=True`, and the compressed-tensor
  Cutlass INT8 kernel.
- The ZSD run is slower than the AaT optimized-serving arm but materially
  better on the current six-dimension judge than Cells C/D: mean `0.6111` and
  `3 / 6` judge-pass versus D mean `0.1667` and `1 / 6`.

Caveats / follow-ups:

- This is an exploratory ablation, not part of the clean core matrix. It stacks
  verifier logic, Self-Ask, optimized MCP persistent sessions, and model-side
  serving changes, so it is best interpreted as a PE-family ceiling.
- Failed boundary runs are intentionally not committed as proof artifacts:
  `9073604` reached model/tool execution but had partial completion and stdout
  JSON pollution; `9074217` exposed an Insomnia AOB portability mismatch in the
  first `MAX_TOKENS` wrapper. Commits `9be831b` and `eb7019b` fixed those
  boundaries before the successful `9074775` rerun.
- Final paper-grade reruns should still freeze a scenario set and trial count
  across the core matrix before promoting this beyond an ablation/sidebar.

## 2026-04-30 — Experiment 1 Cell D optimized-serving capture and judge proof (`#85`)

- **Scope:** Exploratory Cell D optimized-serving AaT capture for the
  `multi_*.json` slice. Cell D uses the Cell C optimized MCP transport and
  additionally changes the serving stack to compressed INT8 weights, BF16
  execution, fp8 KV cache, and prefix caching.
- **Scenario set:** `data/scenarios/multi_*.json`, 2 scenarios × 3 trials = 6
  trial artifacts.
- **Model:** self-hosted `openai/Llama-3.1-8B-Instruct-int8` through local
  vLLM on Insomnia.
- **Branch / git SHA:** `team13/main@ec17dc781f0d703fa365ba348e82ed4b38afb222`
  in the shared Insomnia checkout for the run.
- **Config:** `configs/aat_mcp_model_optimized.env`.
- **Run id / Slurm job id:** `9073472_aat_mcp_model_optimized`.
- **Node / Slurm state:** `ins084`, `COMPLETED 0:0`, elapsed `00:10:01`.
- **W&B:** https://wandb.ai/assetopsbench-smartgrid/assetopsbench-smartgrid/runs/pmwzatie
- **Primary artifacts:**
  - `benchmarks/cell_D/raw/9073472_aat_mcp_model_optimized/meta.json`
  - `benchmarks/cell_D/raw/9073472_aat_mcp_model_optimized/harness.log`
  - `benchmarks/cell_D/raw/9073472_aat_mcp_model_optimized/vllm.log`
  - `benchmarks/cell_D/raw/9073472_aat_mcp_model_optimized/latencies.jsonl`
  - `benchmarks/cell_D/raw/9073472_aat_mcp_model_optimized/_batch_latencies.jsonl`
  - `benchmarks/cell_D/raw/9073472_aat_mcp_model_optimized/replay/replay_meta.json`
  - `benchmarks/cell_D/config.json`, `benchmarks/cell_D/summary.json`
  - `results/metrics/scenario_scores.jsonl`
  - `results/judge_logs/9073472_aat_mcp_model_optimized/SGT-009_run{01,02,03}_judge_log.json`
  - `results/judge_logs/9073472_aat_mcp_model_optimized/SGT-010_run{01,02,03}_judge_log.json`
  - profiler trace directory `profiling/traces/9073472_aat_mcp_model_optimized_torch`
  - W&B profiling artifact `profiling-pmwzatie`
- **Per-trial latencies:** `18.67`, `8.05`, `6.30`, `3.77`, `6.04`, `4.77` s
  with one-time `mcp_setup_seconds=14.64`.
- **Judge result:** Maverick-17B six-dimension judge scored all six Cell D
  trials with `score_6d` values `0.0`, `0.0`, `0.0`, `0.3333`, `0.6667`,
  `0.0`; mean `0.1667`, p50 `0.0`, pass rate `1 / 6` at threshold `0.6`.

What this proves:

- Cell D runs end-to-end on the same first-capture Experiment 1 slice:
  `run_status: "success"`, `6 / 6` complete, `tool_error_count=0`, and
  `tool_call_count_total=18`.
- The serving stack loaded the INT8 checkpoint and vLLM selected
  `CutlassInt8ScaledMMLinearKernel for CompressedTensorsW8A8Int8`. The
  `vllm.log` engine config records `dtype=torch.bfloat16`,
  `quantization=compressed-tensors`, `kv_cache_dtype=fp8`, and
  `enable_prefix_caching=True`.
- Replay/profiling completed after the benchmark run:
  `replay_scenarios` passed both unique scenarios and the torch profiler trace
  was linked to W&B.
- Post-hoc LLM-as-judge scoring completed for all six per-trial trajectories
  and emitted per-trial audit logs.

Caveats / follow-ups:

- Cell D is not part of the clean A/B/C transport-only fairness contract. It is
  an optimized-serving ablation that changes model precision/quantization in
  addition to MCP transport.
- The run was emitted before commit `35efc6f` exported
  `VLLM_DTYPE` / `EXTRA_VLLM_ARGS` for the Python metadata writer. The synced
  `benchmarks/cell_D/config.json` and per-run `meta.json` have an explicit
  `metadata_correction_note`; `harness.log` and `vllm.log` are the primary proof
  that the serving stack used BF16, compressed tensors, fp8 KV cache, and prefix
  caching. Commit `35efc6f` fixes future runs, including ZSD.
- Quality remains poor despite the faster optimized-serving execution. The one
  passing judge trial is not enough to promote D beyond exploratory status; use
  this as latency/systems evidence and motivation for PE-family optimized
  follow-ons.

## 2026-04-30 — Experiment 1 Cell C optimized MCP capture (`#85`, unblocks `#86`)

- **Scope:** Experiment 1 Cell C optimized MCP capture for the `multi_*.json`
  slice, matching the Cell B baseline depth from job `8979314`
- **Scenario set:** `data/scenarios/multi_*.json`, 2 scenarios × 3 trials = 6
  trial artifacts
- **Model:** self-hosted `openai/Llama-3.1-8B-Instruct` through local vLLM on
  Insomnia
- **Branch / git SHA:** `team13/main@7e8d169c7c0789378762b59219694e9b83964b67`
  in the shared Insomnia checkout
- **Config:** `configs/aat_mcp_optimized_singletool_runtime.env` during the
  proof run; this is the merged `configs/aat_mcp_optimized.env` with
  `AAT_PARALLEL_TOOL_CALLS=false` after the local vLLM path rejected parallel
  tool calls
- **Run id / Slurm job id:** `9071639_aat_mcp_optimized`
- **Node / Slurm state:** `ins083`, `COMPLETED 0:0`, elapsed `00:19:07`
- **W&B:** https://wandb.ai/assetopsbench-smartgrid/assetopsbench-smartgrid/runs/ifz8xfhm
- **Primary artifacts:** live artifacts in the shared Insomnia checkout:
  - `benchmarks/cell_C_mcp_optimized/raw/9071639_aat_mcp_optimized/meta.json`
  - `benchmarks/cell_C_mcp_optimized/raw/9071639_aat_mcp_optimized/harness.log`
  - `benchmarks/cell_C_mcp_optimized/raw/9071639_aat_mcp_optimized/vllm.log`
  - `benchmarks/cell_C_mcp_optimized/raw/9071639_aat_mcp_optimized/latencies.jsonl`
  - `benchmarks/cell_C_mcp_optimized/raw/9071639_aat_mcp_optimized/_batch_latencies.jsonl`
  - `benchmarks/cell_C_mcp_optimized/raw/9071639_aat_mcp_optimized/replay/replay_meta.json`
  - `benchmarks/cell_C_mcp_optimized/config.json`, `benchmarks/cell_C_mcp_optimized/summary.json`
  - `results/metrics/scenario_scores.jsonl`
  - `results/judge_logs/9071639_aat_mcp_optimized/SGT-009_run{01,02,03}_judge_log.json`
  - `results/judge_logs/9071639_aat_mcp_optimized/SGT-010_run{01,02,03}_judge_log.json`
  - profiler trace directory `profiling/traces/9071639_aat_mcp_optimized_torch`
  - W&B profiling artifact `profiling-ifz8xfhm`
- **Per-trial latencies:** `60.24`, `10.99`, `7.81`, `6.87`, `6.67`, `6.99` s
  with one-time `mcp_setup_seconds=39.07`
- **Comparison anchor:** Cell B baseline job `8979314_aat_mcp_baseline`
  (`run_status: success`, 6 / 6, p50 `12.91` s, mean `13.38` s)
- **Judge result:** Maverick-17B six-dimension judge scored all six Cell C
  trials with `score_6d` values `0.1667`, `0.1667`, `0.0`, `0.1667`,
  `0.1667`, `0.3333`; mean `0.1667`, p50 `0.1667`, pass rate `0 / 6`
  at threshold `0.6`

What this proves:

- Cell C now runs end-to-end on the canonical multi-scenario Experiment 1 slice:
  `run_status: "success"`, `6 / 6` complete, `tool_error_count=0`, and
  `tool_call_count_total=18`
- the optimized batch runner keeps the four Smart Grid MCP servers alive across
  all six trials and writes canonical per-trial JSON, `_batch_latencies.jsonl`,
  `latencies.jsonl`, `summary.json`, and `meta.json`
- vLLM prefix caching was active in the serving layer; `vllm.log` reported
  prefix-cache hit rates rising through the run
- replay/profiling completed after the benchmark run:
  `replay_scenarios` passed both unique scenarios and the torch profiler trace
  was linked to W&B
- post-hoc LLM-as-judge scoring completed for all six per-trial trajectories
  and emitted per-trial audit logs
- Notebook 02 can now compute the first real `(B - C)` MCP-overhead headline.
  Using the aggregate summary fields, Cell C p50 was `6.99` s versus Cell B
  p50 `12.91` s (about `5.92` s faster at p50). The Cell C mean was slower
  (`16.60` s versus `13.38` s) because the first optimized trial paid a large
  cold-start / first-prefix cost; excluding that first Cell C trial gives a
  steady-state mean near `7.87` s.

Caveats / follow-ups:

- job `9071621_aat_mcp_optimized` is negative evidence for
  `AAT_PARALLEL_TOOL_CALLS=true`: it reached vLLM, MCP bootstrap, model
  requests, and tool execution, but all six trials failed with
  `This model only supports single tool-calls at once!`
- the canonical Cell C config should keep `AAT_PARALLEL_TOOL_CALLS=false` for
  the Insomnia vLLM / Llama-3.1-8B-Instruct path unless a future model/parser
  combination proves true parallel tool-call support
- `ins082` should stay excluded on future Insomnia submits; the earlier
  `9071602` attempt failed before vLLM because the node could not expose a GPU
  to `nvidia-smi`
- the execution path is clean, but the judge result is poor: `0 / 6`
  trajectories pass the current `score_6d >= 0.6` threshold, mainly because
  the agent failed to retrieve/ground the required evidence before answering
- this is the first successful Cell C capture, not the final paper-grade
  5-trial run set; final reruns should use the same scenario/model surface as
  the final A/B captures

## 2026-04-25/26 — Agent-as-Tool Cell A/B and upstream parity smoke proofs (`#104`, unblocks `#25`)

- **Scope:** Agent-as-Tool smoke proofs for Experiment 1 Cell A (direct Python
  tools), Cell B (MCP baseline), and the upstream
  `OpenAIAgentRunner` parity path on the shared SGT-009 / T-015 scenario
- **Scenario:** `data/scenarios/multi_01_end_to_end_fault_response.json`
- **Model:** self-hosted `openai/Llama-3.1-8B-Instruct` through local vLLM on
  Insomnia
- **Current reachable PR branch:** `codex-fnd/aat-smoke-fix`
- **Historical Slurm-recorded SHAs:** these jobs ran before the Apr 26
  author/committer attribution rewrite. The run `meta.json` files therefore
  record pre-rewrite hashes that are no longer reachable from the remote branch:
  Cell A `9541e2661111daa14eb4d99f46d30bdc03681114`, Cell B
  `a10d092d374309f45d282c7f7aec71a7fa8d11df`, upstream parity
  `e43cba33c7d78cf17390ec65bd82aeb4a9ebbe10`. The rewritten PR branch above
  preserves the smoke-fix code/doc lineage and is the checkout target for
  review/merge.
- **Cell A config:** `configs/aat_direct_smoke.env`
- **Cell A run id / Slurm job id:** `8962310_aat_direct_smoke_104`
- **Cell A primary artifacts:** live artifacts in the shared Insomnia checkout:
  - `benchmarks/cell_A_direct/raw/8962310_aat_direct_smoke_104/meta.json`
  - `benchmarks/cell_A_direct/raw/8962310_aat_direct_smoke_104/harness.log`
  - `benchmarks/cell_A_direct/raw/8962310_aat_direct_smoke_104/latencies.jsonl`
  - `benchmarks/cell_A_direct/raw/8962310_aat_direct_smoke_104/2026-04-25_A_llama-3-1-8b-instruct_agent_as_tool_direct_multi_01_end_to_end_fault_response_run01.json`
  - `benchmarks/cell_A_direct/config.json`, `benchmarks/cell_A_direct/summary.json`
- **Cell B config:** `configs/aat_mcp_baseline_smoke.env`
- **Cell B run id / Slurm job id:** `8969519_aat_mcp_baseline_smoke_104`
- **Cell B primary artifacts:** live artifacts in the shared Insomnia checkout:
  - `benchmarks/cell_B_mcp_baseline/raw/8969519_aat_mcp_baseline_smoke_104/meta.json`
  - `benchmarks/cell_B_mcp_baseline/raw/8969519_aat_mcp_baseline_smoke_104/harness.log`
  - `benchmarks/cell_B_mcp_baseline/raw/8969519_aat_mcp_baseline_smoke_104/vllm.log`
  - `benchmarks/cell_B_mcp_baseline/raw/8969519_aat_mcp_baseline_smoke_104/latencies.jsonl`
  - `benchmarks/cell_B_mcp_baseline/raw/8969519_aat_mcp_baseline_smoke_104/2026-04-26_B_llama-3-1-8b-instruct_agent_as_tool_baseline_multi_01_end_to_end_fault_response_run01.json`
  - `benchmarks/cell_B_mcp_baseline/config.json`, `benchmarks/cell_B_mcp_baseline/summary.json`
- **Upstream parity config:** `configs/aat_mcp_baseline_upstream_smoke.env`
- **Upstream parity run id / Slurm job id:** `8970383_aat_mcp_baseline_upstream_smoke_104`
- **Upstream parity primary artifacts:** live artifacts in the shared Insomnia checkout:
  - `benchmarks/cell_B_mcp_baseline/raw/8970383_aat_mcp_baseline_upstream_smoke_104/meta.json`
  - `benchmarks/cell_B_mcp_baseline/raw/8970383_aat_mcp_baseline_upstream_smoke_104/harness.log`
  - `benchmarks/cell_B_mcp_baseline/raw/8970383_aat_mcp_baseline_upstream_smoke_104/vllm.log`
  - `benchmarks/cell_B_mcp_baseline/raw/8970383_aat_mcp_baseline_upstream_smoke_104/latencies.jsonl`
  - `benchmarks/cell_B_mcp_baseline/raw/8970383_aat_mcp_baseline_upstream_smoke_104/2026-04-26_B_llama-3-1-8b-instruct_agent_as_tool_baseline_multi_01_end_to_end_fault_response_run01.json`
- **Upstream parity repeat run id / Slurm job id:** `8970468_aat_mcp_baseline_upstream_smoke_104`
- **Upstream parity repeat primary artifacts:** live artifacts in the shared Insomnia checkout:
  - `benchmarks/cell_B_mcp_baseline/raw/8970468_aat_mcp_baseline_upstream_smoke_104/meta.json`
  - `benchmarks/cell_B_mcp_baseline/raw/8970468_aat_mcp_baseline_upstream_smoke_104/harness.log`
  - `benchmarks/cell_B_mcp_baseline/raw/8970468_aat_mcp_baseline_upstream_smoke_104/vllm.log`
  - `benchmarks/cell_B_mcp_baseline/raw/8970468_aat_mcp_baseline_upstream_smoke_104/latencies.jsonl`
  - `benchmarks/cell_B_mcp_baseline/raw/8970468_aat_mcp_baseline_upstream_smoke_104/2026-04-26_B_llama-3-1-8b-instruct_agent_as_tool_baseline_multi_01_end_to_end_fault_response_run01.json`

What this proves:

- Cell A and Cell B now run through the same OpenAI Agents SDK loop with only
  the tool source changed: direct callables for Cell A, MCP stdio servers for
  Cell B
- the AaT runner reaches local vLLM, uses the pinned AOB prompt, and emits the
  canonical benchmark artifact set for both smoke cells
- Cell A completed `1 / 1` with `run_status: "success"`, wall-clock latency
  12.09 s, and 4 tool calls
- Cell B completed `1 / 1` with `run_status: "success"`, wall-clock latency
  91.78 s, and 4 MCP tool calls after all four Smart Grid MCP servers
  bootstrapped and initialized
- the Cell B smoke specifically validates the local-vLLM compatibility fixes:
  explicit LiteLLM base URL/API key wiring, vLLM auto tool choice with
  `llama3_json`, warmed `.venv-insomnia` MCP server launch, 120 s MCP initialize
  timeout, and `parallel_tool_calls=false` for sequential tool-call turns
- the upstream parity smoke drove AssetOpsBench's `OpenAIAgentRunner` Python
  API end-to-end against the same Smart Grid MCP servers and scenario:
  Slurm `COMPLETED 0:0` in `00:11:18`, benchmark `run_status: "success"`,
  `1 / 1` scenario complete, 36.18 s benchmark latency, 30.14 s upstream
  runner duration, and 4 MCP tool calls
- the repeat upstream parity smoke also succeeded end-to-end:
  Slurm `COMPLETED 0:0` in `00:09:05`, benchmark `run_status: "success"`,
  `1 / 1` scenario complete, 31.48 s benchmark latency, and 4 MCP tool calls
- the upstream parity harness reached MCP bootstrap, MCP initialize,
  model requests, and tool execution: all four servers listed tools,
  local vLLM served five `/v1/chat/completions` calls, and the trajectory
  called `get_sensor_readings`, `get_sensor_correlation`, `forecast_rul`, and
  `create_work_order`
- the Cell A / Cell B fairness guard now checks both model-visible tool names
  and per-tool parameter requiredness. Tool descriptions may still differ
  slightly between Python docstrings and FastMCP-derived schemas; the enforced
  contract is that the callable names and required argument surface match.

Caveats / follow-ups:

- these are one-scenario smoke proofs, not the full `#25` Experiment 1 capture
  slice (`multi_*.json`, 3 trials, A/B/C)
- Cell A was proven on an earlier branch tip before the final Cell B runtime
  hardening; the code-path changes after that point were MCP/vLLM compatibility
  fixes and did not change the direct tool surface
- Cell C is now proven separately in the Apr 30 entry above; at the time of
  these smoke proofs it was still pending optimized MCP readiness.
- the upstream parity proof uses AOB's `OpenAIAgentRunner` Python API rather
  than the `openai-agent` CLI because the CLI cannot pass Smart Grid
  `server_paths`; the wrapper keeps AOB's agent loop and patches only the MCP
  server launch envelope and `parallel_tool_calls=false` for Insomnia/local-vLLM
  compatibility

## 2026-04-13 — Watsonx plan-execute smoke (first canonical benchmark-path proof)

- **Scope:** end-to-end AssetOpsBench plan-execute run against all four Smart Grid MCP servers via Watsonx
- **Branch / state:** canonical `main` at the time of the run
- **Scenario:** `data/scenarios/multi_01_end_to_end_fault_response.json` (SGT-009, transformer T-015)
- **Model:** `watsonx/meta-llama/llama-3-3-70b-instruct`
- **Run name:** `local-20260413-003914_pe_mcp_baseline_watsonx_smoke`
- **W&B:** [9d4442ja](https://wandb.ai/assetopsbench-smartgrid/assetopsbench-smartgrid/runs/9d4442ja)
- **Primary artifacts (all committed in-tree):**
  - `benchmarks/cell_Y_plan_execute/raw/local-20260413-003914_pe_mcp_baseline_watsonx_smoke/meta.json`
  - `benchmarks/cell_Y_plan_execute/raw/local-20260413-003914_pe_mcp_baseline_watsonx_smoke/harness.log`
  - `benchmarks/cell_Y_plan_execute/raw/local-20260413-003914_pe_mcp_baseline_watsonx_smoke/latencies.jsonl`
  - `benchmarks/cell_Y_plan_execute/raw/local-20260413-003914_pe_mcp_baseline_watsonx_smoke/2026-04-13_Y_llama-3-3-70b-instruct_plan_execute_baseline_multi_01_end_to_end_fault_response_run01.json`
  - `benchmarks/cell_Y_plan_execute/config.json`, `benchmarks/cell_Y_plan_execute/summary.json`

What this proves:

- the AssetOpsBench `plan-execute` CLI successfully drove all four Smart Grid MCP servers end-to-end through the 8-tool-call sequence for SGT-009
- the benchmark wrapper produced canonical `benchmarks/cell_Y_plan_execute/raw/<run-id>/` artifacts on the first committed proof run
- wall-clock 93.6 s with the full LLM latency included; `run_status: "success"`, `pass: 1`, `fail: 0`
- this was the earliest committed in-tree proof of the benchmark-facing path and seeded the canonical Cell Y artifact layout that later runs reused

Caveats / follow-ups:

- single-scenario smoke; not a full grid
- uses WatsonX Llama-3.3-70B rather than the eventual Insomnia self-hosted Llama-3.1-8B path (those are the `#58` and `#115` lane)
- superseded as the canonical Cell Y snapshot by the Apr 21 PE + Self-Ask and Verified PE runs, but the raw artifacts remain committed as the earliest proof

## 2026-04-16 — Insomnia benchmark-path validation (`#58`, PR `#115`)

- **Scope:** self-hosted Llama-3.1-8B benchmark-path validation on Insomnia
- **Branch / state:** PR `#115` branch (not yet canonical `main` at the time of validation)
- **Key runtime shape:** `--served-model-name Llama-3.1-8B-Instruct`, `--max-model-len 32768`, local vLLM OpenAI-compatible path
- **Primary artifacts:** committed validation artifacts referenced from PR `#115`

What this proves:

- the long-context benchmark-facing serve path worked on an Insomnia A6000 node
- the benchmark path needed the served-model-name / OpenAI-client alignment
- the successful proof used the longer `32768` context lane rather than the lighter `8192` smoke-path default

Caveats / follow-ups:

- the validated shape still needed to be folded back into shared scripts/docs on canonical history
- startup-time expectations from that run informed the later timeout cleanup

## 2026-04-20 — PE + Self-Ask integration proof (`#24`)

- **Scope:** repo-local PE + Self-Ask runner on Insomnia
- **Branch / git SHA:** historical pre-accounting-fix branch state (around `0591c75`, pre-rebase)
- **Config:** `configs/example_pe_self_ask.env`
- **Run id / Slurm job id:** `8850716_pe_self_ask_mcp_baseline_smoke`
- **W&B:** `y42u88h3`
- **Primary artifacts:** historical live-run artifacts in the Insomnia worktree + W&B `y42u88h3`

What this proves:

- the repo-local Self-Ask PE runner executed end-to-end on Insomnia
- local `vllm==0.19.0`, Smart Grid MCP servers, LiteLLM/OpenAI-compatible local serving, and WandB upload all worked together in one live run

Caveats / follow-ups:

- this was an **integration proof**, not yet a clean method-quality proof
- one scenario still ended with a terminal failed step (`Unknown server 'none'`) even though the benchmark wrapper counted the run as completed
- that accounting bug is now fixed on the branch; rerun after the fix is required before treating this as final PR evidence

## 2026-04-20 — Verified PE integration proof (`#23`)

- **Scope:** repo-local Verified PE runner on Insomnia
- **Branch / git SHA:** historical pre-accounting-fix branch state (around `0591c75`, pre-rebase)
- **Config:** `configs/example_verified_pe.env`
- **Run id / Slurm job id:** `8851966_verified_pe_mcp_baseline_smoke`
- **W&B:** `0v3a5jqi`
- **Primary artifacts:** historical live-run artifacts in the Insomnia worktree + W&B `0v3a5jqi`

What this proves:

- the repo-local Verified PE workflow also executes end-to-end on Insomnia with live verifier / retry behavior
- the runtime stack is the same working local-serving path as the PE + Self-Ask run

Caveats / follow-ups:

- this run also happened before the benchmark-wrapper success-accounting fix
- the raw scenario outputs show semantic failures even though the wrapper summary reported `pass=2`, so rerun on the fixed branch is required

## 2026-04-21 — PE + Self-Ask clean smoke proof snapshot (`#24`)

- **Scope:** repo-local PE + Self-Ask runner on Insomnia
- **Branch / git SHA:** `codex-fnd/issue-23-24-verified-pe-self-ask` at `3a03ab83b7714c1d0f3aed2bc4899ef63fe5511c`
- **Config:** `configs/example_pe_self_ask.env`
- **Run id / Slurm job id:** `8857842_pe_self_ask_mcp_baseline_smoke`
- **W&B:** [otkt77pj](https://wandb.ai/assetopsbench-smartgrid/assetopsbench-smartgrid/runs/otkt77pj)
- **Primary artifacts:**
  - committed snapshot: `benchmarks/cell_Y_plan_execute/config.json`
  - committed snapshot: `benchmarks/cell_Y_plan_execute/summary.json`
  - live raw artifacts: archived in the Insomnia worktree under run id `8857842_pe_self_ask_mcp_baseline_smoke`

What this proves:

- the repo-local PE + Self-Ask runner reached a full `2 / 2` smoke success on the two multi-domain scenarios on the rebased post-`#115` branch
- the live path was clean end-to-end: local vLLM, LiteLLM/OpenAI-compatible serving, Smart Grid MCP servers, benchmark wrapper, and WandB upload
- the committed `config.json` / `summary.json` snapshot now gives the PR an in-tree proof surface without requiring the full raw log bundle in git

Caveats / follow-ups:

- the full raw logs and per-scenario JSONs are intentionally not committed in this branch; they remain archived on Insomnia and externally reflected in W&B
- earlier `8854783_pe_self_ask_mcp_baseline_smoke` remains useful historical evidence, but `8857842` is the committed snapshot aligned to the current rebased branch state

## 2026-04-21 — Verified PE clean smoke proof snapshot (`#23`)

- **Scope:** repo-local Verified PE runner on Insomnia
- **Branch / git SHA:** `codex-fnd/issue-23-24-verified-pe-self-ask` at `3a03ab83b7714c1d0f3aed2bc4899ef63fe5511c`
- **Config:** `configs/example_verified_pe.env`
- **Run id / Slurm job id:** `8857843_verified_pe_mcp_baseline_smoke`
- **W&B:** [x65ej9e0](https://wandb.ai/assetopsbench-smartgrid/assetopsbench-smartgrid/runs/x65ej9e0)
- **Primary artifacts:**
  - committed snapshot: `benchmarks/cell_Z_hybrid/config.json`
  - committed snapshot: `benchmarks/cell_Z_hybrid/summary.json`
  - live raw artifacts: archived in the Insomnia worktree under run id `8857843_verified_pe_mcp_baseline_smoke`

What this proves:

- the repo-local Verified PE runner reached a full `2 / 2` smoke success on the rebased post-`#115` branch
- verifier-time prompt overflows, summarization overflows, and oversized execution-context recycling are all fixed enough for a clean live proof
- the committed `config.json` / `summary.json` snapshot now gives the PR an in-tree proof surface for the Verified PE lane as well

Caveats / follow-ups:

- this is the current authoritative Verified PE smoke snapshot for the PR
- the full raw logs and per-scenario JSONs are intentionally not committed in this branch; they remain archived on Insomnia and externally reflected in W&B

## 2026-04-26 — Experiment 1 Cell A + B canonical capture (`#25`)

- **Scope:** full Experiment 1 Cell A (Agent-as-Tool, direct in-process tools) and Cell B (Agent-as-Tool, MCP baseline) capture across the canonical multi-domain scenario set, executed sequentially in one Slurm allocation via `scripts/run_exp1_ab_capture.sh`. Includes the Apr 21 instrumentation validation: WandB run linkage, nvidia-smi GPU timeline, and a vLLM torch-profiler trace per cell.
- **Branch / git SHA:** `aaron/exp1-ab-capture` rooted at `ed136e8` (committed via PR `#130`)
- **Slurm job id:** `8979314`
- **Slurm state / elapsed:** `COMPLETED 0:0` in `00:10:31`
- **Capture script:** `scripts/run_exp1_ab_capture.sh`
- **Configs:**
  - Cell A: `configs/aat_direct.env`
  - Cell B: `configs/aat_mcp_baseline.env`
  - both with `TORCH_PROFILE=1`, `LAUNCH_VLLM=1`, `ENABLE_WANDB=1`, `ENABLE_SMARTGRID_SERVERS=1` (Cell B only)
- **Scenario set:** `data/scenarios/multi_*.json` (canonical multi-domain pack; 2 scenarios × 3 trials per cell)
- **Model:** self-hosted `openai/Llama-3.1-8B-Instruct` via local vLLM on Insomnia (`vllm==0.19.0`, FP16, max_model_len=8192)

### Cell A primary artifacts

- `benchmarks/cell_A_direct/raw/8979314_aat_direct/` — `meta.json` (with `wandb_run_url` and repo-root-relative `profiling_dir`), `summary.json` (`6 / 6` scenarios, mean `12.19` s, `run_status: success`, `git_sha: ed136e8`), `latencies.jsonl`, `harness.log`, `vllm.log`, per-trial JSONs, replay JSONs.
- `benchmarks/cell_A_direct/config.json` + `summary.json` (cell-level rolled-up).
- **Profiling (gitignored):**
  - `profiling/traces/8979314_cell_a/nvidia_smi.csv` — GPU util / memory / power timeline at 1 Hz, **355 sample rows**
  - `profiling/traces/8979314_cell_a/nvidia_smi.stderr.log` — sampler error sidecar (empty for this run)
  - `profiling/traces/8979314_cell_a/capture_meta.json`
  - `profiling/traces/8979314_aat_direct_torch/*.pt.trace.json.gz` — PyTorch profiler Chrome trace from vLLM `/start_profile` + `/stop_profile`
- **WandB run:** <https://wandb.ai/assetopsbench-smartgrid/assetopsbench-smartgrid/runs/vq976ljq>
- **WandB Artifact:** `profiling-vq976ljq` (gpu-util mean `16.9 %` / max `100 %`, memory used mean `23.8 GiB` / max `42.1 GiB`, power mean `95.7 W` / max `273.3 W`)

### Cell B primary artifacts

- `benchmarks/cell_B_mcp_baseline/raw/8979314_aat_mcp_baseline/` — same shape; `summary.json` is `6 / 6`, mean `13.38` s, `run_status: success`, `git_sha: ed136e8`.
- `benchmarks/cell_B_mcp_baseline/config.json` + `summary.json`.
- **Profiling (gitignored):** `profiling/traces/8979314_cell_b/nvidia_smi.csv` (**249 sample rows**), `nvidia_smi.stderr.log` (empty), `capture_meta.json`, `profiling/traces/8979314_aat_mcp_baseline_torch/*.pt.trace.json.gz`.
- **WandB run:** <https://wandb.ai/assetopsbench-smartgrid/assetopsbench-smartgrid/runs/qejvnoug>
- **WandB Artifact:** `profiling-qejvnoug`

### What this proves

- Cell A and Cell B run through the same OpenAI Agents SDK loop with only the tool source changed. (Cell B − Cell A) wall-clock = `13.38 − 12.19 = 1.20 s` mean is what Notebook 02 will treat as MCP transport overhead.
- All three Apr 21 instrumentation streams produced artifacts and link back to benchmark run metadata:
  1. **WandB:** `wandb_run_url` is in both `meta.json`s; `log_profiling_to_wandb.py` attached `nvidia_smi.csv` + `capture_meta.json` as a WandB Artifact and pushed gpu-util / memory / power summary into `wandb.run.summary`. `meta.json:profiling_dir` is repo-root-relative (`profiling/traces/8979314_cell_{a,b}`), portable across team / personal-scratch checkouts.
  2. **nvidia-smi:** non-empty CSV timelines for both cells with **355 / 249** sample rows respectively under `profiling/traces/8979314_cell_{a,b}/`. Sampler `stderr.log` sidecar is empty for both, confirming no transient nvidia-smi failures.
  3. **PyTorch / vLLM torch profiler:** non-empty `*.pt.trace.json.gz` under `profiling/traces/8979314_aat_{direct,mcp_baseline}_torch/`, captured via the vLLM 0.19.0 `--profiler-config` CLI flag (`profiler=torch`, `torch_profiler_dir=...`) + `scripts/replay_scenarios.sh` while vLLM was still alive in each cell's job phase.

### Bug fixes also in this PR

Three fixes to the team's instrumentation infrastructure that the first run attempts on Apr 26 surfaced (`9430b09`), plus two more added during PR review iteration (`a7de839`, `ed136e8`).

1. `scripts/aat_runner.py:266` — `json.dumps(..., default=str)` in `_write_output`. Tool results sometimes carry `pandas.Timestamp`/`numpy.datetime64` objects that vanilla `json.dumps` rejects; `default=str` makes the encoder fall back to `str()`. Crashed 1 trial in `8978161` Cell A; fix delivers 6/6.
2. `profiling/scripts/capture_around.sh:133` — post-run WandB uploader picks caller `PYTHON_BIN` → `.venv-insomnia/bin/python` → `python3` instead of bare `python3`. Insomnia's system Python 3.9 has no `wandb`; bare `python3` silently dropped the Artifact upload. With the fix, `capture_around` finishes `rc=0` and the artifact attaches to the WandB run.
3. `scripts/run_experiment.sh:753-758` — vLLM 0.19.0 dropped `VLLM_TORCH_PROFILER_DIR` (logs `Unknown vLLM environment variable detected`). Profiling now requires the `--profiler-config` CLI flag (`profiler=torch`, absolute `torch_profiler_dir`). The patched block builds the JSON config and appends to `VLLM_SERVER_ARGS` so `/start_profile` is registered in the FastAPI app.
4. `profiling/scripts/log_profiling_to_wandb.py` — relativize `prof_dir` against the repo root before writing into `meta.json` and WandB config. Fixes Alex's High #3: prior runs leaked the personal-scratch absolute path `/insomnia.../af3623/exp1-clone/...` into committed artifacts.
5. `profiling/scripts/sample_nvidia_smi.sh` — disable `pipefail` for the header-write line. The pipe `nvidia-smi --format=csv | head -1 > FILE` was sending SIGPIPE to nvidia-smi (exit 141) which under `set -euo pipefail` killed the script before the sample loop started — silently producing 1-line (header-only) CSVs in every prior capture (`8962310`, `8969519`, `8978297`, `8979215`). Loop also gets `set +e` plus a `<name>.stderr.log` sidecar to survive transient nvidia-smi failures during sampling. This is the actual root cause behind Alex's Critical #1.

### Caveats / follow-ups

- Cell C (MCP optimized) was not part of this Apr 26 A/B capture; the Apr 30
  Cell C entry above supersedes the old optimized-lane gate.
- `profiling/traces/` is gitignored. Paths above point at the live Insomnia checkout. The WandB Artifact uploads are the portable copies.
- Cell A's torch-profiler **replay pass** got `pass=1 fail=1`: `multi_01_end_to_end_fault_response` hit `ContextWindowExceededError` (8193 vs 8192 tokens). Non-fatal — the main scenario loop's 6/6 is the canonical capture; the replay only feeds the second torch-profiler trace. Bumping `MAX_MODEL_LEN` to 16384 in the configs is a follow-up tweak, not in this PR's scope.
- Run was executed from a personal scratch clone at `/insomnia001/depts/edu/users/af3623/exp1-clone/` because the team-shared checkout's `.git/objects` had perm issues for non-`wax1` writers. Personal clone symlinks `models/` and `.venv-insomnia/` from the shared checkout for storage efficiency.
- The shared `.venv-insomnia` was extended via `uv pip install -r requirements-insomnia.txt` to add `openai-agents==0.14.5` + `griffelib` + `types-requests`, and refreshed `websockets` 16.0 → 15.0.1. Pinged Tanisha.
- Earlier `8978297` and `8979215` attempts were uncommitted / removed in this PR's history because they suffered from the bugs the rerun fixes.
