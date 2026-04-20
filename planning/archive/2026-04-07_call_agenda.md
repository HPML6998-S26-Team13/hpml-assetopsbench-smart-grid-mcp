# Team 13 Call — April 7, 2026 (Tuesday, 2:45 PM ET)

*Weekly team sync. No mentor attending.*

## Agenda (30 min)

**0:00-0:03 — Week 1 recap (Alex)**
- Mid-checkpoint submitted Apr 6 (Courseworks + `reports/2026-04-06_midpoint_submission.pdf`)
- Team repo made **public** on GitHub (Apr 7)
- WatsonX API: received from Dhaval Apr 5, verified end-to-end, 6 Llama models available, Maverick-17B (~84 tok/s interactive) + Llama-3.3-70B-instruct (~19-34 tok/s) benchmarked (see `docs/reference/watsonx_access.md`)
- AssetOpsBench fork synced with upstream
- Dhaval email sent with Hybrid orchestration novelty check — awaiting reply

**0:03-0:15 — Status readouts (2-3 min each)**

- **Tanisha:** delivered all 4 MCP server skeletons + data pipeline + paper LaTeX sectionon Apr 6. Substantive logic landed: IEC 60599 Rogers Ratio DGA analysis (FMSR), RUL forecast + z-score anomaly + OLS trend (TSFM), work-order CRUD + downtime estimation (WO). `transformer_id` key synthesized (T-001–T-020 stratified across 4 health tiers). **What's the plan for W2 hardening, tests, and harness integration?**

- **Aaron:** compute plan committed to `docs/compute_plan.md` with phase-by-phase GPU allocation. **What's the Insomnia/vLLM environment status?** First baseline run ETA? Who writes the profiling harness wrappers (proposed: Aaron authors, Alex runs + analyzes)?

- **Akshat:** eval harness end-to-end + first 5-10 scenarios, **What's actually delivered? What's the ETA on the next 10 scenarios to hit the Apr 13 target of 15+?**

- **Alex:** WatsonX verified + benchmarked + documented, midpoint deck shipped, docs reorg (public-repo cleanup) in progress, task tracker cross-checked against actual commits.

**0:15-0:22 — Week 2 planning (Apr 7-13)**

Priority shifts based on Tanisha's early delivery:
- **MCP server hardening** (Tanisha): all 4 skeletons exist, W2 work is hardening + tests + harness integration
- **Scenario authoring** target: 15+ validated Smart Grid scenarios by Sun Apr 13 (Akshat)
- **Eval harness end-to-end** (Akshat): catching up from W1; gating dependency for everything downstream
- **First baseline agent trajectory through MCP** (Akshat + Tanisha)
- **Insomnia/vLLM environment** up + first inference run (Aaron)
- **Profiling harness scripts** — capture wrappers around PyTorch Profiler, scaffolded so W3 profiling kicks off immediately (Aaron writes capture; Alex owns analysis layer)
- **WandB instrumentation** in MCP servers + agent pipeline; metrics schema definition (Alex) — real coding work, not just project setup
- **Orchestration wiring** for AaT and PE on team's MCP servers (Alex) — preparing for the 3-way comparison in W3

**0:22-0:27 — Experimental tracks + scope claims**

Two experimental tracks underpin the paper. Alex is claiming primary ownership of both:

**Track 1 — Orchestration comparison (3 conditions on the same scenario set):**
- **Agent-as-Tool** (already in AssetOpsBench upstream) — wire to team's MCP servers, run experiments
- **Plan-Execute** (already in AssetOpsBench upstream) — same
- **Hybrid: PE + reflection checkpoints** — novel coding work, ~200-400 LOC. Asked Dhaval for novelty check Apr 6-7; awaiting reply. If green-lit, this is the project's most original contribution. If not, the comparison reduces to AaT vs PE (still substantial).
- This shifts Akshat's previously-slated "AaT vs PE comparison runs" bullet to Alex. Akshat keeps scenarios + eval harness + batched tool-call scheduling. Clean split.

**Track 2 — MCP overhead experiment (3 conditions on the same scenarios):**
- **Condition A:** ReAct + direct function calls (existing AssetOpsBench baseline) — pure tool execution + LLM inference
- **Condition B:** ReAct + MCP unoptimized — adds JSON-RPC serialization + network layer
- **Condition C:** ReAct + MCP optimized — batched parallel calls, connection reuse
- Answers the live industry debate: is MCP worth the overhead for simple industrial tool calls?
- Aaron writes the PyTorch Profiler capture wrappers; Alex owns experiment design + runs + analysis. Same infra and notebooks as Track 1.

**Lecture insight: integrate "Self-Ask" method** (~10 LOC, fixes 10% of failures per Berkeley paper) into all 3 orchestrations. Cheap, high-impact addition. (Alex, folds into orchestration ownership.)

**Lecture insight: 6-dimension LLM-as-Judge scoring** (per AssetOpsBench paper) goes into the eval harness. (Akshat, within his existing scope.)

**Lecture insight: WO agent is architecturally a coding agent** (not data lookup like IoT/FMSR/TSFM). 5-min discussion: does Tanisha's `wo_server` match the upstream pattern (code-execution-style tools) or does it need adjustment? (Tanisha, within MCP hardening scope.)

**Benchmarking is async batch jobs, not synchronous coordination.** Once W2 setup is done (vLLM up, MCP hardened, eval harness wired, WandB instrumented, Slurm template written), W3-W4 benchmark runs are: write a config file → `sbatch run_experiment.sh config.yaml` → walk away → results in WandB by next morning. Nobody needs to be online during runs. Cost-wise, ~1-2 days of free Insomnia GPU time for the full 5-cell experimental grid (5 cells × ~30 scenarios × ~5 trials each); the $4000-5000 AssetOpsBench figure is for frontier models on the full 467-scenario benchmark, not for our setup. Worth a sentence in the paper as a cost-conscious design choice.

**Experimental grid is additive, not multiplicative:** Experiment 1 = 3 MCP conditions × ReAct/AaT only. Experiment 2 = 3 orchestrations × MCP-baseline only. Shared cell: AaT × MCP-baseline. Total unique cells = 5 (4 without Hybrid). NOT 9 cells.

**Team calibration needed:** are we bought in to the 2 experimental tracks + Hybrid (conditional)?

**0:27-0:32 — Stretch scope: Problem Statement B / Future Work**

The April 2 proposal listed an automated scenario generation pipeline as Future Work — an LLM agent that consumes our Kaggle datasets and produces novel maintenance scenarios, with a Knowledge Plugin for transformer engineering standards. This maps to mentor Proposal 4 and would add a meaningful research dimension to the paper.

**Effort:** ~5 person-weeks total. Tight but feasible if loaded onto whoever has slack.

**Proposed PS B distribution (only activated if PS A is on track):**
- **Aaron** — auto-scenario generation pipeline (the LLM agent consuming Kaggle data + Knowledge Plugin → novel scenarios). ~2 weeks. Substantive engineering ownership.
- **Tanisha** — Knowledge Plugin (encode IEC 60599 + IEEE C57 transformer standards). ~1 week. Fits her domain expertise.
- **Alex** — quality evaluation methodology with circularity handling; comparative analysis hand-crafted vs auto-generated; paper section. ~1 week. Pairs with existing analysis work.
- **Akshat** — light validation of auto-generated scenarios against his hand-crafted reference set (~3 days), only if W1 has caught up. **No PS B load until W1 ships.**

**Decision approach:** Lock PS A scope today. Treat PS B as a stretch track. Hard go/no-go on Apr 14 call — green-light only if W1/W2 are on track.

**0:32-0:36 — Decisions + logistics**

- **NeurIPS 2026 — Alex has it covered.** Drafting in NeurIPS Datasets & Benchmarks Track format (more rigorous structure) starting now, back-porting to IEEE template for the class final report. Same content, two output formats — **no double work for the team**. Already in progress on Alex's side. **Alex is sole author of the paper draft;** other team members provide **content briefs** (1-page bullet lists of facts) rather than drafting prose: Tanisha → data pipeline + MCP server facts; Akshat → scenarios + eval methodology; Aaron → infrastructure setup. Alex integrates everything, writes Abstract/Intro/Conclusion, and handles the NeurIPS↔IEEE format conversion. **This frees Tanisha from her previously-slated "paper sections" load** (~3-5 days of writing she can redirect to MCP hardening or PS B Knowledge Plugin). Tanisha keeps Overleaf admin as the canonical source. Abstract due May 4, full paper May 6, class report May 4 (back-port).
- **Runbook as explicit W4 deliverable?** Proposed owners: Aaron (infra + setup steps) + Akshat (eval harness reproduction), each documenting their piece.
- **Repo is public** as of Apr 7. Pull latest before pushing any work.
- **Next call:** April 14, 2:45 PM ET

---

## Decisions needed

1. **NeurIPS 2026 commitment** — commit or defer? (Dhaval endorsed; timeline impact: final report becomes paper draft, no double work; risk: if we fall behind, class deliverables suffer first)
2. **Hybrid orchestration** — conditional commitment pending Dhaval's novelty check reply. Team buy-in for 3-way comparison if green-lit?
3. **MCP server hardening ownership** — Tanisha owns the skeletons she landed, but W2 testing + harness integration can be split. Who takes what?
4. **Runbook ownership + scope** — Aaron + Akshat joint? Who documents what? Explicit W4 deliverable or ongoing?
5. **Profiling harness authorship** — proposed: Aaron writes the wrappers (he owns infra), Alex runs + analyzes results. Confirm?
- **Team name "District 1101"** — are we locking it in? It's already on Slide 1 of the midpoint deck.

---

## Pre-work (come prepared)

- **Everyone:** pull latest from team repo; you're now on the public version. Check that `.env` is in place locally and WatsonX verification script runs (`.venv/bin/python scripts/verify_watsonx.py --list-only`).
- **Akshat:** have status on overdue Sunday tasks + W2 scenario authoring plan.
- **Tanisha:** have a brief on what's still needed to harden the MCP skeletons to production quality.
- **Aaron:** have a status on Insomnia/vLLM environment setup.
- If you're blocked on anything, surface it NOW so we can redistribute.
