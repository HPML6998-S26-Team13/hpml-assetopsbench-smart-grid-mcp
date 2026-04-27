# Changelog

## 2026-04-27

### Tooling

- Added a repo-level PR review watcher (`scripts/pr_review_watcher.sh`)
  that filters open PRs in
  `HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp` to those that
  need a fresh cross-agent review (unmerged, not draft, not approved, no
  LGTM, unclaimed) and emits each candidate as a JSON line. The script
  writes a per-PR request packet using the existing cross-agent review
  filename convention so the same runner does not double-claim across
  iterations. Author hints come from shift coordination notes under
  `docs/coordination/`, and the embedded review prompt asks for
  heightened scrutiny when the PR appears to be authored by the same
  runner kind as the reviewer, or when authorship is unclear. The
  reproducible workflow is documented in `docs/pr_review_watcher.md`.
  Resolves the watcher backlog item pinned in `fdaf248`.

## 2026-04-25

### Runtime / Config

- Tightened the PR `#127` AaT cleanup findings after review: Cell A direct
  tools now fail fast on bare-name collisions and expose non-strict schemas
  matching the MCP required-parameter surface; Cell B MCP launch mode now
  fails fast when `python` mode lacks `AAT_MCP_SERVER_PYTHON`; the MCP
  bootstrap no longer assumes a fixed directory depth; summary aggregation
  scans only per-trial JSON outputs; and the upstream parity wrapper now fails
  earlier on missing Smart Grid server paths, preserves max-turn exhaustion in
  its serialized result, and avoids shadowing a real `claude_agent_sdk`
  install (Alex)
- Added first-class Agent-as-Tool dispatch to `scripts/run_experiment.sh` so
  Cell A/B configs no longer need an explicit `AAT_RUNNER_TEMPLATE` for the
  standard team-local runner. Added a separate upstream
  `OpenAIAgentRunner` parity smoke config/wrapper that uses the AOB Python API
  with Smart Grid MCP server paths, since the upstream CLI has no server-path
  override. The parity wrapper keeps AOB's agent loop but patches its MCP
  server factory onto the same warmed Smart Grid server launch/timeout envelope
  used by the benchmark Cell B smoke, so the parity run measures runner
  behavior rather than missing server dependencies or cold `uv` startup. The
  upstream parity path is smoke-proven on Insomnia by Slurm jobs `8970383`
  (`1 / 1` success, Slurm elapsed `00:11:18`, 4 MCP tool calls) and `8970468`
  (`1 / 1` repeat success, Slurm elapsed `00:09:05`, 4 MCP tool calls).
  Removed the stale Apr 21 meeting-notes backlog item that was already handled
  elsewhere (Alex)
- Hardened the AaT smoke path so stale Insomnia virtualenvs fail fast before
  launching vLLM: `run_experiment.sh` now preflights the pinned AaT dependency
  set, and the Cell A/B AaT configs run `scripts/aat_runner.py` through the
  same explicit `uv --with` dependency pins. The local-vLLM AaT configs also
  enable vLLM auto tool choice with the Llama 3 JSON tool-call parser so the
  Agents SDK's `tool_choice=auto` requests are accepted, and summary generation
  now counts AaT `tool_call_count` / nested `history[*].tool_calls` records
  instead of reporting zero tool calls for successful AaT trials. The Cell B
  MCP path now launches server subprocesses with their data dependencies and
  preflights those imports before vLLM startup, preferring the shared Insomnia
  server Python so MCP initialization is not blocked by per-server dependency
  downloads; its SDK initialize deadline is now configurable and defaults to
  30s for the smoke/configured Cell B path. Cell B MCP server launch now uses
  an explicit bootstrap wrapper with stderr startup milestones and can force
  the same `uv --with` dependency envelope used by local parity tests, so
  initialize hangs identify which server startup stage went silent; the
  Insomnia Cell B configs launch servers from the warmed `.venv-insomnia`
  Python with a longer initialize budget to avoid rebuilding server envs inside
  the MCP connection timeout, and the AaT runner now defaults
  `parallel_tool_calls` to false so local vLLM Llama 3 accepts the sequential
  tool-call loop after MCP execution begins (Alex)

## 2026-04-24

### Config / Docs

- Ported the Apr 21 Team 13 meeting notes from the local reconciliation branch
  onto `main`, preserving the Notion / Google Meet source record and updating
  the Apr 28 agenda / prep docs so they point at the meeting record while
  reflecting the newer `#111` closeout and `#104` runner landing (Alex)
- Clarified the coordination-doc retention rule: `docs/coordination/live_repo_summary.md`
  now has a configurable emphasis window rather than a hard 48-hour eviction
  policy, and stale material moves to `docs/coordination/repo_summary_history.md`
  only when newer active work has displaced it from the live memo (Alex)
- Added a compaction rule to `docs/coordination/shift_coordination_note_template.md`
  so per-agent shift notes stay short working buffers rather than growing into
  local transcripts; settled details should be promoted to the live summary,
  summarized into history only when otherwise unrecoverable, or left to the
  durable artifact that already records them (Alex)
- Clarified the Agent-as-Tool runner design in `docs/orchestration_wiring.md`:
  the team runner at `scripts/aat_runner.py` will wrap the OpenAI Agents SDK
  (`agents.Runner.run()`) directly rather than AOB's `OpenAIAgentRunner`, so
  Cell A (direct) and Cell B (MCP) share the same runner code and `(B - A)` in
  Experiment 1 measures MCP transport overhead by construction. #104 now tracks
  Cell A, Cell B, and a parity smoke against upstream's `openai-agent` CLI
  (Alex)
- Standardized the local Llama-3.1-8B-Instruct `MODEL_REVISION` at
  `0e9e39f249a16976918f6564b8830bc894c89659` in
  `docs/governance/model_registry.yaml`, made `scripts/setup_insomnia.sh`
  default to that resolved checkpoint SHA, and updated the runbooks so future
  Insomnia / fallback setup runs record the same model contract (Alex)

## 2026-04-22

### Config / Docs

- Added `docs/experiment_matrix.md` to pin down the honest core benchmark grid,
  trial policy, Self-Ask tracking, and the recommended order for optional
  follow-on conditions such as `Y + Self-Ask + MCP optimized` and
  `Z + Self-Ask + MCP optimized`, so the experiment story stays identifiable
  instead of drifting into an uncontrolled matrix; the docs now distinguish
  smoke-proven runner paths from canonical config / raw-artifact readiness
  (Alex)
- Tightened the shared planning docs around `#26` / `#32` / `#34`: the
  execution plan and Experiment 1 capture plan now make the staged analysis
  story explicit, including the role of the first real shared Cell B artifact
  as an Experiment 1 / 2 milestone rather than treating the notebook lane as
  purely all-or-nothing (Alex)
- Notebook 02 now turns the shared Cell B milestone into a real contract check
  instead of a prose note: when the first AaT Cell B artifact lands, it will
  verify the dual-use `contributing_experiments` metadata, canonical
  scenario-ID propagation, filename-aligned `trial_index` values, and
  `latencies.jsonl` join-key shape, then export
  `results/metrics/notebook02_cell_b_contract.preflight.csv` alongside the
  availability snapshot. Notebook 02 also runs in a partial-readiness mode
  whenever any subset of cells is present: the per-scenario summary, MCP
  overhead pairwise deltas, and latency figure now publish whatever pair is
  available (Cell A + Cell B today; Cell C overlay automatic when it lands)
  (Alex) (#26)

## 2026-04-21

### Config / Docs

- Renamed the short handoff format to `docs/coordination/shift_coordination_note_template.md`,
  moved the coordination surfaces under `docs/coordination/`, and made the
  purpose explicit: short coordination delta for either concurrent work or
  handoff, separate from `docs/coordination/live_repo_summary.md` and
  `docs/coordination/repo_summary_history.md` (Alex)
- Added an explicit teammate-facing AOB dependency note to
  `docs/orchestration_wiring.md`: PE-family runners and the upcoming AaT runner
  depend on a sibling AssetOpsBench checkout at `AOB_PATH`, and the real AaT
  gap is the missing `--server NAME=PATH` override in upstream CLIs rather than
  the absence of an upstream runner (Alex)
- Corrected the Agent-as-Tool status section in `docs/orchestration_wiring.md`:
  upstream AssetOpsBench does expose first-class AaT CLIs (`claude-agent`,
  `openai-agent`) — the real plumbing gap is that neither CLI supports
  `--server NAME=PATH` overrides, so the team repo needs a thin wrapper around
  the `OpenAIAgentRunner` Python API to point at the Smart Grid MCP servers.
  That wiring work is now tracked under the repurposed `#104` (Alex)
- Fold former `#104` ("Submit the mid-point PowerPoint to Courseworks") into
  `#80`, freeing `#104` as the AaT wiring issue. `planning/archive/task_tracker.md`
  and the earlier mid-point entry in this changelog now point at `#80` (Alex)
- Clarified the execution sequencing for Experiment 1 / 2: Cell C is now
  documented as the chosen optimized MCP bundle rather than a separate full
  optimization matrix, `#29/#30/#31` are explicitly framed as what makes Cell C
  real, Notebook 02 is documented as phased (preflight → early best-effort
  analysis → final rerun on the larger corpus), and older blocker language is
  now called out as mostly referring to final canonical evidence rather than
  first execution (Alex)
- Added a repo-wide documentation discoverability pass: new `scripts/README.md`
  index, stronger root/docs cross-links into the local README surfaces, explicit
  scenario-validator guidance in `data/README.md` and `data/scenarios/README.md`,
  repaired broken relative links in local indexes / archived planning notes, and
  aligned `docs/runbook.md` with `profiling/README.md` so profiling wrappers are
  documented as compute-node-only instead of wrapping `sbatch` from the submit
  host (Alex)
- Refreshed the live planning and handoff surfaces after the Apr 20-21 merge
  wave: `docs/coordination/live_repo_summary.md`, `docs/execution_plan.md`,
  `docs/project_synopsis.md`, and the Apr 21 / Apr 28 call prep + agenda docs
  now reflect that `#113`, `#114`, `#115`, `#119`, and `#120` are merged,
  that `#111` is down to a final proof-run closeout, and that `#25` plus the
  still-missing execution artifacts are now the real gating work rather than
  old PR-status uncertainty (Alex)
- Split the repo handoff layer into a current-state
  `docs/coordination/live_repo_summary.md` and a historical
  `docs/coordination/repo_summary_history.md`, so stale review commentary and
  older milestone transitions can be archived without making the live summary
  unreadable (Alex)
- Updated the canonical Insomnia docs to the current post-merge 3.11 /
  `vllm==0.19.0` reality: login-node checks are now metadata-only, real
  `import vllm` verification is explicitly compute-node-only, and the
  troubleshooting path for empty vLLM logs now points at current failure modes
  rather than the older 3.9 / `vllm==0.8.5` silent-import story (Alex)

- Applied Codex Pass 2 review findings on the `#26/#32` notebooks
  (2 Mediums / 2 Lows, 0 Critical/High): Notebook 02's `_latest_run_dir` now
  parses `meta.json.started_at` into a timezone-aware `datetime`
  (normalizing `Z` to `+00:00`) before comparing, so runs that mix `Z` and
  `-04:00` offsets sort chronologically; Notebook 02's MCP overhead cell
  detects duplicate `(cell, scenario_file, trial_index)` rows and refuses to
  produce a misleading overhead CSV when `pivot_table(aggfunc="first")`
  would silently collapse them; Notebook 03's readiness-gate note now cites
  the authoritative Slurm job IDs from `docs/validation_log.md`
  (`8851966` as the earlier entry, `8857843` as the clean `2/2` snapshot)
  rather than the intermediate re-run IDs; Notebook 03's `load_judge_scores`
  uses fillna-style coalescing instead of guarded rename so a JSONL
  containing mixed pre- and post-normalization rows produces a single
  complete `cell` / `judge_score` / `judge_pass` column set (Alex)
- Applied Codex Pass 1 review findings on the `#26/#32` notebooks
  (3 Highs / 2 Mediums / 1 Low): Notebook 02 MCP overhead now pairs on
  `(scenario_file, trial_index)` before computing B−A / B−C / C−A deltas
  instead of subtracting whole-cell medians; Notebook 03 judge-score loader
  normalizes the `#113` schema (`experiment_cell` → `cell`, `score_6d` →
  `judge_score`, `pass` → `judge_pass`) so the join actually fires when
  `scenario_scores.jsonl` lands; Notebook 03 per-step failure counter is
  now one-count-per-step under the normalized-runner contract instead of
  double-counting `success=False` plus `response.error`; legacy
  pre-normalization scenario artifacts with null `success` / missing
  `scenario.id` are preserved as NaN and excluded from the aggregation
  rather than coerced to `False`; latest-run selection now uses
  `meta.json.started_at` with an mtime fallback instead of lexicographic
  sort on run IDs; `recovery_rate` is NaN for zero-failure cells (Alex)

## 2026-04-20

### Config / Docs

- Promoted `#23` and `#24` from vague backlog wording into active Verified PE / Self-Ask work items, with repo-local runner wiring, example configs, and current planning/docs updated to match that narrower implementation reality (Alex)
- Added explicit runtime preflight + dependency documentation for the repo-local
  Self-Ask PE / Verified PE runners, and committed a small `tmux` watch helper
  so Insomnia proof runs fail fast when the shared env is missing the AOB
  client stack (`litellm`, `mcp[cli]`) (Alex)
- Tightened runner success accounting so top-level scenario `success` now
  propagates detected tool failures from JSON `{"error": ...}` payloads and
  plain-string transport/tool errors instead of trusting the executor's raw
  success bit alone (Alex)
- Reconciled the shared Insomnia dependency overlay and runbook to the actual
  Python 3.11 / `vllm==0.19.0` path now present in the team env, with matching
  `torch`, `transformers`, and `huggingface-hub` pins and no separate cuDNN
  hard pin (Alex)
- Fixed the local vLLM model-name contract for Insomnia runs by explicitly
  serving `Llama-3.1-8B-Instruct`, validating `/v1/models` before the benchmark
  loop, and aligning the smoke/test scripts with that served model ID (Alex)
- Added `docs/governance/model_registry.yaml` as the canonical repo-side record
  for local-vLLM and WatsonX model names, runtime pins, and the current
  non-standardized `MODEL_REVISION` gap, with docs/setup references updated to
  point at it (Alex)
- Added `docs/slurm_cheatsheet.md` — command-first Slurm reference covering
  submit, watch, estimate start, inspect failures, historical timing, and
  cancellation workflows for Insomnia jobs. Linked from `docs/README.md` and
  `docs/insomnia_runbook.md` See-Also section.
- Added `notebooks/01_data_exploration.ipynb` as the reproducible replacement
  for the earlier static dataset smoke-test image, with notebook-generated
  summary CSVs and overview figures under `results/` (Alex)
- Added Experiment 1 / Experiment 2 benchmark scaffolding for `#26` and `#32`:
  explicit Cell A / B / C / Z benchmark directories, experiment-specific config
  templates, and a real Notebook 02 parser/preflight scaffold for future MCP
  overhead analysis (Alex)
- Tightened `notebooks/02_latency_analysis.ipynb` to key off the `summary.json`
  schema now shipped by `scripts/run_experiment.sh` (latency p50/p95, tool-error
  counts, MCP latency, tool call counts) and the `meta.json` profiling fields
  added by `#27` / `01043c5`; adds MCP overhead decomposition (B−A, B−C, C−A)
  at both p50 and p95 with a p50-bar / p95-cap figure (Alex)
- Added `notebooks/03_orchestration_comparison.ipynb` scaffold for Experiment 2
  across Cells B / Y / Z; reads per-scenario `success` / `failed_steps` /
  `history` / `answer` from the PE-Self-Ask and Verified-PE runner outputs,
  computes success rate / mean failed steps / mean history length / recovery
  rate per orchestration, and leaves a hook to join `scenario_scores.jsonl`
  judge scores (per `#17`) once they land (Alex)
- Split dependency guidance into a portable base `requirements.txt`, a
  cluster-serving `requirements-insomnia.txt`, and a notebook-authoring
  `requirements-notebooks.txt`, with setup docs/scripts updated to use `uv`
  consistently (Alex)
- Merged the PS B / abstract-planning docs forward onto the current shared
  `main` line and tightened the abstract scaffold to a seven-sentence default
  so the benchmark artifact, systems comparison, and reproducibility story all
  fit cleanly (follow-up to review feedback) (Alex)
## 2026-04-19

### Config / Docs

- Reframed the optional `#23` third-orchestration follow-on in local planning
  docs from a generic "PE + reflection checkpoints" hybrid toward a
  verifier-gated Plan-Execute / `Plan-Execute-Verify-Replan` design, while
  keeping AaT vs PE as the core committed comparison (Alex)
- Reset the live project board's stale overdue targets on Apr 20, hard-dating
  the remaining W2 carryover to Apr 20-21, pushing selected spillover W3 items
  into W4 explicitly, and syncing the shared planning docs to the new dates
  (Alex)
- Added the repo-local `Manually auto-approve PR` workflow from
  `ai-coding-agents` so future PR review flows can trigger the shared
  auto-approval path directly from GitHub Actions (Alex)

## 2026-04-18

### Config / Docs

- Post-call planning audit synced the shared meeting notes, Apr 21 / Apr 28
  call planning docs, and the main execution / synopsis / orchestration docs
  to the live repo state after the Apr 16 team sync (Alex)
- Lower-churn class / mentor setup docs moved under `docs/reference/`, with
  repo-wide links updated mechanically to match the new paths (Alex)
- Documentation now reflects the active four-cell experiment grid, Cell Z /
  Verified PE as deferred future-work scope, and Llama-3.1-8B-Instruct as the primary local
  benchmark model with 70B reserved for selective WatsonX spot-checks (Alex)
- Added archived remediation notes under `docs/archive/` capturing the
  cross-repo review follow-up and spec companion for that cleanup stream (Alex)
- Archived the Apr 7 meeting notes and the Apr 14 reschedule-planning docs so
  live `planning/` only holds upcoming agendas / prep plus the actual Apr 16
  meeting record (Alex)

## 2026-04-16

### Config / Docs

- Added PS B scenario-evaluation methodology with explicit circularity,
  duplication, and acceptance criteria for generated-vs-hand-crafted scenario
  validation — addresses #51 — M (Alex)
- Added NeurIPS abstract-planning doc with title candidates, evidence
  structure, and a reusable abstract skeleton — addresses #77 — S (Alex)

## 2026-04-13

### Code Changes

- SmartGridBench experiment runner now invokes the canonical Plan-Execute CLI
  with Smart Grid MCP server overrides, benchmark/WandB artifact
  back-references, and explicit adapter surfaces for AaT / the legacy Cell Z
  `hybrid` hook
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

- Mid-point PowerPoint drafted and submitted to Courseworks — #80 closed (Alex)
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
