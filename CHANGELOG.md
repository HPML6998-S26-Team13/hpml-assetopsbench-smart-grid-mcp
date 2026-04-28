# Changelog

## 2026-04-28

### Added

- `data/scenarios/validate_realism_statistical.py` — Layer 3 statistical-fidelity
  validator. Compares synthetic DGA gas distributions and fault-class proportions
  against published real-world DGA data (or against the IEC TC 10 reference
  prevalence when no real dataset is loaded). Six-test battery: KS, Anderson-
  Darling, Wasserstein/EMD per gas; chi-squared on fault prevalence; conditional
  KS per fault class; correlation-matrix delta. Markdown + JSON report card; non-
  zero exit when any test fails. Adds `scipy` to `requirements.txt`.
- `docs/dga_realism_statistical_validation.md` — working spec covering IEC 60599
  (publication 66491) ingestion status, ranked real-DGA datasets (IEEE DataPort,
  IEC TC 10 via Duval & dePablo 2001, Kaggle backstop), test rationale, TC 10
  reference prevalence, acceptance thresholds, pre-May 4 plan, and PR #147 plug-in
  point. Plugs L3 into the existing 6-criteria PS B rubric (`#51`).
- `reports/realism_statistical_v0.md` — baseline run on the current 20-row
  `data/processed/dga_records.csv`. Empirical signal: synthetic fault prevalence
  diverges from TC 10 reference at chi-squared p=0.0007. Triggers the synthesis
  tuning step (extend n + adjust per-fault gas means) in the v1 plan.

### Documentation

- Expanded `docs/insomnia_runbook.md` with operational gaps surfaced after the
  Apr 27 PR `#143` / `#144` landings and the Apr 26 worktree-perms incident:
  - New "Filesystem topology" section with ASCII tree of
    `/insomnia001/depts/edu/users/team13/` (canonical checkout, `worktrees/`
    sibling, `AssetOpsBench/` upstream, `.venv-insomnia/`), plus `quota -s`
    and `df -h` storage-headroom commands.
  - New "Worktrees on Insomnia" subsection: three-flavor `git worktree add`
    recipe (existing local branch, remote-only branch via `-b`, brand-new
    branch off `team13/main`) with explicit warning against passing a
    remote-tracking ref directly (which detaches HEAD). Shared-venv guidance,
    `worktrees/` parent perms gotcha (`drwxrws---` required or teammates
    can't create new worktrees), and `git worktree remove --force`
    data-loss warning.
  - Foreground vLLM example split into "completions-only sanity serve" vs
    "tool-call serve for any benchmark / AaT / PE reproduction."
    `run_experiment.sh:90-104` defaults `VLLM_ENABLE_AUTO_TOOL_CHOICE=1`
    and selects a model-family parser; the top-level Cell A / Cell B
    configs pin those values explicitly, while `configs/experiment2/*.env`,
    `configs/aat_mcp_optimized.env`, and the example configs inherit the
    defaults. Manual reproductions need
    `--enable-auto-tool-choice --tool-call-parser <parser>` regardless of
    cell; the recipe now sources the target config so `MAX_MODEL_LEN`
    matches what the harness expects (`32768` for Cell Y/Z PE configs;
    `8192` for current Cell A/B AaT configs) instead of hard-coding `8192`,
    AND re-applies the same `${VAR:-default}` shell defaults that
    `run_experiment.sh:90-104` would (otherwise sourcing a Cell Y config
    leaves `VLLM_SERVED_MODEL_NAME`, `VLLM_ENABLE_AUTO_TOOL_CHOICE`, and
    `VLLM_TOOL_CALL_PARSER` empty and the manual launch fails on argument
    validation).
  - vLLM 0.19.0 torch profiler change documented across the full doc/script
    cascade: `VLLM_TORCH_PROFILER_DIR` env var dropped, replaced by
    `--profiler-config '{"profiler":"torch","torch_profiler_dir":"..."}'`
    (absolute path, `run_experiment.sh:783-785`). `docs/insomnia_runbook.md`
    Debugging section, `docs/runbook.md` § 4.3, `profiling/README.md`
    PyTorch-Profiler section, and `profiling/scripts/run_vllm_torch_profile.sh`
    header comments + error messages all updated. Canonical capture route is
    now `TORCH_PROFILE=1 bash scripts/run_experiment.sh <config>`; the manual
    foreground recipe is documented for ad-hoc debugging only and now warns
    against env-prefix overrides (cell configs assign `LAUNCH_VLLM=1`
    unconditionally, which clobbers `LAUNCH_VLLM=0` env values when the
    script sources the config) — recommended targets are
    `scripts/replay_scenarios.sh` or a direct `curl` against the foreground
    server, with a temp-config copy reserved for full-harness runs.
    `scripts/vllm_serve.sh` does not
    currently inject `--profiler-config`, flagged in `profiling/README.md`
    for future patch. Profiler artifact references updated from
    `pt.trace.json` to the actual vLLM 0.19 form `*.pt.trace.json.gz`
    (gzipped); `chrome://tracing` requires `gunzip -k` first,
    `https://ui.perfetto.dev` accepts the `.gz` directly. `.gitignore`
    extended to cover `*.pt.trace.json.gz` alongside the existing
    `*.pt.trace.json` and `profiling/traces/` patterns.
  - `profiling/README.md` § Status replaced (was "Apr 14, 2026" stub
    documenting "first profiling runs scheduled for W3" — superseded by
    actual proof runs in `docs/validation_log.md`). New text points to
    `docs/validation_log.md` for capture provenance and
    `docs/insomnia_runbook.md` for operational notes; notebook input
    dependencies (`latencies.jsonl`, `nvidia_smi.csv`) retained.
  - Manual profiler ad-hoc recipe rewritten to avoid the `LAUNCH_VLLM=1`
    config-clobber footgun: cell configs assign `LAUNCH_VLLM=1` (not
    `${LAUNCH_VLLM:-1}`), so an env-prefix `LAUNCH_VLLM=0` is overwritten
    when `run_experiment.sh` sources the config. Doc now recommends
    targeting `scripts/replay_scenarios.sh <bench-run-dir> direct` (skips
    server launch, replays against existing `LITELLM_BASE_URL`) or a direct
    `curl /v1/chat/completions` probe; the only safe full-harness path is
    a temp config copy with `LAUNCH_VLLM=0` and `TORCH_PROFILE=0` appended
    after the original assignment.
  - `scripts/run_exp1_ab_capture.sh` stale `pt.trace.json` references
    (lines 34, 128) updated to `*.pt.trace.json.gz` with explicit
    perfetto/gunzip guidance, matching the doc cascade.
  - `profile_meta.json` "notes" field (emitted by
    `profiling/scripts/run_vllm_torch_profile.sh`) now mirrors the README
    gzip wording so a shared trace artifact is self-explanatory without
    the README.
  - `docs/runbook.md` § 2.2 venv-recovery pointer fixed: replaced stale
    quoted heading "If you need a newer vLLM" (does not exist in
    `insomnia_runbook.md`) with the actual fragment
    `#recreate-the-shared-env-when-needed`.
  - New "Trial output contract (PR `#143`)" subsection: per-trial JSONs now
    carry `data["scenario"]` (full source scenario JSON object, with
    `scenario.id` consumed by Notebook 03) and `data["success"]` (preserved
    if runner wrote a bool, otherwise derived from history step-failure
    signals + answer truthiness). Default `TRIALS=3`. Documented retrofit
    invocations: `python3 scripts/backfill_canonical_scenario.py [--apply]
    [--cell A|B|C|Y|Z]` — script walks `benchmarks/cell_<X>/raw/<run_id>/`
    from the repo root, no positional capture-dir.
  - Email-notifications section rewritten to make
    `MAIL_USER="${USER}@columbia.edu"` the default pattern, with a concrete
    `sbatch ... scripts/run_experiment.sh configs/experiment2/exp2_cell_Y_pe_mcp_baseline.env`
    invocation.
  - New "Excluding bad nodes" section with the `--exclude=ins082` pattern for
    routing around individual nodes that surface
    `RuntimeError: CUDA unknown error - this may be due to an incorrectly set up environment ...`
    (multi-comma form for multiple bad nodes; RCS ticket advice if a node
    stays bad >1 day).
  - Compute-node hostname pattern (`ins0XX`) and live read commands
    (`hostname`, `$SLURMD_NODENAME`) called out near the inference-test recipe.
  - GPU-type list pinned to live `sinfo -o '%P %.6D %.20G %N'` output instead
    of relying on the static A6000/L40/L40S/H100 enumeration.
  - `requirements-insomnia.txt` overlay relationship explained
    (`-r requirements.txt` head-line); pin updates: `mcp[cli]==1.27.0`
    (was `>=1.26.0`), `openai-agents==0.14.5` added.
  - `## See also` cross-links extended to `runbook.md` § WandB,
    `governance/model_registry.yaml`, `scripts/run_experiment.sh`, and
    `scripts/backfill_canonical_scenario.py`.
  - `docs/runbook.md` last-updated bumped to 2026-04-28; obsolete
    `../hpml-worktree-<branch>` worktree snippet replaced with cross-link to
    `insomnia_runbook.md#worktrees-on-insomnia`; profiling cross-links
    rewritten with explicit fragments
    (`#pytorch-profiler-via-vllms-built-in-endpoints`,
    `#debugging-foreground-vllm`).
  - Last-updated dates bumped to 2026-04-28 in `docs/insomnia_runbook.md`,
    `docs/runbook.md`, and `profiling/README.md`.

## 2026-04-27

### Evaluation / Captures

- Landed the first canonical Experiment 2 capture set on Insomnia at
  Llama-3.1-8B-Instruct: `8998340_exp2_cell_Y_pe_mcp_baseline` (Plan-Execute,
  3/6 pass), `8998341_exp2_cell_Y_pe_self_ask_mcp_baseline` (Plan-Execute +
  Self-Ask, 6/6), `8998342_exp2_cell_Z_verified_pe_mcp_baseline` (Verified
  PE, 6/6), and `8998343_exp2_cell_Z_verified_pe_self_ask_mcp_baseline`
  (Verified PE + Self-Ask, 6/6). All four ran 3 trials × 2 multi-domain
  scenarios = 6 runs/cell, matching the Exp 1 canonical depth from PR `#130`.
  Cell B (`8979314_aat_mcp_baseline`) inherits from PR `#130` as the shared
  Exp 1 / Exp 2 anchor — not re-run. Captures emitted natively in canonical
  form (no retrofit) because the runner contract from PR `#143` writes
  `data["scenario"]` and `data["success"]` per trial. PR `#144` (Alex)
- Generated 6-dim Maverick-17B judge scores against
  `watsonx/meta-llama/llama-4-maverick-17b-128e-instruct-fp8` for all 5
  ready cells (A, B, Y, Y+SA, Z, Z+SA). Mean `score_6d` ranking inverts the
  speed/completion ranking: Z + Self-Ask 0.833 (5/6 pass), Z 0.639 (4/6),
  Y + Self-Ask 0.444 (3/6), B 0.278 (2/6), A 0.167 (1/6), Y baseline 0.111
  (0/6). Per-trial Maverick prompts + raw responses captured under
  `results/judge_logs/<run_name>/<scenario_id>_judge_log.json` for
  reproducibility. Aggregate scores in
  `results/metrics/scenario_scores.jsonl`. PR `#144` (Alex)
- Audited Notebook 02 / 03 contracts against runner emission and closed
  three gaps in PR `#143` and PR `#144`: per-trial JSONs now carry both
  `data["scenario"]` (with the input scenario object incl. `id`) and a
  `bool data["success"]`, derived from `trajectory` / `history` step
  signals when the runner does not emit success natively (handles upstream
  AOB `plan-execute` CLI for Cell Y baseline). Notebook 03 now reads
  `history` first then `trajectory` across all four call sites for shape
  consistency. The `failure_breakdown` aggregation widens `any_failure` to
  `success == False` so AOB CLI output is counted correctly. The
  Self-Ask ablation aggregator merges `latency_p50` / `latency_p95` from
  the run inventory so `plot_self_ask_ablation` does not crash on missing
  columns. Existing captures retrofit via
  `scripts/backfill_canonical_scenario.py --apply` (idempotent;
  history-first precedence). PR `#143` (Alex)
- LLM judge (`scripts/judge_trajectory.py`) is now shape-agnostic: dumps
  whatever trajectory the runner emits as JSON text and lets the judge
  LLM parse the format (mirrors AOB's upstream `feat/evaluation-module`
  design at `src/evaluation/runner.py:_trajectory_to_text`). Same 6-criterion
  rubric (task_completion, data_retrieval_accuracy,
  generalized_result_verification, agent_sequence_correct,
  clarity_and_justification, hallucinations) as both Akshat's PR `#113`/`#114`
  team-local judge and AOB's `feat/evaluation-module:src/evaluation/graders/llm_judge.py`.
  Now scores AaT's `history` shape and PE-family `trajectory` shape
  uniformly. Per-cell classifier fields (`experiment_cell`,
  `orchestration_mode`, `mcp_mode`, `model_id`) read from per-run
  `meta.json` first, falling back to cell-level `config.json` — fixes a
  Critical bug where every score row defaulted to `experiment_cell=Y` and
  collapsed Notebook 03's per-cell join. PR `#144` (Alex)
- Defaulted `VLLM_ENABLE_AUTO_TOOL_CHOICE=1` and made
  `VLLM_TOOL_CALL_PARSER` model-family-aware in `scripts/run_experiment.sh`
  (`llama-3.x` → `llama3_json`, `qwen` → `hermes`, `mistral` → `mistral`,
  fallback → `llama3_json`). Replay-phase always invokes `aat_runner`
  regardless of the original cell's orchestration; non-AaT cells were
  starting vLLM without the tool-choice flags and the replay invariably
  failed with `litellm.BadRequestError: "auto" tool choice requires
  --enable-auto-tool-choice and --tool-call-parser to be set`. The
  underlying replay-phase / aat_runner-vs-cell-runner design tension is
  pinned to backlog as a deeper investigation. PR `#144` (Alex)

### Project board / coordination

- Apr 27 size audit applied across the GitHub Project: bumped `#26`, `#104`,
  `#58` to L; cut `#79`, `#96` to S and `#108` to L; filled `Estimate` field
  for the bumped issues (`#23`=6, `#26`=10, `#104`=12). Round 3 placeholder
  squashes also executed: `#95` → `#79`, `#91` → `#92`, `#84` → `#82`,
  `#89` → `#88`. Round 1 load-balance reassignments and Round 2 writing
  rebalance still pending team buy-in at Apr 28 sync. (Alex)
- Posted comments on `#132` (gpu_type='unknown' fix — flagged W5→W4
  bundling with `#135`) and `#135` (MAX_MODEL_LEN=32768 — confirmed same-day
  W4 placement to land before W5 captures). (Alex)
- Pinned a Dhaval question to `Final_Project/planning/Dhaval_Email_Thread.md`
  (personal repo) on AOB's `feat/evaluation-module` branch:
  upstream-merge timeline, judge-model intent (Maverick vs the branch's
  Claude Opus default), and migration recommendation for our team-local
  judge once the AOB module merges. (Alex)

### Config / Docs

- Added `docs/failure_taxonomy_evidence.md` as the dedicated working surface
  for `#35` (failure taxonomy classification + evidence table), split out of
  the combined `docs/failure_analysis_scaffold.md` so each issue (`#35`,
  `#64`, `#36`, `#5`) has its own reviewable PR. This doc carries the
  Berkeley categories, taxonomy decision ladder, evidence table schema,
  populated Apr 22 evidence pass, paper-safe wording guide, classification
  workflow, and artifact readiness ledger. The CSV export
  `results/metrics/failure_evidence_table.csv` stays owned by `#36` (Alex)
- Added `docs/failure_visuals_mitigation.md` as the dedicated working surface
  for `#64` (failure visuals + mitigation plan), split out of the combined
  `docs/failure_analysis_scaffold.md` so each issue (`#35`, `#64`, `#36`,
  `#5`) has its own reviewable PR. This doc carries the visuals scaffold,
  figure-ready aggregation contract (one CSV per figure), mitigation ranking
  rubric, the Apr 22 initial mitigation ranking, the mitigation experiment
  card, and the promotion gate from `#64` into `#65` / `#66`. The table-side
  exports (`mitigation_run_inventory.csv`, `mitigation_before_after.csv`)
  stay owned by `#36` (Alex)
- Refocused `docs/failure_analysis_scaffold.md` on the `#36` before/after
  metric pack only (export contract, comparison ledger,
  comparison-ready status labels, fill order) and dropped
  `docs/neurips_draft.md` from this surface since the paper-writing lane
  moved to its own `#5` PR. Cross-references to the new `#35`
  taxonomy/evidence doc and `#64` visuals/mitigation doc are added (Alex)
- Added `docs/neurips_draft.md` as the dedicated NeurIPS paper-writing
  scaffold for `#5`, lifted out of the combined `#35/#64/#36/#5` staging in
  PR `#124` so each issue has its own reviewable PR. Carries working title,
  one-paragraph claim, draft abstract, contribution list, claim ledger
  (which claims are already evidence-backed vs blocked), and section
  scaffold with reusable draft prose for Introduction, Related Work,
  Benchmark / Method, Experiments, Results, Discussion, Limitations. Owner
  field updated to flag that section co-authoring is under discussion for
  the Apr 28 team sync (Round 2 writing rebalance proposal) (Alex)

### Planning / Coordination

- Split Cell C analysis out of `#26` into `#86` (mirror of `#85`-from-`#25`
  capture-side split). `#26` now scopes to NB02 Cell A/B analysis; `#86` covers
  NB02 Cell C analysis, gated on `#85`. Reopened `#26` (PR `#123` had used
  `Closes #26` and auto-closed it on merge), scope-narrowed body, added
  splinter cross-references. Posted formal audit comment on `#86`. Swept
  generic `#26` references across active docs (`live_repo_summary.md`,
  `experiment1_capture_plan.md`, `execution_plan.md`, `project_synopsis.md`,
  `results/README.md`) to mention `#86` where the reference covered full
  Cell A/B/C scope; left A/B-scoped references (e.g., shared Cell B
  preflight) unchanged. (Alex)

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

## 2026-04-23

### Config / Docs

- Added a short tracked `.claude/rules/project-board.md` rule so team-repo GitHub Project comments stay factual, proportional to issue size, and concise in closeout mode without turning the rule layer into a long template surface (Alex)

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
- Notebook 03 now has a run-centric Self-Ask ablation layer for the PE-family
  lanes: it scans the raw Y / Z run inventory, classifies each run as baseline
  vs Self-Ask from committed artifacts rather than trusting the mutable cell
  root `summary.json`, writes
  `results/metrics/notebook03_self_ask_run_inventory.preflight.csv`, and will
  emit `notebook03_self_ask_ablation.{csv,png}` as soon as a ready
  baseline/self-ask pair exists for Y and/or Z. The orchestration comparison
  also runs in a preliminary mode when no canonical scenario.id propagation
  exists yet, aggregating on `scenario_file` and tagging the output with
  `mode=preliminary` so reviewers can spot the difference (Alex) (#34)
- Promoted the Experiment 2 config surface out of placeholder state: renamed
  `configs/experiment2/exp2_cell_Z_hybrid_mcp_baseline.env` to
  `exp2_cell_Z_verified_pe_mcp_baseline.env`, added Y + Self-Ask, Z + Self-Ask
  variants, aligned `SCENARIO_SET_NAME` with Cell B for clean cross-experiment
  joins, and turned on `TORCH_PROFILE=1` by default in all four exp2 configs
  for HPML profiling. Added `docs/experiment2_capture_plan.md` documenting the
  Insomnia run sequence, the legacy `cell_Z_hybrid` directory mapping, and
  what each merged run unlocks downstream (Alex) (#32)

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
