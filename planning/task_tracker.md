# SmartGridBench Task Tracker

*Canonical task tracker for the SmartGridBench project. Last updated: April 7, 2026.*
*Weeks: W2 = Apr 7-13, W3 = Apr 14-20, W4 = Apr 21-27, W5 = Apr 28-May 3.*

## Done

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
- [x] Team repo made public + docs reorganization for public release (Alex) — Apr 7

## In Progress

- [ ] Get AssetOpsBench evaluation harness running end-to-end (Akshat) — was due Sun Apr 5
- [ ] Draft first 5-10 Smart Grid transformer scenarios (Akshat) — was due Sun Apr 5
- [ ] **NeurIPS 2026 paper.** Drafting in NeurIPS Datasets & Benchmarks Track format, then back-porting to IEEE template for the class final report. Same content, two output formats — no double work. Abstract due May 4, full paper due May 6. Class report due May 4 (back-ported). Started Apr 7.

## Backlog

### W2 (Apr 7-13) — Foundation + MCP servers + scenarios

**Foundation (Tier 1 — must complete to unblock everything else):**

- [ ] Insomnia/vLLM environment up + Llama-3.1-8B-Instruct serving (Aaron)
- [ ] Profiling harness scripts — PyTorch Profiler + Nsight wrappers (Aaron)
- [ ] Slurm batch script template (Aaron)
- [ ] Complete IoT MCP server hardening + tests + harness integration (Tanisha) — skeleton exists with list_assets, get_asset_metadata, list_sensors, get_sensor_readings
- [ ] Complete TSFM MCP server hardening + tests (Tanisha) — skeleton exists with get_rul, forecast_rul, detect_anomalies, trend_analysis
- [ ] Complete FMSR MCP server hardening + tests (Tanisha) — skeleton exists with list/search failure modes, get_sensor_correlation, get_dga_record, analyze_dga (Rogers Ratio)
- [ ] Complete WO MCP server hardening + tests (Tanisha) — skeleton exists with fault records + work-order CRUD + estimate_downtime
- [ ] Investigate WO server architectural pattern (Tanisha, lecture insight) — should `wo_server` expose code-execution-style tools rather than CRUD-style? Per Dhaval's lecture, the upstream WO agent is architecturally a coding agent.
- [ ] WandB instrumentation in MCP servers + agent pipeline; metrics schema definition (Alex)
- [ ] Reach 15+ validated Smart Grid scenarios (Akshat)
- [ ] Validate scenario format against AssetOpsBench structure (Akshat)
- [ ] 6-dimension LLM-as-Judge scoring in eval harness (Akshat, lecture insight) — implement the 6 scoring dimensions from the AssetOpsBench paper
- [ ] First baseline agent trajectory through MCP — the integration moment (Akshat + Tanisha + Alex)
- [ ] Team members pull latest, install `ibm-watsonx-ai` into their `.venv`, run verify script (Team)
- [ ] First end-to-end judge call using Maverick-17B on a real agent trajectory (Akshat)
- [ ] Set up WandB project with initial experiment logs (Team)

### W3 (Apr 14-20) — Baseline profiling + experimental design

- [ ] Wire Agent-as-Tool + Plan-Execute orchestrations to team's MCP servers (Alex)
- [ ] Hybrid orchestration prototype implementation (Alex) — conditional on mentor novelty check reply
- [ ] Self-Ask integration (~10 LOC) in all 3 orchestrations (Alex, lecture insight) — addresses "Fail to Ask for Clarification" failures per Berkeley failure paper
- [ ] Run Experiment 1 (MCP overhead): 3 conditions × N scenarios — Aaron writes profiling capture, Alex owns experiment design + analysis
  - [ ] Direct Python calls (existing AssetOpsBench)
  - [ ] MCP baseline (our servers, unoptimized)
  - [ ] MCP optimized (after tuning)
- [ ] Notebook 02: latency analysis — MCP overhead cost breakdown (Alex)
- [ ] Integrate WandB logging into profiling pipeline (Aaron + Alex)
- [ ] First WandB experiment logs live (Team)

### W4 (Apr 21-27) — Optimizations + orchestration comparison

- [ ] Apply INT8 quantization via vLLM (Aaron)
- [ ] KV-cache tuning experiments (Aaron)
- [ ] Batched tool-call scheduling implementation (Akshat)
- [ ] Run Experiment 2 (Orchestration comparison): 3 orchestrations × N multi-domain scenarios on MCP-baseline — AaT vs PE vs Hybrid (Alex)
- [ ] Reach 30+ scenarios (Akshat + Team)
- [ ] Notebook 03: orchestration comparison (Alex)
- [ ] Failure mode taxonomy analysis (Alex, lecture insight) — apply Berkeley failure paper categories (Specification / Inter-Agent / Task Verification) to our experiment results
- [ ] Collect before/after profiling data across all metrics (Alex)
- [ ] Runbook: consolidate all setup + experiment reproduction steps into `docs/runbook.md` (Aaron + Akshat)
- [ ] GCP fallback setup instructions — how to spin up A100 instance if Insomnia is down (Aaron)

### W5 (Apr 28-May 3) — Report + presentation

- [ ] NeurIPS draft — Alex sole author, drafting in Datasets & Benchmarks Track format
- [ ] Class final report — back-ported from NeurIPS draft to IEEE template (Alex)
- [ ] Content brief: Methodology + Data section facts, 1-page bullet list (Tanisha → Alex)
- [ ] Content brief: Scenarios + Eval section facts (Akshat → Alex)
- [ ] Content brief: Infrastructure + Profiling section facts (Aaron → Alex)
- [ ] Final presentation deck (Alex)
- [ ] WandB dashboard polish (Team)
- [ ] Open-source PR to AssetOpsBench (Team)
- [ ] NeurIPS 2026 abstract (Alex) — due May 4
- [ ] NeurIPS 2026 full paper submission (Alex primary, Team support?) — due May 6
- [ ] Runbook final review — verify all experiments are reproducible from doc (Team)

## Stretch — Problem Statement B / Future Work

Conditional on Apr 14 go/no-go: activated only if Tier 1 W2 work is on track.

- [ ] Auto-scenario generation pipeline — LLM agent consuming Kaggle data + Knowledge Plugin → novel scenarios (Aaron) — ~2 weeks. Substantive engineering ownership.
- [ ] Knowledge Plugin: encode IEC 60599 + IEEE C57 transformer engineering standards as a structured knowledge document the scenario-gen LLM can consume (Tanisha) — ~1 week
- [ ] Quality evaluation methodology: LLM-as-Judge against hand-crafted reference set, with circularity handling (Alex) — ~3-4 days
- [ ] Comparative analysis: hand-crafted vs auto-generated scenarios on agent performance, in notebook 04 (Alex)
- [ ] Validate auto-generated scenarios against hand-crafted reference set (Akshat) — light pickup, only if W2 has caught up
- [ ] Paper section on PS B methodology + circularity discussion (Alex)
- [ ] Reach 50+ scenarios total (manual + auto-generated)

## Blocked

*(nothing currently blocked)*

## Notes

- NeurIPS 2026 Datasets & Benchmarks Track: abstract May 4, submission May 6
- Final deadline: May 4 (presentation + report + code)
- Weekly meetings: Tuesdays 2:45 PM ET
- AssetOpsBench has 467 scenarios across 6 HuggingFace subsets (152 original + 315 newer); our contribution is the 7th asset domain (Smart Grid transformers)
- Two experimental tracks: Experiment 1 (MCP overhead, 3 conditions) and Experiment 2 (Orchestration comparison, 3 orchestrations on MCP-baseline). 5 unique cells total. See [`../docs/execution_plan.md`](../docs/execution_plan.md) for the full operational plan with task dependency map and benchmarking workflow.

---

*This task tracker has been the canonical record of project tasks since April 1, 2026, superseding ad-hoc task tracking in meeting notes and individual notes. For the dependency map between tasks, the experimental design, and the operational benchmarking workflow, see [`../docs/execution_plan.md`](../docs/execution_plan.md).*
