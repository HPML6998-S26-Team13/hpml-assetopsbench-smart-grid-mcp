# Apr 1, 2026 | HPML Final Project - Team 13 Sync

Attendees: [Alex Xin](mailto:wax1@columbia.edu), [Akshat Bhandari](mailto:ab6174@columbia.edu), [Tanisha Rathod](mailto:tr2828@columbia.edu), [Aaron Fan](mailto:af3623@columbia.edu)

### Human notes

Good energy on the call. Everyone had done their pre-work. Akshat was especially prepared -- gave a clear walkthrough of the AssetOpsBench repo and MCP server structure that got everyone on the same page quickly. Tanisha's dataset research was thorough. Aaron confirmed compute access. Problem statement decision was fast (unanimous for A).

Key realization: no single dataset covers all four agent domains. We'll need to combine datasets and possibly synthesize linking keys. This is the first real engineering challenge.

Dhaval's latest email (same day) noted that many other teams are already in the implementation phase. We need to move fast this week.

### Summary

* **Problem Statement:** Team confirmed Problem Statement A unanimously -- extend AssetOpsBench with 30+ Smart Grid transformer scenarios, wrap four tool domains as MCP servers, and profile/optimize the LLM agent inference pipeline. Statement B (automated scenario generation) is a possible stretch goal if time permits.

* **MCP Servers / AssetOpsBench Architecture:** Akshat walked through the repo. MCP servers are standardized APIs that LLMs call to fetch data or perform actions -- wrapping existing APIs in a format any LLM can understand. AssetOpsBench has 250 industrial scenarios. Each scenario has a task type and a setting (e.g., compressor, chiller). The LLM gets a question and a set of MCP tools it can call. Tools are simple -- e.g., IoT tools just list asset IDs, list sensor names, and get readings. Our job: create equivalent tools and scenarios for power transformers.

* **Four agent domains to implement:**
    * IoT agent -- fetches sensor readings (DGA gas levels, temperature, voltage)
    * TSFM agent -- runs anomaly detection and time-series forecasting on sensor data
    * FMSR agent -- maps sensor patterns to known failure modes (e.g., high H2 + C2H2 = arcing)
    * WO agent -- creates and prioritizes work orders based on detected issues

* **Scenario format:** Existing scenarios use placeholders (entity, entity class, location, metric, event type, time range, etc.) that we adapt for our transformer domain.

* **Datasets:** Tanisha compiled five candidate datasets from Kaggle. Three CC0 (public domain), two have licensing restrictions (ODbL, author copyright) that may need IBM approval. No single dataset covers all four agent domains -- will need to combine on a common key, likely a synthesized transformer ID.
    * Power Transformers FDD & RUL (3,000 files x 420 rows, CC0) -- fault detection + remaining useful life
    * DGA Fault Classification (201 rows, CC0) -- gas analysis to fault type mapping
    * Smart Grid Fault Records (506 rows, CC0) -- fault type, maintenance status, downtime
    * See `docs/hpml_datasets.pdf` for full comparison table

* **Compute:** Aaron confirmed Insomnia cluster access. 6x H100 (2-hr session limit), ~100x A6000. Also $500 GCP credits per person. Since we're benchmarking (not training), A6000 or A100 is sufficient. Llama-3-8B fits in ~16GB. A100 40GB spot on GCP ~$1.81/hr, 80GB ~$2.50/hr.

* **Work distribution (updated):**
    * Alex -- project coordination, mid-point report, profiling analysis, report writing
    * Akshat -- scenario design, evaluation harness, agent pipeline
    * Tanisha -- MCP server implementation (all domains), dataset compilation, Overleaf
    * Aaron -- scenario design, compute plan + infrastructure, data pipeline

* **Weekly meetings:** Tuesdays 2:45 PM ET (primary). Alternative: Wednesdays ~1 PM or Thursdays. Adjusted from Wednesday to accommodate Akshat/Aaron class schedules.

### Action Items

**By Thu Apr 2:**
- [ ] Tanisha: Set up Overleaf with problem statement + proposed solution draft, share with Dhaval
- [ ] Alex: Draft mid-point PowerPoint (5-slide template) and send for team review
- [ ] Alex: Consolidate all meeting docs and clarify next steps in shared repo
- [ ] Alex: Request WatsonX API key -- join Codabench (https://www.codabench.org/competitions/10206/) and request in forum, AND fill out Google Form (https://docs.google.com/forms/d/16L0f6ozrraTqu9_gUE6etoRCUsDTEOX62sfYEy7zmE8/viewform). Hard blocker for running scenarios.
- [ ] Team: Fork AssetOpsBench, clone, run `uv sync` + unit tests to verify install

**By Sun Apr 5:**
- [ ] Akshat: Get AssetOpsBench evaluation harness running end-to-end
- [ ] Akshat: Draft first 5-10 Smart Grid transformer scenarios following existing format
- [ ] Aaron: Commit compute plan to `docs/compute_plan.md` -- GPU needs per project phase, Insomnia vs GCP recommendation
- [ ] Tanisha: Begin MCP server skeleton for at least one domain (IoT or FMSR)
- [ ] Alex: Incorporate any Dhaval feedback from Overleaf into problem statement, iterate
- [ ] Alex: Finalize mid-point PowerPoint with team input

**By Mon Apr 6:**
- [ ] Team: Mid-point PowerPoint submitted by Alex to Courseworks by Mon Apr 6 11:59pm

**By Tue Apr 7 (next meeting):**
- [ ] Akshat: Have scenario format validated against AssetOpsBench structure
- [ ] Aaron: Insomnia or GCP environment ready for first inference run
- [ ] Tanisha: IoT MCP server functional (can list assets, get sensor readings from dataset)
- [ ] Tanisha: Dataset integration -- common key linking across the CC0 datasets
- [ ] Team: WatsonX API key obtained and shared (or fallback plan identified)
