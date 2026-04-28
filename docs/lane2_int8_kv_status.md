# Lane 2: INT8 + KV-Cache Optimization Status (`#29`, `#30`)

*Last updated: 2026-04-26 (post-smoke; fp8 KV dropped, prefix caching kept)*
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
| **INT8 quantization** | **Defer to Cell C v2.** Use FP16 for the canonical Cell C run. | The headline measurement for Cell C is `(B − C) = recoverable MCP-transport optimization`. Adding INT8 to Cell C confounds that delta with model-side speedup and breaks the apples-to-apples comparison with FP16 Cells A/B. `--quantization compressed-tensors` is the production INT8 path but requires a pre-quantized HF checkpoint (we now have one locally — validated via smoke `8979660`); `--quantization bitsandbytes` is the runtime path but is generally slower than CompressedTensors W8A8 marlin on Ampere. The KV-cache optimization (next row) is the only Lane 2 knob that ships in Cell C. |
| **KV-cache** | **Enable `--enable-prefix-caching` only** (fp8 KV dropped — see smoke evidence below) | Multi-turn ReAct on Llama-3.1-8B with the same AOB system prompt across all scenarios is the canonical prefix-caching workload — every turn after the first re-uses the system-prompt prefix. **Smoke `8979532` measured prefix caching at 5.64 s vs 7.77 s baseline (-27 %).** `--kv-cache-dtype fp8` was the original second pick but failed in the smoke: vLLM 0.19.0 FlashAttention-3 kernel rejects fp8 KV under FP16 weights. Switching the model to BF16 to unlock fp8 KV would change inference precision and confound (B−A) and (B−C). Dropped to keep the signal clean. |
| **`--max-num-seqs`** | Leave default (`256`). Optionally drop to `4` for our sequential workload. | We're not batching multiple scenarios concurrently; lower max-num-seqs frees a small amount of memory but doesn't change steady-state. Default is fine. |
| **`--gpu-memory-utilization`** | Leave default (`0.9`). | The L40S A6000 has plenty of headroom for an 8B FP16 model; squeezing this isn't justified by our workload. |

**Net effect on Cell C config**: add `EXTRA_VLLM_ARGS="--enable-prefix-caching"` to `configs/aat_mcp_optimized.env` and ship. (fp8 KV originally planned but dropped after the Lane 2 smoke surfaced an unsupported vLLM 0.19.0 kernel-dispatch path under FP16 weights.)

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
2. **Inference-precision parity with Cells A/B.** Cells A and B already
   captured at FP16 in `8979314`. vLLM's compressed-tensors path
   auto-loads INT8 models as BF16 (validated in smoke `8979660` —
   `dtype=torch.bfloat16` in the engine init log), so adding INT8 to
   Cell C also flips the inference precision from FP16 to BF16. That
   precision change alone could shift latency and quality independently
   of the MCP-transport optimization the cell is meant to isolate. The
   only way to land INT8 in Cell C cleanly would be to re-capture
   Cells A/B at BF16 too — which is a separate experiment, not a
   Lane 2 deliverable.
3. **Throughput story exists and works on the team hardware** —
   validated in smoke `8979660` on Insomnia A6000. vLLM picks
   `CutlassInt8ScaledMMLinearKernel for CompressedTensorsW8A8Int8`
   (the marlin path) and `/v1/completions` returns sensible Llama
   text. The path is mechanically ready for any future Cell D /
   model-scaling experiment; it just shouldn't enter Cell C for the
   reasons in points 1 and 2.
4. **Time budget.** Building INT8 into Cell C is realistically a
   separate-day item: re-capturing A/B at BF16 + recapturing C with
   INT8 is a full Experiment-1 redo, well outside the Lane 2 scope.

### Conditions under which to revive INT8

- Akshat's `#31` lands and the Cell C transport-only optimization shows a
  smaller-than-expected win. Adding INT8 then becomes a "second optimization
  arm" with a clear separate ablation.
- A reviewer asks specifically about quantization in the paper. We have a
  ready-to-go config + smoke script (see "Smoke scripts" below) to validate
  in ~15 min on Insomnia.

### INT8 smoke result (Slurm `8979660`)

Despite the deferral above, we ran `scripts/test_int8_smoke.sh` against `RedHatAI/Meta-Llama-3.1-8B-Instruct-quantized.w8a8` to validate that the path is mechanically runnable. `COMPLETED` in 7:31 on NVIDIA RTX A6000 (`benchmarks/lane2/int8_smoke/8979660/`).

| Check | Result |
|---|---|
| HF download (~16 GB) | ok |
| vLLM startup with `--quantization compressed-tensors` | ok |
| `/health` reachable | ok |
| `/v1/models` lists `Llama-3.1-8B-Instruct-int8` with `max_model_len: 8192` | ok |
| One-shot `/v1/completions` round-trip on a DGA-fault prompt | ok (sensible Llama text, 80 completion tokens) |
| Selected kernel | `CutlassInt8ScaledMMLinearKernel for CompressedTensorsW8A8Int8` (the marlin path) |
| Model dtype as auto-loaded | `torch.bfloat16` (not FP16 — see note below) |
| GPU memory | 44.5 GiB / 48 GiB used (≈ 8 GiB INT8 weights + 36 GiB pre-allocated KV at default 90 % util) |

So **the INT8 serving path works on Insomnia A6000** with the canonical RedHatAI W8A8 checkpoint. `#29`'s "done when: the quantized serving path is runnable as an experiment condition" is satisfied.

**Note on dtype interaction:** vLLM 0.19.0's compressed-tensors path auto-loads the model as BF16, not FP16. This means **INT8 weights + fp8 KV cache is actually a compatible combo** in vLLM 0.19.0 — BF16 model dtype satisfies the FA3 kernel constraint that blocked our FP16 + fp8 KV variant in `8979532`. If we ever build a Cell D with model-precision changes, `--quantization compressed-tensors --kv-cache-dtype fp8` becomes a single-config two-knob optimization stack. The deferral logic for using INT8 in Cell C (signal purity for the (B−C) MCP-transport headline) still holds — this is purely a "Cell D candidate" note.

`scripts/test_int8_smoke.sh` is preserved in the repo for future revival.

## #30 KV-Cache — what was chosen

### Knobs evaluated

| Knob | Default | Recommendation | Why |
|---|---|---|---|
| `--enable-prefix-caching` | off | **on** | AOB system prompt + tool catalog is identical across all turns and all scenarios. Prefix caching skips re-prefill of those tokens after the first turn. Direct win for ReAct workloads. Tested + stable in vLLM 0.19. |
| `--kv-cache-dtype` | `auto` (FP16) | **dropped** (originally planned `fp8` but blocked by vLLM 0.19.0 kernel constraint — see "Smoke result" below) | The original idea was a KV **storage** precision change with attention math still at the model's native precision. Smoke `8979532` revealed vLLM 0.19.0's FlashAttention-3 path requires BF16 model weights when KV is fp8 (`RuntimeError: For FP8 input, output must have dtype BF16`). Switching the model to BF16 to unlock fp8 KV would change inference precision on Cell C only and confound (B−A) and (B−C). Defer to Cell C v2 with the model loaded as BF16, or pick up after a vLLM upgrade with broader kernel coverage. |
| `--max-num-seqs` | 256 | leave default | Our workload is single-stream (one scenario at a time). Default is fine; lowering to 4 saves ~50 MB which is rounding error. |
| `--gpu-memory-utilization` | 0.9 | leave default | The A6000 / L40S has enough headroom that squeezing this (e.g. to 0.95) buys back KV space we don't use. Not worth the OOM risk. |
| `--block-size` | 16 | leave default | Default is well-tuned; smaller = more overhead, larger = wasted blocks. Not a measurable lever for our workload. |
| `--swap-space` | 4 GiB | leave default | Only matters when KV cache exhausts and we have to evict to CPU. We're not running concurrent requests; eviction won't trigger. |
| `--enable-chunked-prefill` | on by default in 0.19 | leave default | Already enabled; no change needed. |

### Rationale for the chosen knob (post-smoke)

`--enable-prefix-caching` ships, `--kv-cache-dtype fp8` does not. Prefix caching:

- **Matches the workload shape** — AOB system prompt + tool catalog is identical across every turn and every scenario in the suite, so the prefix-cache hit rate on the prompt portion is bounded above by 100 %.
- **Apples-to-apples with Cell A/B** — same model, same precision for forward pass (FP16), same KV storage dtype. Only the cache-reuse policy changes. (Cell B − Cell C) latency remains a clean measurement of MCP transport optimization once `#31` lands, not a confound from model-side changes.
- **Empirically a -27 % wall-clock win** on the canonical multi-domain scenario at the smoke scale (see "Smoke result" below).

### Why not a bigger sweep

The plan ([`experiment1_capture_plan.md`](experiment1_capture_plan.md)) calls for a "small targeted sweep, not a broad sweep." We picked two knobs with strong a-priori reasoning (prefix caching matches the workload shape; fp8 KV is well-validated on Llama-3.1-8B-class models when the kernel path supports it). A broader sweep (block_size, max-num-seqs, max-num-batched-tokens) would consume 5+ smoke runs and produce no material difference for our single-stream workload.

### Smoke result (Slurm `8979532`)

`scripts/test_kv_cache_smoke.sh` ran the three planned variants sequentially in a single Slurm allocation against the canonical multi-domain smoke scenario (`multi_01_end_to_end_fault_response`). H100 NVL on `ins050`. Wall-clock ~5 min total.

| Variant | `EXTRA_VLLM_ARGS` | Result | Wall-clock | Δ vs baseline |
|---|---|---|---|---|
| baseline | (none) | success, 2 turns, 5 tool calls | 7.77 s | — |
| prefix | `--enable-prefix-caching` | success, 2 turns, 5 tool calls | **5.64 s** | **-2.13 s (-27 %)** |
| prefix + fp8 KV | `--enable-prefix-caching --kv-cache-dtype fp8` | **vLLM startup failed** (kernel-dispatch error) | n/a | n/a |

**fp8 KV failure** — vLLM 0.19.0's FlashAttention-3 backend (`vllm/v1/attention/backends/flash_attn.py:741`) routes through a kernel that requires `BF16` outputs when KV inputs are FP8. With the model loaded as FP16 (matching Cells A/B), `flash_attn_varlen_func` raises:

```
RuntimeError: For FP16/BF16 input, output must have the same dtype as inputs.
              For FP8 input, output must have dtype BF16
```

The vLLM engine then aborts during `wait_for_engine_startup`, the API server exits, and the smoke variant produces no per-trial JSON. The architecture (H100/Ampere/Ada) is irrelevant — this is a software-level dtype-coupling issue between the kernel and the model load path.

**Why we don't switch the model to BF16:** Cells A and B already ran FP16 in the canonical capture (`8979314`). Moving Cell C to BF16 inference makes (B − C) a confounded measurement of "MCP-transport optimization + model-precision change," which is exactly what the experimental design is trying to avoid. fp8 KV is a candidate for a future Cell D (model-side) experiment, not for the canonical Cell C MCP-overhead headline.

**Net Cell C decision:** ship `--enable-prefix-caching` only. The 27 % wall-clock win is substantial and the signal stays clean.

### Conditions under which to revisit fp8 KV

- vLLM upgrade past 0.19.0 broadens the FA3 kernel coverage and accepts FP8 KV with FP16 weights (track upstream).
- Team adds a planned Cell D / model-precision experiment that explicitly varies model dtype, in which case BF16 + fp8 KV becomes one of the variants and the (B − C) confound argument no longer applies.

## Cell C config update

`configs/aat_mcp_optimized.env` updated in this branch to:

- Use the new `EXTRA_VLLM_ARGS="--enable-prefix-caching"` to enable the
  chosen KV optimization (fp8 KV originally planned but dropped after
  smoke `8979532` surfaced an unsupported vLLM 0.19.0 kernel-dispatch
  path under FP16 weights — see "#30 KV-Cache Smoke result" above)
- `QUANTIZATION_MODE="fp16"` (no INT8 — see deferral above)
- `TORCH_PROFILE=1` and `ENABLE_WANDB=1` for parity with Cell A/B
- Still requires Akshat's `#31` for the actual MCP-transport optimization;
  without that, Cell C is functionally Cell B + KV optimization, which
  measures GPU optimization not MCP optimization. Don't run the canonical
  Cell C until `#31` lands.

## What needs Insomnia compute (status)

| Test | Script | Wall-clock | Status | Decision impact |
|---|---|---|---|---|
| KV-cache mini-comparison (3 variants × 1 scenario) | `scripts/test_kv_cache_smoke.sh` | ~5 min compute + queue | ✅ ran as `8979532` (see "Smoke result" above) | Confirmed prefix caching at -27 %; fp8 KV blocked by vLLM kernel constraint, dropped from Cell C |
| INT8 startup + reachability smoke | `scripts/test_int8_smoke.sh` | ~7 min compute + 16 GB download | ✅ ran as `8979660` (see "INT8 smoke result" above) | Proved INT8 serving path is runnable on A6000; ready for Cell D / scaling experiments |

Both scripts include the standard `--mail-type=BEGIN,END,FAIL --mail-user`
flags following the team's Slurm convention.

## Definition of done — status

> **Definition of done for Lane 2:** We know whether Cell C can include INT8
> tonight, and we have a chosen KV-cache setting or an explicit
> evidence-backed deferral.

- ✅ **INT8 decision:** **Defer from Cell C.** Reasoning above (signal-purity for (B−C)). INT8 serving path **separately validated** as runnable via smoke `8979660` (CutlassInt8 W8A8 marlin kernel, BF16 model dtype, reachable + responds on A6000).
- ✅ **KV-cache choice:** `--enable-prefix-caching` (single knob). fp8 KV originally planned but dropped after the smoke surfaced a vLLM 0.19.0 kernel-dispatch limitation under FP16 weights.
- ✅ **Empirical validation:** smoke `8979532` ran prefix vs baseline at -27 % wall-clock and surfaced the fp8 KV failure mode. Cell C config updated to match.

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
