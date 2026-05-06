# Content brief — Scenarios + Eval + Judge

*Last updated: 2026-05-06. Owner: Akshat (issue #42). Audience: Alex, for the paper's scenarios + eval sections.*

This is a 1-page fact pack. Numbers are reproducible from the artifacts cited in each bullet. Cross-checked against `evidence_registry.csv` (PR #188) and `scenario_scores.jsonl` on `team13/main@87a9b77` (post-PR191 disposition merge).

## Scenarios

- **Canonical corpus:** 31 hand-authored Smart Grid scenarios at `data/scenarios/*.json`. Validated by `python data/scenarios/validate_scenarios.py` (`Validation passed for 31 scenario files and 5 negative fixtures`). Closes HPML #15 (15+ floor) and HPML #33 (30+ stretch).
- **Pending promotion:** PR #195 promotes 5 `accept_with_edits` generated rows into canonical (`SGT-031..SGT-035`). Validator passes 36+5 once #195 lands. Brief assumes pre-merge state of 31; bump to 36 on merge.
- **Negative fixtures:** 5 at `data/scenarios/negative_checks/*.json` covering single-/multi-domain mismatches, missing-domain coverage, and unknown-tool rejection.
- **Domain mix (current 31):** FMSR 7 (incl. 1 AOB-style), IoT 6, Multi 8, TSFM 4, WO 6.
- **Asset universe:** T-001..T-020 (`data/processed/asset_metadata.csv`). All scenario `asset_id`s validate against this list.
- **Tool universe:** 19 canonical MCP tools across IoT/FMSR/TSFM/WO domains, defined in `data/scenarios/validate_scenarios.py:CANONICAL_TOOLS`. Validator rejects unknown tools and cross-domain tool use in single-domain scenarios.

## Generated scenarios (PS B)

- **Three batches:** `data/scenarios/generated/{first_review_20260502, first_review_20260503, v02_first_review_20260505}/`. 5 SGT-GEN-* records each. Total **15 generated candidates** validated under the methodology in `docs/ps_b_evaluation_methodology.md`.
- **Disposition outcome (PR #191, merged):** machine-readable table at `data/scenarios/generated/disposition_2026-05-06.csv`. **5 `accept_with_edits` / 10 `reject_duplicate` / 0 `reject_unusable` / 0 `reject_structural`.** Both methodology bars (≥70% accept-or-edits; <20% reject_duplicate) fail at 33% / 67%; no batch publishes as benchmark-ready, but the 5 `accept_with_edits` rows are bounded-edit candidates.
- **Promotion path:** PR #195 ports the 5 with provenance retained (source path, disposition CSV reference, applied-edits list, and reviewer-selected comparator) under canonical names `fmsr_07`, `iot_07`, `iot_08`, `wo_07`, `iot_09`.
- **#55 stretch (50+):** still short at 36 even after PR #195 — needs ≥14 hand-crafted companions or an explicit defer per the `post-class-defer` label.

## Eval harness

- **Orchestration paths:** `plan_execute`, `verified_pe`, `agent_as_tool`. Cell mapping per `evidence_registry.csv`:
  - **Direct/MCP path** (Cells A/B/C/D + 70B variants) — Agent-as-Tool with direct or MCP calls.
  - **PE family** (Y/YS/Z/ZS + Y/YS/Z/ZS-70B + ZSD + Y/YS/ZS-TP, follow-on/extra) — plan-execute + verified-PE + Self-Ask ablations.
- **Models judged:** `openai/Llama-3.1-8B-Instruct` (1,835 paper-grade rows), `watsonx/meta-llama/llama-3-3-70b-instruct` (435), `openai/Llama-3.1-8B-Instruct-int8` (150).
- **Pipeline entry:** `scripts/run_experiment.sh <config.env>` (Slurm-aware on Insomnia, Slurm-skipped on GCP). Configs in `configs/`. Resumable via `SMARTGRID_RUN_ID` + `SMARTGRID_RESUME` (PR #170).
- **Artifacts per run:** `benchmarks/cell_<X>/raw/<run-id>/` with `meta.json`, `latencies.jsonl`, `harness.log`, `vllm.log` (if `LAUNCH_VLLM=1`), and one `<scenario>_t<n>.json` per scenario × trial. WandB run URL stamped in `meta.json` when `ENABLE_WANDB=1`.
- **Compute provenance:** `gpu_type` in `summary.json` records Insomnia A6000 vs GCP A100 vs other (PR #145). Canonical 8B rows on Insomnia A6000 (Apr 26-28) + GCP A100 (`gcp_a100_final_20260503`).

## Judge

- **Default judge model:** `watsonx/meta-llama/llama-4-maverick-17b-128e-instruct-fp8` (overridable with `--judge-model`). Pipeline: `scripts/judge_trajectory.py` -> `results/metrics/scenario_scores.jsonl` (one JSON per line; schema `v1`).
- **Six rubric dimensions** (booleans; True = good except `dim_hallucinations` where False = good): `task_completion`, `data_retrieval_accuracy`, `agent_sequence_correct`, `clarity_and_justification`, `generalized_result_verification`, `hallucinations`. Schema in `docs/judge_schema.md`.
- **Aggregate:** `score_6d = (sum of 5 True booleans + NOT hallucinations) / 6`, range [0, 1]. Pass threshold 0.6 (≥4/6).
- **Audit logs:** `results/judge_logs/<run_name>/<scenario_id>_runNN_judge_log.json` — full prompt + response per call when `--log-dir` is set.
- **Manual sanity audit:** `results/metrics/manual_judge_audit.csv` — 12 stratified mitigation trajectories with 12/12 judge/manual pass-label agreement (judge-calibration check, not paper-grade mitigation evidence).

## Evidence numbers (cite in §Eval and §Failure analysis)

- **Total judge rows:** 3,716 in `results/metrics/scenario_scores.jsonl`.
- **Paper-grade subset:** 2,420 rows (37 paper-eligible run_names per `evidence_registry.csv`; `include_in_paper=true`).
- **Paper-grade failures:** 1,276 (`pass=false` ↔ `score_6d < 0.6` align perfectly). Programmatically classified in PR #193's `results/metrics/failure_taxonomy_current.csv`. Auto-label distribution: `low_task_completion=944`, `low_data_retrieval_accuracy=182`, `low_agent_sequence_correct=78`, `low_generalized_result_verification=72`. (`low_hallucinations` and `low_clarity_and_justification` don't appear as the dominant label because they only co-occur with earlier-priority dim failures; they're visible in `failed_dims`.)
- **Failed-dim co-occurrence:** failure rows fail 2-6 dims at once (4-dim mode is largest at 469 rows). `failed_dims` column in `failure_taxonomy_current.csv` carries the full pattern per row.
- **Hand audit (#194):** 46-row stratified sample (one per non-empty (cell, auto-label) stratum, deterministic seed) flagged for manual review. Owner TBD.
- **Excluded rows:** 1,296 (3,716 − 2,420). Reasons in `evidence_registry.csv:reason` — most common: post-PR180 cohort superseded by post-PR175 clean floor (28 run_names); legacy final-six A100 matrix (11); pre-PR173/final-six mitigation diagnostic (8). All preserved (`status=superseded` / `diagnostic` / `invalid_tooling`) rather than expunged.

## Safe paper claims

- "31 hand-authored validated scenarios across 5 task domains" — sourced from validator output. (Bump to 36 after PR #195.)
- "All 31 scenarios passed schema validation, asset-id resolution, and tool-canonicality checks before inclusion."
- "2,420 LLM-judge rows form the paper-grade evaluation cohort, drawn from a larger 3,716-row evaluation pool with 1,296 rows explicitly tracked as superseded or diagnostic."
- "Of 1,276 paper-grade failures, 74% present `task_completion` as the highest-priority failed rubric dimension, with 4-5 dim co-occurring failures most common." (Source: `failure_taxonomy_current.csv` after PR #193 lands.)
- "An auto-generated batch of 15 scenarios produced 5 bounded-edit promotions and 10 near-duplicate rejections under the methodology in `docs/ps_b_evaluation_methodology.md`." (PR #191 disposition; PR #195 promotion.)

## Anti-claims (do not state in paper)

- ❌ "≥70% acceptance" on the generated batch — the methodology bar fails at 33%.
- ❌ "Manual hand audit confirms the auto-taxonomy on every paper-grade failure" — only the 46-row stratified sample + paper-cited rows are slated for manual review (#194).
- ❌ "All 19 MCP tools have been exercised across paper-grade rows" — no row-level coverage map yet; needs trajectory-walk to confirm.
- ❌ "50+ scenarios" — corpus is 31 (36 after #195). #55 stretch deferred.

## Pointers (for fact-checking this brief)

- Validator + canonical scenarios: `data/scenarios/validate_scenarios.py`, `data/scenarios/*.json`, `data/scenarios/README.md`
- PS B / generated: `data/scenarios/generated/README.md`, `data/scenarios/generated/disposition_2026-05-06.csv`, `docs/ps_b_evaluation_methodology.md`
- Evidence registry: `docs/evidence_registry.md`, `results/metrics/evidence_registry.csv`
- Judge schema: `docs/judge_schema.md`, `scripts/judge_trajectory.py`, `results/metrics/scenario_scores.jsonl`
- Failure inventory: `results/metrics/failure_taxonomy_current.csv` + `scripts/build_failure_taxonomy.py` (PR #193)
- Runbook: `docs/runbook.md` (infra), `docs/eval_harness_readme.md` (eval harness side, owns #67)
