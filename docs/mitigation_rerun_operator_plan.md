# Mitigation Rerun Operator Plan

*Last updated: 2026-05-03*  
*Issues: #35, #36, #64, #66*

This is the runner-facing plan for the missing-evidence mitigation ladder.
It is written for whoever owns the compute session. The taxonomy lane consumes
the completed artifacts afterward.

## Goal

Produce the evidence needed to populate
`results/metrics/mitigation_before_after.csv` for #66:

1. matched baseline reruns for `Y + Self-Ask` and `Z + Self-Ask`
2. detection-only guarded reruns for the same two family lanes
3. recovery reruns for the same two family lanes
4. adjudication reruns for the same two family lanes
5. judge rows for every run in all four tiers
6. run IDs, artifact paths, and provenance sufficient for #35/#36/#64/#66

This is evidence work, not new mitigation implementation. The baseline plus
three post-baseline mitigation rungs are covered here: detection guard,
retry/replan recovery, and explicit fault/risk adjudication.

Status as of 2026-05-03: the GCP A100 four-tier cohort
`mitigation_final6_4tier_a100_20260503T121709Z` completed and was judged for all
8 rows, 240 trial JSONs, and 240 judge rows. The measured row inventory is in
`results/metrics/gcp_a100_mitigation_4tier_summary.csv`; the before/after
interpretation table remains a deliberate follow-up, not an automatic copy of
the raw cohort summary.

## Current anchors

| Family lane | Baseline config | Detection config | Recovery config | Adjudication config |
|---|---|---|---|---|
| `Y + Self-Ask` | `configs/mitigation_final6_5x6/YS_BASELINE.env` | `configs/mitigation_final6_5x6/YS_GUARD.env` | `configs/mitigation_final6_5x6/YS_REPAIR.env` | `configs/mitigation_final6_5x6/YS_ADJ.env` |
| `Z + Self-Ask` | `configs/mitigation_final6_5x6/ZS_BASELINE.env` | `configs/mitigation_final6_5x6/ZS_GUARD.env` | `configs/mitigation_final6_5x6/ZS_REPAIR.env` | `configs/mitigation_final6_5x6/ZS_ADJ.env` |

The source templates remain under `configs/mitigation/`. The current GCP A100
operator copies live under `configs/mitigation_final6_5x6/` in the run checkout
and must be preserved with the artifact package if they are not committed before
the run.

The current four-tier GCP cohort uses:

| Field | Value |
|---|---|
| model | `openai/Llama-3.1-8B-Instruct` |
| scenario set | final-six selected scenarios |
| scenario files | `multi_01_end_to_end_fault_response.json`, `multi_02_dga_to_workorder_pipeline.json`, `fmsr_04_dga_full_diagnostic_chain.json`, `iot_04_load_current_overload_check.json`, `tsfm_02_hotspot_temp_anomaly.json`, `wo_04_fault_record_downtime_update.json` |
| trials | `5` |
| transport | MCP baseline |
| baseline flag | no mitigation flags enabled |
| detection flag | `ENABLE_MISSING_EVIDENCE_GUARD=1` for guard/recovery/adjudication configs |
| recovery flag | `ENABLE_MISSING_EVIDENCE_REPAIR=1` for recovery/adjudication configs |
| adjudication flag | `ENABLE_EXPLICIT_FAULT_RISK_ADJUDICATION=1` for adjudication configs only |

With the final-six scenario set and `TRIALS=5`, each config should produce
30 per-trial JSON files.

## Compute choice

Use the GCP A100 path while Insomnia remains drained or unreliable. This is
acceptable for #66 because the immediate target is mitigation behavior and
artifact quality, not a clean Insomnia-vs-GCP latency claim.

Do not silently compare GCP A100 latency against Insomnia A6000/A100 latency as
if they were the same hardware and environment. Record the provider, zone,
host, GPU, git SHA, config path, and dirty state in the run handoff.

## GCP config handling

The canonical mitigation configs are Insomnia-shaped templates. They set
runtime fields directly, including:

```bash
SERVING_STACK="insomnia_vllm"
LAUNCH_VLLM=1
VLLM_MODEL_PATH="models/Llama-3.1-8B-Instruct"
```

Because `scripts/run_experiment.sh` sources the config file, exporting
different values before the command will not override assignments inside the
file. For GCP, use one of these approaches:

1. Preferred for publishable reruns: create GCP-specific copies of the
   configs, preserving all scientific fields and changing only runtime /
   provenance fields such as `SERVING_STACK`, `VLLM_MODEL_PATH`, and any
   GCP-local serving knobs.
2. Acceptable for an emergency run: create temporary GCP config copies and
   preserve those exact files with the artifact handoff. Do not edit the
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
- `ENABLE_EXPLICIT_FAULT_RISK_ADJUDICATION`
- `CONTRIBUTING_EXPERIMENTS`
- `SCENARIO_DOMAIN_SCOPE`
- `TEMPERATURE`
- `MAX_TOKENS`
- `MAX_MODEL_LEN`
- `QUANTIZATION_MODE`
- `ENABLE_SMARTGRID_SERVERS`
- `JUDGE_MODEL`

If any of these fields change, the run is no longer directly comparable to the
baseline anchors above. Mark it `incomparable` in the handoff package unless
Alex explicitly approves a new comparison baseline.

## Execution order

Run in this order. The current overnight plan executes all four tiers, including
fresh matched baselines, so the mitigation comparison does not depend on older
Insomnia or GCP L4 evidence.

| Order | Lane | Config | Purpose |
|---:|---|---|---|
| 1 | `Y + Self-Ask + baseline` | `YS_BASELINE.env` | Establish the matched unmitigated PE+Self-Ask baseline on the final-six A100 environment. |
| 2 | `Z + Self-Ask + baseline` | `ZS_BASELINE.env` | Establish the matched unmitigated Verified PE+Self-Ask baseline on the same environment. |
| 3 | `Y + Self-Ask + guard` | `YS_GUARD.env` | Count unsupported clean completions in the PE+Self-Ask lane. |
| 4 | `Z + Self-Ask + guard` | `ZS_GUARD.env` | Count unsupported clean completions in the strongest PE-family lane. |
| 5 | `Y + Self-Ask + repair` | `YS_REPAIR.env` | Test whether bounded retry can repair Y+SA evidence gaps inside the same trial. |
| 6 | `Z + Self-Ask + repair` | `ZS_REPAIR.env` | Test whether detector-driven retry / suffix replan improves Z+SA outcomes. |
| 7 | `Y + Self-Ask + adjudication` | `YS_ADJ.env` | Test whether structured fault/risk adjudication changes Y+SA finalization after evidence repair. |
| 8 | `Z + Self-Ask + adjudication` | `ZS_ADJ.env` | Test whether structured fault/risk adjudication changes the strongest PE-family lane after evidence repair. |

The recovery flags do not increase `TRIALS`. They allow at most two internal
repair attempts per trial, with at most one retry per unresolved evidence
target:

```bash
MISSING_EVIDENCE_REPAIR_MAX_ATTEMPTS=2
MISSING_EVIDENCE_REPAIR_MAX_ATTEMPTS_PER_TARGET=1
```

## Run commands

On GCP, run the four-tier cohort through the batch wrapper so skip/resume,
manifest capture, and per-row judging stay consistent:

```bash
export COHORT_TSV=configs/mitigation_final6_5x6/cohort_4tier.tsv
export SMARTGRID_BATCH_ID=mitigation_final6_4tier_a100_<UTC>
export PLAN_EXECUTE_REPO_LOCAL=1
export AOB_PYTHON=/home/wax/AssetOpsBench/.venv/bin/python

bash scripts/run_gcp_context_batch.sh --resume-batch "$SMARTGRID_BATCH_ID"
```

If a row must be repaired manually, run the same config directly from the repo
checkout and then judge that run directory:

```bash
bash scripts/run_experiment.sh configs/mitigation_final6_5x6/YS_REPAIR.env
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
   - 30 `*_runNN.json` files for the final-six, five-trial setup
3. `meta.json` records the real git SHA, config path, host, GPU, vLLM version,
   CUDA version, and NVIDIA driver version. If any runtime version is missing
   from `meta.json`, capture it in the handoff notes.
4. Detection-only runs have `mitigation_guard` metadata in per-trial JSONs.
5. Recovery runs have both `mitigation_guard` and `mitigation_repair` metadata
   when repair is enabled.
6. Adjudication runs have `fault_risk_adjudication` metadata in per-trial JSONs
   when adjudication is enabled. `decision="finalize"` must cite
   `deciding_evidence`; `decision="refuse_due_missing_evidence"` must include
   `missing_evidence`.
7. Failures are not just wrapper failures. If the run says success but every
   tool call failed, stop and inspect `harness.log` for tool-call traces and
   `latencies.jsonl` for zero-duration or missing tool calls before treating
   the row as valid.

Useful quick count:

```bash
find benchmarks/cell_Y_plan_execute/raw/<run-id> -maxdepth 1 -name '*_run[0-9][0-9].json' | wc -l
find benchmarks/cell_Z_hybrid/raw/<run-id> -maxdepth 1 -name '*_run[0-9][0-9].json' | wc -l
```

## Judge pass

The batch wrapper judges each row after capture. If judging must be repeated
manually, score the run directory:

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
marked as unjudged / partial. Each tier should have 60 judge rows total:

```text
2 family lanes x 6 scenarios x 5 trials = 60
```

The full four-tier mitigation cohort should have 240 judge rows:

```text
2 family lanes x 4 tiers x 6 scenarios x 5 trials = 240
```

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
- vLLM version, CUDA version, and NVIDIA driver version
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
- Adjudication should be judged against recovery and reported as a separate
  finalization-policy rung, not folded into recovery.
- The useful ladder is:

```text
baseline -> detection guard -> repair/replan recovery -> adjudication
```

Adjudication is now an available rung, but it should still be interpreted
against detection/recovery. The code path and configs exist; the claim waits
for matched rows.

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
2 family lanes x 4 measured rungs x 6 scenarios x 5 trials
```

The current GCP A100 run executes the baseline rung too, which keeps the four
tiers matched on provider, GPU, scenario set, trial count, and runtime patch
state:

```text
2 family lanes x 4 rungs x 6 scenarios x 5 trials = 240 trial JSONs
```

If the baseline rung is intentionally reused from an already judged, exactly
matched core run, mark that reuse explicitly in the handoff and execute only
the three post-baseline rungs:

```text
2 family lanes x 3 post-baseline rungs x 6 scenarios x 5 trials = 180 trial JSONs
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
