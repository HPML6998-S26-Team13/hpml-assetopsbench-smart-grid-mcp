# Final Report Back-Port Scaffold

*Last updated: 2026-05-02*
*Owner: Alex Xin*
*Issues: `#40`, with source draft tracked by `#5` / `#39`*

This is the control surface for turning the NeurIPS Datasets & Benchmarks draft
into the class IEEE-format final report without content drift. The source of
truth for claims and prose remains `docs/neurips_draft.md`; this file defines
the conversion path. The first content-bearing class report drafting surface is
now `reports/final_report_ieee_draft.md`.

## Source-of-truth order

Use this order when the report and paper disagree:

1. `docs/validation_log.md` and committed benchmark artifacts for run IDs,
   artifact paths, and what a run proves.
2. `results/metrics/*.csv` and `results/figures/*` for result tables and
   figure inputs.
3. `docs/neurips_draft.md` for canonical paper framing and reusable prose.
4. This file for class-report section placement and conversion checks.

Do not introduce class-report-only claims unless they are explicitly marked as
class-format framing. If a factual claim changes, update `docs/neurips_draft.md`
first and then back-port it here.

## Section map

| IEEE final report section | Source in NeurIPS draft / repo | Conversion note |
|---|---|---|
| Abstract | `docs/neurips_draft.md` abstract | Same core paragraph; trim venue-specific wording if needed. |
| Introduction | Introduction + contribution paragraphs | Keep the benchmark gap, MCP systems variable, and AaT vs PE framing. |
| Models and Data Description | Benchmark Extension + `docs/data_pipeline.tex` | Emphasize source datasets, shared `transformer_id`, scenarios, and four tool domains. |
| Training and Profiling Methodology | System Design + runbook/profiling docs | The class heading says training, but our work is inference/profiling; phrase the section as serving, orchestration, and profiling methodology. |
| Performance Tuning Methodology | Experiment 1 Cell C / D / ZSD optimization discussion | Separate clean transport optimization from exploratory optimized-serving ablations. |
| Experimental Results | Results + failure analysis sections | Use Notebook 02/03 exports, validation ledger references, and failure taxonomy figures after PR `#151` or equivalent artifacts land. |
| Conclusion | Discussion / limitations / future work | Keep claims conservative; include AOB upstream path as future work, not a deadline blocker. |

## Required report figures and tables

Minimum report-ready set:

- Experiment 1 latency comparison from Notebook 02.
- Experiment 2 orchestration comparison from Notebook 03.
- Failure taxonomy count figure after PR `#151` or equivalent artifacts land.
- Failure stage-by-cell heatmap after PR `#151` or equivalent artifacts land.
- Experiment matrix / trial-policy table.
- Artifact ledger table with Slurm run IDs and repo paths.

Optional if evidence lands in time:

- Mitigation before/after figure from `mitigation_before_after.csv`.
- PE-family optimized-serving ablation table.
- Scenario-realism / generated-scenario validation figure.

## May 2 draft status

`reports/final_report_ieee_draft.md` now contains the first full IEEE-section
draft with current evidence tables for:

- Experiment 1 A/B/C transport latency.
- Experiment 2 B/Y/Z and PE-family Self-Ask quality.
- Failure taxonomy class counts.
- Figure and artifact checklist.

The draft intentionally distinguishes canonical `team13/main` facts from
pending deadline work. In particular, it does not claim the 30-scenario floor is
complete until PR #156 plus generator-accepted scenarios are merged and
validated.

## Back-port checklist

- [ ] Freeze the result tables and figure files that the class report cites.
- [x] Copy the NeurIPS abstract into the report and trim only for class format.
- [x] Convert the benchmark-extension section into Models and Data Description.
- [x] Convert the system-design section into methodology, avoiding any claim
      that we trained a model when we only served and profiled inference.
- [x] Convert the optimization discussion into Performance Tuning Methodology.
- [ ] Insert result figures with captions that include source CSV / run IDs in
      the final IEEE LaTeX surface.
- [ ] Insert the artifact ledger and validation caveats in the final IEEE
      LaTeX surface.
- [ ] Check every numeric claim against `results/metrics/` or
      `docs/validation_log.md`.
- [ ] Compile the IEEE Overleaf report and record the compile/export status in
      the issue or PR thread.

## Current status

The report back-port now has a content-bearing Markdown draft, but the
IEEE-format LaTeX report has not yet been compiled/exported. `#40` should
remain open until the final IEEE Overleaf report is generated from the NeurIPS
source without content drift and the numeric claims are checked against the
final frozen artifacts.
