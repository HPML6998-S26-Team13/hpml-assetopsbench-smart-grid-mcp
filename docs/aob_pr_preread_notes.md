# AOB #27 Pre-read Notes — IBM Upstream PR Body Pair Session

*For Saturday May 3, ~10 AM ET pair session with Alex.*
*Tanisha's role: "paper-framing voice" — fill in Why sections; Alex drives technical specifics.*
*Owner: Tanisha Rathod | Created: 2026-05-01*

---

## What we're writing

Two PR body drafts for IBM/AssetOpsBench (saved in `docs/upstream_pr_drafts/`):

1. **PR 1** — Phase 1 evaluation adapter (standalone): maps SmartGridBench trajectory JSON → AOB `PersistedTrajectory` interface, enabling AOB's LLM-judge module to score our runs.
2. **PR 2** — Phases 2+3 combined: Smart Grid 7th-domain MCP servers + scenarios + orchestration runners.

---

## Context Alex will bring (technical); Tanisha's prep (framing)

### PR 1 — Why framing to prepare

**Central argument:** Using AOB's evaluation module rather than maintaining `scripts/judge_trajectory.py` in the team repo avoids drift — a shared judge rubric means Smart Grid Bench results can be directly compared against all 6 existing AOB domains without rubric translation.

**Supporting points to articulate:**
- AOB already has a vetted 6-criterion LLM-as-judge rubric used across all domains; building parallel plumbing creates a maintenance burden and narrows comparability
- Phase 1 adapter is standalone value: any future Smart Grid contribution or third-party fork benefits from the evaluation path without needing the full domain port
- Parity threshold we set: κ ≥ 0.8 + ≥ 95% judge-pass classification agreement (per spec § Q-EVAL-PARITY) — principled bar, not hand-wavy

**Exclusions to frame positively (not defensively):**
- No class experiment captures — keeps IBM's review scope narrow
- No Slurm/Insomnia operational docs — cluster-specific, not upstream-useful
- No proprietary data — fully reproducible from `data/generate_synthetic.py`

---

### PR 2 — Why framing to prepare

**Central argument:** Power transformer maintenance is a high-value asset-ops use case the existing 6 AOB domains don't cover. Adding it as a 7th domain extends AOB's coverage into grid infrastructure — a distinct industrial setting with published IEEE/IEC standards for ground truth.

**Supporting points to articulate:**
- **Why transformers specifically:** DGA dissolved gas analysis has a standardized fault classification method (IEC 60599:2022 Rogers Ratio) that produces machine-verifiable ground truth — exactly what a benchmark needs. Other industrial domains often lack this.
- **Why now:** The IEC encoding (PR #149, merged) and scenario set (21 validated, targeting 30) are already exercised by 9 experimental cells across 2 orchestration families. Results are in. The domain port is ready, not speculative.
- **Why MCP transport:** AOB's current ReAct/direct-function path doesn't expose the latency cost of the standardization layer. Our Cell A vs B comparison (+0.94s p50 / +1.20s mean MCP overhead from experiment_matrix_summary.csv, 9 cells of orchestration data) is the first published measurement of this tradeoff for industrial maintenance agents — directly relevant to any team considering MCP for enterprise deployment.
- **Why orchestration comparison matters for IBM:** Dhaval's own framing: Plan-Execute remains the preferred structured enterprise baseline (predictable resources, auditability). Verified PE + Self-Ask hitting 83.3% judge pass vs 33.3% for bare MCP baseline is the kind of number a practitioner can act on.

**Key numbers to have ready (from the experiment matrix):**
- 19 tools across 4 servers (IoT 4, FMSR 5, TSFM 4, WO 6)
- 21 validated hand-crafted scenarios, 5 domain types, 3 difficulty levels
- ZS (Verified PE + Self-Ask): 0.833 judge score, 83.3% pass rate — best condition
- AT-I (direct) vs AT-M (MCP): 12.15s vs 13.09s (p50) — +7.8% p50 overhead; mean overhead +1.20s (+9.8%)
- Optimized serving (INT8/BF16 KV): 53% latency reduction in AaT cells

**Deferred items to explicitly call out (not hide):**
- D1: Live LLM-judge parity run not yet complete (gated on WatsonX capacity for the adapter comparison run)
- D3: Processed CSVs not shipped — regenerable via `data/generate_synthetic.py`
- D4: Live MCP smoke against AOB-side servers pending D3 resolution
- Final canonical run (5 trials/cell) pending scenario set finalization

---

## What's already done in the AOB fork (phases complete)

| Phase | Status | Branch |
|---|---|---|
| Phase 0 — Design decisions | Complete | — |
| Phase 1 — Eval adapter | Code complete | `aob/sg-evaluation-adapter` |
| Phase 2 — Smart Grid domain port | Complete | `aob/sg-domain-port` |
| Phase 3a — PE + Self-Ask runners | Complete | `aob/sg-orchestration-runners` |
| Phase 3b — Verified PE runners | Complete | `aob/sg-orchestration-runners` |
| Phase 3c — AaT batch mode | Complete | `aob/sg-aat-batch-mode` |
| Phase 4 — IBM upstream PRs | **In progress** (this task) | — |

---

## Session agenda (suggested)

1. **(Tanisha pre-session, tonight):** Read `docs/plans/aob-extraction.md`, `aob-extraction_spec.md`, `aob-extraction_deferred.md`. These notes cover what you need.
2. **(Pair session start):** Alex walks through Phase 1/2/3 branch state and what's actually in each PR body template.
3. **(Tanisha's turns):** Fill TODO blocks in "Why" paragraphs for both bodies using the framing points above.
4. **(Together):** Edit the Deferred follow-up sections using the D1–D12 registry in `aob-extraction_deferred.md`.
5. **(Commit target):** Save both drafts to `docs/upstream_pr_drafts/pr1_evaluation_adapter.md` and `docs/upstream_pr_drafts/pr2_smart_grid_domain.md` in the AOB fork.

---

## Files to skim before the session (priority order)

1. `docs/plans/aob-extraction.md` — phase summary + what's done
2. `docs/plans/aob-extraction_spec.md` — design decisions locked in Phase 0
3. `docs/plans/aob-extraction_deferred.md` — D1–D12 deferred items (cite in PR bodies)
4. `docs/methodology_fact_pack.md` — numbers and facts for the Why sections *(this repo)*
5. AOB issue #27 template — the two PR body templates are already written; you're filling TODOs
