# Before/After Metric Pack for `#36`

*Last updated: 2026-04-27*
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
  `nvidia-smi`, and `torch.profiler` integration; PR `#128` added the PS B
  scenario-generation support artifacts.
- These artifacts now define the live "before" baseline — any future
  mitigation rerun must pair against the same scenario set, model, and
  capture wrapper to keep the comparison honest.

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

This is the minimal rerun ledger we can already define for `#36`. The Apr 27
pass keeps the same lanes; the canonical "after" runs are unchanged because no
new mitigation rerun has landed since the Apr 26 refresh.

| lane | before run | after run | before status | after status | after metrics already committed | missing for full comparison |
|---|---|---|---|---|---|---|
| PE + Self-Ask | `8850716_pe_self_ask_mcp_baseline_smoke` | `8857842_pe_self_ask_mcp_baseline_smoke` | integration proof with terminal `Unknown server 'none'` | clean `2/2` smoke success | `success_rate=1.0`, `failure_count=0`, `latency_seconds_mean=67.11`, `latency_seconds_p95=99.57`, `tool_call_count_mean=9.5` | before-side exported metrics in repo form; raw per-scenario outputs on canonical history |
| Verified PE | `8851966_verified_pe_mcp_baseline_smoke` | `8857843_verified_pe_mcp_baseline_smoke` | semantic failures masked by wrapper success accounting | clean `2/2` smoke success | `success_rate=1.0`, `failure_count=0`, `latency_seconds_mean=93.59`, `latency_seconds_p95=139.64`, `tool_call_count_mean=10.5` | before-side exported metrics in repo form; raw per-scenario outputs on canonical history |

When the Cell A/B canonical capture wave from PR `#130` produces matched
mitigation reruns, append rows here in the same shape and update the
`comparison_ready` status when both sides have a complete metric pack.

## Export contract by file

This is the narrowest useful contract for the outputs that `#36` should
eventually materialize. Any consumer (notebook, paper, slide deck) should
read these tables, not the raw run JSON.

`results/metrics/failure_evidence_table.csv`

- one row per classified evidence item
- required columns: `run_name`, `cell`, `orchestration_mode`, `mcp_mode`,
  `scenario_id`, `trial_index`, `failure_stage`, `taxonomy_label`, `symptom`,
  `artifact_path`, `evidence_note`, `candidate_mitigation`, `priority`
- this table is owned by `#35` (see `docs/failure_taxonomy_evidence.md`); the
  `#36` lane only needs the join keys to remain stable

`results/metrics/mitigation_run_inventory.csv`

- one row per mitigation lane
- required columns: `lane`, `mitigation_name`, `before_run`, `after_run`,
  `before_status`, `after_status`, `notes`

`results/metrics/mitigation_before_after.csv`

- one row per `(lane, phase, run_name)`
- required columns: `lane`, `phase`, `run_name`, `cell`, `success_rate`,
  `failure_count`, `latency_seconds_mean`, `latency_seconds_p95`,
  `tool_call_count_mean`, `judge_pass_rate`, `benchmark_run_dir`,
  `profiling_dir`, `torch_profile_dir`, `replay_dir`, `profiling_summary`,
  `profiling_gpu_util_mean`, `profiling_gpu_util_max`,
  `profiling_gpu_mem_used_mib_mean`, `profiling_gpu_mem_used_mib_max`,
  `profiling_power_draw_w_mean`, `profiling_power_draw_w_max`

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

- `results/metrics/failure_evidence_table.csv` (owned by `#35`; `#36`
  consumes its join keys)
- `results/metrics/mitigation_run_inventory.csv`
- `results/metrics/mitigation_before_after.csv`
- `results/figures/failure_taxonomy_counts.png` (owned by `#64`)
- `results/figures/mitigation_before_after.png` (owned by `#64`; `#36`
  supplies the table behind it)

## Minimum deliverable definition

For `#36`:

- one clean before/after metrics table covering at least one matched
  mitigation lane
- one figure-ready export that no longer requires raw-log spelunking

## Before/after comparison guardrails

`#36` should avoid accidental apples-to-oranges reruns. Keep these rules:

- compare one mitigation lane at a time
- hold `cell`, `orchestration_mode`, `mcp_mode`, `model_id`, and scenario set
  fixed unless the mitigation itself is the variable under study
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

## Immediate fill order

If new artifacts arrive gradually, fill the exports in this order:

1. `failure_evidence_table.csv` (in `#35`'s lane)
2. `mitigation_run_inventory.csv`
3. `mitigation_before_after.csv`
4. only then render the figures (`#64`'s lane)

That order preserves the evidence trail even when the figure lane is still
waiting on one missing rerun.
