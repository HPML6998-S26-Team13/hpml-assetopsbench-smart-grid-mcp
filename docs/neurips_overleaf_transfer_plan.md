# NeurIPS Overleaf Transfer Plan

*Last updated: 2026-05-03*
*Owner: Alex Xin*
*Issues: #5, #39, #40, #47, #48, #78*

This is the paper handoff layer between the repo Markdown drafts and the
NeurIPS 2026 Overleaf project:

https://www.overleaf.com/project/69f5a380e638a31066dc0bd1

The Overleaf project already contains the official NeurIPS 2026 template and is
configured for anonymous Evaluations & Datasets mode. It also has a first real
paper draft in Overleaf commit `4a85633`. This repo file records what was
copied into Overleaf, what must stay caveated, and what remains blocked on
final evidence.

## Transfer Principle

Move stable structure and conservative prose into Overleaf immediately. Do not
wait for the final scenario floor, mitigation reruns, or any 70B appendix
decision before populating the paper skeleton. Those pending facts can remain
as TODO markers or explicitly caveated result rows.

Source-of-truth order:

1. `docs/validation_log.md` and committed benchmark artifacts for run IDs.
2. `results/metrics/*.csv` and `results/figures/*` for numbers and figures.
3. `docs/neurips_draft.md` for canonical prose.
4. `docs/neurips_submission_packet.md` for deadline and claim-state control.
5. This transfer plan for Overleaf copy order and blocked/pending markers.

## Overleaf Population Status

Completed in Overleaf commit `4a85633`:

- current title and abstract candidate
- main NeurIPS sections from the repo draft surface
- first-capture transport and orchestration tables
- initial figure assets for Notebook 02, Notebook 03, and PE-family follow-on

Still pending before submission:

- visual compile proof in Overleaf
- NeurIPS checklist answers
- final references and citation cleanup
- final scenario-count wording
- final mitigation before/after disposition

## Copy Into Overleaf / Keep In Sync

### Title and abstract

Source:

- `docs/neurips_submission_packet.md`
- `docs/neurips_abstract_outline.md`
- `docs/neurips_draft.md`

Transfer:

- Working title: "SmartGridBench: MCP-Based Industrial Agent Benchmarking for
  Smart Grid Transformer Operations"
- Abstract candidate from `docs/neurips_submission_packet.md`.
- If the abstract form enforces a tighter word budget, first remove the
  sentence beginning "Preliminary six-trial captures show...".

Status: ready for Overleaf draft paste; final numerical language should be
rechecked after any new captures land.

### Introduction

Source:

- `docs/neurips_draft.md` section `1. Introduction`

Transfer:

- Benchmark gap: Smart Grid transformer maintenance is under-covered.
- Systems gap: protocolized tool access is usually treated as plumbing, not a
  measured variable.
- Study frame: SmartGridBench separates transport effects from orchestration
  behavior.

Status: ready for Overleaf draft paste.

### Benchmark extension

Source:

- `docs/neurips_draft.md` section `2. Benchmark Extension`
- `docs/data_pipeline.tex`
- `docs/archive/scenario_realism_validation.md`
- `docs/knowledge/generated_scenario_authoring_and_ground_truth.md`

Transfer:

- Public transformer-related sources reconciled onto a shared synthetic
  `transformer_id`.
- Four tool domains: IoT, FMSR, TSFM, and WO.
- Scenario realism and generated-scenario circularity controls.

Status: ready for Overleaf draft paste with one TODO: final scenario count.

Do not yet write "30 validated scenarios" as complete. Use:

> The deadline target is a 30-scenario validated corpus; the final count is
> frozen only after PR #156 and generator-accepted scenarios are merged and
> validated.

### System design and artifact contract

Source:

- `docs/neurips_draft.md` section `3. System Design`
- `docs/runbook.md`
- `docs/wandb_schema.md`
- `docs/orchestration_wiring.md`

Transfer:

- MCP servers and direct adapter explain Cells A/B/C.
- `scripts/run_experiment.sh` explains the common artifact contract.
- `benchmarks/cell_<X>/raw/<run-id>/` explains run-level traceability.
- W&B and profiling references are supporting artifacts, not standalone claims.

Status: ready for Overleaf draft paste.

### Experimental design

Source:

- `docs/neurips_draft.md` section `4. Experimental Design`
- `docs/experiment_matrix.md`

Transfer:

- Experiment 1: A/B/C transport axis.
- Experiment 2: B/Y/Z orchestration axis.
- B is the anchor condition shared by both experiments.
- PE + Self-Ask, Verified PE + Self-Ask, Cell D, and 70B/context-window checks
  are follow-ons or appendix candidates unless promoted by final evidence.

Status: ready for Overleaf draft paste.

### Results skeleton

Source:

- `docs/neurips_submission_packet.md` current results snapshot
- `results/metrics/experiment_matrix_summary.csv`
- `results/metrics/notebook02_latency_summary.csv`
- `results/metrics/notebook03_orchestration_comparison.csv`
- `results/metrics/notebook03_self_ask_ablation.csv`
- `results/metrics/experiment_matrix_summary.csv`

Transfer:

- Add the current A/B/C transport table with a caption that says
  "first six-trial capture".
- Add the B/Y/Z and PE-family table with a caption that says "small-sample
  orchestration and follow-on evidence".
- Use `notebook03_orchestration_comparison.csv` for `B/Y/Z`; use
  `notebook03_self_ask_ablation.csv` and `experiment_matrix_summary.csv` for
  `YS/ZS`. Do not imply that `notebook03_pe_family_follow_on.csv` contains the
  Self-Ask rows.
- Keep C and D separate: C is the clean optimized-MCP transport row; D is an
  optimized-serving ablation.

Status: ready for Overleaf as a draft results table. Do not call these final
rerun results unless a later PR replaces them.

### Failure analysis and mitigation

Source:

- `docs/neurips_draft.md` section `6. Failure Analysis and Mitigation`
- `docs/failure_taxonomy_evidence.md`
- `docs/failure_visuals_mitigation.md`
- `docs/mitigation_recovery_adjudication.md`
- `results/metrics/failure_taxonomy_counts.csv`
- `results/figures/failure_taxonomy_counts.svg`
- `results/figures/failure_stage_cell_heatmap.svg`

Transfer:

- Failure taxonomy class counts.
- Evidence-resolution failure as the dominant paper discussion point.
- Missing-evidence guard as implemented mitigation, with outcome rows pending.

Status: taxonomy ready; mitigation before/after rows pending.

### Limitations and reproducibility

Source:

- `docs/neurips_draft.md` section `7. Reproducibility and Limitations`
- `docs/neurips_submission_packet.md` final blockers
- `docs/validation_log.md`

Transfer:

- Small first-capture result set.
- Final scenario count pending.
- Generated-scenario circularity.
- Academic GPU/resource limits.
- Artifact-led reproducibility.

Status: ready for Overleaf draft paste.

## Leave As TODO In Overleaf

Use visible TODO markers for these until evidence freezes:

- final scenario count and corpus table
- final repeated transport distribution, if reruns land
- missing-evidence mitigation before/after rows
- final citations and related-work compression
- NeurIPS checklist answers
- final figure captions with run IDs and source CSV paths
- class-report back-port proof after NeurIPS source stabilizes

## Figure Insertion Queue

Minimum figure set:

| Order | Figure | Source | Status |
|---:|---|---|---|
| 1 | Experiment 1 latency comparison | `results/figures/notebook02_latency_comparison.png` | ready as first-capture figure |
| 2 | Experiment 2 orchestration comparison | `results/figures/notebook03_orchestration_comparison.png` | ready as first-capture figure |
| 3 | PE-family follow-on | `results/figures/notebook03_pe_family_follow_on.png`; source rows for `YS/ZS` come from `results/metrics/notebook03_self_ask_ablation.csv` / `experiment_matrix_summary.csv` | optional; include if space permits |
| 4 | Failure taxonomy counts | `results/figures/failure_taxonomy_counts.svg` | ready |
| 5 | Failure stage/cell heatmap | `results/figures/failure_stage_cell_heatmap.svg` | ready |

Every caption should include either a source CSV path or a run-ID reference.

## Class Report Back-Port Note

The class IEEE report should not be authored separately from scratch. After the
Overleaf NeurIPS source is populated, use `reports/final_report_ieee_draft.md`
and `docs/final_report_backport_scaffold.md` as the conversion checklist:

- NeurIPS Introduction -> IEEE Introduction.
- NeurIPS Benchmark Extension -> IEEE Models and Data Description.
- NeurIPS System/Experimental Design -> IEEE Training and Profiling Methodology.
- NeurIPS Results/Failure Analysis -> IEEE Experimental Results.
- NeurIPS Limitations/Conclusion -> IEEE Conclusion.

Issue #40 and #78 should stay open until the IEEE LaTeX template is populated,
compiled, exported, and checked against the final NeurIPS source.
