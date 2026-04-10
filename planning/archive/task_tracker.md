# SmartGridBench Task Tracker

*Archived planning snapshot for the SmartGridBench project. Last updated: April 9, 2026.*
*Weeks: W1 = Mar 31-Apr 6, W2 = Apr 7-13, W3 = Apr 14-20, W4 = Apr 21-27, W5 = Apr 28-May 4, FW = May 5+.*
*Roadmap view note: In the GitHub Projects board, `Iteration` is the primary timeline field. Every task, including completed work, stays assigned to the week it was due so the roadmap remains readable historically. `Priority` uses `P0` for critical-path or deadline-driven work, `P1` for important supporting work, and `P2` for stretch/future work.*
*Current canonical task state now lives in the GitHub Project and issue bodies. This archived snapshot preserves the final repo-based planning view before task execution moved fully into GitHub. For exact task definitions, deliverables, dependencies, and coordination handoffs, see [`task_specs.md`](./task_specs.md).*

## GitHub Workstreams

These are the long-lived parent issues used in the GitHub project. They cross weekly iterations and answer "what bucket of work is this?" while `Iteration` answers "when are we doing it?"

- `#69` — `WS1 Serving, observability, and experiment plumbing`
- `#70` — `WS2 Scenarios and evaluation harness`
- `#71` — `WS3 MCP server hardening and benchmark integration`
- `#72` — `WS4 MCP overhead profiling and optimization (Experiment 1)`
- `#73` — `WS5 Orchestration comparison and failure analysis (Experiment 2)`
- `#74` — `WS6 Problem Statement B - scenario generation extension`
- `#75` — `WS7 Runbook and reproducibility`
- `#76` — `WS8 Writing and final delivery`

## Done

### W1 (Mar 31-Apr 6) — Foundations + midpoint checkpoint

- [x] #79 — Fork AssetOpsBench, clone, run `uv sync` + unit tests (Team)
- [x] #80 — Draft mid-point PowerPoint, 5-slide template (Alex)
- [x] #81 — Set up Overleaf with problem statement, share with Dhaval (Tanisha)
- [x] #82 — Request WatsonX API key via Codabench (Alex)
- [x] #83 — Receive WatsonX credentials from Dhaval — Apr 5
- [x] #84 — Set up `.env` with WatsonX credentials in team repo (gitignored) (Alex) — Apr 5
- [x] #85 — Install `ibm-watsonx-ai` into team `uv venv` at `.venv/` (Alex) — Apr 5
- [x] #86 — Write `scripts/verify_watsonx.py` — auth + model listing + inference + latency benchmark (Alex) — Apr 5
- [x] #87 — Verify 6 Llama models available on our WatsonX account (Alex) — Apr 5
- [x] #88 — Benchmark Maverick-17B and Llama-3.3-70B latency (short + long prompts) (Alex) — Apr 5
- [x] #89 — Document WatsonX access in `docs/watsonx_access.md` with setup, model list, usage patterns, latency (Alex) — Apr 5
- [x] #90 — Add `ibm-watsonx-ai` to `requirements.txt` (Alex) — Apr 5
- [x] #91 — Document team repo strategy in `docs/repo_strategy.md` (Alex) — Apr 5
- [x] #92 — Consolidate all meeting docs and clarify next steps in shared repo (Alex)
- [x] #93 — Draft NeurIPS 2026 proposal in Overleaf (Tanisha)
- [x] #94 — Send proposal + PDF to Dhaval (Alex)
- [x] #95 — Sync fork with upstream IBM/AssetOpsBench (Alex)
- [x] #96 — Compute plan committed to `docs/compute_plan.md` (Aaron) — Apr 5
- [x] #97 — MCP server skeletons for IoT, FMSR, TSFM, WO (Tanisha) — Apr 6 (commit `717e9b4`); all four domains, with substantive logic in `fmsr_server.analyze_dga` (IEC 60599 Rogers Ratio), `tsfm_server` (RUL forecast + z-score anomalies + OLS trend), `wo_server` (full work-order CRUD)
- [x] #98 — Data pipeline `data/build_processed.py` — downloads + joins 5 Kaggle datasets, synthesizes `transformer_id` key (T-001–T-020) stratified across 4 health tiers (Tanisha) — Apr 6 (commit `717e9b4`)
- [x] #99 — Standalone synthetic generator `data/generate_synthetic.py` for offline dev/CI (Tanisha) — Apr 6
- [x] #100 — Processed CSVs landed in `data/processed/` — `asset_metadata`, `dga_records`, `failure_modes`, `fault_records`, `rul_labels`, `sensor_readings` (97k+ rows total) (Tanisha) — Apr 6 (commit `9ccdb26`)
- [x] #101 — Dataset integration — common `transformer_id` key across CC0 datasets (Tanisha) — Apr 6 (subsumed by data pipeline)
- [x] #102 — `docs/data_pipeline.tex` — paper-ready LaTeX section on dataset schemas, shared-key strategy, output schemas, limitations, reproducibility (Tanisha) — Apr 6
- [x] #103 — `docs/dataset_visualization.png` — sample/smoke-test visualization confirming data pipeline output is well-formed (6 panels: H2 over time, C2H2 arcing indicator, RUL window, RUL distribution by tier, DGA gas snapshot, fault records by tier) (Tanisha) — Apr 6. **Note:** image is a static snapshot (no tracked generator script in repo). Follow-up: commit a generator notebook into `notebooks/`, or accept as static.
- [x] #104 — Submit mid-point PowerPoint to Courseworks (Alex) — Mon Apr 6 11:59pm

### W2 (Apr 7-13) — Public release cleanup

- [x] #105 — Team repo made public + docs reorganization for public release (Alex) — Apr 7
- [x] #106 — Author Insomnia setup / serve / test scripts — `scripts/setup_insomnia.sh`, `scripts/vllm_serve.sh`, `scripts/test_inference.sh` (Aaron) — Apr 7

## Milestones

- [x] M1 Proposal finalized, mid-point report submitted — Apr 6
- [x] M2 Team repo public — Apr 7
- [ ] M3 Foundation and stack ready — Apr 13
- [ ] M4 Experiment 1 completed (MCP overhead) — Apr 20
- [ ] M5 Experiment 2 + failure analysis completed — Apr 27
- [ ] M6 Problem Statement B evaluation ready — Apr 27
- [ ] M7 Final paper / report / deck ready — May 4

## In Progress

- [ ] #56 — Replay local Smart Grid scenario files onto the org repo `main` branch and push first batch (Akshat)
- [ ] #57 — Replay local benchmark / harness README work onto the org repo `main` branch and push (Akshat)
- [ ] #3 — Run one existing benchmark scenario end-to-end on the canonical stack (Akshat)
- [ ] #4 — Draft first 5-10 Smart Grid transformer scenarios and commit them to the canonical repo (Akshat)
- [ ] #6 — Successful first Insomnia A6000 vLLM serve smoke test for Llama-3.1-8B-Instruct (Aaron)
- [ ] #58 — Validate all four MCP servers with the benchmark Llama path, not only Claude Desktop (Tanisha)
- [ ] #5 — NeurIPS 2026 paper — draft in NeurIPS format first, then back-port to IEEE final report (Alex)

## Backlog

### W2 (Apr 7-13) — Foundation + MCP servers + scenarios

**Foundation (Tier 1 — must complete to unblock everything else):**

- [ ] #8 — Generic Slurm experiment template for benchmark jobs (Aaron)
- [ ] #7 — Profiling capture wrappers — PyTorch Profiler around benchmark runs (Aaron)
- [ ] #59 — Profiling capture wrappers — Nsight / `nvidia-smi` / GPU utilization collection (Aaron)
- [ ] #9 — Complete IoT MCP server hardening + tests + harness contract (Tanisha)
- [ ] #10 — Complete TSFM MCP server hardening + tests + harness contract (Tanisha)
- [ ] #11 — Complete FMSR MCP server hardening + tests + harness contract (Tanisha)
- [ ] #12 — Complete WO MCP server hardening + tests + harness contract (Tanisha)
- [ ] #13 — WO server architecture review against Dhaval's “WO agent is a coding agent” guidance (Tanisha)
- [ ] #15 — Reach 15+ validated Smart Grid scenarios in the canonical repo (Akshat)
- [ ] #16 — Validate Smart Grid scenario format against AssetOpsBench schema and conventions (Akshat)
- [ ] #60 — Real-world scenario validation plan (Akshat)
- [ ] #17 — 6-dimension LLM-as-Judge scoring in eval harness (Akshat)
- [ ] #18 — First Smart Grid scenario runs end-to-end through MCP with trajectory artifact captured (Akshat)
- [ ] #20 — First judge-scored trajectory lands with logs / artifacts using Maverick-17B (Akshat)
- [ ] #14 — WandB metrics schema definition for servers, trajectories, and experiment cells (Alex)
- [ ] #61 — WandB instrumentation in MCP servers and agent pipeline (Alex)
- [ ] #22 — Wire Agent-as-Tool orchestration to the team's MCP servers (Alex)
- [ ] #62 — Wire Plan-Execute orchestration to the team's MCP servers (Alex)
- [ ] #63 — Follow up with Dhaval on hybrid orchestration novelty and Smart Grid scenario realism / validation criteria (Alex)
- [ ] #19 — Each team member sync the org repo `main` branch, install `ibm-watsonx-ai` into `.venv`, and run the verify script locally (Team)
- [ ] #21 — Set up WandB project with initial experiment logs (Team)

### W3 (Apr 14-20) — Baseline profiling + experimental design

- [ ] #23 — Hybrid orchestration prototype implementation (Alex)
- [ ] #24 — Self-Ask integration (~10 LOC) in all 3 orchestrations (Alex)
- [ ] #25 — Run Experiment 1 profiling captures (Direct vs MCP-baseline vs MCP-optimized) and publish raw artifacts for analysis (Aaron)
- [ ] #26 — Notebook 02: latency analysis — MCP overhead experiment design, parsing, and writeup (Alex)
- [ ] #27 — Integrate WandB logging into profiling pipeline (Aaron)
- [ ] #28 — First WandB experiment logs live (Team)
- [ ] #37 — Runbook section: infrastructure / serving / Slurm / profiling setup (`docs/runbook.md`) (Aaron)
- [ ] #50 — Knowledge Plugin: encode IEC 60599 + IEEE C57 transformer engineering standards as a structured knowledge document the scenario-gen LLM can consume (Tanisha)
- [ ] #2 — Auto-scenario generation prototype — first generated Smart Grid scenario batch from Kaggle data + Knowledge Plugin (Aaron)
- [ ] #51 — Quality evaluation methodology: LLM-as-Judge against hand-crafted reference set, with circularity handling (Alex)
- [ ] #77 — NeurIPS abstract outline + title candidates (Alex)

### W4 (Apr 21-27) — Optimizations + orchestration comparison

- [ ] #29 — Apply INT8 quantization via vLLM (Aaron)
- [ ] #30 — KV-cache tuning experiments (Aaron)
- [ ] #31 — Batched tool-call scheduling implementation (Akshat)
- [ ] #32 — Run Experiment 2 (Orchestration comparison): 3 orchestrations × N multi-domain scenarios on MCP-baseline (Alex)
- [ ] #33 — Reach 30+ scenarios (Akshat)
- [ ] #34 — Notebook 03: orchestration comparison (Alex)
- [ ] #35 — Failure taxonomy classification + evidence table (Alex)
- [ ] #64 — Failure taxonomy visuals + mitigation plan (Alex)
- [ ] #65 — Implement chosen mitigation(s) from failure taxonomy analysis (Alex)
- [ ] #66 — Re-run affected benchmark cells after mitigation and compare before/after (Alex)
- [ ] #36 — Collect before/after profiling data across all metrics (Alex)
- [ ] #67 — Runbook section: eval harness / scenario execution / judge reproduction (`docs/runbook.md`) (Akshat)
- [ ] #38 — GCP fallback setup instructions — how to spin up A100 instance if Insomnia is down (Aaron)
- [ ] #68 — Auto-scenario generation scale-up — refine pipeline and expand generated scenario set (Aaron)
- [ ] #53 — Validate auto-generated scenarios against hand-crafted reference set (Akshat)
- [ ] #52 — Comparative analysis: hand-crafted vs auto-generated scenarios on agent performance, in notebook 04 (Alex)
- [ ] #55 — Reach 50+ scenarios total in canonical repo (manual + auto-generated) (Akshat)

### W5 (Apr 28-May 3) — Report + presentation

- [ ] #39 — NeurIPS draft — Datasets & Benchmarks Track format (Alex)
- [ ] #78 — Class report back-port checklist from NeurIPS draft to IEEE template (Alex)
- [ ] #40 — Class final report — back-ported from NeurIPS draft to IEEE template (Alex)
- [ ] #41 — Content brief: Methodology + Data + MCP server facts, 1-page bullet list (Tanisha)
- [ ] #42 — Content brief: Scenarios + Eval + judge facts, 1-page bullet list (Akshat)
- [ ] #43 — Content brief: Infrastructure + Profiling + serving facts, 1-page bullet list (Aaron)
- [ ] #44 — Final presentation deck (Alex)
- [ ] #45 — WandB dashboard polish (Team)
- [ ] #46 — Open-source PR to AssetOpsBench (Team)
- [ ] #47 — NeurIPS 2026 abstract (Alex)
- [ ] #48 — NeurIPS 2026 full paper submission (Alex)
- [ ] #49 — Runbook final review — verify all experiments are reproducible from doc (Team)
- [ ] #54 — Paper section on Problem Statement B methodology + circularity discussion (Alex)

## Blocked

*(nothing currently blocked)*

## Notes

- NeurIPS 2026 Datasets & Benchmarks Track: abstract May 4, submission May 6
- Final deadline: May 4 (presentation + report + code)
- Weekly meetings: Tuesdays 2:45 PM ET
- AssetOpsBench has 467 scenarios across 6 HuggingFace subsets (152 original + 315 newer); our contribution is the 7th asset domain (Smart Grid transformers)
- Problem Statement B / scenario-generation work is activated and scheduled across W3-W5, not parked as stretch.
- Two experimental tracks: Experiment 1 (MCP overhead, 3 conditions) and Experiment 2 (Orchestration comparison, 3 orchestrations on MCP-baseline). 5 unique cells total. See [`../../docs/execution_plan.md`](../../docs/execution_plan.md) for the full operational plan with task dependency map and benchmarking workflow.

---

*This archive preserves the final repo-based task snapshot before execution tracking moved fully into GitHub Projects. For the dependency map between tasks, the experimental design, and the operational benchmarking workflow, see [`../../docs/execution_plan.md`](../../docs/execution_plan.md).*
