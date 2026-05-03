# Experiment Matrix and Follow-On Conditions

*Last updated: 2026-05-03*  
*Owner: Alex Xin*  
*Issues: core framing for `#25`, `#32`, `#35`, `#64`, `#5`*

This note keeps the experiment matrix honest and small. It distinguishes:

- the **core cells** the paper must land cleanly
- the **variant flags** already supported in repo-local runners
- the **optional follow-on cells** that could be worth adding if the core grid
  lands early

## Short answer

Current first-capture results table. A machine-readable copy lives at
`results/metrics/experiment_matrix_summary.csv`; the focused optimized-serving
follow-on deltas live at `results/metrics/optimized_serving_ablation.csv`.

| Legacy | Display code | Meaning | Run | Status | N | Canonical | Success | p50 latency | p95 latency | Judge score | Judge pass |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A | AT-I | Agent-as-Tool direct Python tools | `8979314_aat_direct` | success | 6 | 6/6 | 1.00 | 12.15 | 17.29 | 0.167 | 1/6 (16.7%) |
| B | AT-M | Agent-as-Tool MCP baseline | `8979314_aat_mcp_baseline` | success | 6 | 6/6 | 1.00 | 13.09 | 16.27 | 0.278 | 2/6 (33.3%) |
| C | AT-TP | Agent-as-Tool optimized MCP transport + prefix cache | `9071639_aat_mcp_optimized` | success | 6 | 6/6 | 1.00 | 7.40 | 47.93 | 0.167 | 0/6 (0.0%) |
| D | AT-TPQ | Agent-as-Tool optimized MCP transport + INT8/BF16/fp8 KV | `9073472_aat_mcp_model_optimized` | success | 6 | 6/6 | 1.00 | 6.17 | 16.01 | 0.167 | 1/6 (16.7%) |
| Y | PE-M | Plan-Execute MCP baseline | `8998340_exp2_cell_Y_pe_mcp_baseline` | partial | 6 | 6/6 | 0.50 | 52.06 | 116.32 | 0.111 | 0/6 (0.0%) |
| YS | PE-S-M | Plan-Execute + Self-Ask MCP baseline | `8998341_exp2_cell_Y_pe_self_ask_mcp_baseline` | success | 6 | 6/6 | 1.00 | 59.00 | 83.20 | 0.444 | 3/6 (50.0%) |
| Z | V-M | Verified PE MCP baseline | `8998342_exp2_cell_Z_verified_pe_mcp_baseline` | success | 6 | 6/6 | 1.00 | 119.64 | 152.36 | 0.639 | 4/6 (66.7%) |
| ZS | V-S-M | Verified PE + Self-Ask MCP baseline | `8998343_exp2_cell_Z_verified_pe_self_ask_mcp_baseline` | success | 6 | 6/6 | 1.00 | 33.78 | 58.03 | 0.833 | 5/6 (83.3%) |
| ZSD | V-S-TPQ | Verified PE + Self-Ask + optimized MCP/model stack | `9074775_exp2_cell_ZSD_verified_pe_self_ask_mcp_model_optimized` | success | 6 | 6/6 | 1.00 | 55.17 | 107.39 | 0.611 | 3/6 (50.0%) |

Current recommendation on trials:

- **First complete artifact chain:** `3` trials per `(cell, scenario, model)` is acceptable.
- **Final canonical run set:** `5` trials per `(cell, scenario, model)` should be the default.

The harness semantics are:

```text
for each cell
  for each scenario file
    for each trial in 1..TRIALS
      run once
```

So yes: `Cell A + Scenario 1 + Llama-3.1-8B-Instruct + 5 trials` means five
independent runs under the same config, then aggregate in `summary.json` and the
analysis notebooks.

## Inspecting a run

Every row above has a raw run directory under `benchmarks/cell_*/raw/<run-name>/`.
For example, to inspect `8979314_aat_direct`:

- run-level metadata: `benchmarks/cell_A_direct/raw/8979314_aat_direct/meta.json`
- per-trial latencies: `benchmarks/cell_A_direct/raw/8979314_aat_direct/latencies.jsonl`
- per-trial trajectories: `benchmarks/cell_A_direct/raw/8979314_aat_direct/*_runNN.json`
- runner logs: `benchmarks/cell_A_direct/raw/8979314_aat_direct/harness.log` and `vllm.log`
- replay proof: `benchmarks/cell_A_direct/raw/8979314_aat_direct/replay/`
- cell-level summary snapshot: `benchmarks/cell_A_direct/summary.json`
- judge rows: `results/metrics/scenario_scores.jsonl` filtered by `run_name`
- judge audit logs: `results/judge_logs/8979314_aat_direct/`

The same pattern works for B/C/D/Y/Z/ZS/ZSD. The CSV summary includes the raw
directory path so a notebook or script can jump from the compact table to full
artifacts.

## Optimized Serving Ablation

The exploratory optimized-serving comparison is intentionally separated from
the core A/B/C and B/Y/Z notebook tables:

| Comparison | Baseline | Variant | p50 delta | p95 delta | Judge score delta | Judge pass delta | Interpretation |
|---|---|---|---:|---:|---:|---:|---|
| AaT optimized serving over optimized transport | AT-TP `9071639_aat_mcp_optimized` | AT-TPQ `9073472_aat_mcp_model_optimized` | -1.23 | -31.92 | +0.000 | +0.167 | Cell D improved first-capture AaT latency versus Cell C, but judge quality stayed equally weak. |
| Verified PE + Self-Ask optimized serving | V-S-M `8998343_exp2_cell_Z_verified_pe_self_ask_mcp_baseline` | V-S-TPQ `9074775_exp2_cell_ZSD_verified_pe_self_ask_mcp_model_optimized` | +21.39 | +49.36 | -0.222 | -0.333 | Adding optimized serving to the current best PE-family runner slowed the first-capture run and reduced judge pass rate. |

Machine-readable copy:
`results/metrics/optimized_serving_ablation.csv`.

## Runnable today vs pending

What we can honestly run on the current runner surface right now:

| Condition | Status | Why |
|---|---|---|
| `A` | analysis-ready first capture | Slurm job `8979314_aat_direct` completed `6 / 6`, with judge rows and canonical scenario embedding |
| `B` | analysis-ready first capture | Slurm job `8979314_aat_mcp_baseline` completed `6 / 6`, with judge rows and canonical shared-anchor metadata for Experiments 1 and 2 |
| `C` | analysis-ready first capture | Slurm job `9071639_aat_mcp_optimized` completed `6 / 6` with optimized batch/connection reuse and prefix caching; judge mean `0.167`, pass `0 / 6` |
| `D` | analysis-ready exploratory capture | Slurm job `9073472_aat_mcp_model_optimized` completed `6 / 6` with Cell C transport plus compressed INT8/BF16/fp8-KV serving; replay `2 / 2`, profiler `profiling-pmwzatie`, judge mean `0.167`, pass `1 / 6` |
| `Y` | analysis-ready first capture | Slurm job `8998340_exp2_cell_Y_pe_mcp_baseline` completed `3 / 6` successful trials; judge mean `0.111`, pass `0 / 6` |
| `Y + Self-Ask` | analysis-ready first capture | Slurm job `8998341_exp2_cell_Y_pe_self_ask_mcp_baseline` completed `6 / 6`; judge mean `0.444`, pass `3 / 6` |
| `Z` | analysis-ready first capture | Slurm job `8998342_exp2_cell_Z_verified_pe_mcp_baseline` completed `6 / 6`; judge mean `0.639`, pass `4 / 6` |
| `Z + Self-Ask` | analysis-ready first capture | Slurm job `8998343_exp2_cell_Z_verified_pe_self_ask_mcp_baseline` completed `6 / 6`; judge mean `0.833`, pass `5 / 6` |
| `Z + Self-Ask + D` | analysis-ready exploratory ablation | Slurm job `9074775_exp2_cell_ZSD_verified_pe_self_ask_mcp_model_optimized` completed `6 / 6` with persistent MCP sessions plus the Cell D INT8/BF16/fp8-KV serving profile; judge mean `0.611`, pass `3 / 6` |

Important distinction:

- **Runner-runnable** means there is a smoke-proven script/config path that can
  execute a condition.
- **Analysis-ready** means the canonical config has produced raw per-scenario
  JSONs under `benchmarks/cell_*/raw/<run-id>/` for the notebook contract.
- Current canonical history has first-capture, judge-scored raw run sets for
  A/B/C/Y/Z plus the Self-Ask and optimized-serving follow-ons. The remaining
  paper-depth gap is scale, not basic runner/artifact availability.

Important honesty rule:

- `MCP_MODE=optimized` is now a behaviorally distinct AaT transport path for
  Cell C. On the Insomnia vLLM / Llama-3.1-8B-Instruct path it means batch
  runner + MCP connection reuse + prefix caching, with sequential tool-call
  turns (`AAT_PARALLEL_TOOL_CALLS=false`).
- Exploratory Cell D deliberately changes the serving stack too: it uses the
  same optimized AaT MCP transport as Cell C, then adds the compressed-tensors
  INT8 checkpoint, BF16 dtype, and fp8 KV cache. Treat D as a follow-on
  "optimized serving" condition, not as evidence for the clean A/B/C transport
  delta.
- `MCP_MODE=optimized` is now wired for repo-local PE-family runners as a
  behaviorally distinct persistent-session path. The first committed follow-on
  is `Z + Self-Ask + D`; job `9074775` is its first successful Insomnia proof
  and judge-scored capture.

## Core design rule

Keep one variable fixed per experiment.

- **Experiment 1** fixes orchestration to AaT and varies transport: `A -> B -> C`.
- **Experiment 2** fixes transport to MCP baseline and varies orchestration:
  `B -> Y` and optionally `Z`.

That is why the repo does **not** currently commit to the full multiplicative
grid. If we vary orchestration and transport at the same time, we lose the clean
story for both experiments.

## How Self-Ask is tracked

Self-Ask is a **runner variant**, not a new official cell ID.

| Condition | Tracking shape |
|---|---|
| PE + Self-Ask | `Y` with `ENABLE_SELF_ASK=1` |
| Verified PE + Self-Ask | `Z` with `ENABLE_SELF_ASK=1` |
| Verified PE without Self-Ask | `Z` with `ENABLE_SELF_ASK=0` |

This matters for both notebooks and the paper. We should present Self-Ask as a
mitigation / ablation toggle on top of PE-family methods, not as a whole new
benchmark axis unless it becomes central enough to deserve that promotion.

This also means the right near-term Experiment 2 order is:

1. run `Y` using the canonical Experiment 2 config
2. promote and run a canonical `Y + Self-Ask` config
3. promote and run a canonical `Z` Verified PE config
4. promote and run a canonical `Z + Self-Ask` config
5. only then decide whether the optimized-transport follow-ons are honest to run

## How mitigation is tracked

The core experiment matrix stays focused on method cells and non-mitigation
ablations. Treat mitigation as a sparse overlay dimension, not as a full new
Cartesian product across every cell.

For the current missing-evidence ladder, the dense slice is:

```text
family lane: Y + Self-Ask, Z + Self-Ask
mitigation rung: baseline, detection guard, repair/replan recovery
scenario: data/scenarios/multi_*.json
trial: 1..TRIALS
```

The baseline rung already exists through `8998341` and `8998343`. The #66
runner plan therefore executes only the two new mitigation rungs for the two
family lanes, then records the outcome in
`results/metrics/mitigation_before_after.csv`.

This is closer to a sparse tensor slice than a new all-cells matrix. If the
scenario set later expands to 30 scenarios and the final trial target becomes
5, the mitigation slice is:

```text
2 family lanes x 3 rungs x 30 scenarios x 5 trials
```

It is not:

```text
all cells x all mitigations x all scenarios x all trials
```

Operator details for the current #66 rerun pass live in
`docs/mitigation_rerun_operator_plan.md`.

## Review of the two extra conditions

### 1. `Y + Self-Ask + MCP optimized`

Verdict: **worth keeping as the first optional follow-on condition** once the
core grid is real.

Why it is attractive:

- it stays aligned with the IBM-facing story: Plan-Execute remains the structured
  enterprise baseline
- it asks a practical question: does PE stay behind AaT mainly because of
  reasoning quality, or is some of the gap just transport friction?
- it combines two plausible production-facing mitigations rather than an
  academic-only ablation

Why it is not a core cell yet:

- it mixes two changes at once relative to `Y`: Self-Ask and optimized MCP
- it depends on the optimized MCP bundle for `C` becoming technically real first
- it should not be introduced before `B` and `Y` both have clean comparable
  baseline artifacts

Recommended interpretation if we run it:

- **not** a replacement for vanilla `Y`
- a follow-on cell answering: "How far can Plan-Execute be pushed with a cheap
  clarification hook plus better transport?"

### 2. `Z + Self-Ask + MCP optimized`

Verdict: **reasonable as a second optional follow-on, but only after the first
optional condition above**.

Why it is interesting:

- it is the strongest "best engineered PE-family" condition in the current repo
- it tests whether verifier gates + clarification + lower transport overhead
  together produce a materially better enterprise-style agent loop

Why it should come later:

- it is farther from the clean core paper claim
- it compounds three moving parts: verifier logic, Self-Ask, and optimized MCP
- if it beats everything else, the explanation becomes harder to defend cleanly
  without enough intermediate evidence

Recommended interpretation if we run it:

- a **best-effort engineered PE-family ceiling**, not part of the minimal
  honesty-preserving comparison

## Conditions we should not prioritize

### `Y + direct tools`

Recommendation: **do not prioritize**.

Reason:

- it weakens the IBM / MCP production story
- it expands the matrix without helping the main paper claim much
- it makes Experiment 2 less about orchestration under the team's actual MCP
  stack and more about an alternate plumbing path that IBM would not standardize on

### `Z + direct tools`

Recommendation: **do not prioritize** for the same reason, plus the verifier
logic is already enough complexity without adding an off-story transport mode.

### Full 8B / 70B duplicated grid

Recommendation: **do not run as a full matrix**.

Keep 70B as a spot-check lane only. The repo docs already treat 70B that way,
and that is the right tradeoff for time, cost discipline, and interpretability.

### Custom WatsonX deployment

Decision: **do not pursue a custom WatsonX deployment for the May 2026
submission**.

Hosted WatsonX 70B remains useful as a model-scale spot check, but it should not
be labeled as prefix-cached (`P`) or quantized/model-serving (`Q`) evidence
unless IBM exposes runtime metadata for those knobs. A custom WatsonX deployment
could make the serving stack more inspectable, but it adds access, quota,
hourly billing, model-upload, and runtime-debugging risk too close to the due
date. Use Insomnia-local vLLM for `P`/`Q` claims.

## Recommended sequence

1. Land the honest core cells: `A`, `B`, `C`, `Y`.
2. In parallel, while AaT is still pending, use the smoke-proven PE-family
   runners to promote and capture the baseline / Self-Ask ladder: `Y`,
   `Y + Self-Ask`, `Z`, `Z + Self-Ask`.
3. Add `Z` to the core report only if the optional third-method lane stays
   stable and analysis-ready after canonical raw artifacts land.
4. Treat Self-Ask as a PE-family ablation, not a headline cell explosion.
5. If the optimized MCP transport becomes behaviorally real outside AaT, run
   `Y + Self-Ask + MCP optimized`.
6. Run `Z + Self-Ask + D` as the current best-engineered PE-family ceiling now
   that the Cell D serving path has clean replay/judge proof.

## Promotion rule for optional follow-ons

Do not promote an optional condition into the active run queue unless all of
these are true:

1. the shared baseline artifacts for `B` and `Y` exist and are analysis-ready
2. the optimized MCP bundle is real enough to support `C`
3. the follow-on condition can get at least the same final trial count policy
   as the core cells
4. the paper can still explain the condition in one sentence without adding a
   new axis to the main claim

If any of those fail, keep the condition in the "interesting but not yet worth
running" bucket.

## What this means for the paper

Use Dhaval's framing carefully:

- **Benchmark reality:** AaT tends to win because ReAct gives reflection.
- **Production reality:** IBM still prefers Plan-Execute because it is more
  predictable and inspectable.

That makes the strongest paper structure:

1. show the clean baseline comparison honestly
2. show one or two targeted PE-family mitigations
3. avoid turning the paper into an uncontrolled matrix of every possible combo

## Current working recommendation

Default paper lane:

- Experiment 1: `A / B / C`
- Experiment 2: `B / Y`
- Optional follow-on: `Z`

Default mitigation / extension lane:

- `Y + Self-Ask` after canonical config promotion
- `Z + Self-Ask` after canonical config promotion
- if extra time exists: `Y + Self-Ask + MCP optimized`
- `Z + Self-Ask + D` as the strongest current ablation, now with first proof
  from job `9074775`

That keeps the story sharp:

- **core result:** transport cost and orchestration baseline
- **follow-on result:** whether structured PE-family methods can recover ground
  through lightweight reasoning and systems fixes
