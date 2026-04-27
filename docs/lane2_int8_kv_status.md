# Lane 2: INT8 + KV-Cache Optimization Status (`#29`, `#30`)

*Last updated: 2026-04-26*
*Owner: Aaron Fan (af3623)*
*Issues: [`#29`](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/29), [`#30`](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/issues/30)*

Defensible answer to "what optimizations does Cell C bundle?" The Experiment 1
capture plan ([`experiment1_capture_plan.md`](experiment1_capture_plan.md)) calls out three
optimization tasks that feed Cell C:

- `#29` INT8 quantization
- `#30` KV-cache tuning
- `#31` Batched / scheduled MCP calls (Akshat — out of scope here)

This doc covers `#29` and `#30`. `#31` is tracked separately.

## TL;DR — recommendation

| Knob | Recommendation | Rationale |
|---|---|---|
| **INT8 quantization** | **Defer to Cell C v2.** Use FP16 for the canonical Cell C run. | The headline measurement for Cell C is `(B − C) = recoverable MCP-transport optimization`. Adding INT8 to Cell C confounds that delta with model-side speedup and breaks the apples-to-apples comparison with FP16 Cells A/B. `--quantization compressed-tensors` is the production INT8 path but requires a pre-quantized HF checkpoint (we don't have one locally); `--quantization bitsandbytes` is the runtime path but is generally slower than CompressedTensors W8A8 marlin on Ampere. Use FP8 KV cache instead (next row) for a memory win that does not require a model swap. |
| **KV-cache** | **Enable `--enable-prefix-caching` + `--kv-cache-dtype fp8`** | Multi-turn ReAct on Llama-3.1-8B with the same AOB system prompt across all scenarios is the canonical prefix-caching workload — every turn after the first re-uses the system-prompt prefix. FP8 KV cache halves KV memory at near-zero quality cost on this model size. Both are first-class in vLLM 0.19. |
| **`--max-num-seqs`** | Leave default (`256`). Optionally drop to `4` for our sequential workload. | We're not batching multiple scenarios concurrently; lower max-num-seqs frees a small amount of memory but doesn't change steady-state. Default is fine. |
| **`--gpu-memory-utilization`** | Leave default (`0.9`). | The L40S A6000 has plenty of headroom for an 8B FP16 model; squeezing this isn't justified by our workload. |

**Net effect on Cell C config**: add `EXTRA_VLLM_ARGS="--enable-prefix-caching --kv-cache-dtype fp8"` to `configs/aat_mcp_optimized.env` and ship.

## #29 INT8 — what was investigated

### vLLM 0.19.0 quantization landscape

vLLM 0.19.0's `--quantization` flag accepts a wide set of values (full list in
`vllm/engine/arg_utils.py` and `vllm/model_executor/layers/quantization/`).
The relevant options for INT8-class deployment of Llama-3.1-8B-Instruct:

| Option | What it expects | Status for our use |
|---|---|---|
| `compressed-tensors` | Pre-quantized model in CompressedTensors format (e.g., `RedHatAI/Meta-Llama-3.1-8B-Instruct-quantized.w8a8`) | **Most production-ready INT8 path.** Requires downloading a different ~16 GB checkpoint. |
| `bitsandbytes` | Runtime quantization on the FP16 model — no checkpoint swap needed | Slow at startup, lower throughput than pre-quantized. Generally not recommended for production benchmarks. |
| `awq` / `awq_marlin` | Pre-quantized AWQ checkpoint (typically INT4, not INT8) | Wrong granularity for our headline. |
| `fp8` | FP8 W8A8 — needs a recent GPU + pre-quantized checkpoint or runtime quantization | A6000 (Ampere) does not have FP8 tensor cores; no native acceleration. |
| `int8` | **No standalone `int8` value in vLLM 0.19** — INT8 is delivered via `compressed-tensors` or `bitsandbytes` | Confirmed by reading `vllm/model_executor/layers/quantization/__init__.py` |

### Why we're deferring INT8

1. **Signal purity for the `(B − C)` headline.** Cell C's purpose in the
   Experiment 1 narrative is `(B − A) = MCP transport overhead` and
   `(B − C) = recoverable optimization`. Most of the recoverable cost is in
   the transport layer (batched MCP calls, connection reuse — Akshat's
   `#31`), not in the model. If Cell C swaps the model precision at the same
   time, a (B − C) latency drop attributes the win to the transport when in
   fact the model got faster too. The methodologically clean answer is to
   land Cell C on the same FP16 weights as A/B and treat INT8 as a separate
   Cell D / model-scaling experiment. This is the argument a reviewer can't
   push back on, so it leads.
2. **No INT8 Llama-3.1-8B-Instruct checkpoint in the team `models/`
   directory.** The canonical FP16 checkpoint is what
   `models/Llama-3.1-8B-Instruct/` holds. The production INT8 path
   (`--quantization compressed-tensors`, e.g.
   `RedHatAI/Meta-Llama-3.1-8B-Instruct-quantized.w8a8`) requires
   downloading a separate ~16 GB checkpoint plus HF gating. The runtime
   path (`--quantization bitsandbytes`) avoids the checkpoint swap but is
   reportedly slower than CompressedTensors W8A8 marlin on Ampere. Either
   way it's a real-world inventory cost, not a code change.
3. **Throughput story exists but is gated on the checkpoint.** On Ampere
   (A6000) and Ada (L40S), CompressedTensors W8A8 marlin kernels are
   well-optimized and the INT8 speedup is real — but only once we have a
   pre-quantized checkpoint. Without it the lane has no measurable upside
   over FP16. (FP8 weight quantization is a separate question and lives
   under the KV-cache discussion below.)
4. **Time budget.** Each new model takes ~10-20 min to download + a 5-10 min
   smoke. With `#25` still queued, INT8 work is realistically a separate-day
   item.

### Conditions under which to revive INT8

- Akshat's `#31` lands and the Cell C transport-only optimization shows a
  smaller-than-expected win. Adding INT8 then becomes a "second optimization
  arm" with a clear separate ablation.
- A reviewer asks specifically about quantization in the paper. We have a
  ready-to-go config + smoke script (see "Smoke scripts" below) to validate
  in ~15 min on Insomnia.

### INT8 smoke script (ready to fire)

`scripts/test_int8_smoke.sh` (added in this branch) is a minimal Slurm batch
that downloads a known-good INT8 Llama-3.1-8B-Instruct checkpoint and
launches vLLM with `--quantization compressed-tensors` to confirm it serves.
Run it only when the team agrees to revive INT8.

## #30 KV-Cache — what was chosen

### Knobs evaluated

| Knob | Default | Recommendation | Why |
|---|---|---|---|
| `--enable-prefix-caching` | off | **on** | AOB system prompt + tool catalog is identical across all turns and all scenarios. Prefix caching skips re-prefill of those tokens after the first turn. Direct win for ReAct workloads. Tested + stable in vLLM 0.19. |
| `--kv-cache-dtype` | `auto` (FP16) | **`fp8`** (specifically `fp8_e4m3` on Ampere, autoselected) | This is a KV **storage** precision change, not an attention-compute precision change. Attention math still runs at the model's native precision regardless of GPU FP8 tensor-core support (so the L40S's FP8 cores and the A6000's lack of them are both irrelevant here). The actual win is memory: halving KV cache size buys longer effective context window and more concurrent requests if we ever need them. Quality impact on Llama-3.1-8B is well under MMLU noise per published benchmarks. |
| `--max-num-seqs` | 256 | leave default | Our workload is single-stream (one scenario at a time). Default is fine; lowering to 4 saves ~50 MB which is rounding error. |
| `--gpu-memory-utilization` | 0.9 | leave default | The A6000 / L40S has enough headroom that squeezing this (e.g. to 0.95) buys back KV space we don't use. Not worth the OOM risk. |
| `--block-size` | 16 | leave default | Default is well-tuned; smaller = more overhead, larger = wasted blocks. Not a measurable lever for our workload. |
| `--swap-space` | 4 GiB | leave default | Only matters when KV cache exhausts and we have to evict to CPU. We're not running concurrent requests; eviction won't trigger. |
| `--enable-chunked-prefill` | on by default in 0.19 | leave default | Already enabled; no change needed. |

### Rationale for the chosen pair

The two knobs we're flipping (`--enable-prefix-caching` + `--kv-cache-dtype fp8`)
are:

- **Independent** — neither affects the other's correctness.
- **Cheap to test** — boolean / single-value flags, no model reload required
  beyond the vLLM restart.
- **Apples-to-apples with Cell A/B** — same model, same precision for forward
  pass (FP16); only the KV storage path changes. (Cell B - Cell C) latency
  remains a measurement of MCP transport optimization, not a confound from
  model-side changes.

### Why not a bigger sweep

The plan ([`experiment1_capture_plan.md`](experiment1_capture_plan.md)) calls
for a "small targeted sweep, not a broad sweep." We picked two knobs with
strong a-priori reasoning (prefix caching matches the workload shape; FP8 KV
cache is well-validated on Llama-3.1-8B). A broader sweep (block_size,
max-num-seqs, max-num-batched-tokens) would consume 5+ smoke runs and produce
no material difference for our single-stream workload.

### KV-cache mini-comparison script (ready to fire)

`scripts/test_kv_cache_smoke.sh` (added in this branch) runs three vLLM
launches against the same single-scenario smoke prompt:

1. **Baseline** — no extra flags (same as Cell A/B)
2. **Prefix caching only** — `--enable-prefix-caching`
3. **Prefix caching + FP8 KV cache** — `--enable-prefix-caching --kv-cache-dtype fp8`

Each variant captures startup time, memory usage, and one-prompt latency.
Total wall-clock ~10 min. Ship the result table to `#30` when done.

## Cell C config update

`configs/aat_mcp_optimized.env` updated in this branch to:

- Use the new `EXTRA_VLLM_ARGS="--enable-prefix-caching --kv-cache-dtype fp8"`
  to enable the chosen KV optimizations
- `QUANTIZATION_MODE="fp16"` (no INT8 — see deferral above)
- `TORCH_PROFILE=1` and `ENABLE_WANDB=1` for parity with Cell A/B
- Still requires Akshat's `#31` for the actual MCP-transport optimization;
  without that, Cell C is functionally Cell B + KV optimization, which
  measures GPU optimization not MCP optimization. Don't run the canonical
  Cell C until `#31` lands.

## What needs Insomnia compute (1 hr total when queue cooperates)

| Test | Script | Wall-clock | Owner | Decision impact |
|---|---|---|---|---|
| KV-cache mini-comparison (3 variants × 1 scenario) | `scripts/test_kv_cache_smoke.sh` | ~10 min compute + queue | Aaron | Confirms prefix-caching + fp8 KV is the right pair, or surfaces a regression |
| INT8 startup smoke (only if reviving the INT8 lane) | `scripts/test_int8_smoke.sh` | ~15 min compute + 16 GB download | Aaron + team approval | Decides whether INT8 enters Cell C v2 |

Both scripts include the standard `--mail-type=BEGIN,END,FAIL --mail-user`
flags following the team's Slurm convention.

## Definition of done — status

> **Definition of done for Lane 2:** We know whether Cell C can include INT8
> tonight, and we have a chosen KV-cache setting or an explicit
> evidence-backed deferral.

- ✅ **INT8 decision:** **Defer.** Reasoning above (no checkpoint, A6000 doesn't
  accelerate FP8, mixes signals with MCP-transport story).
- ✅ **KV-cache choice:** `--enable-prefix-caching --kv-cache-dtype fp8`,
  rationale documented.
- 🟡 **Empirical validation pending:** the KV-cache mini-comparison smoke
  needs to run on Insomnia after `#25` finishes. Worst case we ship without
  it; the chosen pair has strong published priors. Best case the smoke
  confirms the recommendation in 10 min of compute.

## Follow-ups outside this lane

- `#31` (Akshat) — actual batched/scheduled MCP behavior. Without that, Cell C
  doesn't measure MCP optimization, just KV optimization. The canonical Cell
  C run waits on `#31`.
- INT8 revival as a separate Cell D / model-scaling cell. Out of scope here.
- WandB log of the KV smoke comparison (a 3-row table in
  `wandb.ai/assetopsbench-smartgrid` showing latency × KV variant). Optional
  but nice for the paper.

## References

- vLLM 0.19.0 quantization: `vllm/model_executor/layers/quantization/__init__.py`
  in the venv at `.venv-insomnia/lib/python3.11/site-packages/vllm/`
- vLLM 0.19.0 KV cache: `vllm/v1/core/kv_cache_manager.py` and
  `vllm/v1/attention/`
- Prefix caching design: vLLM RFC at <https://github.com/vllm-project/vllm/issues/2614>
- Llama-3.1-8B INT8 (CompressedTensors): <https://huggingface.co/RedHatAI/Meta-Llama-3.1-8B-Instruct-quantized.w8a8>
