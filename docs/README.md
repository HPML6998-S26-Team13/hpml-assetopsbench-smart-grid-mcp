# Documentation Index

Living, authored documentation for the SmartGridBench project. Everything in this directory is a doc that **evolves** with the project - domain background, setup guides, architecture notes, methodology. Planning artifacts (roadmap, meeting agendas, working notes) live in [../planning/](../planning/). Frozen deliverables (shipped PDFs, slide decks) live in [../reports/](../reports/). Historical supporting notes that are no longer live move into [archive/](archive/). Lower-churn class / mentor / setup references now live under [reference/](reference/).

## Document index

| File | Purpose | Start here if… |
|---|---|---|
| [project_synopsis.md](project_synopsis.md) | Cold-start project overview with full domain background, problem statement, team roles, timeline, current status | You're new to the project and want the complete picture in ~10 minutes |
| [reference/project_reference.md](reference/project_reference.md) | Class requirements, grading rubric, mentor guidance, course context, report templates | You need to know what HPML class/Dhaval expects as deliverables |
| [execution_plan.md](execution_plan.md) | Task dependency map (Tier 1-5 critical path) + benchmarking operations (async batch workflow, 5-cell experimental grid, role clarifications) | You want to know what blocks what, who owns what, and what running experiments actually looks like operationally |
| [runbook.md](runbook.md) | Canonical end-to-end reproducibility runbook for the infra side — preconditions, first-time setup, submitting benchmark cells, profiling workflow, troubleshooting decision tree, pointers to detailed runbooks | You need to stand up the serving / benchmark / profiling pipeline from scratch without verbal help |
| [validation_log.md](validation_log.md) | Canonical log of concrete serve / benchmark / profiling proofs, including run IDs, artifacts, what each run actually proved, and caveats | You need the durable record of live validation runs rather than the how-to runbooks |
| [compute_plan.md](compute_plan.md) | Phase-by-phase GPU allocation across Insomnia (H100, A6000) and $500/person GCP budget, hardware strategy decisions | You need to spin up an environment or pick a GPU for a workload |
| [gcp_fallback.md](gcp_fallback.md) | Emergency GCP A100 spin-up runbook — when to use it, instance selection, env setup, artifact persistence, shutdown, spot preemption handling, budget tracking, known GPU differences from Insomnia | Insomnia is down / queue-saturated and you need GPUs now, or you're considering a one-off A100 run |
| [insomnia_runbook.md](insomnia_runbook.md) | Verified Insomnia setup notes - Slurm account/partition/QoS, scratch storage, CUDA/cuDNN workarounds, vLLM Python-version gotcha, login-node etiquette, queue tips, foreground-debug recipe | You're hitting weird Slurm/CUDA/vLLM behavior on Insomnia and need verified working settings |
| [governance/model_registry.yaml](governance/model_registry.yaml) | Canonical registry for the current local-vLLM and WatsonX model contracts, including served model names, repo-facing model IDs, runtime pins, and the standardized `MODEL_REVISION` for the local Llama mirror | You need the quick source of truth for which model names/IDs/runtime pins the repo is actually supposed to use |
| [slurm_cheatsheet.md](slurm_cheatsheet.md) | Command-first Slurm reference for submit, watch, estimate start, inspect failures, and historical timing on Insomnia | You need the exact command for `sbatch`, `srun`, `squeue`, `sacct`, `scontrol`, or `scancel` without rereading the longer runbook |
| [coordination/live_repo_summary.md](coordination/live_repo_summary.md) | Current-state control-room memo for incoming agents: merged PRs, open loops, validation ledger, and current repo truth | You need the stable current state without rereading issue threads and PRs |
| [coordination/repo_summary_history.md](coordination/repo_summary_history.md) | Rolling archive of removed/condensed live-summary material with enough detail for timeline and audit use | You need historical context that has already been trimmed out of the live summary |
| [coordination/shift_coordination_note_template.md](coordination/shift_coordination_note_template.md) | Short per-agent coordination-note template for concurrent work or handoff, with retirement guidance into the live summary and history doc | You want a compact coordination note without turning it into a second full repo summary |
| [orchestration_wiring.md](orchestration_wiring.md) | Current repo-side orchestration status for Plan-Execute, Agent-as-Tool, and Hybrid, including what is genuinely wired now versus only adapter-ready | You need to know what `#22` / `#62` cover in this repo and what is still upstream or mentor-gated |
| [experiment_matrix.md](experiment_matrix.md) | Sharp statement of the core experiment grid, trial policy, Self-Ask tracking, and which optional follow-on cells are worth adding later | You want one defensible answer to "what exactly are we running?" before the matrix sprawls |
| [experiment1_capture_plan.md](experiment1_capture_plan.md) | Capture plan for Experiment 1 (`#25`): Cell A/B/C config layout, fairness contract, runner requirements, team dependencies, and proposed run sequence through Apr 22 | You need to know what blocks the Direct / MCP-baseline / MCP-optimized captures and how the artifacts feed Alex's Notebook 02 |
| [failure_analysis_scaffold.md](failure_analysis_scaffold.md) | Before/after metric pack for `#36`: outcome / failure-shape / latency / profiling field list, comparison ledger, export contract, comparison-ready status labels | You need the canonical contract for what the `#36` rerun lane has to produce so notebook and paper exports stay joinable |
| [failure_taxonomy_evidence.md](failure_taxonomy_evidence.md) | Failure taxonomy classification for `#35`: Berkeley categories, decision ladder, evidence schema, populated Apr 22 evidence pass, paper-safe wording guide, classification workflow | You need to label observed failures with concrete artifact backing instead of vibes, and you want one evidence row per `(run_name, scenario_id, trial_index)` |
| [failure_visuals_mitigation.md](failure_visuals_mitigation.md) | Visuals scaffold + figure-ready aggregation contract + mitigation ranking rubric + Apr 22 mitigation ranking + promotion gate into `#65` / `#66` for `#64` | You need to decide which mitigation goes first into implementation/rerun and what figure each visual should render from |
| [scenario_realism_validation.md](scenario_realism_validation.md) | Mentor-facing realism-validation pack for the current Smart Grid scenario families, including representative scenarios, known realism gaps, and the concrete questions to send Dhaval | You need to sanity-check whether the current Smart Grid scenarios read like believable transformer maintenance work |
| [ps_b_evaluation_methodology.md](ps_b_evaluation_methodology.md) | Validation rubric for comparing generated PS B scenarios against the hand-crafted Smart Grid set, including duplication checks, acceptance thresholds, and explicit circularity handling | You need the concrete standard Akshat should apply when validating generated scenarios |
| [neurips_abstract_outline.md](neurips_abstract_outline.md) | Working title list, abstract skeleton, and evidence map for the NeurIPS paper lane | You need a prepared outline for the final abstract rather than drafting from scratch under deadline pressure |
| [neurips_draft.md](neurips_draft.md) | Live NeurIPS paper-writing scaffold for `#5`: title, one-paragraph claim, draft abstract, working contribution list, claim ledger, section scaffold, draft prose ready to lift into Overleaf | You want the paper effort to move beyond outline-only planning into a real draft surface with reusable section text |

| [reference/watsonx_access.md](reference/watsonx_access.md) | WatsonX API setup walkthrough, available models, usage patterns, latency benchmark results (Maverick vs 70B) | You need to onboard your local `.venv` to hit the hosted Llama models |
| [eval_harness_readme.md](eval_harness_readme.md) | End-to-end Windows runbook for AssetOpsBench harness, WatsonX setup, Docker path, `scenario-server` grading flow, **both CODS benchmark tracks** (`cods_track1`, `cods_track2`), smoke script (`../scripts/run_harness_smoke.cmd`), and proof expectations for canonical runs | You need to quickly prove harness execution is working this week and run new scenario prompts |
| [data_pipeline.tex](data_pipeline.tex) | Paper-ready LaTeX section describing dataset schemas, shared-key strategy, output formats, reproducibility | You're writing the paper/report and need the data-pipeline section |
| [dataset_visualization.png](dataset_visualization.png) | Historical 6-panel sample visualization of the processed datasets (static smoke test only; [../notebooks/01_data_exploration.ipynb](../notebooks/01_data_exploration.ipynb) is the reproducible successor) | You want to compare the old static smoke-test image with the new notebook-backed exploration path |
| [hpml_datasets.pdf](hpml_datasets.pdf) | Tanisha's reference writeup on the 5 Kaggle source datasets (formats, row counts, licensing) | You need background on where the data came from |
| `images/` | Inline figures referenced by the `.md` files | - |
| `archive/` | Historical docs that were once live but are now frozen reference artifacts | You need provenance, not the current operating picture |

## Related directories

- [knowledge/](knowledge/) - PS B generation support: scenario family matrix, operational context profiles, DGA trend templates, event/alarm templates, WO playbook, and scenario authoring contract with ground-truth field spec.
- [../scripts/README.md](../scripts/README.md) - Executable entrypoints and helper scripts.
- [../configs/README.md](../configs/README.md) - Benchmark config schema and cell naming.
- [../data/README.md](../data/README.md) - Data pipeline and processed dataset policy.
- [../data/scenarios/README.md](../data/scenarios/README.md) - Scenario authoring guide and validator entrypoint.
- [../mcp_servers/README.md](../mcp_servers/README.md) - Smart Grid MCP server layout and tool surfaces.
- [../benchmarks/README.md](../benchmarks/README.md) - Raw benchmark artifact layout.
- [../notebooks/README.md](../notebooks/README.md) - Analysis notebook contract.
- [../results/README.md](../results/README.md) - Derived metrics / figures contract.
- [../profiling/README.md](../profiling/README.md) - Profiling capture workflow and wrappers.
- [../planning/](../planning/) - Meeting agendas, working notes, and archived planning snapshots. Current task state now lives in the [GitHub Project](https://github.com/orgs/HPML6998-S26-Team13/projects/1/views/1); historical tracker/spec snapshots live in [../planning/archive/task_tracker.md](../planning/archive/task_tracker.md) and [../planning/archive/task_specs.md](../planning/archive/task_specs.md).
- [../reports/](../reports/) - Frozen deliverables (mid-point submission PDF, proposal PDFs, draft archive).
- [governance/](governance/) - Small repo-truth governance artifacts, starting with the model/runtime registry for local vLLM and WatsonX naming/pinning.

## Conventions

- **One purpose per file** - if a doc is doing two things, split it.
- **Date-stamped markdown updates** - every doc should have a `*Last updated: YYYY-MM-DD*` line near the top. Stale dates are a smell.
- **Cross-reference other docs by relative path** - e.g. [compute plan](compute_plan.md), not absolute URLs. Keeps the repo portable.
- **Low-churn reference docs live under `reference/`** - class requirements, mentor guidance, and setup references that change less often should live there rather than crowding the top-level index.
- **Paper-ready content (LaTeX) lives here** - finished paper sections can be dropped into Overleaf as `.tex` files. Don't mix draft and final in the same file; use git history for versions.
- **No shipped deliverables here** - if it's a frozen PDF/PPTX/Keynote export that was submitted or emailed, it belongs in `../reports/`, not `docs/`.
- **No planning artifacts here** - the roadmap and meeting agendas belong in `../planning/`; durable coordination surfaces live under `coordination/`.
