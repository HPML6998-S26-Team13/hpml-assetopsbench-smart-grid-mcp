# Documentation Index

Living, authored documentation for the SmartGridBench project. Everything in this directory is a doc that **evolves** with the project — domain background, setup guides, architecture notes, methodology. Planning artifacts (roadmap, meeting agendas, working notes) live in [`../planning/`](../planning/). Frozen deliverables (shipped PDFs, slide decks) live in [`../reports/`](../reports/).

## Document index

| File | Purpose | Start here if… |
|---|---|---|
| [`project_synopsis.md`](project_synopsis.md) | Cold-start project overview with full domain background, problem statement, team roles, timeline, current status | You're new to the project and want the complete picture in ~10 minutes |
| [`project_reference.md`](project_reference.md) | Class requirements, grading rubric, mentor guidance, course context, report templates | You need to know what HPML class/Dhaval expects as deliverables |
| [`execution_plan.md`](execution_plan.md) | Task dependency map (Tier 1-5 critical path) + benchmarking operations (async batch workflow, 5-cell experimental grid, role clarifications) | You want to know what blocks what, who owns what, and what running experiments actually looks like operationally |
| [`compute_plan.md`](compute_plan.md) | Phase-by-phase GPU allocation across Insomnia (H100, A6000) and $500/person GCP budget, hardware strategy decisions | You need to spin up an environment or pick a GPU for a workload |
| [`watsonx_access.md`](watsonx_access.md) | WatsonX API setup walkthrough, available models, usage patterns, latency benchmark results (Maverick vs 70B) | You need to onboard your local `.venv` to hit the hosted Llama models |
| [`repo_strategy.md`](repo_strategy.md) | Team repo vs AssetOpsBench fork split, what lives where, public-repo hygiene, gitignored items | You're trying to figure out where to put new code or what should/shouldn't be committed |
| [`mid_checkpoint_notes.md`](mid_checkpoint_notes.md) | Long-form reference notes backing the mid-point submission (Apr 6) | You want the detailed narrative behind the 5-slide mid-point deck |
| [`data_pipeline.tex`](data_pipeline.tex) | Paper-ready LaTeX section describing dataset schemas, shared-key strategy, output formats, reproducibility | You're writing the paper/report and need the data-pipeline section |
| [`dataset_visualization.png`](dataset_visualization.png) | 6-panel sample visualization of the processed datasets (smoke test / sanity check, not a reproducible artifact) | You want to eyeball what the processed data looks like |
| [`hpml_datasets.pdf`](hpml_datasets.pdf) | Tanisha's reference writeup on the 5 Kaggle source datasets (formats, row counts, licensing) | You need background on where the data came from |
| `images/` | Inline figures referenced by the `.md` files | — |

## Related directories

- [`../planning/`](../planning/) — Meeting agendas, working notes, and the canonical task tracker. **Start with [`../planning/task_tracker.md`](../planning/task_tracker.md)** for current task state across all weeks (Done / In Progress / Backlog by week / Stretch).
- [`../reports/`](../reports/) — Frozen deliverables (mid-point submission PDF, proposal PDFs, draft archive).

## Conventions

- **One purpose per file** — if a doc is doing two things, split it.
- **Date-stamped markdown updates** — every doc should have a `*Last updated: YYYY-MM-DD*` line near the top. Stale dates are a smell.
- **Cross-reference other docs by relative path** — e.g. `[compute plan](compute_plan.md)`, not absolute URLs. Keeps the repo portable.
- **Paper-ready content (LaTeX) lives here** — finished paper sections can be dropped into Overleaf as `.tex` files. Don't mix draft and final in the same file; use git history for versions.
- **No shipped deliverables here** — if it's a frozen PDF/PPTX/Keynote export that was submitted or emailed, it belongs in `../reports/`, not `docs/`.
- **No planning artifacts here** — the roadmap, meeting agendas, and ephemeral coordination notes belong in `../planning/`.
