# AOB extraction: deferred-items registry

*Companion to [aob-extraction.md](aob-extraction.md) + [aob-extraction_spec.md](aob-extraction_spec.md). Captures every item that was DEFERRED (not done, not abandoned) during Phase 0/1/2/3a/3b/3c execution on 2026-04-28 → 2026-04-30. Each entry names the gating condition, owner, and resumption recipe so a future session can pick it up cold.*

*Last updated: 2026-04-30 (D5 + D6 marked resolved; Phase 3c landed as `OpenAIAgentRunner.run_batch()`, post-v1-review hardening at `aob/sg-aat-batch-mode @ 6872cea`).*

*Archived: 2026-05-05 — AOB extraction phase wound down. AOB PR #34 merged 2026-05-03; org-fork phase branches pushed; IBM-upstream PR work continues under AOB #27 (Cut scope: domain + SG_DATA_DIR + 30 scenarios + IEC/DGA correctness). Any Phase 4 deferred work that resumes will be tracked via fresh issues, not this registry. Preserved as historical record of what was deferred during Phase 0–3 execution.*

---

## Summary

| # | Item | Phase | Gated on | Effort | Severity |
|---|---|---|---|---|---|
| D1 | Live LLM-judge parity run | 1 | Watsonx / Insomnia LLM access | 2-4 hr | Medium — paper-narrative risk if rubric formulas diverge in practice |
| D2 | `compute_parity` comparison script | 1 | D1 output | 2-3 hr | Medium — depends on D1 |
| D3 | CSV data export + `SG_DATA_DIR` documentation | 2 | Decision on data licensing/distribution | 2-4 hr | Medium — blocks any AOB user from running SG servers |
| D4 | Live MCP transport smoke (Cell A/B equivalent against AOB-side servers) | 2 | D3 + LLM endpoint | 4-8 hr | High — blocks Phase 4 upstream PR confidence |
| D5 | Cross-branch scenario validation test | 2 | — | done | Resolved 2026-04-29 on consolidated stack — see D5 detail |
| D6 | Team-AaT batch-mode port | 3c | — | done | Resolved 2026-04-30 as `OpenAIAgentRunner.run_batch()` on `aob/sg-aat-batch-mode @ 6872cea` (`9477bef` initial port + `6872cea` v1 M1 empty-prompts guard) — see D6 detail |
| D7 | Smart-Grid-specific repair logic | 3 | Out of scope by design | n/a | Stays in team repo — NOT a deferral |
| D8 | Eval rubric reconciliation upstream | 4 | Dhaval ack | 2-4 hr (PR) + review | Medium — formula divergence cosmetic but visible |
| D9 | Upstream PR(s) to IBM/AssetOpsBench | 4 | Dhaval coordination + AOB `feat/evaluation-module` merge | 1-2 weeks | High — long pole, unknown review cadence |
| D10 | AOB README delta — Smart Grid 7th domain claim count | 4 | D9 timing | <1 hr | Low — depends on AOB main count at PR time |
| D11 | Per-cell `REPLAY_RUNNER` knob | n/a (post-paper) | None — design clarity required | 4-6 hr | Low — already in `pm/backlog.md` as Future |
| D12 | Final 5×6 canonical re-run | n/a (paper-final) | Team agrees on final scenario set | 1-2 days Slurm | High — paper-final evidence; already in `pm/backlog.md` |

---

## D1 — Live LLM-judge parity run

**What:** Run AOB's `feat/evaluation-module` LLM judge against the 36 canonical Smart Grid Bench trials (6 cells × 6 trials per Phase 1 smoke). Compare per-trial 6-criterion booleans against `results/metrics/scenario_scores.jsonl` (team's existing judge output). Compute Cohen's κ + judge-pass-classification agreement.

**Gating:** Watsonx access (preferred — matches team's `meta-llama/llama-4-maverick-17b-128e-instruct-fp8`) OR Insomnia GPU + a local Maverick-ish judge.

**Resumption recipe** (verbatim from `~/coding/AssetOpsBench/src/evaluation/adapters/parity_report.md`):
```bash
# 1. Adapt 36 canonical trials → PersistedTrajectory JSON files
cd ~/coding/AssetOpsBench
git switch aob/sg-evaluation-adapter
uv run python -c "
from pathlib import Path
from evaluation.adapters import load_team_run_dir
TEAM = Path('/Users/wax/coding/hpml-assetopsbench-smart-grid-mcp')
TARGETS = [
    TEAM / 'benchmarks/cell_A_direct/raw/8979314_aat_direct',
    TEAM / 'benchmarks/cell_B_mcp_baseline/raw/8979314_aat_mcp_baseline',
    TEAM / 'benchmarks/cell_Y_plan_execute/raw/8998340_exp2_cell_Y_pe_mcp_baseline',
    TEAM / 'benchmarks/cell_Y_plan_execute/raw/8998341_exp2_cell_Y_pe_self_ask_mcp_baseline',
    TEAM / 'benchmarks/cell_Z_hybrid/raw/8998342_exp2_cell_Z_verified_pe_mcp_baseline',
    TEAM / 'benchmarks/cell_Z_hybrid/raw/8998343_exp2_cell_Z_verified_pe_self_ask_mcp_baseline',
]
out_dir = Path('/tmp/sg_trajectories'); out_dir.mkdir(exist_ok=True)
for t in TARGETS:
    for rec in load_team_run_dir(t):
        path = out_dir / f'{rec.run_id}__{rec.scenario_id}__{rec.runner}.json'
        path.write_text(rec.model_dump_json(indent=2))
"

# 2. Run AOB evaluator with LLM judge configured for Watsonx Maverick
uv run evaluate \
    --trajectories /tmp/sg_trajectories \
    --scenarios /Users/wax/coding/hpml-assetopsbench-smart-grid-mcp/data/scenarios \
    --judge-model meta-llama/llama-4-maverick-17b-128e-instruct-fp8 \
    --judge-backend watsonx \
    --output /tmp/aob_eval_report.json
```

**Owner:** Alex (or whoever has Watsonx capacity).

**Acceptance:** parity report at `~/coding/AssetOpsBench/src/evaluation/adapters/parity_report.md` is updated with measured κ + agreement %. Per Phase 0 spec § Q-EVAL-PARITY: target κ ≥ 0.8 + judge-pass-classification ≥ 95%.

---

## D2 — `compute_parity` comparison script

**What:** Stand-alone Python script that takes (a) AOB judge JSON output from D1 and (b) team-side `scenario_scores.jsonl`, joins on `(run_id, scenario_id, trial_index)`, computes per-dim Boolean κ + aggregate score correlation + judge-pass classification agreement.

**Gating:** D1 output exists (need both score sources to compare).

**Skeleton location:** `~/coding/AssetOpsBench/src/evaluation/adapters/compute_parity.py` (NEW file, not yet created).

**Owner:** Whoever runs D1 — natural extension.

**Acceptance:** script outputs a Markdown table of per-dim κ values + aggregate agreement %; report writes to `results/aob_eval_parity.md` in team repo.

---

## D3 — CSV data export + `SG_DATA_DIR` documentation

**What:** The 5 processed CSVs (`asset_metadata.csv`, `sensor_readings.csv`, `failure_modes.csv`, `dga_records.csv`, `rul_labels.csv`, `fault_records.csv`) live in team-repo `data/processed/`. Phase 2 servers read them via `$SG_DATA_DIR` env var but the data isn't shipped with the AOB fork. Decide:
- **Option A:** Ship a small sample CSV bundle in `~/coding/AssetOpsBench/src/scenarios/local/sg_sample_data/` for smoke-test reproducibility (KB-scale). Full CSVs stay in HPML team repo.
- **Option B:** Document the team-repo `data/` pipeline as a prerequisite + cross-link from AOB README. AOB users who want to run SG servers must clone HPML repo to populate `$SG_DATA_DIR`.
- **Option C (heaviest):** Move the data-pipeline scripts (`data/build_*.py`, Kaggle source-dataset loaders) into AOB so AOB users can regenerate from upstream Kaggle datasets.

**Gating:** Data licensing review (Kaggle dataset terms) + Dhaval input on what AOB downstream researchers expect.

**Recommended:** Option B for immediate Phase 4; Option A if a small reproducible smoke is needed; Option C only if AOB upstream wants to own the full pipeline.

**Owner:** Alex + Dhaval.

**Acceptance:** Documented in AOB-side `docs/sg_data_provenance.md` (or equivalent); team-repo CSV provenance preserved.

---

## D4 — Live MCP transport smoke (Cell A/B equivalent against AOB-side servers)

**What:** End-to-end smoke that:
1. Populates `$SG_DATA_DIR` with team-repo CSVs (or sample bundle).
2. Starts the four AOB-side `sg-{iot,fmsr,tsfm,wo}-mcp-server` processes.
3. Runs `OpenAIAgentRunner` against `multi_01_end_to_end_fault_response` scenario through MCP transport.
4. Captures the resulting trajectory and verifies all 19 tools dispatch correctly.

**Gating:** D3 (CSV data) + LLM endpoint (Watsonx or Insomnia vLLM) + agent runtime + at least one MCP client (the AOB-side or `mcp inspect`).

**Effort:** 4-8 hr — most time is in data setup + endpoint config.

**Owner:** Alex / whoever runs D1.

**Acceptance:** AOB-side smoke reproduces (B − A) latency direction observed in team repo's `8979314_*` captures; trajectory shape validates via `evaluation.models.PersistedTrajectory`.

**Why High severity:** without this, Phase 4 upstream PR has no end-to-end proof that the port actually works; reviewers (Dhaval, IBM/AOB maintainers) will reasonably ask for it.

---

## D5 — Cross-branch scenario validation test — **RESOLVED 2026-04-29 (v2 review pass)**

**What:** `~/coding/AssetOpsBench/src/servers/smart_grid/tests/test_scenarios.py` previously used `pytest.importorskip("evaluation.models")` because the evaluation module lived on `aob/sg-evaluation-adapter` while scenarios lived on `aob/sg-domain-port` as sibling branches.

**Resolution:** v1 cross-agent review surfaced the sibling-branch issue (H1). All three branches were rebased into a linear stack post-v2: `aob/sg-evaluation-adapter` (`c7bc99e`) → `aob/sg-domain-port` (`bece2fa`) → `aob/sg-orchestration-runners` (`0892b92`). The `evaluation.models` import now resolves on the consolidated tip, and the scenario test runs without the `importorskip` skip path. Reviewer confirmation: 73/73 focused-test run on consolidated tip (`20260429_230056_ADHOC_aob-extraction-v2_RESPONSE.md`).

**Status:** Closed. The `importorskip` line in `test_scenarios.py` could be dropped as a tiny followup commit, but it does not block — it now resolves the import successfully.

---

## D6 — Team-AaT batch-mode port — **RESOLVED 2026-04-30**

**What:** Ported team-repo `scripts/aat_runner.py`'s `_main_multi` (Cell C MCP-optimized batch mode from PR `#134`) into AOB's `OpenAIAgentRunner` as a `run_batch(prompts, trials)` method (Option A from the original spec). Added `parallel_tool_calls` constructor knob (default `False`). MCP connection reuse via single `AsyncExitStack` enter/exit per batch.

**Resolution:** Branch `aob/sg-aat-batch-mode @ 6872cea` (initial port `9477bef` + v1 M1 empty-prompts guard `6872cea`) off the consolidated 3a+3b tip `0892b92`. 10 unit tests at `src/agent/openai_agent/tests/test_runner_batch.py`; `uv run pytest src/agent -q` → 177/177 green (167 prior + 10 new). Per-trial errors land in the new `AgentResult.error` field (backward-compatible default `None`) instead of aborting the batch.

**Out-of-scope vs the team-repo source (intentional):**
- Team-repo writes per-trial JSON files and `_batch_latencies.jsonl` to disk. AOB's port returns `list[AgentResult]` and lets callers persist via `observability.persist_trajectory()` if needed — file layout is a harness concern, not a runner concern.
- Team-repo enforces `mcp_mode == "optimized"` and validates `--scenarios-glob` from the CLI. AOB's port is one layer below the CLI; the AOB CLI can layer those checks separately.

**Status:** Closed. Live AOB-side smoke reproducing the team's (B − C) latency recovery on a 2-scenario × 3-trial run is still a Phase 4 / paper-final concern (gated on Watsonx/Insomnia access — see D1/D4).

---

## D7 — Smart-Grid-specific repair logic (NOT a deferral; out of scope by design)

**What:** Sensor-task repair (`repair_sensor_task_text`), invalid-sensor skip (`should_skip_invalid_sensor_step`), DGA cross-domain rejection, sensor ID alias map (`SENSOR_ALIAS_MAP`). All in team-repo `scripts/orchestration_utils.py`.

**Why it stays in team repo:** these helpers encode Smart-Grid-specific knowledge (which sensor IDs are valid, which fault types belong to FMSR vs IoT, how to canonicalize "winding_temp_c" vs "winding_temp"). They don't generalize to AOB's other 4 domains.

**Owner:** N/A — stays as customization layer in HPML team repo.

**Acceptance:** N/A — explicit non-goal of Phase 3.

---

## D8 — Eval rubric reconciliation upstream

**What:** Team's `scripts/judge_trajectory.py` and AOB's `src/evaluation/graders/llm_judge.py` use IDENTICAL rubric keys (per Phase 1 static-analysis parity report) but DIFFERENT aggregate score formulas:
- Team: `score_6d = (count_true_first_5 + (1 if hallucinations is False else 0)) / 6`
- AOB: `score = (count_true_first_5 / 5.0) - (0.2 if hallucinations is True)`

Two reconciliation paths:
- **(a)** Port team's even-weighted-6 formula upstream as a `score_6d` mode in AOB's LLM judge. Preserves our headline numbers (Z+SA 0.833, etc.).
- **(b)** Adopt AOB's formula in team repo and re-score the 36 canonical trials. Team's headline numbers shift slightly but stay directionally identical.

**Gating:** Dhaval preference (does AOB upstream want a `score_6d` knob?).

**Effort:** ~2-4 hr for the upstream PR if (a); ~1-2 hr for re-scoring if (b).

**Owner:** Alex + Dhaval.

**Acceptance:** team-repo paper headline matches AOB-published numbers (whichever direction).

---

## D9 — Upstream PR(s) to IBM/AssetOpsBench

**What:** Per Q-UPSTREAM-PR-CADENCE in spec — hybrid cadence:
- PR 1: Phase 1 evaluation adapter (`feat/evaluation-module` adoption + SG adapter). Standalone PR; helps any AOB user.
- PR 2 (combined): Phase 2 Smart Grid 7th domain + Phase 3a/3b orchestration runners + (optionally) 3c team-AaT batch.

**Gating:**
- AOB `feat/evaluation-module` upstream merge (Phase 1 PR depends on it landing first OR carries the diff inline).
- Dhaval coordination per Q-DHAVAL-COORDINATION (informal ack on Q-NAMING + Q-UPSTREAM-PR-CADENCE; explicit gate for Phase 4 PRs).
- D4 live smoke evidence (reviewers will want it).
- Authorship attribution decision (per spec § Authorship — Co-Authored-By trailers vs CONTRIBUTORS.md block; humans only per CLAUDE.md hard rule 3).

**Effort:** 1-2 weeks calendar time (review iteration + Dhaval bandwidth + IBM/AOB CI).

**Owner:** Alex.

**Acceptance:** PR 1 merged to AOB main; PR 2 merged to AOB main; Smart Grid Bench is a first-class AOB domain.

---

## D10 — AOB README delta — Smart Grid 7th domain claim count

**What:** AOB main README currently says "4 domain-specific agents". Phase 2 README delta (currently in `aob/sg-domain-port` branch) says "4 ... plus an optional Smart Grid 7th-domain add-on" — but other AOB upstream branches (e.g., `feat/vibration-mcp-server`) may bump the official count to 5/6/7 between now and Phase 4 PR-merge time.

**Gating:** D9 timing — final count depends on what AOB main says when our PR opens.

**Effort:** <1 hr — adjust the count text + cross-references.

**Owner:** Whoever opens the Phase 2/3 combined PR.

**Acceptance:** README delta in our PR doesn't over-claim or under-claim relative to AOB main at merge time.

---

## D11 — Per-cell `REPLAY_RUNNER` config knob

**What:** Currently `run_experiment.sh:1130` skips replay for non-AaT cells. If cell-aware replay traces become useful (per `docs/archive/replay_phase_analysis.md` § Implementation sketch), add an opt-in `REPLAY_RUNNER=match-cell|aat|none` config knob so PE/Verified PE cells can produce per-cell-representative torch traces.

**Gating:** None — design clarity question; nobody is currently asking for cell-aware replay traces.

**Effort:** 4-6 hr — needs MCP server lifecycle integration for non-AaT runners.

**Owner:** Aaron (profiling lane).

**Acceptance:** opt-in knob lands; default behaviour unchanged (replay skipped for non-AaT).

**Status:** already pinned in `pm/backlog.md` as a Future item; not a true AOB-extraction deferral.

---

## D12 — Final 5×6 canonical re-run

**What:** Once team agrees on final scenario set (likely 6 scenarios: 2 multi + 1 each from fmsr/iot/tsfm/wo) and trial count is bumped to 5, re-run all Experiment 1 + Experiment 2 cells (A, B, C, Y, Y+SA, Z, Z+SA) at 5×6 from a clean slate. Replaces the current 3×2 first-canonical snapshots.

**Gating:** Team scenario-set decision (per Apr 28 team call follow-up) + Insomnia capacity.

**Effort:** 1-2 days Slurm time (5 trials × 6 scenarios × 7 cells ≈ ~30 hr aggregate compute on a single A6000).

**Owner:** Aaron + Akshat for capture; Alex for analysis.

**Acceptance:** report-final figures regenerate cleanly from 5×6 captures.

**Status:** already pinned in `pm/backlog.md`; paper-final not Phase-4 dependency, but D4 smoke and D8 rubric reconciliation should both happen first if final paper numbers depend on them.

---

## Resumption checklist (when starting a fresh session)

1. Read this file + [aob-extraction.md](aob-extraction.md) + [aob-extraction_spec.md](aob-extraction_spec.md).
2. Run `git status` in BOTH repos:
   - team repo `~/coding/hpml-assetopsbench-smart-grid-mcp` (root `main`)
   - AOB fork `~/coding/AssetOpsBench` (check current branch — `aob/sg-{evaluation-adapter,domain-port,orchestration-runners}`)
3. Verify last good state: `git log --oneline -3` on each branch.
4. For ANY deferred item that needs LLM access, check Watsonx/Insomnia status before starting.
5. Update `pm/backlog.md` AOB-extraction pin and the relevant phase status block in `docs/archive/aob-extraction.md` whenever a deferral resolves.

---

## Cross-references

- Plan: [aob-extraction.md](aob-extraction.md)
- Spec: [aob-extraction_spec.md](aob-extraction_spec.md)
- Phase 1 parity report: `~/coding/AssetOpsBench/src/evaluation/adapters/parity_report.md` (on `aob/sg-evaluation-adapter` branch)
- Replay-phase analysis (separate but related): `docs/archive/replay_phase_analysis.md`
- Y-baseline 3.12 disclosure (separate but related): `docs/methods_python_version_disclosure.md`
- Backlog pins: `pm/backlog.md` lines 5-9 (final 5×6 re-run + AOB-extraction-plan + replay knob + replay analysis)
