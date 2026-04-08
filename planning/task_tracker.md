# SmartGridBench Task Tracker

*Canonical task tracker for the SmartGridBench project. Last updated: April 8, 2026.*
*Weeks: W1 = Mar 31-Apr 6, W2 = Apr 7-13, W3 = Apr 14-20, W4 = Apr 21-27, W5 = Apr 28-May 4, FW = May 5+.*
*Roadmap view note: In the GitHub Projects board, `Iteration` is the primary timeline field. Every task, including completed work, stays assigned to the week it was due so the roadmap remains readable historically. `Priority` uses `P0` for critical-path or deadline-driven work, `P1` for important supporting work, and `P2` for stretch/future work.*
*Execution note: for exact task definitions, deliverables, dependencies, and coordination handoffs, see [`task_specs.md`](./task_specs.md). A task remains open until it is merged into the canonical repo or otherwise independently verified; local-only work counts as in progress, not done.*

## Done

### W1 (Mar 31-Apr 6) — Foundations + midpoint checkpoint

- [x] Fork AssetOpsBench, clone, run `uv sync` + unit tests (Team)
- [x] Draft mid-point PowerPoint, 5-slide template (Alex)
- [x] Set up Overleaf with problem statement, share with Dhaval (Tanisha)
- [x] Request WatsonX API key via Codabench (Alex)
- [x] Receive WatsonX credentials from Dhaval — Apr 5
- [x] Set up `.env` with WatsonX credentials in team repo (gitignored) (Alex) — Apr 5
- [x] Install `ibm-watsonx-ai` into team `uv venv` at `.venv/` (Alex) — Apr 5
- [x] Write `scripts/verify_watsonx.py` — auth + model listing + inference + latency benchmark (Alex) — Apr 5
- [x] Verify 6 Llama models available on our WatsonX account (Alex) — Apr 5
- [x] Benchmark Maverick-17B and Llama-3.3-70B latency (short + long prompts) (Alex) — Apr 5
- [x] Document WatsonX access in `docs/watsonx_access.md` with setup, model list, usage patterns, latency (Alex) — Apr 5
- [x] Add `ibm-watsonx-ai` to `requirements.txt` (Alex) — Apr 5
- [x] Document team repo strategy in `docs/repo_strategy.md` (Alex) — Apr 5
- [x] Consolidate all meeting docs and clarify next steps in shared repo (Alex)
- [x] Draft NeurIPS 2026 proposal in Overleaf (Tanisha)
- [x] Send proposal + PDF to Dhaval (Alex)
- [x] Sync fork with upstream IBM/AssetOpsBench (Alex)
- [x] Compute plan committed to `docs/compute_plan.md` (Aaron) — Apr 5
- [x] MCP server skeletons for IoT, FMSR, TSFM, WO (Tanisha) — Apr 6 (commit `717e9b4`); all four domains, with substantive logic in `fmsr_server.analyze_dga` (IEC 60599 Rogers Ratio), `tsfm_server` (RUL forecast + z-score anomalies + OLS trend), `wo_server` (full work-order CRUD)
- [x] Data pipeline `data/build_processed.py` — downloads + joins 5 Kaggle datasets, synthesizes `transformer_id` key (T-001–T-020) stratified across 4 health tiers (Tanisha) — Apr 6 (commit `717e9b4`)
- [x] Standalone synthetic generator `data/generate_synthetic.py` for offline dev/CI (Tanisha) — Apr 6
- [x] Processed CSVs landed in `data/processed/` — `asset_metadata`, `dga_records`, `failure_modes`, `fault_records`, `rul_labels`, `sensor_readings` (97k+ rows total) (Tanisha) — Apr 6 (commit `9ccdb26`)
- [x] Dataset integration — common `transformer_id` key across CC0 datasets (Tanisha) — Apr 6 (subsumed by data pipeline)
- [x] `docs/data_pipeline.tex` — paper-ready LaTeX section on dataset schemas, shared-key strategy, output schemas, limitations, reproducibility (Tanisha) — Apr 6
- [x] `docs/dataset_visualization.png` — sample/smoke-test visualization confirming data pipeline output is well-formed (6 panels: H2 over time, C2H2 arcing indicator, RUL window, RUL distribution by tier, DGA gas snapshot, fault records by tier) (Tanisha) — Apr 6. **Note:** image is a static snapshot (no tracked generator script in repo). Follow-up: commit a generator notebook into `notebooks/`, or accept as static.
- [x] Submit mid-point PowerPoint to Courseworks (Alex) — Mon Apr 6 11:59pm

### W2 (Apr 7-13) — Public release cleanup

- [x] Team repo made public + docs reorganization for public release (Alex) — Apr 7

## Milestones

- [x] Mid-point report submitted — Apr 6
- [x] Team repo public — Apr 7
- [ ] W2 foundation stack ready (serving, profiling harness, hardened MCP servers, 15+ validated scenarios) — Apr 13
- [ ] Experiment 1 completed (MCP overhead) — Apr 20
- [ ] Experiment 2 completed (orchestration comparison) — Apr 27
- [ ] Final class deliverables ready (report + deck + code) — May 4
- [ ] NeurIPS 2026 abstract submitted — May 4
- [ ] NeurIPS 2026 full paper submitted — May 6

## In Progress

- [ ] Replay local Smart Grid scenario files onto canonical `team13/main` and push first batch (Akshat)
- [ ] Replay local benchmark / harness README work onto canonical `team13/main` and push (Akshat)
- [ ] Get AssetOpsBench evaluation harness running end-to-end on the canonical branch (Akshat)
- [ ] Draft first 5-10 Smart Grid transformer scenarios and commit them to the canonical repo (Akshat)
- [ ] Successful first Insomnia A6000 vLLM serve smoke test for Llama-3.1-8B-Instruct (Aaron)
- [ ] Validate all four MCP servers with the benchmark Llama path, not only Claude Desktop (Tanisha)
- [ ] NeurIPS 2026 paper — draft in NeurIPS format first, then back-port to IEEE final report (Alex)

## Backlog

### W2 (Apr 7-13) — Foundation + MCP servers + scenarios

**Foundation (Tier 1 — must complete to unblock everything else):**

- [ ] Generic Slurm experiment template for benchmark jobs (Aaron)
- [ ] Profiling capture wrappers — PyTorch Profiler around benchmark runs (Aaron)
- [ ] Profiling capture wrappers — Nsight / `nvidia-smi` / GPU utilization collection (Aaron)
- [ ] Complete IoT MCP server hardening + tests + harness contract (Tanisha)
- [ ] Complete TSFM MCP server hardening + tests + harness contract (Tanisha)
- [ ] Complete FMSR MCP server hardening + tests + harness contract (Tanisha)
- [ ] Complete WO MCP server hardening + tests + harness contract (Tanisha)
- [ ] WO server architecture review against Dhaval's “WO agent is a coding agent” guidance (Tanisha)
- [ ] Reach 15+ validated Smart Grid scenarios in the canonical repo (Akshat)
- [ ] Validate Smart Grid scenario format against AssetOpsBench schema and conventions (Akshat)
- [ ] Real-world scenario validation plan (Akshat)
- [ ] 6-dimension LLM-as-Judge scoring in eval harness (Akshat)
- [ ] First baseline agent trajectory through MCP end-to-end (Akshat)
- [ ] First end-to-end judge call using Maverick-17B on a real trajectory (Akshat)
- [ ] WandB metrics schema definition for servers, trajectories, and experiment cells (Alex)
- [ ] WandB instrumentation in MCP servers and agent pipeline (Alex)
- [ ] Wire Agent-as-Tool orchestration to the team's MCP servers (Alex)
- [ ] Wire Plan-Execute orchestration to the team's MCP servers (Alex)
- [ ] Follow up with Dhaval on hybrid orchestration novelty and Smart Grid scenario realism / validation criteria (Alex)
- [ ] Each team member sync canonical `team13/main`, install `ibm-watsonx-ai` into `.venv`, and run the verify script locally (Team)
- [ ] Set up WandB project with initial experiment logs (Team)

### W3 (Apr 14-20) — Baseline profiling + experimental design

- [ ] Hybrid orchestration prototype implementation (Alex)
- [ ] Self-Ask integration (~10 LOC) in all 3 orchestrations (Alex)
- [ ] Run Experiment 1 profiling captures (Direct vs MCP-baseline vs MCP-optimized) and publish raw artifacts for analysis (Aaron)
- [ ] Notebook 02: latency analysis — MCP overhead experiment design, parsing, and writeup (Alex)
- [ ] Integrate WandB logging into profiling pipeline (Aaron)
- [ ] First WandB experiment logs live (Team)
- [ ] Knowledge Plugin: encode IEC 60599 + IEEE C57 transformer engineering standards as a structured knowledge document the scenario-gen LLM can consume (Tanisha)
- [ ] Auto-scenario generation prototype — first generated Smart Grid scenario batch from Kaggle data + Knowledge Plugin (Aaron)
- [ ] Quality evaluation methodology: LLM-as-Judge against hand-crafted reference set, with circularity handling (Alex)

### W4 (Apr 21-27) — Optimizations + orchestration comparison

- [ ] Apply INT8 quantization via vLLM (Aaron)
- [ ] KV-cache tuning experiments (Aaron)
- [ ] Batched tool-call scheduling implementation (Akshat)
- [ ] Run Experiment 2 (Orchestration comparison): 3 orchestrations × N multi-domain scenarios on MCP-baseline (Alex)
- [ ] Reach 30+ scenarios (Akshat)
- [ ] Notebook 03: orchestration comparison (Alex)
- [ ] Failure taxonomy classification + evidence table (Alex)
- [ ] Failure taxonomy visuals + mitigation plan (Alex)
- [ ] Implement chosen mitigation(s) from failure taxonomy analysis (Alex)
- [ ] Re-run affected benchmark cells after mitigation and compare before/after (Alex)
- [ ] Collect before/after profiling data across all metrics (Alex)
- [ ] Runbook section: infrastructure / serving / Slurm / profiling setup (`docs/runbook.md`) (Aaron)
- [ ] Runbook section: eval harness / scenario execution / judge reproduction (`docs/runbook.md`) (Akshat)
- [ ] GCP fallback setup instructions — how to spin up A100 instance if Insomnia is down (Aaron)
- [ ] Auto-scenario generation scale-up — refine pipeline and expand generated scenario set (Aaron)
- [ ] Validate auto-generated scenarios against hand-crafted reference set (Akshat)
- [ ] Comparative analysis: hand-crafted vs auto-generated scenarios on agent performance, in notebook 04 (Alex)
- [ ] Reach 50+ scenarios total in canonical repo (manual + auto-generated) (Akshat)

### W5 (Apr 28-May 3) — Report + presentation

- [ ] NeurIPS draft — Datasets & Benchmarks Track format (Alex)
- [ ] Class final report — back-ported from NeurIPS draft to IEEE template (Alex)
- [ ] Content brief: Methodology + Data + MCP server facts, 1-page bullet list (Tanisha)
- [ ] Content brief: Scenarios + Eval + judge facts, 1-page bullet list (Akshat)
- [ ] Content brief: Infrastructure + Profiling + serving facts, 1-page bullet list (Aaron)
- [ ] Final presentation deck (Alex)
- [ ] WandB dashboard polish (Team)
- [ ] Open-source PR to AssetOpsBench (Team)
- [ ] NeurIPS 2026 abstract (Alex)
- [ ] NeurIPS 2026 full paper submission (Alex)
- [ ] Runbook final review — verify all experiments are reproducible from doc (Team)
- [ ] Paper section on Problem Statement B methodology + circularity discussion (Alex)

## Blocked

*(nothing currently blocked)*

## Notes

- NeurIPS 2026 Datasets & Benchmarks Track: abstract May 4, submission May 6
- Final deadline: May 4 (presentation + report + code)
- Weekly meetings: Tuesdays 2:45 PM ET
- AssetOpsBench has 467 scenarios across 6 HuggingFace subsets (152 original + 315 newer); our contribution is the 7th asset domain (Smart Grid transformers)
- Problem Statement B / scenario-generation work is activated and scheduled across W3-W5, not parked as stretch.
- Two experimental tracks: Experiment 1 (MCP overhead, 3 conditions) and Experiment 2 (Orchestration comparison, 3 orchestrations on MCP-baseline). 5 unique cells total. See [`../docs/execution_plan.md`](../docs/execution_plan.md) for the full operational plan with task dependency map and benchmarking workflow.

---

*This task tracker has been the canonical record of project tasks since April 1, 2026, superseding ad-hoc task tracking in meeting notes and individual notes. For the dependency map between tasks, the experimental design, and the operational benchmarking workflow, see [`../docs/execution_plan.md`](../docs/execution_plan.md).*
