# Final Presentation Run of Show

*Created: 2026-05-02*
*Owner: Alex Xin*
*Issue: #44*

This is the production companion for `docs/final_presentation_deck.md`. The deck
already has slide-by-slide content; this file turns it into a presentation plan
with timing, proof objects, and final build gates.

Current editable PPTX draft:
`reports/archive/2026-05-03_final_presentation_smartgridbench_draft.pptx`.
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
| Experimental design | 4-6 | 2:00 | Explain scenario status, artifact contract, and A/B/C vs B/Y/Z split. |
| Results | 7-9 | 3:30 | Show transport, orchestration, and failure-taxonomy evidence. |
| Mitigation + reproducibility | 10-11 | 2:00 | Explain why failures become a mitigation ladder and how claims trace to artifacts. |
| Close | 12 | 1:00 | Land the benchmark-design thesis. |
| Buffer | backup | 1:30 | In-envelope reserve; use only if asked about grid size, quality caveats, or remaining work. |

If time is tight, cut Slide 10 down to one sentence and move mitigation details
to backup. Do not cut Slide 9; the failure-taxonomy result is one of the
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
- committed scenario artifacts
- common benchmark output contract

Avoid claiming final scenario counts until the 30-scenario floor is merged and
validated.

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
- Orchestration: vanilla PE is weak, while Verified PE + Self-Ask is currently
  strongest on judged quality.
- Failure taxonomy: evidence verification, not transport plumbing, is the
  dominant failure class.

Avoid:

- "MCP is faster" as a global claim.
- "Plan-Execute is better" as a global claim.
- "30 scenarios are complete" until merged/validated.

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
| 4 | Scenario-count status | `data/scenarios/`, `data/scenarios/validate_scenarios.py`, PR #156, generator acceptance status |
| 5 | Artifact-contract diagram | `scripts/run_experiment.sh`, `benchmarks/cell_<X>/` |
| 6 | Experiment matrix | `docs/experiment_matrix.md` |
| 7 | Transport table | `results/metrics/notebook02_latency_summary.csv`, `results/metrics/experiment_matrix_summary.csv` |
| 8 | Orchestration table | `results/metrics/notebook03_orchestration_comparison.csv`, `results/metrics/notebook03_self_ask_ablation.csv`, `results/metrics/experiment_matrix_summary.csv` |
| 9 | Failure taxonomy | `results/metrics/failure_taxonomy_counts.csv`, `results/figures/failure_taxonomy_counts.svg` |
| 10 | Mitigation ladder | `docs/mitigation_recovery_adjudication.md`, `results/metrics/mitigation_run_inventory.csv` |
| 11 | Reproducibility map | `docs/validation_log.md`, `results/metrics/`, `results/figures/` |

## PowerPoint Build Checklist

- [x] Create a first editable PPTX build from
      `docs/final_presentation_deck.md`.
- [ ] Decide whether to keep the artifact-tool visual system or convert into
      the class deck template before submission.
- [ ] Use one claim per slide; move extra bullets into speaker notes.
- [ ] Add source footer to every result slide.
- [ ] Insert `results/figures/failure_taxonomy_counts.svg` and
      `results/figures/failure_stage_cell_heatmap.svg`.
- [ ] Decide whether `results/figures/notebook03_pe_family_follow_on.png` is a
      main slide or backup slide.
- [ ] Keep Cell D / 70B context evidence in backup unless the paper promotes it
      before deck freeze.
- [ ] Dry-run once against 10-12 minute timing.
- [ ] Re-check every numeric slide against `results/metrics/` after any final
      rerun PR merges.

## Open Gates

| Gate | Owner | Deck effect |
|---|---|---|
| PR #156 and generated scenarios | Tanisha/Akshat, Alex shepherd | Slide 4 can claim 30 validated scenarios only after this settles. |
| Mitigation rerun rows | Alex | Slide 10 can become results-bearing only if header-only `results/metrics/mitigation_before_after.csv` gets real rows. |
| Final paper figures | Alex + team inputs | Slides 7-9 should mirror the paper figures and captions. |
| Overleaf/source paper freeze | Alex | Deck conclusion should match the final paper claim wording. |

Until those gates clear, #44 should remain open.
