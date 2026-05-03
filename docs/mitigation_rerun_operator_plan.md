# Mitigation Rerun Operator Plan

*Last updated: 2026-05-03*  
*Issues: #35, #36, #64, #66*

This is the runner-facing plan for the missing-evidence mitigation ladder.
It is written for whoever owns the compute session. The taxonomy lane consumes
the completed artifacts afterward.

## Goal

Produce the evidence needed to populate
`results/metrics/mitigation_before_after.csv` for #66:

1. detection-only guarded reruns for `Y + Self-Ask` and `Z + Self-Ask`
2. recovery reruns for the same two family lanes
3. judge rows for every new run
4. run IDs, artifact paths, and provenance sufficient for #35/#36/#64/#66

This is evidence work, not new mitigation implementation. The guard and
recovery code are already on `team13/main`.

## Current anchors

| Family lane | Baseline run | Detection config | Recovery config |
|---|---|---|---|
| `Y + Self-Ask` | `8998341_exp2_cell_Y_pe_self_ask_mcp_baseline` | `configs/mitigation/missing_evidence_guard_pe_self_ask.env` | `configs/mitigation/missing_evidence_repair_pe_self_ask.env` |
| `Z + Self-Ask` | `8998343_exp2_cell_Z_verified_pe_self_ask_mcp_baseline` | `configs/mitigation/missing_evidence_guard_verified_pe_self_ask.env` | `configs/mitigation/missing_evidence_repair_verified_pe_self_ask.env` |

The current configs use:

| Field | Value |
|---|---|
| model | `openai/Llama-3.1-8B-Instruct` |
| scenario glob | `data/scenarios/multi_*.json` |
| current scenario files | `multi_01_end_to_end_fault_response.json`, `multi_02_dga_to_workorder_pipeline.json` |
| trials | `3` |
| transport | MCP baseline |
| detection flag | `ENABLE_MISSING_EVIDENCE_GUARD=1` |
| recovery flag | `ENABLE_MISSING_EVIDENCE_REPAIR=1` for recovery configs only |

With the current two-scenario glob and `TRIALS=3`, each config should produce
six per-trial JSON files.

## Compute choice

Use GCP if Insomnia remains drained or unreliable. This is acceptable for #66
because the immediate target is mitigation behavior and artifact quality, not a
clean Insomnia-vs-GCP latency claim.

Do not silently compare GCP L4 latency against Insomnia A6000/A100 latency as
if they were the same hardware class. Record the host, GPU, git SHA, config
path, and dirty state in the run handoff.

## GCP config handling

The four canonical mitigation configs are Insomnia-shaped templates. They set
runtime fields directly, including:

```bash
SERVING_STACK="insomnia_vllm"
LAUNCH_VLLM=1
VLLM_MODEL_PATH="models/Llama-3.1-8B-Instruct"
```

Because `scripts/run_experiment.sh` sources the config file, exporting
different values before the command will not override assignments inside the
file. For GCP, use one of these approaches:

1. Preferred for publishable reruns: create GCP-specific copies of the four
   configs, preserving all scientific fields and changing only runtime /
   provenance fields such as `SERVING_STACK`, `VLLM_MODEL_PATH`, and any
   GCP-local serving knobs.
2. Acceptable for an emergency run: create temporary GCP config copies and
   preserve those exact files with the artifact handoff. Do not edit the four
   canonical Insomnia templates in place.

Scientific fields that should stay fixed unless Alex explicitly changes the
plan:

- `EXPERIMENT_NAME`
- `EXPERIMENT_CELL`
- `EXPERIMENT_FAMILY`
- `SCENARIO_SET_NAME`
- `SCENARIOS_GLOB`
- `MODEL_ID`
- `ORCHESTRATION`
- `MCP_MODE`
- `TRIALS`
- `ENABLE_SELF_ASK`
- `ENABLE_MISSING_EVIDENCE_GUARD`
- `ENABLE_MISSING_EVIDENCE_REPAIR`
- `MISSING_EVIDENCE_REPAIR_MAX_ATTEMPTS`
- `MISSING_EVIDENCE_REPAIR_MAX_ATTEMPTS_PER_TARGET`
- `CONTRIBUTING_EXPERIMENTS`
- `SCENARIO_DOMAIN_SCOPE`

## Execution order

Run in this order. Do not run recovery before detection-only rows exist.

| Order | Lane | Config | Purpose |
|---:|---|---|---|
| 1 | `Y + Self-Ask + guard` | `missing_evidence_guard_pe_self_ask.env` | Count unsupported clean completions in the PE+Self-Ask lane. |
| 2 | `Z + Self-Ask + guard` | `missing_evidence_guard_verified_pe_self_ask.env` | Count unsupported clean completions in the strongest PE-family lane. |
| 3 | `Y + Self-Ask + repair` | `missing_evidence_repair_pe_self_ask.env` | Test whether bounded retry can repair Y+SA evidence gaps inside the same trial. |
| 4 | `Z + Self-Ask + repair` | `missing_evidence_repair_verified_pe_self_ask.env` | Test whether detector-driven retry / suffix replan improves Z+SA outcomes. |

The recovery flags do not increase `TRIALS`. They allow at most two internal
repair attempts per trial, with at most one retry per unresolved evidence
target:

```bash
MISSING_EVIDENCE_REPAIR_MAX_ATTEMPTS=2
MISSING_EVIDENCE_REPAIR_MAX_ATTEMPTS_PER_TARGET=1
```

## Run commands

On GCP, run directly from the repo checkout, not through Slurm:

```bash
bash scripts/run_experiment.sh <gcp-adjusted-config>
```

For example:

```bash
bash scripts/run_experiment.sh configs/mitigation/gcp_missing_evidence_guard_pe_self_ask.env
bash scripts/run_experiment.sh configs/mitigation/gcp_missing_evidence_guard_verified_pe_self_ask.env
bash scripts/run_experiment.sh configs/mitigation/gcp_missing_evidence_repair_pe_self_ask.env
bash scripts/run_experiment.sh configs/mitigation/gcp_missing_evidence_repair_verified_pe_self_ask.env
```

If running on Insomnia instead, submit the same configs through the normal
Slurm path from `docs/insomnia_runbook.md`.

## Per-run validation

After each run, verify:

1. A raw run directory exists under the expected cell directory:
   - `Y`: `benchmarks/cell_Y_plan_execute/raw/<run-id>/`
   - `Z`: `benchmarks/cell_Z_hybrid/raw/<run-id>/`
2. The run directory contains:
   - `meta.json`
   - `latencies.jsonl`
   - `harness.log`
   - `vllm.log`
   - six `*_runNN.json` files for the current two-scenario, three-trial setup
3. `meta.json` records the real git SHA, config path, host, and GPU.
4. Detection-only runs have `mitigation_guard` metadata in per-trial JSONs.
5. Recovery runs have both `mitigation_guard` and `mitigation_repair` metadata
   when repair is enabled.
6. Failures are not just wrapper failures. If the run says success but every
   tool call failed, stop and inspect before treating the row as valid.

Useful quick count:

```bash
find benchmarks/cell_Y_plan_execute/raw/<run-id> -maxdepth 1 -name '*_run[0-9][0-9].json' | wc -l
find benchmarks/cell_Z_hybrid/raw/<run-id> -maxdepth 1 -name '*_run[0-9][0-9].json' | wc -l
```

## Judge pass

After each run completes, score the run directory:

```bash
python scripts/judge_trajectory.py \
    --run-dir benchmarks/cell_Y_plan_execute/raw/<run-id> \
    --scenario-dir data/scenarios \
    --out results/metrics/scenario_scores.jsonl \
    --log-dir results/judge_logs
```

For `Z`, replace the run directory with:

```bash
benchmarks/cell_Z_hybrid/raw/<run-id>
```

The judge output must join back on:

- `run_name`
- `cell`
- `scenario_id`
- `trial_index`

Do not populate before/after rows until judge rows exist or the row is clearly
marked as unjudged / partial.

## Handoff package

For each completed run, hand back:

- config file used
- run ID
- raw run directory
- `meta.json`
- `summary.json` or cell-level summary snapshot
- judge rows appended to `results/metrics/scenario_scores.jsonl`
- judge log directory
- W&B URL if present
- host / GPU / GCP zone or Insomnia Slurm job ID
- notes on any retry, preemption, restart, or dirty checkout

The taxonomy lane will then populate:

- `results/metrics/mitigation_before_after.csv`
- mitigation before/after figure sources
- #35/#36/#64/#66 issue comments
- paper/report/deck wording

## What counts as a mitigation win

The primary recovery metric is:

```text
supported_success_after_repair_rate
```

A recovery run only counts as a win when the final answer is supported by the
repaired evidence and the judge row passes. A trial that merely flips
`success=true` without evidence support is not a mitigation win.

Expected interpretation:

- Detection-only guard may reduce nominal success rate. That is not bad by
  itself; it means unsafe confident completions are no longer counted as clean.
- Recovery should be judged against detection-only, not directly against the
  unguarded baseline.
- The useful ladder is:

```text
baseline -> detection guard -> repair/replan recovery
```

Adjudication is not part of this execution request. It remains a future rung
unless detection/recovery results show enough under-constrained fault/risk
cases to justify implementation.

## Experiment matrix relationship

`docs/experiment_matrix.md` should remain the core method matrix: cells,
orchestration families, Self-Ask variants, optimized-serving variants, model,
scenario, and trial counts. In that sense, it is mostly the no-mitigation
matrix plus non-mitigation ablations.

Mitigation should be represented as a sparse overlay dimension, not as a full
new Cartesian product over every cell.

The clean mental model is:

```text
core observation = (family_lane, scenario_id, model_id, trial_index)
mitigation_rung = baseline | detection_guard | repair_replan | adjudication
```

For #66, the dense part of the overlay is intentionally small:

```text
2 family lanes x 3 measured rungs x 2 scenarios x 3 trials
```

The baseline rung already exists, so the runner only needs to execute:

```text
2 family lanes x 2 new rungs x 2 scenarios x 3 trials = 24 new trial JSONs
```

If the scenario set later expands to 30 scenarios and the final trial target
becomes 5, that becomes:

```text
2 family lanes x 3 rungs x 30 scenarios x 5 trials
```

That is a sparse tensor slice, not a reason to run every mitigation against
A/B/C/D/Y/Z/YS/ZS/ZSD. Full tensor expansion would blur the experimental story
and burn compute without improving attribution.

Recommended documentation path after the runs land:

1. Keep `docs/experiment_matrix.md` focused on the core and optional
   non-mitigation cells.
2. Add a short "Mitigation overlay" table to `docs/experiment_matrix.md` only
   after run IDs exist.
3. Treat `results/metrics/mitigation_before_after.csv` as the canonical
   machine-readable mitigation matrix.
4. Keep `docs/mitigation_recovery_adjudication.md` as the design/spec source
   for the ladder semantics.
