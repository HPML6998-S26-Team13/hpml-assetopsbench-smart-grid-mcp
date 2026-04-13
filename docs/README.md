# Documentation Index

Living, authored documentation for the SmartGridBench project. Everything in this directory is a doc that **evolves** with the project - domain background, setup guides, architecture notes, methodology. Planning artifacts (roadmap, meeting agendas, working notes) live in [`../planning/`](../planning/). Frozen deliverables (shipped PDFs, slide decks) live in [`../reports/`](../reports/). Historical supporting notes that are no longer live move into [`archive/`](archive/).

## Document index

| File | Purpose | Start here if… |
|---|---|---|
| [`project_synopsis.md`](project_synopsis.md) | Cold-start project overview with full domain background, problem statement, team roles, timeline, current status | You're new to the project and want the complete picture in ~10 minutes |
| [`project_reference.md`](project_reference.md) | Class requirements, grading rubric, mentor guidance, course context, report templates | You need to know what HPML class/Dhaval expects as deliverables |
| [`execution_plan.md`](execution_plan.md) | Task dependency map (Tier 1-5 critical path) + benchmarking operations (async batch workflow, 5-cell experimental grid, role clarifications) | You want to know what blocks what, who owns what, and what running experiments actually looks like operationally |
| [`compute_plan.md`](compute_plan.md) | Phase-by-phase GPU allocation across Insomnia (H100, A6000) and $500/person GCP budget, hardware strategy decisions | You need to spin up an environment or pick a GPU for a workload |
| [`insomnia_runbook.md`](insomnia_runbook.md) | Verified Insomnia setup notes — Slurm account/partition/QoS, scratch storage, CUDA/cuDNN workarounds, vLLM Python-version gotcha, login-node etiquette, queue tips, foreground-debug recipe | You're hitting weird Slurm/CUDA/vLLM behavior on Insomnia and need verified working settings |
| [`orchestration_wiring.md`](orchestration_wiring.md) | Current repo-side orchestration status for Plan-Execute, Agent-as-Tool, and Hybrid, including what is genuinely wired now versus only adapter-ready | You need to know what `#22` / `#62` cover in this repo and what is still upstream or mentor-gated |
| [`scenario_realism_validation.md`](scenario_realism_validation.md) | Mentor-facing realism-validation pack for the current Smart Grid scenario families, including representative scenarios, known realism gaps, and the concrete questions to send Dhaval | You need to sanity-check whether the current Smart Grid scenarios read like believable transformer maintenance work |
| [`watsonx_access.md`](watsonx_access.md) | WatsonX API setup walkthrough, available models, usage patterns, latency benchmark results (Maverick vs 70B) | You need to onboard your local `.venv` to hit the hosted Llama models |
| [`eval_harness_readme.md`](eval_harness_readme.md) | End-to-end Windows runbook for AssetOpsBench harness, WatsonX setup, Docker path, `scenario-server` grading flow, **both CODS benchmark tracks** (`cods_track1`, `cods_track2`), smoke script (`../scripts/run_harness_smoke.cmd`), and proof expectations for canonical runs | You need to quickly prove harness execution is working this week and run new scenario prompts |
| [`repo_strategy.md`](repo_strategy.md) | Team repo vs AssetOpsBench fork split, what lives where, public-repo hygiene, gitignored items | You're trying to figure out where to put new code or what should/shouldn't be committed |
| [`data_pipeline.tex`](data_pipeline.tex) | Paper-ready LaTeX section describing dataset schemas, shared-key strategy, output formats, reproducibility | You're writing the paper/report and need the data-pipeline section |
| [`dataset_visualization.png`](dataset_visualization.png) | 6-panel sample visualization of the processed datasets (smoke test / sanity check, not a reproducible artifact) | You want to eyeball what the processed data looks like |
| [`hpml_datasets.pdf`](hpml_datasets.pdf) | Tanisha's reference writeup on the 5 Kaggle source datasets (formats, row counts, licensing) | You need background on where the data came from |
| `images/` | Inline figures referenced by the `.md` files | — |
| `archive/` | Historical docs that were once live but are now frozen reference artifacts | You need provenance, not the current operating picture |

## Related directories

- [`../planning/`](../planning/) — Meeting agendas, working notes, and archived planning snapshots. Current task state now lives in the [GitHub Project](https://github.com/orgs/HPML6998-S26-Team13/projects/1/views/1); historical tracker/spec snapshots live in [`../planning/archive/task_tracker.md`](../planning/archive/task_tracker.md) and [`../planning/archive/task_specs.md`](../planning/archive/task_specs.md).
- [`../reports/`](../reports/) — Frozen deliverables (mid-point submission PDF, proposal PDFs, draft archive).

## Conventions

- **One purpose per file** — if a doc is doing two things, split it.
- **Date-stamped markdown updates** — every doc should have a `*Last updated: YYYY-MM-DD*` line near the top. Stale dates are a smell.
- **Cross-reference other docs by relative path** — e.g. `[compute plan](compute_plan.md)`, not absolute URLs. Keeps the repo portable.
- **Paper-ready content (LaTeX) lives here** — finished paper sections can be dropped into Overleaf as `.tex` files. Don't mix draft and final in the same file; use git history for versions.
- **No shipped deliverables here** — if it's a frozen PDF/PPTX/Keynote export that was submitted or emailed, it belongs in `../reports/`, not `docs/`.
- **No planning artifacts here** — the roadmap, meeting agendas, and ephemeral coordination notes belong in `../planning/`.
