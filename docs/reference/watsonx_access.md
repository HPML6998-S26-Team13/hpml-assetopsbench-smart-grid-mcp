# WatsonX.ai Access

*Last updated: April 18, 2026*  
*Verified by: Wei Alexander Xin*

## Overview

Dhaval Patel (IBM mentor) provided the team with a WatsonX.ai project account for
accessing IBM-hosted Llama models. This document describes what's available, how to
set up access locally, and how we plan to use it in the project.

Current planning default:
- use self-hosted Llama-3.1-8B-Instruct on Insomnia for the main local benchmark grid
- use WatsonX Maverick-17B for judge calls
- use WatsonX Llama-3.3-70B-instruct only for selective scaling spot-checks rather than a duplicated full-grid run plan

**Repo location:** Everything in this doc (`.env`, `.venv/`, `scripts/verify_watsonx.py`)
lives in the canonical team repo at [HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp).
Alex's personal repo is now only a mirror. If you have a different local checkout,
point it at the org repo `main` branch before treating it as source of truth.

## Setup

1. Credentials live in `.env` at the repo root (gitignored). Ask Alex for the values.
   Required variables:

   ```
   WATSONX_PROJECT_ID=...
   WATSONX_API_KEY=...
   WATSONX_URL=https://us-south.ml.cloud.ibm.com
   ```

2. Use the team `uv venv` (already exists at `.venv/`). If you don't have one yet:

   ```bash
   cd ~/coding/hpml-assetopsbench-smart-grid-mcp
   uv venv          # creates .venv/ if missing
   ```

3. Install the SDK into the team venv:

   ```bash
   uv pip install ibm-watsonx-ai
   ```

   The SDK currently pins `pandas<2.4`, which forces pandas down to 2.3.3 in this venv.
   Don't install ibm-watsonx-ai into your conda `AI_env` if you have one - it'll
   downgrade pandas there too. Keep WatsonX work isolated to the team `.venv`.

4. Verify access (use the venv python directly so we don't depend on activation state):

   ```bash
   .venv/bin/python scripts/verify_watsonx.py --list-only
   ```

   You should see 6 Llama models listed. Then test inference:

   ```bash
   .venv/bin/python scripts/verify_watsonx.py --model meta-llama/llama-4-maverick-17b-128e-instruct-fp8
   ```

   A successful verification run should:
   - print the WatsonX host URL and authenticate cleanly
   - list matching models without exposing secret values
   - return a non-empty completion payload for the chosen model

   For latency measurements:

   ```bash
   .venv/bin/python scripts/verify_watsonx.py \
     --model meta-llama/llama-4-maverick-17b-128e-instruct-fp8 \
     --benchmark --trials 5 --max-tokens 128
   ```

## Available Models

Verified April 5, 2026 via `verify_watsonx.py`. All 6 Llama models are accessible with
our project credentials:

| Model ID | Role in project | Notes |
|----------|-----------------|-------|
| `meta-llama/llama-4-maverick-17b-128e-instruct-fp8` | **LLM-as-Judge** (primary) | 17B active params, 128 experts, FP8 quantized. Matches AssetOpsBench's judge model. |
| `meta-llama/llama-3-3-70b-instruct` | **Scaling comparison** | FP8 quantized. Use for Phase 3 datapoint showing performance vs 8B on same workload. |
| `meta-llama/llama-3-1-8b` | Fallback only | **Base model, not instruction-tuned.** Not suitable as a direct replacement for our primary Llama-3.1-8B-Instruct (which we self-host on Insomnia). |
| `meta-llama/llama-3-1-70b-gptq` | Unused | Older 70B, GPTQ quantized. Llama-3.3-70B-instruct is strictly better for our needs. |
| `meta-llama/llama-3-2-11b-vision-instruct` | Unused | Vision model, not relevant to our text-only agent pipeline. |
| `meta-llama/llama-guard-3-11b-vision` | Unused | Content moderation / safety model, not relevant. |

**Important:** WatsonX does not have `llama-3-1-8b-instruct` (the instruction-tuned
8B model we use for primary profiling). This is fine because we self-host that model
on Insomnia via vLLM - WatsonX can't give us the GPU-level profiling traces we need
for Phase 2 anyway. WatsonX fills gaps WHERE self-hosting is impractical: the judge
(34GB) and the 70B scaling datapoint (140GB).

## Usage Patterns

### Simple inference call

```python
import os
from pathlib import Path
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference

# Load .env (or use python-dotenv)
for line in Path(".env").read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        k, _, v = line.partition("=")
        os.environ[k.strip()] = v.strip()

creds = Credentials(
    url=os.environ["WATSONX_URL"],
    api_key=os.environ["WATSONX_API_KEY"],
)

model = ModelInference(
    model_id="meta-llama/llama-4-maverick-17b-128e-instruct-fp8",
    credentials=creds,
    project_id=os.environ["WATSONX_PROJECT_ID"],
)

response = model.generate_text(
    prompt="Evaluate this agent trajectory: ...",
    params={"max_new_tokens": 256, "temperature": 0.1},
)
```

### Where to use WatsonX

WatsonX-hosted rows do not need a local GPU. The client machine only runs the
benchmark harness, MCP/direct tool code, artifact writing, and API requests;
the 70B / judge inference happens on IBM-hosted infrastructure. A laptop,
Insomnia CPU/login context, or non-GPU GCP VM can run these jobs when it has
the repo checkout, Python environment, credentials, network, and enough
wall-clock time.

| Workload | Use WatsonX? | Why |
|----------|--------------|-----|
| Llama-3.1-8B-Instruct profiling (Phase 2) | No | Need GPU-level traces from self-hosted vLLM on Insomnia |
| Llama-3.1-8B-Instruct serving for agent runs | Maybe | Primary path is Insomnia vLLM; WatsonX only if 3.1-8B base is acceptable (probably not) |
| Llama-3.3-70B scaling comparison (Phase 3) | Yes | 140GB too expensive to self-host for one datapoint |
| Llama-4-Maverick-17B judge (Phase 4) | Yes | 34GB model, free via WatsonX, matches AssetOpsBench |

## Verified Inference + Latency (April 5, 2026)

Test prompt (smoke test, all runs): *"Answer in one short sentence: What is a smart grid?"*
- ~10 input tokens, `max_new_tokens=128`, `temperature=0.1`
- 1 cold call + 5 warm trials per model
- All requests serial, single client, no batching

### Llama-4-Maverick-17B (`meta-llama/llama-4-maverick-17b-128e-instruct-fp8`)

| Metric | Value |
|---|---|
| Cold call | 1.43s |
| Warm avg | 1.52s (5 trials) |
| Warm range | 1.41s - 1.58s |
| Approx tokens/sec | ~84 |

**Verdict:** Fast and consistent. Cold ≈ warm (model is hot on the backend). Variance
is tight (~10%). Suitable for interactive use.

### Llama-3.3-70B-instruct (`meta-llama/llama-3-3-70b-instruct`, FP8)

| Metric | Value |
|---|---|
| Cold call | 19.51s |
| Warm avg | 6.59s (5 trials) |
| Warm range | 1.65s - 16.33s |
| Approx tokens/sec | ~19 |

**Verdict:** Highly variable. Two of five warm trials were 1.6-2.0s (similar to Maverick),
the other three were 11-16s. The wide variance and slow cold call suggest the model is
not pinned to GPU and is being loaded on demand. **Implication:** for our scaling
comparison datapoint, we should run several trials and report distribution, not a single
number - the warm path is bursty.

### Caveats

- These are **end-to-end wall-clock latencies** from a Mac in NYC to `us-south` (Dallas),
  not pure model inference time. Network adds ~50-100ms.
- Single-prompt, single-client, serial. Real workloads will have queueing, batching effects.
- `temperature=0.1` is near-greedy; temperature 0 might be slightly faster.
- Both models actually generated less than 128 tokens in the response (early stop on EOS),
  so the "tokens/sec" estimate is a lower bound on real throughput.

## Long-prompt Benchmark: Code Review (April 5, 2026)

To validate behavior under realistic workloads, we also ran a ~1400-input-token code
review prompt (`scripts/benchmark_prompts/code_review_long.txt`) with `max_new_tokens=500`.
The prompt asks the model to review a multi-file MCP server implementation for
correctness, security, performance, and protocol compliance.

| Model | Cold | Warm avg | Warm range | Approx tok/s |
|---|---|---|---|---|
| Maverick-17B | 7.34s | 6.35s (3 trials) | 6.12s - 6.72s | ~79 |
| Llama-3.3-70B | 14.52s | 14.76s (3 trials) | 14.08s - 15.29s | ~34 |

**Key observations:**

1. **Maverick's throughput is stable at ~80 tok/s** regardless of prompt length (84 tok/s
   at 128 tokens, 79 tok/s at 500 tokens). Round-trip plus processing scales roughly
   linearly with output length.

2. **70B's variance disappears on longer runs.** The short-prompt benchmark showed wild
   variance (1.65s - 16.33s across 5 trials at 128 tokens). At 500 tokens the warm range
   is a tight 14.1-15.3s. Hypothesis: shorter requests sometimes get routed to a cold
   instance and eat a warm-up hit; longer requests either amortize the warm-up or
   consistently land on hot instances. For our scaling comparison we should prefer
   longer-generation scenarios and run several trials.

3. **Maverick is ~2.3x faster than 70B** on matched workloads (6.35s vs 14.76s). Given
   that Maverick is 17B active params (Llama 4 MoE) and 70B is dense, this is expected.

4. **Quality was qualitatively similar on this code review task.** Both models correctly
   identified the path traversal vulnerability, string-timestamp comparison bug, unbounded
   cache growth, and missing error handling. Neither flagged the `compute_rolling_stats`
   iteration bug (`for col in df.columns` without excluding non-numeric columns beyond
   `timestamp`). Both are usable for "second opinion" code review.

### Can we use Maverick for general code review?

Technically yes - ~6s for a 500-token review is interactive-speed, and the quality on our
test prompt was solid. But a few caveats:

- **Usage-policy risk:** WatsonX access was granted for the project. If usage analytics
  flag heavy non-project queries, Dhaval/IBM might pull access. Keep general-purpose
  code review on Claude/Codex; reserve WatsonX for project work and occasional experiments.
- **Quality ceiling:** Maverick is strong for a 17B active-param model, but noticeably
  below Claude Sonnet 4.6 / GPT-5 for deep architectural critique. Good as a second
  opinion, not as a primary reviewer.
- **No tool use, no multi-turn:** The `generate_text` endpoint is single-shot completion.
  If you want agent-style iterative review, you'd need to build that harness yourself.

Sample responses:

**Maverick-17B:**
> A smart grid is an electricity network that uses digital technology to monitor and
> manage the transport of electricity from all generation sources to meet the varying
> electricity demands of end users.

**Llama-3.3-70B-instruct:**
> A smart grid is a modernized electrical grid that uses advanced technologies to
> manage and distribute electricity efficiently and reliably.

## Limits and Gotchas

- **Base vs instruct:** WatsonX has `llama-3-1-8b` (base) not `llama-3-1-8b-instruct`.
  For anything requiring instruction-following or chat, use our self-hosted Insomnia
  deployment instead.
- **Region:** All endpoints are in `us-south` (Dallas). Expect some latency from NYC.
- **Quotas:** Not yet documented. If we hit rate limits during heavy use, check
  WatsonX console at https://dataplatform.cloud.ibm.com/ for our project's usage tier.
- **API key rotation:** The current key is shared across the team. After the project
  concludes, Dhaval should rotate or we should request individual keys.

## References

- Verification script: `scripts/verify_watsonx.py`
- WatsonX Python SDK docs: https://ibm.github.io/watsonx-ai-python-sdk/
- WatsonX console: https://dataplatform.cloud.ibm.com/
- Foundation model specs API: `client.foundation_models.get_model_specs()`
