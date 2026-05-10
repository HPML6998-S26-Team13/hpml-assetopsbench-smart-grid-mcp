---
status: canonical
scope: team-repo
owner: Team 13
canonical: true
---

# Final Presentation Run of Show

*Created: 2026-05-02*
*Owner: Alex Xin*
*Issue: #44*

This is the production companion for `docs/final_presentation_deck.md`. The deck
already has slide-by-slide content; this file turns it into a presentation plan
with timing, proof objects, and final build gates.

Current editable PPTX draft:
`reports/2026-05-03_final_presentation_smartgridbench_draft.pptx`.
It is a reviewable build, not the final submitted deck, until the open gates at
the end of this file clear.

## Presentation Goal

In one class presentation, make three ideas stick:

1. SmartGridBench is a real AssetOpsBench extension for Smart Grid transformer
   maintenance.
2. The experiment separates transport effects from orchestration effects instead
   of blending every variable into a full grid.
3. Failure accounting matters because many "successful" agent trajectories are
   still weak if they do not ground the final maintenance recommendation.

## Recommended Time Budget

Target: 10-12 minutes plus Q&A.

| Segment | Slides | Time | Job |
|---|---|---:|---|
| Setup | 1-3 | 2:00 | Name the artifact and why Smart Grid transformer maintenance matters. |
| Experimental design | 4-6 | 2:00 | Explain workload scope, artifact contract, and A/B/C vs B/Y/Z split. |
| Results | 7-10 | 4:00 | Show transport, profiling, orchestration, and failure-taxonomy evidence. |
| Mitigation + reproducibility | 11-12 | 2:00 | Explain why failures become a mitigation ladder and how claims trace to artifacts. |
| Close | 13 | 1:00 | Land the benchmark-design thesis and upstreaming status. |
| Buffer | backup | 1:30 | In-envelope reserve; use only if asked about grid size, quality caveats, or remaining work. |

If time is tight, cut Slide 11 down to one sentence and move mitigation details
to backup. Do not cut Slide 10; the failure-taxonomy result is one of the
strongest differentiators.

## Main Story Beats

### Opening

Say:

> We built SmartGridBench, a Smart Grid transformer-maintenance extension of
> AssetOpsBench, then used it to measure how tool protocol, orchestration, and
> failure accounting change what an industrial-agent benchmark can honestly
> claim.

Why:

This frames the project as more than a dataset port and more than a demo.

### Benchmark artifact

Keep the artifact claim concrete:

- four Smart Grid tool domains
- shared transformer asset key
- 36 paper-grade canonical scenarios (31 hand-authored + 5 promoted generated)
  + 5 negative fixtures
- common benchmark output contract
- [IBM AssetOpsBench PR #287](https://github.com/IBM/AssetOpsBench/pull/287)
  opened as the upstream thin domain cut

The repo's `data/scenarios/` directory currently holds 61 scenario files
because PR #199 added 25 post-submission stretch scenarios; those 25 are NOT
judged or in paper claims. Avoid implying that all result tables have been
regenerated over the 36-scenario corpus, and never imply evaluation across
the 61 repo total. Most paper-grade evidence still uses the post-PR175
31-scenario floor.

### Experiment split

Say:

> B is our anchor cell. In Experiment 1, it is the MCP baseline against direct
> tools and optimized MCP. In Experiment 2, it is the Agent-as-Tool baseline
> against Plan-Execute variants.

Why:

This helps the audience understand why the matrix is intentionally not a full
cartesian product.

### Results interpretation

Use conservative wording:

- Transport: optimized MCP improves the first-capture p50, but C has a cold-tail
  p95 and does not improve judge quality.
- Profiling: W&B / profiler inventory coverage is now a first-class result; PE
  and Verified PE still have a torch-trace hook gap in the spot checks.
- Orchestration: vanilla PE is weak, while Verified PE + Self-Ask is currently
  strongest on judged quality.
- Failure taxonomy: current claims should cite the 1,276-failure PR #197 surface,
  not the historical 35-row taxonomy scaffold.
- Mitigation: PR #198 supports mixed before/after effects, not a universal lift.

Avoid:

- "MCP is faster" as a global claim.
- "Plan-Execute is better" as a global claim.
- "All 36 scenarios were fully re-evaluated" unless a refreshed evidence pull
  lands.
- "IBM accepted/merged SmartGridBench" while PR #287 is only draft-open.

### Close

Say:

> The lesson is that benchmark infrastructure choices are part of the scientific
> result. If protocol, orchestration, and failure accounting are not recorded,
> the benchmark can look clean while hiding the reasons an agent actually
> succeeded or failed.

## Proof Objects by Slide

| Slide | Proof object | Source |
|---:|---|---|
| 3 | Tool-domain table | `mcp_servers/`, `docs/data_pipeline.tex` |
| 4 | Workload / dataset overview | `data/scenarios/`, `data/scenarios/validate_scenarios.py`, PR #195, IBM PR #287, `paper_dataset_overview.png` |
| 5 | Artifact-contract diagram | `scripts/run_experiment.sh`, `benchmarks/cell_<X>/` |
| 6 | Experiment matrix | `docs/experiment_matrix.md` |
| 7 | Transport table | `results/metrics/notebook02_latency_summary.csv`, `results/metrics/experiment_matrix_summary.csv` |
| 8 | Profiling inventory | `results/metrics/profiling_inventory.csv` |
| 9 | Orchestration table | `results/metrics/notebook03_orchestration_comparison.csv`, `results/metrics/notebook03_self_ask_ablation.csv`, `results/metrics/experiment_matrix_summary.csv` |
| 10 | Failure taxonomy | `results/metrics/failure_taxonomy_current.csv`, `results/metrics/failure_taxonomy_current_auto_label_counts.csv`, `docs/failure_taxonomy_audit_2026-05-07.md` |
| 11 | Mitigation ladder | `docs/mitigation_recovery_adjudication.md`, `results/metrics/mitigation_before_after.csv` |
| 12 | Reproducibility map | `docs/validation_log.md`, `results/metrics/`, `results/figures/`, IBM PR #287 |

## PowerPoint Build Checklist

- [x] Create a first editable PPTX build from
      `docs/final_presentation_deck.md`.
- [ ] Decide whether to keep the artifact-tool visual system or convert into
      the class deck template before submission.
- [ ] Use one claim per slide; move extra bullets into speaker notes.
- [ ] Add source footer to every result slide.
- [ ] Mention IBM AssetOpsBench PR #287 on Slide 4 or Slide 12; update the badge
      from draft to Ready if it leaves draft state before the talk.
- [ ] Insert `results/figures/failure_taxonomy_current_auto_label_counts.svg`
      or a current table derived from `failure_taxonomy_current*.csv`.
- [ ] Decide whether `results/figures/notebook03_pe_family_follow_on.png` is a
      main slide or backup slide.
- [ ] Keep Cell D / 70B context evidence in backup unless the paper promotes it
      in main text; #95 is closed but exploratory.
- [ ] Dry-run once against 10-12 minute timing.
- [ ] Re-check every numeric slide against `results/metrics/` after any final
      rerun PR merges.

## Open Gates

| Gate | Owner | Deck effect |
|---|---|---|
| IBM AssetOpsBench PR #287 state | Alex | Slide should say draft-open now; change to Ready only after GitHub draft state flips and DCO is green. |
| Current evidence freeze | Alex + team inputs | Slides 7-11 should cite PR #197/#198 current CSVs and captions, not stale notebook figures. |
| Final paper figures | Alex + team inputs | Slides 7-11 should mirror the paper figures and captions. |
| Overleaf/source paper freeze | Alex | Deck conclusion should match the final paper claim wording. |

Until those gates clear, #44 should remain open.
