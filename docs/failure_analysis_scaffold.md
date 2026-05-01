# Before/After Metric Pack for `#36`

*Last updated: 2026-05-01*
*Owner: Alex Xin*
*Issue: `#36`*

This doc carries the metric pack, before/after rerun ledger, and export
contract for `#36` (collect before/after profiling and benchmark data so we can
show whether the chosen mitigations changed outcomes). The earlier combined
scaffold for `#35`, `#64`, and `#36` was split on 2026-04-27. The failure
taxonomy + evidence work now lives in `docs/failure_taxonomy_evidence.md`
(`#35`), the visuals and mitigation ranking rubric live in
`docs/failure_visuals_mitigation.md` (`#64`), and the NeurIPS paper-writing
surface lives in `docs/neurips_draft.md` (`#5`). This file keeps only the
`#36`-specific metric, comparison, and export work.

## Primary inputs

- `benchmarks/cell_*/raw/<run-id>/` — raw scenario outputs (failures,
  trajectories) used as the before/after evidence ground truth
- `benchmarks/cell_*/summary.json` — per-run summary used to seed the metric
  pack
- `results/metrics/scenario_scores.jsonl` — judge scores when judge data
  exists
- `docs/validation_log.md` — canonical run-history index that anchors run
  identifiers used by the comparison ledger
- `notebooks/03_orchestration_comparison.ipynb` — primary consumer of the
  exports below
- `scripts/run_exp1_ab_capture.sh`, `scripts/replay_scenarios.sh` — capture
  and replay-profiling helpers; the `#36` exports must stay aligned with
  whatever these scripts emit

## Apr 27 status refresh

Since the Apr 26 refresh, the canonical `team13/main` lane has advanced:

- Cell A direct AaT smoke (`8962310_aat_direct_smoke_104`) and Cell B MCP
  baseline AaT smoke (`8969519_aat_mcp_baseline_smoke_104`) succeeded;
  upstream AOB parity smoke (`8970383`, `8970468`) succeeded.
- Notebook 02 partial-readiness mode landed in PR `#123` and Notebook 03
  preliminary mode landed in PR `#136`.
- Experiment 1 A/B canonical captures landed in PR `#130` with WandB,
  `nvidia-smi`, and `torch.profiler` integration. The first job
  (`8979314_aat_direct` / `8979314_aat_mcp_baseline`) ran 6 scenarios per
  side on `Llama-3.1-8B-Instruct` over scenario set `smartgrid_multi_domain`
  (hash `ca66cd16…2691e48`). Both sides hit `success_rate=1.0`; canonical
  AaT MCP overhead from this single job is `+1.20s` mean per-trial latency
  (`+9.8%`) and `+7.17s` total wall clock (`+9.8%`).
- PR `#128` added the PS B scenario-generation support artifacts.
- These artifacts now define the live "before" baseline — any future
  mitigation rerun must pair against the same scenario set, model, and
  capture wrapper to keep the comparison honest.

## Apr 30 export status

`results/metrics/failure_evidence_table.csv` is now populated with 35
judge-failed rows from `results/metrics/scenario_scores.jsonl`. That clears
the first fill target for `#35` and gives `#64` a concrete source table for
taxonomy-count and stage-by-cell visuals. It does **not** make before/after
mitigation claims comparison-ready; those still need matched after-side reruns
and `mitigation_before_after.csv`.

The first mitigation planning table is also populated:
`results/metrics/mitigation_run_inventory.csv`. This is a lane inventory, not
a before/after result. It now records the implemented detector row as pending
guarded Y+SA / Z+SA reruns, the retry/replan recovery row as a dependent
candidate after those detector rows exist, and three lower-priority candidates.
No completed after-run claim exists yet.

## May 1 guard and rerun scaffold status

The selected `missing_evidence_final_answer_guard` is now implemented in the
benchmark stack and can be enabled with one config variable:
`ENABLE_MISSING_EVIDENCE_GUARD=1`.

Implementation surfaces:

- `scripts/mitigation_guards.py` — deterministic guard logic and metadata.
- `scripts/run_experiment.sh` — applies the guard to every per-trial payload
  during post-processing and records `missing_evidence_guard` in config,
  summary, and meta JSON.
- `configs/mitigation/missing_evidence_guard_pe_self_ask.env` — matched
  rerun template for the PE + Self-Ask lane.
- `configs/mitigation/missing_evidence_guard_verified_pe_self_ask.env` —
  matched rerun template for the Verified PE + Self-Ask lane.
- `results/metrics/mitigation_before_after.csv` — header-only comparison
  export contract. It intentionally contains no data rows until real rerun
  artifacts exist.

The guard turns misleading clean completion into explicit mitigation metadata:
`mitigation_guard.triggered`, `blocked_final_answer`, `blocked_work_order`,
and `hits`. A trial is marked unsuccessful only when missing/untrusted
evidence is followed by a substantive final answer or work-order emission.

### Mitigation ladder lanes

Use two PE-family lanes for the mitigation ladder:

| Family lane | Baseline run | Detection-only rerun | Recovery rerun |
|---|---|---|---|
| `Y + Self-Ask` | `8998341_exp2_cell_Y_pe_self_ask_mcp_baseline` | `configs/mitigation/missing_evidence_guard_pe_self_ask.env` | future `missing_evidence_retry_replan_guard` config |
| `Z + Self-Ask` | `8998343_exp2_cell_Z_verified_pe_self_ask_mcp_baseline` | `configs/mitigation/missing_evidence_guard_verified_pe_self_ask.env` | future Verified PE recovery config using bounded retry / suffix replan |

Interpretation:

- The detection-only guard is an accounting / truthfulness gate. It can reduce
  nominal `success_rate` because it turns unsupported confident completions into
  explicit failures.
- The recovery rung should reuse the same missing-evidence detector during
  execution, then retry the evidence-producing step or replan only the dependent
  suffix. It is still one benchmark trial; it does not increase `TRIALS`.
- The adjudication rung should wait until evidence detection / repair is
  measured, because fault/risk adjudication is meaningful only when the deciding
  evidence exists.

## Before/after metric pack

These metrics should be collected per cell and per rerun wave so each row of
`mitigation_before_after.csv` is fully populated.

### Outcome metrics

- `success_rate`
- `failure_count`
- `scenarios_completed / scenarios_attempted`
- `judge_pass_rate` when judge scores exist

### Failure-shape metrics

- mean `failed_steps`
- mean `tool_error_count`
- recovery rate
- `repair_attempt_count` and `repair_success_rate` for the recovery rung
- mean `history_length`
- mean `verification.replans_used` for `Z`

### Latency / systems metrics

- `latency_seconds_mean`
- `latency_seconds_p50`
- `latency_seconds_p95`
- `mcp_latency_seconds_mean`
- `tool_latency_seconds_mean`
- `profiling_gpu_util_mean` / `profiling_gpu_util_max` when profiling exists
- `profiling_gpu_mem_used_mib_mean` / `profiling_gpu_mem_used_mib_max`
- `profiling_power_draw_w_mean` / `profiling_power_draw_w_max`

### Capture / profiling source paths

For the current Experiment 1 capture wrapper, record these fields when A/B
artifacts land:

- `benchmark_run_dir`: `benchmarks/cell_A_direct/raw/<job>_aat_direct` or
  `benchmarks/cell_B_mcp_baseline/raw/<job>_aat_mcp_baseline`
- `profiling_dir`: `profiling/traces/<job>_cell_a` or
  `profiling/traces/<job>_cell_b`
- `torch_profile_dir`: `profiling/traces/<job>_aat_direct_torch` or
  `profiling/traces/<job>_aat_mcp_baseline_torch` when `TORCH_PROFILE=1`
- `replay_dir`: `<benchmark_run_dir>/replay` when profiler replay outputs are
  present

### Join keys

Use these fields consistently so notebook outputs, benchmark artifacts, and
W&B stay joinable:

- `run_name`
- `wandb_run_url`
- `cell`
- `orchestration_mode`
- `mcp_mode`
- `scenario_id`
- `trial_index`
- `model_id`

## Current before/after comparison ledger

This is the minimal rerun ledger we can already define for `#36`. PR `#130`
added the canonical Cell A/B captures from job `8979314` on Llama-3.1-8B
(scenario set `smartgrid_multi_domain`, hash
`ca66cd16b7704157f9d21c74e1c8d40c1d2d19ab60957d4d05ad737c27691e48`); those
rows now seed the canonical "AaT transport baseline" lane. Mitigation
reruns against this lane have not yet landed.

| lane | before run | after run | before status | after status | after metrics already committed | missing for full comparison |
|---|---|---|---|---|---|---|
| PE + Self-Ask (smoke) | `8850716_pe_self_ask_mcp_baseline_smoke` | `8857842_pe_self_ask_mcp_baseline_smoke` | integration proof with terminal `Unknown server 'none'` | clean `2/2` smoke success | `success_rate=1.0`, `failure_count=0`, `latency_seconds_mean=67.11`, `latency_seconds_p95=99.57`, `tool_call_count_mean=9.5` | before-side exported metrics in repo form; raw per-scenario outputs on canonical history |
| Verified PE (smoke) | `8851966_verified_pe_mcp_baseline_smoke` | `8857843_verified_pe_mcp_baseline_smoke` | semantic failures masked by wrapper success accounting | clean `2/2` smoke success | `success_rate=1.0`, `failure_count=0`, `latency_seconds_mean=93.59`, `latency_seconds_p95=139.64`, `tool_call_count_mean=10.5` | before-side exported metrics in repo form; raw per-scenario outputs on canonical history |
| AaT transport baseline (Cell A) | n/a (this is the baseline) | `8979314_aat_direct` | n/a | clean `6/6` canonical capture | `success_rate=1.0`, `failure_count=0`, `wall_clock_seconds_total=73.13`, `latency_seconds_mean=12.19`, `latency_seconds_p50=11.47`, `latency_seconds_p95=18.57`, `tool_call_count_total=20`, `tool_call_count_mean=3.33`, `tool_error_count=0` | tokens / judge / MCP latency dims unpopulated on Cell A by definition |
| AaT transport baseline (Cell B) | `8979314_aat_direct` | `8979314_aat_mcp_baseline` | clean Cell A (6/6) | clean Cell B (6/6) | `success_rate=1.0`, `failure_count=0`, `wall_clock_seconds_total=80.30`, `latency_seconds_mean=13.38`, `latency_seconds_p50=12.91`, `latency_seconds_p95=16.65`, `tool_call_count_total=21`, `tool_call_count_mean=3.50`, `tool_error_count=0` | `mcp_latency_seconds_mean`, `mcp_latency_seconds_p95`, `tool_latency_seconds_mean`, token / judge dims still NULL on the capture |
| Detection guard (PE + Self-Ask) | `8998341_exp2_cell_Y_pe_self_ask_mcp_baseline` | pending guarded rerun | first-capture baseline exists | `pending_rerun` via `configs/mitigation/missing_evidence_guard_pe_self_ask.env` | no after-side metrics yet | run guarded config, judge outputs, then populate `mitigation_before_after.csv` |
| Detection guard (Verified PE + Self-Ask) | `8998343_exp2_cell_Z_verified_pe_self_ask_mcp_baseline` | pending guarded rerun | first-capture baseline exists | `pending_rerun` via `configs/mitigation/missing_evidence_guard_verified_pe_self_ask.env` | no after-side metrics yet | run guarded config, judge outputs, then populate `mitigation_before_after.csv` |
| Evidence repair retry/replan (PE + Self-Ask) | detection-guard after-run for `Y + Self-Ask` | future recovery rerun | depends on detection-only row | `candidate_next` | no implementation yet | implement bounded retry/replan guard only after the detection-only row exists |
| Evidence repair retry/replan (Verified PE + Self-Ask) | detection-guard after-run for `Z + Self-Ask` | future recovery rerun | depends on detection-only row | `candidate_next` | no implementation yet | reuse Verified PE retry/suffix-replan substrate, but drive it from deterministic missing-evidence detection |

Same job (`8979314`) produced both Cell A and Cell B captures, so the
transport-overhead row pairs the two sides under one job ID. Observed
canonical AaT MCP overhead from this single job: latency mean
`+1.20s` (`+9.8%`), wall-clock total `+7.17s` (`+9.8%`), tool-call count
`+1` (`6 → 7%` increase in mean), zero tool errors on either side. This is
one job, six scenarios, three trials per scenario; treat it as a
`partial_export` row pending repeat captures and the still-NULL MCP
latency dims.

When mitigation reruns against this AaT transport baseline land, append
rows in the same shape and update the `comparison_ready` status when both
sides have a complete metric pack.

### Ladder comparison rule

Do not compare all mitigation permutations. Each row should compare only one
transition:

| Compare | Question answered |
|---|---|
| baseline -> detection guard | how many unsafe clean completions were hidden by the baseline |
| detection guard -> repair retry/replan | how many evidence gaps can become supported successes with bounded recovery |
| repair retry/replan -> adjudication | whether final fault/risk choice improves once evidence is available |

The detection guard should be treated as a de facto requirement for
production-oriented reporting after it is adopted. Keep old unguarded baselines
for comparability, but do not claim a future production-safe run unless the
truthfulness gate is active or an equivalent evidence gate is present.

## Export contract by file

This is the narrowest useful contract for the outputs that `#36` should
eventually materialize. Any consumer (notebook, paper, slide deck) should
read these tables, not the raw run JSON.

`results/metrics/failure_evidence_table.csv`

- one row per classified evidence item
- required columns: `run_name`, `cell`, `orchestration_mode`, `mcp_mode`,
  `scenario_id`, `trial_index`, `failure_stage`, `taxonomy_label`, `symptom`,
  `artifact_path`, `evidence_note`, `candidate_mitigation`, `priority`
- schema owned by `#36` export contract (this doc); populated rows produced
  under `#35` (see `docs/failure_taxonomy_evidence.md`)

`results/metrics/mitigation_run_inventory.csv`

- one row per mitigation lane
- required columns: `lane`, `mitigation_name`, `before_run`, `after_run`,
  `before_status`, `after_status`, `notes`
- current status: populated with five lanes: one implemented detector pending
  guarded reruns, one dependent retry/replan recovery candidate pending
  implementation, and three lower-priority candidates; no completed after-run
  claims yet

`results/metrics/mitigation_before_after.csv`

- one row per `(lane, phase, run_name)`
- current status: schema/header exists; no after-run rows yet
- required columns (organized by group; column order can stay flexible as
  long as every column appears):

  identity / metadata: `lane`, `phase`, `run_name`, `cell`,
  `orchestration_mode`, `mcp_mode`, `model_id`, `slurm_job_id`, `git_sha`,
  `scenario_set_name`, `scenario_set_hash`, `experiment_family`,
  `experiment_cell`, `wandb_run_url`, `benchmark_config_path`,
  `benchmark_summary_path`, `host_name`, `gpu_type`, `run_status`,
  `finished_at`

  outcome: `scenarios_attempted`, `scenarios_completed`, `success_rate`,
  `failure_count`

  latency: `wall_clock_seconds_total`, `latency_seconds_mean`,
  `latency_seconds_p50`, `latency_seconds_p95`,
  `mcp_latency_seconds_mean`, `mcp_latency_seconds_p95`,
  `tool_latency_seconds_mean`

  tool / token shape: `tool_call_count_total`, `tool_call_count_mean`,
  `tool_error_count`, `input_tokens_total`, `output_tokens_total`,
  `tokens_per_second_mean`

  judge: `judge_score_mean`, `judge_score_p50`, `judge_score_p95`,
  `judge_score_p5`, `judge_pass_rate`

  artifact roots: `benchmark_run_dir`, `profiling_dir`, `torch_profile_dir`,
  `replay_dir`, `profiling_summary`

  profiling samples: `profiling_gpu_util_mean`, `profiling_gpu_util_max`,
  `profiling_gpu_mem_used_mib_mean`, `profiling_gpu_mem_used_mib_max`,
  `profiling_power_draw_w_mean`, `profiling_power_draw_w_max`

  Every column in `benchmarks/cell_*/summary.json` is mirrored here so the
  CSV is a strict superset of what the capture wrapper already emits. Fields
  that the capture has not produced for a given row (e.g., judge scores when
  judge data is not yet wired) stay NULL on that row but the column must
  exist on the CSV.

  Mitigation fields appended for `#65` / `#66`:
  `mitigation_name`, `mitigation_enabled`,
  `mitigation_guard_triggered`, `mitigation_guard_blocked_final_answer`,
  `mitigation_guard_blocked_work_order`, `comparison_status`, and `notes`.

## Current safe claims

These claims are already supported by committed artifacts or the canonical
validation log:

- PE-family failures are not just latency problems; the dominant visible risks
  are correctness and accounting failures.
- Answer/tool inconsistency appears in more than one Y-cell artifact and is
  already strong enough to justify an explicit evidence-consistency
  mitigation.
- Wrapper-level masking can invalidate benchmark summaries unless
  runner-level error promotion is enforced.
- Clean PE + Self-Ask and Verified PE smoke reruns exist after the earlier
  failure cases, which is enough to motivate a before/after mitigation
  figure.
- AaT Cell A and Cell B smoke proofs now exist, so the paper can treat the
  A/B runner surface as proven and reserve the remaining caveat for full
  matched captures rather than runner feasibility.

## Claims that still need more evidence

- any frequency claim stronger than "recurring in the currently committed
  artifact set"
- any mitigation claim tied to judge-quality improvement rather than just
  clean execution and success accounting
- any statement that Self-Ask or Verified PE closes the gap to AaT, because
  the shared `B` anchor is still missing as a final comparable artifact chain
- any quantitative MCP-overhead claim from the A/B smoke pair alone; those
  smokes prove artifact shape, not the final matched trial distribution

## Export targets

When the rerun lane fills in, the clean metric surfaces should be:

- `results/metrics/failure_evidence_table.csv` (schema owned by `#36`
  export contract; populated rows produced under `#35`)
- `results/metrics/mitigation_run_inventory.csv`
- `results/metrics/mitigation_before_after.csv`
- `results/figures/failure_taxonomy_counts.svg` (owned by `#64`)
- `results/figures/failure_stage_cell_heatmap.svg` (owned by `#64`)
- `results/figures/mitigation_priority_table.svg` (owned by `#64`)
- future before/after mitigation figure once `mitigation_before_after.csv`
  has real guarded rerun rows (`#36` supplies the table behind it)

## Minimum deliverable definition

For `#36`:

- one clean before/after metrics table covering at least one matched
  mitigation lane
- one figure-ready export that no longer requires raw-log spelunking

## Before/after comparison guardrails

`#36` should avoid accidental apples-to-oranges reruns. Keep these rules:

- compare one mitigation lane at a time
- advance the ladder on `Y + Self-Ask` and `Z + Self-Ask` before considering
  other cells
- hold `cell`, `orchestration_mode`, `mcp_mode`, `model_id`, and scenario set
  fixed unless the mitigation itself is the variable under study
- keep detection-only rows separate from recovery rows; the recovery rung is a
  superset of the detector, not an orthogonal factor to permute
- do not treat historical smoke proofs and final canonical benchmark captures
  as one pooled dataset
- if the before-side artifact lacks a field that the after-side export has,
  record it as missing rather than silently imputing
- keep quality claims separate from execution-cleanliness claims unless judge
  data exists on both sides

## Comparison-ready status labels

Use the same status values in `mitigation_run_inventory.csv` so rerun state
is readable without raw log archaeology:

| Status | Meaning |
|---|---|
| `historical_only` | cited in validation log, but raw comparison artifact is incomplete in-tree |
| `partial_export` | enough metrics exist for a provisional row, but not the full pack |
| `comparison_ready` | before/after rows can support a figure or paper sentence |

### Asymmetric-field rule

A row stays `partial_export` until **both sides carry the same field set**
on the columns the comparison claim depends on. If the after-side has
profiling samples (`profiling_gpu_util_*`, `profiling_power_draw_w_*`) but
the before-side does not — or vice versa — the row is `partial_export`,
not `comparison_ready`, even when both rows otherwise look complete. The
guardrail in the previous section (record asymmetric fields as missing
rather than imputing) governs *how* the row is written; this rule governs
*what status it gets*. Promote to `comparison_ready` only when both sides
carry the columns the figure or paper sentence will actually read.

## Immediate fill order

If new artifacts arrive gradually, fill the exports in this order:

1. `failure_evidence_table.csv` (done for the first judge-derived pass; needs
   refresh only if final reruns change judge rows)
2. `mitigation_run_inventory.csv` (done for the first mitigation lane
   selection and now marks the selected lane implemented pending rerun; the
   next candidate rung is `missing_evidence_retry_replan_guard`)
3. `mitigation_before_after.csv` (schema exists; populate after guarded rerun)
4. only then render before/after figures (`#64`'s lane)

That order preserves the evidence trail even when the figure lane is still
waiting on one missing rerun.
