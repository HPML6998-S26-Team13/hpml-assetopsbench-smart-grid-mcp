# Changelog

## 2026-04-18

### Config / Docs

- Post-call planning audit synced the shared meeting notes, Apr 21 / Apr 28
  call planning docs, and the main execution / synopsis / orchestration docs
  to the live repo state after the Apr 16 team sync (Alex)
- Lower-churn class / mentor setup docs moved under `docs/reference/`, with
  repo-wide links updated mechanically to match the new paths (Alex)
- Documentation now reflects the active four-cell experiment grid, Hybrid as
  deferred future-work scope, and Llama-3.1-8B-Instruct as the primary local
  benchmark model with 70B reserved for selective WatsonX spot-checks (Alex)
- Added archived remediation notes under `docs/archive/` capturing the
  cross-repo review follow-up and spec companion for that cleanup stream (Alex)
- Archived the Apr 7 meeting notes and the Apr 14 reschedule-planning docs so
  live `planning/` only holds upcoming agendas / prep plus the actual Apr 16
  meeting record (Alex)

## 2026-04-13

### Code Changes

- SmartGridBench experiment runner now invokes the canonical Plan-Execute CLI
  with Smart Grid MCP server overrides, benchmark/WandB artifact
  back-references, and explicit adapter surfaces for AaT/Hybrid
  — #61, #62, #22 (partial) — M (Alex)
- Added local WatsonX/WandB runner support so benchmark runs can reuse the
  team repo `.env` plus the root project `.venv` without manual export glue
  — #61, #62 — XS (Alex)
- WO server now normalizes priority / status casing so benchmark agents can
  send title-case values like `High` while stored work orders stay canonical
  lowercase — #62 — XS (Alex)

### Config / Docs

- Added orchestration wiring notes documenting what is truly runnable now for
  `#61`, `#62`, and the repo-side portion of `#22`
  — #61, #62, #22 (partial) — S (Alex)
- Added benchmark config docs and an example env for the shared runner path
  — #61, #62 — S (Alex)
## 2026-04-11

### Code Changes

- Slurm experiment runner skeleton for batch job submission — S (Aaron)
- Scenario realism validation doc with IEEE C57.104 / IEC 60599 research
  findings; narrowed mentor questions from 5 to 3 — #60 closed — M (Alex)

### Config / Docs

- Insomnia docs updated to point at shared `team13` checkout (Aaron)
- Documented Slurm email notification pattern (Aaron)
- Shared Insomnia venv set up at `/insomnia001/depts/edu/users/team13/`
  with group permissions for all teammates (Alex)
- Known issue: `setup_insomnia.sh` torch pin still 2.7.0, needs 2.6.0
  for vLLM 0.8.5 compat — #111 filed (Alex)

## 2026-04-10

### Code Changes

- Cross-repo review remediation: scenario validation, synthetic data guards,
  MCP server safeguards, Insomnia/WatsonX script hardening — #108 closed — L (Alex)
- Scenario format validated against AssetOpsBench schema — #16 closed — S (Akshat)

### Config / Docs

- Canonical WandB metrics schema for servers, trajectories, and experiment
  cells — #14 closed — M (Alex)
- Insomnia runbook: Slurm account/partition/QoS, scratch vs $HOME, broken
  `module load cuda`, vLLM Python-version gotcha, login-node etiquette,
  foreground-debug recipe, SSH multiplexing (Aaron)
- Generalized team-facing docs away from local-machine assumptions (Alex)
- Local scenario files and harness README replayed onto org repo —
  #56, #57 closed (Akshat)

## 2026-04-09

### Code Changes

- Smart-grid scenarios and end-to-end eval harness runbook — L (Akshat)
- Black formatting pass across codebase — XS (Akshat)

### Config / Docs

- Planning docs sync, call prep, and archive cleanup (Alex)
- GitHub org created under HPML6998-S26-Team13 (Aaron)
- GitHub Project tracker created with 70+ issues across 9 workstreams;
  backfilled all completed work as closed issues #79-#106 (Alex)

## 2026-04-08

### Config / Docs

- Clarified planning model, task splits, and Phase B schedule after
  Apr 7 team sync (Alex)

## 2026-04-07

### Config / Docs

- Team repo made public; docs reorganized for external audience —
  #105 closed (Alex)
- W2 execution planning locked (Alex)
- Insomnia setup/serve/test scripts authored: `setup_insomnia.sh`,
  `vllm_serve.sh`, `test_inference.sh` — #106 closed (Aaron)

## 2026-04-06 — Mid-checkpoint

### Code Changes

- Data pipeline: `build_processed.py` joins 5 CC0 Kaggle datasets via
  shared `transformer_id` key (T-001 through T-020); outputs 6 processed
  CSVs (96k+ rows) — #98, #100, #101 closed — L (Tanisha)
- MCP server skeletons for all four domains (IoT, FMSR, TSFM, WO) on
  shared base class; FMSR `analyze_dga` implements IEC 60599 Rogers Ratio;
  TSFM includes RUL forecast + z-score anomaly detection + OLS trend;
  WO includes full CRUD — #97 closed — XL (Tanisha)
- Standalone synthetic data generator for offline dev/CI — #99 closed — S (Tanisha)
- WatsonX verification script `scripts/verify_watsonx.py`: auth, model
  listing, inference, latency benchmarks — #86 closed — M (Alex)

### Config / Docs

- Mid-point PowerPoint submitted to Courseworks — #104 closed (Alex)
- WatsonX.ai setup: credentials received from Dhaval (#83), `.env`
  configured (#84), `ibm-watsonx-ai` installed (#85), 6 Llama models
  confirmed (#87), Maverick-17B + Llama-3.3-70B latency benchmarked
  (#88), documented in `docs/reference/watsonx_access.md` (#89) (Alex)
- `ibm-watsonx-ai` added to `requirements.txt` — #90 closed (Alex)
- LaTeX data pipeline section and dataset visualization — #102, #103
  closed (Tanisha)
- Processed CSVs tracked in `data/processed/` with .gitignore exception (Tanisha)

## 2026-04-05 — Project created, previous work merged

### Code Changes

- AssetOpsBench forked and synced — #79, #95 closed — S (Alex)
- Initial repo scaffolding: README, .gitignore, Black CI, project
  reference doc, WandB link, dataset research — S (Alex)

### Config / Docs

- Meeting notes from Apr 1 team sync, roadmap with timeline and
  work distribution, team roles documented — #91, #92 closed (Alex)
- NeurIPS framing and scenario count update (Alex)
- Compute plan at `docs/compute_plan.md`: GPU needs per phase,
  Insomnia vs GCP decision framework, 4-week hardware map —
  #96 closed (Aaron)
- Overleaf set up with problem statement, shared with Dhaval —
  #81, #93, #94 closed (Tanisha, Alex)

### Prior work (pre-repo)

Team formed and project planning began in March; significant coordination
and deliverables preceded the repo creation date:

- Project proposals submitted; mentor kickoff with Dhaval Patel (Team)
- Guest lecture on AssetOpsBench by Dhaval — 467 scenarios, 4 domains,
  Agent-as-Tool vs Plan-Execute comparison
- Intro call with Dhaval and Shuxin Lin — project assignment combining
  Proposals 1+4; guidance on scope and deliverables
- Kickoff planning session — three problem statements ranked (A>B>C),
  work distribution finalized, roadmap drafted (Alex)
- First full team sync — Problem Statement A approved unanimously;
  Akshat walked through AssetOpsBench structure; Tanisha presented 5
  Kaggle dataset candidates (3 CC0); Aaron confirmed Insomnia access
  (6x H100, ~100x A6000) (Team)
- NeurIPS 2026 proposal shared with Dhaval via Overleaf (Tanisha, Alex)
- Dhaval endorses NeurIPS 2026 Datasets & Benchmarks Track submission;
  requests explicit 3-condition orchestration comparison framing and
  `transformer_id` key documentation (Dhaval)
- WatsonX API credentials received from Dhaval (Alex)
