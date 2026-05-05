# Infrastructure / Profiling / Serving Brief (`#43`)

*Last updated: 2026-05-05*
*Owner: Aaron Fan (af3623)*
*Audience: Alex (paper §3 System Design + §infra paragraphs of `#39` / `#40`)*

One-page fact pack. Concrete numbers and repo paths only — verbatim-quotable, no narrative. Cross-reference the longer docs for "how to set up" (`docs/runbook.md`, `docs/insomnia_runbook.md`, `docs/gcp_fallback.md`); this file is for "what we ran on, with what versions, against which artifacts."

## Models

- **Scenario-execution model:** `meta-llama/Llama-3.1-8B-Instruct` — locally served on Insomnia and GCP via vLLM, OpenAI-compatible endpoint at `http://127.0.0.1:8000/v1`.
  - Local mirror: `models/Llama-3.1-8B-Instruct/` (symlinked from team-shared on Insomnia, fresh download on GCP).
  - Pinned `MODEL_REVISION` for reproducibility: `docs/governance/model_registry.yaml`.
- **Judge model:** `watsonx/meta-llama/llama-4-maverick-17b-128e-instruct-fp8` — via WatsonX HTTP API, no local serving. Default in `scripts/judge_trajectory.py:141`.
- **Optional comparison:** `watsonx/meta-llama/llama-3-3-70b-instruct` (FP8) — used by hosted-WatsonX cells like ZS70B (`configs/watsonx_70b_*`).

## Serving stack

- **vLLM** `0.19.0` (pinned in `requirements-insomnia.txt`).
- **Python** `3.11.x` (vLLM 0.10+ requirement; team venv at `.venv-insomnia/`).
- **Inference precision:** FP16 (default for canonical Cell A/B/Y/Z). FP8 used only by ZS70B / hosted-WatsonX paths.
- **Context window:** `MAX_MODEL_LEN=32768` for canonical AaT cells (`configs/aat_*.env`); 8192 retained on smoke configs only. Bump landed in PR #145 (#135) after Cell A run `8979314` hit the 8192 ceiling on a replay.
- **Tool-call parser:** `llama3_json` for Llama-3.x (model-family-aware default in `scripts/run_experiment.sh:108-114`).
- **KV-cache optimization** (Cell C): `--enable-prefix-caching` only. `--kv-cache-dtype fp8` was tested in Lane 2 smoke `8979532` and dropped due to a vLLM 0.19.0 FA3 kernel constraint under FP16 weights. Documented in `docs/lane2_int8_kv_status.md`.
- **INT8 quantization** (deferred): runnable on A6000 via `--quantization compressed-tensors` against `RedHatAI/Meta-Llama-3.1-8B-Instruct-quantized.w8a8`, validated in smoke `8979660`. Not in any canonical Cell C config — kept out for `(B−C)` signal purity.

## Compute environments

| Path | When | GPU | Cost | Status post-2026-05-03 |
|---|---|---|---|---|
| **Insomnia** (Columbia HPC) | Default | NVIDIA RTX A6000 (48 GB) or NVIDIA L40S | $0 (account `edu`, partition `short`, qos `short`, time ≤ 2h) | Canonical for the Apr captures (Cells A/B/Y/Z). Down for CVE-fix maintenance late 2026-05-03 → uncertain return; team partially shifted to GCP. |
| **GCP A100** | Fallback / preemption-tolerant batches | NVIDIA A100-40GB (`a2-highgpu-1g`, ~$1.81/hr spot) or A100-80GB (`a2-ultragpu-1g`, ~$2.50/hr spot) | $500/person credit (~276 GPU-hr A100-40GB spot per member) | **Canonical post-2026-05-03** for new captures. Resumable runs via `SMARTGRID_RUN_ID` / `SMARTGRID_RESUME` env vars (PR #170). Manifest of canonical GCP captures: `logs/gcp_a100_context_20260503T063343Z_manifest.tsv`. |
| **WatsonX hosted** | Judge + 70B comparison | n/a (hosted) | Free per IBM credit allocation | Always-on; no Insomnia dependency. |

## Slurm run shape (Insomnia)

- **Account:** `edu`
- **Partition / QoS:** `short` / `short`
- **GPU:** `--gres=gpu:1` (A6000 or L40S; assignment is non-deterministic — `#132` adds `gpu_type` to `summary.json` so each run records its actual hardware)
- **Memory:** `64G` standard; `32G` for verification jobs
- **Time:** `02:00:00` standard cap (replay + capture); `01:30:00` for verification (e.g. AOB smoke checks)
- **Email:** `--mail-type=BEGIN,END,FAIL --mail-user=$MAIL_USER` per CLAUDE.md
- **Submit pattern:** `sbatch scripts/run_experiment.sh configs/aat_*.env` from the repo root
- **Run dir:** `benchmarks/cell_<X>/raw/<SLURM_JOB_ID>_<EXPERIMENT_NAME>/`
- **Per-run artifacts:** `meta.json`, `summary.json` (cell-level, overwritten per run), `latencies.jsonl`, `harness.log`, `vllm.log`, `2026-MM-DD_<cell>_<model>_<orch>_<mcp>_<scenario>_runNN.json` (one per trial), `replay/` (torch profiler replay results)

## Profiling instrumentation

Three streams, all attached per-run:

1. **nvidia-smi GPU timeline** (1 Hz sampling, full job duration)
   - Wrapper: `profiling/scripts/capture_around.sh`
   - Sampler: `profiling/scripts/sample_nvidia_smi.sh`
   - Output: `profiling/traces/<SLURM_JOB_ID>_<cell>/nvidia_smi.csv` + `nvidia_smi.stderr.log` (sidecar; PR #130 hardening)
   - Sample fields: `timestamp, index, name, utilization.gpu, utilization.memory, memory.used, memory.total, temperature.gpu, power.draw`
   - Aggregate stats land in `meta.json:profiling_summary` (mean/max GPU util, mean/max mem MiB, mean/max power W, sample count)

2. **PyTorch Profiler trace via vLLM `--profiler-config`** (replay pass, after the main scenario loop)
   - Output: `profiling/traces/<SLURM_JOB_ID>_<run-id>_torch/*.pt.trace.json.gz` — Chrome trace format, openable in Perfetto / chrome://tracing
   - Triggered by `TORCH_PROFILE=1` in the cell config; replay re-runs scenarios via `scripts/replay_scenarios.sh` while vLLM is still alive in the same job

3. **WandB Artifact upload** (link profiling outputs to the benchmark run)
   - `profiling/scripts/log_profiling_to_wandb.py` — resumes the run via the URL parsed from `meta.json:wandb_run_url`, attaches `nvidia_smi.csv` + `capture_meta.json` as a single Artifact, pushes summary stats into `wandb.run.summary`
   - Profiling Artifact name: `profiling-<wandb-run-id>`

## WandB linkage

- **Project:** `wandb.ai/assetopsbench-smartgrid/assetopsbench-smartgrid`
- **Run init:** `scripts/run_experiment.sh` does `wandb.init(...)` after the scenario loop completes; `wandb_run_url` lands in both `config.json` and `meta.json`
- **Required config fields** (canonical, per `docs/wandb_schema.md`): identity (`schema_version`, `git_sha`, `git_branch`, `run_name`), experiment (`experiment_family`, `experiment_cell`, `orchestration_mode`, `mcp_mode`, `scenario_set_name`, `scenario_set_hash`), model/serving (`model_id`, `model_provider`, `serving_stack`, `quantization_mode`, `context_window`, `temperature`, `max_tokens`, `vllm_extra_args`, `vllm_extra_args_list`), hardware (`compute_env`, `gpu_type`, `gpu_count`, `host_name`, `slurm_job_id`)
- **Required summary metrics:** outcome (`run_status`, `scenarios_attempted`, `scenarios_completed`, `success_rate`), latency (`wall_clock_seconds_total`, `latency_seconds_mean`, `latency_seconds_p50`, `latency_seconds_p95`, `mcp_setup_seconds`), tokens (`input_tokens_total`, `output_tokens_total`, `total_tokens_total`, `tokens_per_second_mean` — PR #174 adds these end-to-end-agent throughput fields, NOT pure model-decode tok/s)
- **Profiling Artifact join:** `wandb.run.summary.profiling/nvidia_smi_samples` should equal `wc -l` of the underlying CSV minus the header

## Canonical evidence runs (cite-by-job-id)

- **Cell A (AaT direct):** Slurm `8979314` on Insomnia A6000, 6/6 success, mean 12.19s, mean GPU util 16.9%, mean memory 23.8 GiB. WandB: `vq976ljq`. PR #130.
- **Cell B (AaT MCP baseline):** Slurm `8979314` (same job) on Insomnia A6000, 6/6 success, mean 13.38s. (B−A) MCP transport overhead = +1.20s mean / paired median ~23ms. WandB: `qejvnoug`. PR #130.
- **Cell Y (Plan-Execute) + Y+Self-Ask:** PR #144 first canonical capture on Insomnia.
- **Cell Z (Verified PE) + Z+Self-Ask:** PR #144 first canonical capture; **Z+SA leads at 0.833 mean / 5/6 judge-pass** on the 6-trial slice. Convergent with AOB §5.6 Maverick AaT 59→66% Self-Ask delta.
- **GCP A100 context-window closeout:** seven rows, all `run_rc=0` and `judge_rc=0`, manifest at `logs/gcp_a100_context_20260503T063343Z_manifest.tsv` (PR #172).
- **KV-cache smoke:** Slurm `8979532` on Insomnia H100 NVL — `--enable-prefix-caching` measured at -27% wall-clock vs baseline; fp8 KV failed at vLLM startup (kernel constraint).
- **INT8 smoke:** Slurm `8979660` on Insomnia A6000 — `--quantization compressed-tensors` reachable + responds, CUTLASS Int8 W8A8 marlin kernel selected.
- **AOB#15 verification:** Slurm `9130342` on Insomnia ins092 — all three pytest suites green at AOB SHA `6872cea`.

## Reproducibility entry points

- **Single command:** `sbatch scripts/run_experiment.sh configs/<cell>.env` from repo root, with `MAIL_USER` exported. Identical entry point for every cell.
- **Resumable GCP runs:** `SMARTGRID_RUN_ID=<id> SMARTGRID_RESUME=1 sbatch scripts/run_experiment.sh ...` (PR #170)
- **Replay (Cell C connection-reuse + torch profiler):** automatic when `TORCH_PROFILE=1` and `LAUNCH_VLLM=1` in the cell config
- **Stable run pin:** every `summary.json` records `git_sha` of the actual code that ran (PR #130 closed the dirty-tree gap)

## Known limitations to surface in the paper

1. **Sample size on the canonical headline:** Cell A/B reported as first-canonical / partial; N=6 trials per cell. Mean +1.20s overhead, paired median ~23ms, p95 noisy. Not yet a final distribution claim.
2. **Cell C split to `#85`** (gated on Akshat's `#31`/`#134` for batched MCP). Without that, "Cell C" would be Cell B + a GPU-side knob, which measures GPU optimization not MCP optimization.
3. **GPU type non-deterministic** on Insomnia (A6000 vs L40S vs H100 NVL depending on Slurm assignment) — `#132` makes `gpu_type` stamp into `summary.json` per run, so cross-run comparisons can filter accordingly.
4. **Token throughput is end-to-end agent throughput, NOT pure model decode tok/s** — denominator includes tool-call round-trips + MCP serialization + orchestration time. Inline note in `scripts/run_experiment.sh` summary builder; PR #174.
5. **vLLM 0.19.0 FA3 kernel constraint:** `--kv-cache-dtype fp8` requires BF16 model weights. Cell C ships FP16 + prefix-caching only. INT8 path is BF16 (CompressedTensors default), so a future Cell D that swaps the model precision could combine INT8 + fp8 KV.
6. **Insomnia CVE-fix downtime late 2026-05-03 onward** — uncertain return. GCP A100 path became canonical for new captures from 2026-05-03; documented in `docs/gcp_fallback.md`.
7. **Replay context-window edge** on Cell A scenarios: one of two replay scenarios hit the (then) 8192 limit on `8979314` (multi_01, 8193 input tokens). PR #145 bumped canonical configs to 32768; smoke configs stay at 8192.

## Refs (for Alex's verification)

- `docs/runbook.md` — reproduction entry point + day-to-day Slurm flow
- `docs/insomnia_runbook.md` — Insomnia-specific quirks (account, scratch, SSH agent, CUDA workaround)
- `docs/gcp_fallback.md` — GCP A100 spin-up, instance selection, preemption handling, artifact persistence
- `docs/lane2_int8_kv_status.md` — INT8 + KV-cache decision evidence
- `docs/wandb_schema.md` — required WandB config + summary fields
- `docs/governance/model_registry.yaml` — canonical model IDs + revisions + runtime pins
- `docs/validation_log.md` — per-canonical-capture run IDs + WandB URLs + artifact paths
- `profiling/README.md` — three-stream capture workflow (nvidia-smi, torch profiler, WandB Artifact)
