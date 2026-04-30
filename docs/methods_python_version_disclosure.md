# Methods-section disclosure: Python interpreter version skew across cells

*Drafting note for the paper's Experimental Setup / Implementation Details section. Per backlog cleanup pin: "Y baseline 3.12 vs others 3.11 — fairness contract caveat documented; methods-section disclosure language needed."*

## Suggested wording (formal-academic register)

> **Orchestration client interpreter.** Five of the six PE-family conditions
> (Cell B AaT, Cell Y+SA, Cell Z, Cell Z+SA, and the Cell A direct AaT) execute
> their orchestration clients under Python 3.11 from a shared `uv`-managed
> virtual environment (`.venv-insomnia`). The sixth condition, Cell Y vanilla
> Plan-Execute, runs upstream AssetOpsBench's `plan-execute` CLI under its
> pinned Python 3.12 toolchain via `uv run plan-execute` from the upstream
> AssetOpsBench repository. We keep Cell Y on the upstream toolchain
> deliberately to evaluate "vanilla AOB Plan-Execute as published" rather than
> a monkey-patched 3.11-compatible variant.
>
> The interpreter version difference is confined to the orchestration client.
> The model server (vLLM 0.19.0 serving Llama-3.1-8B-Instruct), the four MCP
> servers (`iot`, `fmsr`, `tsfm`, `wo`), the scenario slice, and the decoding
> parameters (`temperature=0.0`, `max_tokens=0`) are identical across all
> conditions. Wall-clock measurements include model inference time and MCP
> tool execution time, which dominate orchestration-client interpreter
> overhead by approximately two orders of magnitude on the workloads we
> measure: per-trial wall clocks range from ≈12 s (Cell A direct) to ≈90 s
> (Cell Z verified PE), of which Python-side bookkeeping (`json`, `litellm`
> async calls, `pydantic` validation) accounts for under 1 s per trial in
> our profiling captures (`benchmarks/cell_*/raw/<run_id>/profiling/`). Per-cell
> latency comparisons are therefore dominated by orchestration-method effects,
> not interpreter effects.
>
> A reader who wants Cell Y on 3.11 for strict-parity ablation can re-run our
> Cell Y configuration against the repo-local
> `scripts/plan_execute_self_ask_runner.py --self-ask=false` path; we publish
> that wrapper as part of the artifact release for this purpose.

## Where this should appear

Most natural fit: paper § "Experimental Setup → Implementation Details" or
§ "Methods → Orchestration Implementations", as a final paragraph after the
table that lists per-cell runner files / configs / model.

If Cell Y comparisons are featured prominently in the headline tables (e.g.,
Y vs Y+SA Self-Ask lift, B vs Y AaT-vs-PE), the disclosure paragraph should
appear before those tables, not after.

## Backing artifacts (cite by repo-relative path)

- `docs/experiment2_capture_plan.md` § "Runner Python version caveat" (lines 35-46) — the in-repo policy doc that establishes this contract.
- Per-trial wall-clock distributions for the latency-dominance argument:
  `benchmarks/cell_*/raw/<run_id>/latencies.jsonl` plus `summary.json`
  per-cell (means / p50 / p95).
- Optional supplementary: `benchmarks/cell_*/raw/<run_id>/profiling/`
  nvidia_smi.csv + torch trace gzips when present, for the GPU-bound vs
  client-bound breakdown.

## What NOT to claim

- Do not claim "Cell Y on 3.12 is faster/slower because of the version skew" —
  the data won't support that and the workload is not interpreter-bound.
- Do not claim the version skew is unmeasurable; just claim it is dominated
  by other factors. Reviewers may ask for a strict-parity ablation; we have
  the wrapper to produce one if needed.

## TODO before paper-final

- [ ] Decide whether to include a strict-parity ablation table (Y on 3.11 via
      the repo-local wrapper). Cheap to produce; adds reviewer-defensibility.
- [ ] Confirm the per-trial Python-side bookkeeping budget (≈1 s claim above)
      against actual trace data — the current number is an estimate from PE
      smoke captures; tighten with the canonical Y / Y+SA captures.
- [ ] If we keep the canonical Cell Y captures from `8998340_*` (Python 3.12
      / Tanisha's `/insomnia001/home/tr2828/smartgrid/.venv312`), name the
      venv path explicitly in the disclosure footnote so future readers can
      reproduce the exact toolchain.
