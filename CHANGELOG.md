# Changelog

## 2026-05-03

### Changed

- Added the first editable final-presentation PPTX draft at
  `reports/archive/2026-05-03_final_presentation_smartgridbench_draft.pptx`
  and refreshed the #44 deck docs / report inventory to record the May 3 build
  status, layout QA result, and remaining scenario, mitigation, and dry-run
  gates. Refs #44; issue remains open.

## 2026-05-02

### Changed

- Added `docs/neurips_overleaf_transfer_plan.md` and linked it from the
  NeurIPS draft, submission packet, and IEEE back-port scaffold so #5 / #39 /
  #40 / #47 / #48 / #78 have a concrete Overleaf copy queue with caveats for
  pending scenario-count, rerun, mitigation, and compile gates.
- Added `docs/final_presentation_run_of_show.md` and expanded
  `docs/final_presentation_deck.md` with timing, speaker-note, source-proof,
  and production-checklist scaffolding for #44.
- Added the first reviewable #2 generated-scenario batch under
  `data/scenarios/generated/first_review_20260502/`: five WatsonX-generated
  candidate scenarios, one per PS B family, with prompts, raw responses,
  provenance, nearest-handcrafted comparators, and a batch-local validation
  summary for the #53 review pass.
- Added `docs/mitigation_recovery_adjudication.md`, an implementation-ready
  spec for the follow-on mitigation ladder: bounded missing-evidence
  retry/replan recovery and explicit fault/risk adjudication. The spec keeps
  recovery dependent on the existing detection guard and marks the adjudication
  key as reserved until runner code consumes it.
- Implemented the `missing_evidence_retry_replan_guard` for repo-local
  PE-family runners. PE + Self-Ask can retry bounded read-only
  evidence-producing steps; Verified PE + Self-Ask can also drive suffix
  replanning from deterministic missing-evidence detection. Added matched
  recovery rerun configs under `configs/mitigation/`.
- Refreshed the #64 / #66 / #36 / #5 documentation surfaces so mitigation
  planning distinguishes implemented detection, implemented recovery, and
  deferred adjudication without claiming rerun evidence that does not exist.
- Regenerated the mitigation inventory and priority figure labels so
  `missing_evidence_retry_replan_guard` is `implemented_pending_rerun`
  and `explicit_fault_risk_adjudication_step` is
  `spec_ready_deferred_until_repair`.

## 2026-05-01

### Changed

- Documented the mitigation-ladder policy for `#64` / `#66`: use `Y +
  Self-Ask` and `Z + Self-Ask` as the family lanes, treat
  `missing_evidence_final_answer_guard` as the detection / truthfulness gate,
  record `missing_evidence_retry_replan_guard` as the next recovery rung, and
  avoid a full cell-by-mitigation permutation grid.
- Implemented the first failure-taxonomy mitigation lane for `#65` /
  `#66`: `scripts/mitigation_guards.py` adds the
  `missing_evidence_final_answer_guard`, and `scripts/run_experiment.sh`
  applies it when `ENABLE_MISSING_EVIDENCE_GUARD=1`. The guard scans
  emitted trial trajectories for missing, empty, or untrusted evidence and
  blocks clean final-answer / work-order success when a substantive answer
  follows that gap.
- Added guarded mitigation rerun configs under `configs/mitigation/` for
  PE + Self-Ask and Verified PE + Self-Ask, plus the header-only
  `results/metrics/mitigation_before_after.csv` contract for #66. These
  scaffold matched reruns without claiming after-run improvement before
  Insomnia artifacts exist.
- Added a paper/report delivery scaffold for `#5`, `#39`, and `#40`:
  `docs/neurips_draft.md` now records its issue scope, current NeurIPS draft
  completion state, failure-taxonomy figure links, and the handoff to the class
  report back-port; `docs/final_report_backport_scaffold.md` defines the IEEE
  section map, drift-control rules, figure/table requirements, and conversion
  checklist.

### Removed / migrated

- `docs/coordination/` directory removed from this team repo and migrated
  to Alex's personal class repo at
  `/Users/wax/coding/Classes/COMS-E6998/docs/coordination/`. Files moved
  (tracked): `live_repo_summary.md`, `repo_summary_history.md`,
  `shift_coordination_note_template.md`. Per-session
  `shift_coordination_note__*.md` files (untracked) were also relocated.
  Rationale: the coordination tooling is Alex-only; teammates do not
  operate it. Personal-repo privacy lets full-detail orchestration
  lessons (commit refs, URL patterns, copyright reasoning) stay durable
  without public-repo audit risk.
- Reference updates in `CLAUDE.md` (MECE convention section, hard
  rule 10, canonical-docs list), `.claude/rules/planning-docs.md`,
  `planning/2026-04-28_meeting_notes.md`,
  `planning/2026-04-28_post_meeting_action_plan.md`,
  `planning/2026-04-28_dhaval_shuxin_meeting_notes.md`,
  `docs/plans/aob-extraction.md`, `docs/plans/aob-extraction_spec.md` —
  meeting notes now point at the GitHub Project board for current task
  status; plan docs point at the personal-repo coordination dir; CLAUDE.md
  documents the move and the new cross-repo location for future agents.

### Validated

- Backfilled judge-score summary fields into the committed first-capture
  `summary.json` snapshots for A/B/C/D/Y/Z/ZSD, normalizing each snapshot from
  its own run-local `meta.json`, `latencies.jsonl`, per-trial JSONs, and
  `results/metrics/scenario_scores.jsonl`.
- Added `results/metrics/optimized_serving_ablation.csv` and linked it from
  `docs/experiment_matrix.md` / `results/README.md` so the exploratory Cell D
  and ZSD serving-stack deltas are findable without mixing them into the core
  notebook tables.
- Extended `scripts/backfill_canonical_scenario.py` to recognize D and ZSD raw
  artifact directories for future canonical-scenario consistency checks.

## 2026-04-30

### AOB extraction (in fork `~/coding/AssetOpsBench`, local-only)

- Phases 0/1/2/3a+3b+3c all code-complete on a linear 4-branch stack:
  `aob/sg-evaluation-adapter @ c7bc99e` → `aob/sg-domain-port @ bece2fa`
  → `aob/sg-orchestration-runners @ 0892b92` →
  `aob/sg-aat-batch-mode @ 6872cea` (integration tip). 177/177 full
  agent suite green; 60/60 evaluation; 25/25 Smart Grid; 35 new
  plan-execute tests; 10 new run_batch tests.
- Two cross-agent review tracks against Codex `3ab548b5`, both LGTM
  0/0/0/0 at v4 — original Phases 0/1/2/3a+3b (4 iterations) + Phase 3c
  team-AaT batch mode (4 iterations).
- Phase 3c lands `OpenAIAgentRunner.run_batch(prompts, trials)` with MCP
  connection reuse via single `AsyncExitStack`, plus
  `parallel_tool_calls` constructor knob (default `False`). Per-trial
  errors captured in new `AgentResult.error` field instead of aborting
  the batch. Empty `prompts` and `trials < 1` rejected with
  `ValueError` before any MCP server is constructed.
- D5 (cross-branch scenario validation) and D6 (team-AaT batch-mode
  port) closed in `docs/plans/aob-extraction_deferred.md`.
- Branches local-only on fork; not pushed to `origin/eggrollofchaos`.
  Phase 4 (upstream PR(s) to `IBM/AssetOpsBench`) explicitly deferred.

### Documentation

- `benchmarks/README.md` — document the raw benchmark log convention:
  committed `harness.log` / `vllm.log` files preserve original runner output
  and may contain ANSI/debug text or trailing whitespace, so repository-wide
  whitespace checks should exclude `benchmarks/*/raw/` and publication-clean
  logs should be derived separately under `results/`.

- `docs/dga_realism_statistical_validation.md` — doc reframe pointing
  §§ 2.4 / 9 / 12.5 / 14 to PR #149's `fault_table` JSON + FMSR server
  `_rogers_ratio()` as the canonical encoding of IEC 60599:2022 Table 1.
  - § 2.4 / § 14 cross-reference the JSON encoding instead of "ask Alex"
    or external sources.
  - § 9 risks: edition-mismatch row marked resolved (PR #149); new row
    added for stray-gassing under-representation as actionable Akshat
    decision based on v1 chi² results.
  - § 12.5 help map cleaned up: Alex retains AOB-refactor scope, Tanisha
    retains paper framing scope.
  - § 13 Appendix A rewritten as a citation + encoding-conventions
    pointer. Bibliography path documented (purchase via webstore.iec.ch
    ~CHF 364 or Columbia ILL before paper submission). Notes paraphrased
    rather than reproduced, in line with IEC copyright.

- `docs/coordination/live_repo_summary.md` — slid emphasis window to
  2026-04-30 15:30 EDT; added PR #150 to Active review PRs.

No code or behavior changes from PR #150 (doc-only).

### Validated

- Backfilled the first-capture Experiment 1/2 analysis surfaces after Cell C/D/ZSD
  landed: A/B raw trial JSONs now carry canonical `scenario` objects, Cell B
  metadata records its shared `exp1_mcp_overhead` + `exp2_orchestration` role,
  Notebook 02 exports full A/B/C MCP-overhead rows, and Notebook 03 exports
  canonical B/Y/Z, PE-family, Self-Ask, and failure-breakdown aggregates.
  Added `results/metrics/experiment_matrix_summary.csv` plus the human-facing
  results table and run-inspection guide in `docs/experiment_matrix.md`.
- Recorded the first successful exploratory Z + Self-Ask + D optimized
  PE-family ablation: Slurm job
  `9074775_exp2_cell_ZSD_verified_pe_self_ask_mcp_model_optimized` on
  Insomnia `ins084`, `6 / 6` success, W&B `48nqpclw`, `tool_error_count=0`,
  and canonical artifacts under
  `benchmarks/cell_ZSD/raw/9074775_exp2_cell_ZSD_verified_pe_self_ask_mcp_model_optimized`.
  The run stacks Verified PE + Self-Ask with optimized MCP persistent sessions
  and the Cell D INT8/BF16/fp8-KV serving profile.
- Generated six-dimension Maverick-17B judge scores for ZSD job `9074775`:
  six per-trial rows in `results/metrics/scenario_scores.jsonl`, mean
  `score_6d=0.611`, p50 `0.833`, and pass rate `3 / 6` at threshold `0.6`.
- Recorded the first successful exploratory Cell D optimized-serving capture:
  Slurm job `9073472_aat_mcp_model_optimized` on Insomnia `ins084`, `6 / 6`
  success, W&B `pmwzatie`, replay `2 / 2`, profiler artifact
  `profiling-pmwzatie`, and canonical artifacts under
  `benchmarks/cell_D/raw/9073472_aat_mcp_model_optimized`. The vLLM log proves
  compressed-tensors INT8 loading, BF16 execution, fp8 KV cache, prefix
  caching, and the compressed-tensors Cutlass INT8 kernel.
- Generated six-dimension Maverick-17B judge scores for Cell D job `9073472`:
  six per-trial rows in `results/metrics/scenario_scores.jsonl`, mean
  `score_6d=0.167`, p50 `0.0`, and pass rate `1 / 6` at threshold `0.6`.
- Recorded the first successful Experiment 1 Cell C optimized capture:
  Slurm job `9071639_aat_mcp_optimized` on Insomnia `ins083`, `6 / 6`
  success, W&B `ifz8xfhm`, replay `2 / 2`, profiler artifact
  `profiling-ifz8xfhm`, and canonical artifacts under
  `benchmarks/cell_C_mcp_optimized/raw/9071639_aat_mcp_optimized`.
  This gives Notebook 02 a first real `(B-C)` MCP-overhead comparison against
  Cell B job `8979314_aat_mcp_baseline`.
- Generated six-dimension Maverick-17B judge scores for Cell C job `9071639`:
  six per-trial rows in `results/metrics/scenario_scores.jsonl`, mean
  `score_6d=0.167`, p50 `0.167`, and pass rate `0 / 6` at threshold `0.6`.

### Changed

- Added the first CSV-backed failure taxonomy export:
  `results/metrics/failure_evidence_table.csv` classifies 35 judge-failed rows
  from `results/metrics/scenario_scores.jsonl` into Berkeley-style failure
  labels for `#35`, with docs refreshed in
  `docs/failure_taxonomy_evidence.md`,
  `docs/failure_visuals_mitigation.md`,
  `docs/failure_analysis_scaffold.md`, and `results/README.md`.
- Added `scripts/render_failure_taxonomy_figures.py` plus the first
  failure-analysis derived outputs:
  `results/metrics/failure_taxonomy_counts.csv`,
  `results/metrics/failure_symptom_counts.csv`,
  `results/metrics/failure_stage_cell_counts.csv`,
  `results/metrics/mitigation_run_inventory.csv`,
  `results/figures/failure_taxonomy_counts.svg`,
  `results/figures/failure_stage_cell_heatmap.svg`, and
  `results/figures/mitigation_priority_table.svg`. The mitigation inventory
  selects `missing_evidence_final_answer_guard` as the first follow-on lane
  while keeping after-run claims pending until a matched rerun exists.
- Hardened repo-local PE-family follow-on runs after ZSD job `9073604`
  exposed two ablation-specific failure boundaries: LiteLLM diagnostics could
  prepend text to stdout and corrupt per-trial JSON files, and the 8192-token
  INT8 context window could be exceeded by verifier/replan prompts with the
  inherited 2048 output-token request. `run_experiment.sh` now sanitizes
  wrapper stdout into canonical JSON, `orchestration_utils.py` honors
  `MAX_TOKENS` for repo-local PE-family LiteLLM calls, and the ZSD config caps
  generations at 1024 tokens. Plan normalization also accepts short server
  aliases such as `i` for `iot`.
- `configs/aat_mcp_optimized.env` now keeps
  `AAT_PARALLEL_TOOL_CALLS=false` for the canonical Insomnia vLLM /
  Llama-3.1-8B-Instruct path. Job `9071621` reached model/tool execution but
  failed all six trials because vLLM rejected parallel tool-call requests; the
  successful Cell C shape preserves batch/connection reuse plus prefix caching
  with sequential tool-call turns.
- `scripts/judge_trajectory.py` now writes audit logs with trial-indexed
  filenames (`<scenario_id>_runNN_judge_log.json`) so multi-trial scoring no
  longer overwrites earlier trials for the same scenario.
- Added exploratory Cell D config `configs/aat_mcp_model_optimized.env` for
  AaT optimized MCP plus compressed-tensors INT8, BF16 dtype, fp8 KV cache, and
  prefix caching. `scripts/run_experiment.sh` now exposes `VLLM_DTYPE` so this
  does not rely on duplicate `--dtype` flags; existing cells still default to
  `float16`.
- Fixed the AaT torch-profiler replay environment so model-variant cells replay
  against the same `MODEL_ID` and MCP bootstrap settings as the parent
  benchmark run instead of falling back to the default FP16 served model.
- Added PE-family optimized MCP execution for follow-on ablations: repo-local
  Plan-Execute/Verified PE runners can now request `MCP_MODE=optimized` and
  reuse initialized MCP stdio sessions inside a scenario run. Added the
  exploratory `Z + Self-Ask + D` config that stacks Verified PE + Self-Ask with
  the Cell D INT8/BF16/fp8-KV serving profile.
- Fixed run metadata export for model-optimized cells so `config.json` and
  per-run `meta.json` record `VLLM_DTYPE` and `EXTRA_VLLM_ARGS` from sourced
  configs instead of falling back to Python subprocess defaults.

## 2026-04-29

### Fixed (PR #149 review v2)

- `mcp_servers/fmsr_server/server.py` — apply review v2 fixes:
  - **High 1**: divergent ratios were leaking `math.inf` into the public
    `analyze_dga` result, breaking strict JSON serialization
    (`json.dumps(result, allow_nan=False)` raised on the zero-denominator
    reproducer). Added `_ratio_field()` and `_build_result()` helpers
    that normalize outbound ratio fields: a divergent ratio is now
    reported as `null` plus a sibling `r{1,2,3}_divergent: true` flag.
    Internal table matching still uses the true infinity, so
    classification correctness is preserved. Finite-ratio results omit
    the `*_divergent` keys entirely (avoids surprising consumers with
    always-false flags).
  - The `analyze_dga` tool docstring documents the divergent-flag
    convention.
  - **Low 2**: `data/knowledge/transformer_standards.json:47`
    `match_order` boundary phrasing aligned to the encoded
    min-inclusive/max-exclusive convention (`R2 ∈ [1.0, 2.5)`,
    `R3 ≥ 2.0`); matches `range_semantics` and the server table now.
- `tests/test_fmsr_server.py` — three zero-denominator regressions
  reshaped to assert the new public output: ratio field is `None`,
  `r{1,2,3}_divergent` is `True`, and `json.dumps(result, allow_nan=False)`
  succeeds. Added `test_analyze_dga_finite_ratios_have_no_divergent_flags`
  ensuring finite-ratio results stay clean. All 27 fmsr tests pass.

### Fixed (PR #149 review v1)

- `mcp_servers/fmsr_server/server.py` — apply review v1 fixes:
  - **High 1**: zero-denominator collapse to 0.0 in `_rogers_ratio` could
    silently misclassify samples. Reproducer at the v1 head: `h2=500,
    ch4=200, c2h2=120, c2h4=100, c2h6=0` has R3=+inf (real ratio diverges)
    and matches D2 row, but the prior code reported `iec_code=N` and
    `r3_c2h4_c2h6=0.0`. Replaced inline `x / y if y > 0 else 0.0` with a
    `_ratio()` helper that returns `math.inf` when denominator==0 and
    numerator>0, `0.0` when both are zero, and the finite quotient
    otherwise. The `_in_range` boundary checks already handle `math.inf`
    correctly (inf >= lo passes; inf < hi fails for finite hi).
  - **Low 4**: comments at server.py:67-69 + tests docstring at line 15
    aligned to encoded boundary semantics (`R3 ≥ 2.0`, `R2 ∈ [1.0, 2.5)`)
    so future boundary tests do not infer a stricter table.
- `tests/test_fmsr_server.py` — three regression tests added for
  zero-denominator divergence: `test_analyze_dga_zero_c2h6_diverges_r3`
  (the High 1 reproducer; expects D2 + isinf(R3)),
  `test_analyze_dga_zero_c2h4_diverges_r2` (R2=+inf falls outside D2 →
  N), `test_analyze_dga_zero_h2_diverges_r1` (R1=+inf, R3<1 → T1). All 26
  fmsr tests pass.
- `data/knowledge/README.md` — **Medium 3**: D2 example block
  refreshed to the new IEC-aligned profile (H2=500, CH4=200, C2H2=120,
  C2H4=100, C2H6=30) with R1=0.40, R2=1.20, R3=3.33 noted; pointer to
  `alignment_note` instead of removed `server_rogers_table_note`.
- `docs/knowledge/scenario_generation_support.json` — **High 2**:
  `dga_trend_templates` regenerated against IEC-aligned profiles.
  - `endpoint_verification_note` updated with the new canonical profile
    values and a regeneration date.
  - `rising_hydrogen_pd`: terminal step uses new PD profile (R3=0.188);
    intermediate steps re-tuned so R3 stays above 0.2 (PD ceiling) until
    T-60.
  - `accelerating_arc_d1_to_d2`: D1 + D2 endpoints replaced with new
    canonical profiles; intermediate T-14 step (H2=500, CH4=120, C2H2=90,
    C2H4=70, C2H6=40) verified D1; description rewritten to attribute
    D1→D2 to R3 crossing 2.0 and R1 doubling.
  - `thermal_t1_to_t3_progression`: T1, T2, T3 endpoints refreshed; T1
    profile changed substantially (R1=2.00 instead of 0.50 — new T1 row
    requires R1≥1).
  - `stable_condition3_d1`: D1 endpoint + drift trajectory rewired
    around the new D1 profile (C2H2=80, C2H4=60, C2H6=40); R3 stays
    below D2's 2.0 threshold across all three steps.
  - All 5 templates × 3 steps = 15 classifications verified to round-trip
    via `_rogers_ratio`.

### Changed — IEC 60599:2022 Table 1 reconciliation (§ 7 task 2b)

- `mcp_servers/fmsr_server/server.py` — rewrite `_ROGERS_TABLE` to match
  IEC 60599:2022 Table 1 (4th ed., publication 66491, p.13) for all six
  fault rows (PD, D1, D2, T1, T2, T3). Prior table diverged on every
  electrical-discharge row and on T1 R1; documented three-way divergence
  in `docs/dga_realism_statistical_validation.md` § 2.4 + Appendix B.
  - **D1 R1**: `[0.1, 1.0)` → `[0.1, 0.5)` (per IEC).
  - **D1 R2**: `[0.1, 3.0)` → `[1.0, ∞)`.
  - **D1 R3**: `[0, 1.0)` → `[1.0, ∞)`.
  - **D2 R2**: `[0.1, 3.0)` → `[0.6, 2.5)`.
  - **D2 R3**: `[1.0, ∞)` → `[2.0, ∞)`.
  - **T1 R1**: `[0.1, 1.0)` → `[1.0, ∞)`. R2 changed to NS (any).
  - **T1 R3**: `[1.0, 3.0)` → `[0, 1.0)`.
  - **T2 R3**: `[1.0, 3.0)` → `[1.0, 4.0)`.
  - **T3 R2**: `[0, 0.1)` → `[0, 0.2)`.
  - **T3 R3**: `[3.0, ∞)` → `[4.0, ∞)`.
  - **PD R1**: `[0.1, 1.0)` → `[0, 0.1)`. R3 changed `[0, 1.0)` → `[0, 0.2)`.
  - **Match order** changed to most-severe first (D2, D1, T3, T2, T1, PD)
    so first-match-wins resolves IEC's overlapping ranges toward the
    higher-severity code.
  - Adds explicit all-zero guard at the top of `_rogers_ratio` so a sample
    with no detectable gases returns N (PD's R1/R3 ranges include 0 under
    IEC, which would otherwise produce a spurious PD).
- `data/knowledge/transformer_standards.json`:
  - `meta.sources[0].edition` `"3rd"` → `"4th"` (3rd ed. = 2015; 2022 release
    is 4th ed.). Added `publication_id: 66491`.
  - `iec_60599.rogers_ratio_method.fault_table` rewritten to match the
    server table 1:1. Adds explicit `range_semantics` and `match_order`
    keys documenting the convention.
  - `representative_gas_profiles.profiles` regenerated. All seven profiles
    (PD, D1, D2, T1, T2, T3, N) verified to round-trip via
    `analyze_dga`. Removes the `server_rogers_table_note` divergence
    record (no longer applicable). Adds `alignment_note` capturing the
    pre-fix → post-fix transition.
  - `scenario_generator_hints.fault_diagnosis_scenario.example` updated
    with new D2 profile values.
- `tests/test_fmsr_server.py`:
  - `test_analyze_dga_high_c2h2_ratio` (T-018: R1=0.17, R2=18.5, R3=8.67)
    now expects `D1` (was `N`). Under strict IEC, R2 >> 2.5 falls outside
    D2's `[0.6, 2.5)` cap, so D1 wins.
  - Module docstring updated to reflect IEC contract (D2 R2 ∈ [0.6, 2.5),
    samples with R2 >> 2.5 → D1).
  - All 23 fmsr tests pass; 7/7 representative profiles round-trip.
- `docs/dga_realism_statistical_validation.md`:
  - § 2.4 marked **resolved**; pre-fix divergence retained as historical
    context with post-fix status column.
  - § 7 plan rewritten for new ownership split: Akshat owns scenario-truth
    + L3 v1 + synthesis tuning; Alex owns this PR + AOB fork refactor +
    project planning; Tanisha owns NeurIPS / final paper framing.
  - § 12.4 (Akshat handoff decisions) updated: table-fix is no longer a
    pending decision; v0 baseline (n=20, p=0.0106) preserved as evidence.
  - § 14 Appendix B marked **historical (pre-2b)**.

**Why all six rows in one PR (vs. only PD/D1 per the original § 2.4 plan):**
once the standard's text was in front of us for two rows, the others were
one-line edits each. Bundling them is cheaper for downstream consumers
(PR #147 generator path) than landing two PRs.

**Known downstream impact:** any synthetic scenarios already generated by
PR #147 carry fault labels assigned under the pre-fix table. Re-classify
or regenerate before treating them as IEC-compliant ground truth. The L3
validator (`validate_realism_statistical.py`) is unaffected at the
distribution level but its chi² fault-prevalence baseline will shift on
re-run; v0 baseline preserved at `reports/realism_statistical_v0.{md,json}`.

### Fixed (PR #148 review v4)

- `data/scenarios/validate_realism_statistical.py` — apply review v4 fixes:
  - **High 1**: real fault labels are now validated after source-specific
    mapping. Adds a `REAL_LABEL_ALIASES` table (`N` → `Normal`, IEC codes
    pass through, common case-variants normalize). `load_real()` raises
    `ValueError` on any post-mapping label not in `FAULT_CODES`, naming
    the offenders. The chi-squared detail now reports both raw and
    recognized real-row counts (`n_real_recognized=N/M`) so any future
    drop is visible if validation is bypassed.
  - **Medium 2**: `docs/dga_realism_statistical_validation.md` § 6.5
    (Dependencies) updated to reflect the actual install contract: this
    PR adds `scipy` and `openpyxl` to `requirements.txt`; `.xls` is
    intentionally unsupported.
  - **Low 3**: § 12.1 (Akshat handoff) example now uses `.xlsx` plus
    `--real-source ieee_dataport` consistently; module docstring usage
    example matches.

### Fixed (PR #148 review v3)

- `data/scenarios/validate_realism_statistical.py` — apply review v3 fixes:
  - **High 1**: NaN no longer leaks into report. Three changes:
    (a) `chi2_fault_prevalence()` now drops classes where both observed
    and expected are zero before calling `stats.chisquare()` (SciPy
    returned NaN for those terms even with the v5 zero-expected guard);
    rescales the trimmed reference so totals still match.
    (b) Adds a post-test finiteness guard so any future non-finite
    statistic is reported as a structured failure.
    (c) `correlation_delta()` checks for all-NaN delta (which happens
    when a gas column is constant in either frame) and returns a
    descriptive failure instead of `np.nanmax` returning NaN.
    JSON dump now uses `allow_nan=False` so any future non-finite
    metric fails loudly during report generation rather than emitting
    bare `NaN` to the JSON file.
  - **Medium 2**: `load_real()` no longer claims `.xls` support. The
    v4 fix added `.xls` to the routing table but `xlrd` is not in
    `requirements.txt`. Routing `.xls` now raises `ValueError` with
    instructions to convert to `.xlsx` or `.csv`.
  - **Medium 3**: PR body updated separately on GitHub (the previous
    body still referenced the pre-v4 `p = 0.0007` baseline and didn't
    list `openpyxl`).

### Fixed (PR #148 review v2)

- `data/scenarios/validate_realism_statistical.py` + `requirements.txt` —
  apply review v2 fixes:
  - **High 1**: added `openpyxl` to `requirements.txt`. The v4
    fix introduced `pd.read_excel()` for IEEE DataPort's `.xlsx` files
    but did not add the engine; a fresh environment built from the PR
    would have failed before producing any L3 report.
  - **High 2**: `correlation_delta()` now computes both correlation
    matrices over the intersection of gas columns present in synthetic
    and real, and emits a structured failing `TestResult` with
    diagnostic detail when fewer than two gases are shared. Previously
    a real dataset with only some gas columns triggered a numpy
    broadcast `ValueError` (5x5 vs N x N).
  - **Medium 3**: `chi2_fault_prevalence()` now detects the
    "synthetic has rows in a class that the reference has zero
    expected count for" case BEFORE calling SciPy and emits a
    descriptive failing `TestResult` instead of allowing SciPy to
    return NaN (which then leaked bare `NaN` into the JSON report).

- `docs/dga_realism_statistical_validation.md` + `CHANGELOG.md` — apply
  review v2 doc fixes:
  - **Medium 4**: corrected stale `p = 0.0007` references in § 1 and
    in the original Apr-28 Added entry; the v4-regenerated baseline is
    `p = 0.0106` on `n_syn = 20`.
  - **Medium 5**: removed remaining "licensed IEC" + personal-class-
    repo path leak from the v2 Changelog entry; rewrote in team-visible
    language matching § 2.4 ("ask Alex for working notes that cite the
    paywalled standard").
  - **Medium 6**: replaced the remaining numeric IEC range snippets in
    § 2.4 + Appendix B with non-numeric contradiction summaries. Pull
    canonical bounds from IEC 60599:2022 Table 1 directly (or from
    Alex's working notes) when implementing the fix-the-table PR.

### Fixed (PR #148 review v1)

- `data/scenarios/validate_realism_statistical.py` — apply review v1 fixes:
  - **Critical 1**: synthetic fault labels now mapped to IEC codes through
    `PROJECT_LABEL_TO_IEC` before chi-squared counting, so the headline test
    no longer silently drops rows. The v0 baseline now reports `n_syn=20` (was 10
    out of 20). `load_synthetic` raises `ValueError` on unmapped labels rather
    than dropping them, so future generator changes fail loudly instead of
    quietly.
  - **High 2**: chi-squared real-vs-synthetic comparison now scales real
    proportions to `n_syn` via largest-remainder rounding (`_scale_to_total`),
    so SciPy's "observed and expected totals must match" precondition is
    always satisfied regardless of real-dataset row count.
  - **High 3**: Anderson-Darling now uses `ad.pvalue` directly (modern SciPy
    returns it on the `[0, 1]` scale). The previous `/ 100` divisor turned
    capped 0.25 p-values into 0.0025 and failed every AD test.
  - **Medium 5**: `load_real()` now reads `.xlsx`/`.xls` files in addition to
    CSV, and accepts a `--real-source` flag selecting from `REAL_LABEL_MAPS`
    (currently includes the IEEE DataPort integer-fault-code map; placeholders
    for Kaggle and Duval 2001 TC 10 reproductions).
  - **Medium 6**: `conditional_ks_per_fault()` now emits a structured
    failing `TestResult` when a real dataset is missing a gas column, mirroring
    the behavior of the marginal KS / EMD paths instead of crashing with
    `KeyError`.
  - **Medium 8**: `_md_cell()` helper escapes `|` and newlines/CR before
    rendering test details into the Markdown report table.
  - **Low 9**: removed unused `Callable` import.
- `docs/dga_realism_statistical_validation.md` — apply review v1 doc fixes:
  - **High 4**: removed verbatim IEC 60599:2022 Table 1 reproduction from
    Appendix A. Replaced with a reconciliation procedure, citation block,
    and a non-verbatim implementation summary that points back to the diff
    pattern in Appendix B (which only describes our internal tables vs the
    standard's, not the standard's content).
  - **Medium 7**: removed personal-class-repo path references from the
    tracked doc; replaced with team-visible language ("ask Alex", "external
    citation"). The full row-by-row working notes still exist; they're held
    by Alex outside this repo because they cite paywalled IEC text.
- `reports/realism_statistical_v0.md` + `.json` — regenerated against the
  corrected validator. Chi-squared on full 20-row synthetic vs TC 10 reference
  is now `χ²=16.67, p=0.0106` (was `23.33, p=0.0007` operating on 10 rows).

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
  diverges from TC 10 reference at chi-squared p=0.0106 (post-v4 regenerated;
  the original commit recorded p=0.0007 but was operating on only 10 of 20 rows
  due to a label-mapping bug fixed in v4). Triggers the synthesis
  tuning step (extend n + adjust per-fault gas means) in the v1 plan.

### Changed

- `docs/dga_realism_statistical_validation.md` § 2.4 — added three-way
  fault-table divergence finding from comparing IEC 60599:2022 Table 1 against
  `transformer_standards.json` `fault_table` (Table B) and
  `mcp_servers/fmsr_server/server.py` `_rogers_ratio()` (Table C). Worst
  divergences are on D1, D2, and the T2/T3 boundary; the server's own
  `server_rogers_table_note` already documents the C-vs-A drift. Pattern
  (B↔C agreement > B↔A or C↔A) suggests both encodings derived from a
  derivative source rather than IEC text. Pre-May 4 plan amended: new
  task 2b (fix Tables B + C for at least PD/D1; lockstep with FMSR test
  fixtures). The full row-by-row working notes are held by Alex outside
  this repo because they cite the paywalled IEC text.
- `scripts/run_experiment.sh:1130` — replay phase now guarded by
  `ORCHESTRATION=agent_as_tool`. Previously the post-benchmark torch-profiler
  replay invoked `replay_scenarios.sh` (which always drives `aat_runner.py`)
  regardless of the originating cell's orchestration mode. For PE / Verified
  PE cells (Y, Z) the AaT-shaped replay produced a torch trace under the
  cell's `raw/<run>/profiling/` directory that didn't represent the cell's
  actual workload. Cell A/B/C behavior is unchanged (replay still fires).
  Cell Y/Z get an explicit "SKIPPED" message and rely on main-loop profiling
  for coverage. Resolves `pm/backlog.md` 2026-04-27 pin (c). Full design
  rationale in `docs/replay_phase_analysis.md`.

### Documentation

- New `docs/replay_phase_analysis.md` — two-question investigation of the
  vLLM replay phase: (Q1) "first prefill repeats on warmup" is intentional
  steady-state capture by design; (Q2) replay-cell-awareness resolved by
  Option 1 — skip replay for non-AaT cells.
- New `docs/methods_python_version_disclosure.md` — paper-section disclosure
  language for the Cell Y vanilla Plan-Execute Python 3.12 vs others 3.11
  fairness-contract caveat. Includes paper-ready paragraph with the
  interpreter-overhead-vs-model-time argument and TODOs for a strict-parity
  ablation.
- New `docs/plans/aob-extraction.md` + companion `docs/plans/aob-extraction_spec.md`
  — 4-phase plan + spec for extracting Smart Grid Bench artifacts from the
  team repo into Alex's AssetOpsBench fork (`eggrollofchaos/AssetOpsBench`)
  with eventual upstream PR(s) to `IBM/AssetOpsBench`. Phase 1 covers
  `feat/evaluation-module` adoption + SG-per-trial-JSON adapter (resolves
  `pm/backlog.md` 2026-04-27 pin (b) once parity proven). Phases 2-3 cover
  Smart Grid 7th-domain + orchestration-runners upstreaming.
- Updated `profiling/README.md` and `docs/insomnia_runbook.md` to document
  the new replay-phase skip behavior for non-AaT cells; recommended-recipe
  example switched from `cell_Y_plan_execute` to `cell_A_direct` to avoid
  modeling the misleading replay path.
- Fixed 4 broken commit-link refs in `docs/coordination/live_repo_summary.md`
  and `docs/coordination/repo_summary_history.md` (PR `#125` `b480604` →
  `1001a32`; PR `#126` `8548b8a` → `a12b102`; both noted as
  post-Apr-27-rewrite).

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
