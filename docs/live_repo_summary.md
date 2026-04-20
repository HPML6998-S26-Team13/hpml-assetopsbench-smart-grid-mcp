# Live Repo Summary — 48h Handoff

*Last updated: 2026-04-21 ~02:35 EDT*
*Window covered: 2026-04-19 00:00 EDT → 2026-04-21 02:35 EDT*
*Audience: incoming coding agent (Claude or Codex). Read this first, then jump to the paths in §8.*

> Legend: **[V]** verified from code/git/GH • **[I]** inference from artifacts • **[?]** unresolved / open question.

---

## 1. Executive Snapshot

- **[V]** `team13/main` now includes PR `#115` (`de11fd7`), PR `#119` (`3a3004f`), PR `#113` (`01fa799`), PR `#114` (`152627b`), and PR `#120` (`b08500e`). This docs sync keeps the planning and handoff surfaces aligned with that merged state.
- **[V]** Big Apr-20 pushes to `team13/main`: `#118` (reproducible `notebooks/01_data_exploration.ipynb`) and `#116` (PS B methodology + NeurIPS abstract outline) both merged. Then a rapid 5-commit infra series (`01043c5` → `b0f0d40`): profiling↔WandB linkage, Experiment 1 (Cell A/B/C) scaffolding, canonical `docs/runbook.md`, `docs/gcp_fallback.md`, and the #111 Insomnia reconciliation.
- **[V]** Issues `#23` (Verified PE) and `#24` (PE + Self-Ask hook) are now **closed** via merged PR `#119`. The authoritative clean proof snapshots are `8857842_pe_self_ask_mcp_baseline_smoke` and `8857843_verified_pe_mcp_baseline_smoke`, with committed `config.json` / `summary.json` snapshots on `team13/main` and raw logs archived on Insomnia + W&B.
- **[V]** PR `#115` (tanisha/server-hardening) is merged. PR `#119` then stacked the repo-local Verified PE / PE + Self-Ask runners on top of that hardened serve path.
- **[V]** `#111` (Insomnia script/docs reconciliation) should now be read as a post-merge cleanup/confirmation item: keep Aaron's setup improvements, merge the newer proven stack direction forward, do one clean proof run on `main`, then close. Item 9 is effectively moving under `#25`, not gating `#111`.
- **[V]** Experiment 1 (MCP overhead, `#25`): config scaffolds (`configs/aat_{direct,mcp_baseline,mcp_optimized}.env`), `mcp_servers/direct_adapter.py`, and profiling↔WandB plumbing are in place. **The Cell A (ReAct / Agent-as-Tool) runner is the gating missing piece.**
- **[V]** PR `#120` is now merged. The Notebook 02/03 consumer-side analysis scaffolds are on canonical history, while `#26` and `#32` correctly remain open because the real Cell A/B/C and B/Y/Z captures still need to land.
- **[V]** The useful runtime lesson from today is that the repo-local PE family should treat AssetOpsBench as a **library slice**, not as a monolithic package entrypoint: import the actual `plan_execute` surfaces directly, keep the dependency surface to what that path really needs (`litellm`, `mcp[cli]`, vLLM/OpenAI-compatible serving), and avoid package-level imports that drag in unrelated SDKs.
- **[V]** Open PR status has simplified: `#112` is the only still-relevant older open PR in this lane and still carries `CHANGES_REQUESTED`. `#113`, `#114`, and `#120` are all merged.

---

## 2. Recent Timeline (reverse chronological; only significant events)

All times in EDT. Hashes as of 2026-04-21 02:35.

| When (EDT) | Ref | Where | Why it matters |
|---|---|---|---|
| 2026-04-21 ~02:27 | merge `b08500e` | `team13/main` | PR `#120` merged. Notebook 02/03 analysis scaffolds for `#26/#32` are now on canonical history; the issues stay open because execution artifacts are still pending. |
| 2026-04-21 ~02:10 | merge `152627b` | `team13/main` | PR `#114` merged. Maverick judge audit logs and repo-relative path fixes are now on canonical history; `#20` is closed with a rollout note. |
| 2026-04-21 ~02:09 | merge `01fa799` | `team13/main` | PR `#113` merged. Canonical harness smoke proof, six-dimension judge scoring, and the first Smart Grid trajectory artifact are now on `main`; `#3`, `#17`, and `#18` are closed with rollout notes. |
| 2026-04-21 ~01:58 | merge `3a3004f` | `team13/main` | PR `#119` merged. Repo-local Verified PE + PE + Self-Ask runners are now on canonical history; issues `#23` and `#24` are closed. |
| 2026-04-21 ~00:25 | run `8857842_pe_self_ask_mcp_baseline_smoke` | `codex-fnd/issue-23-24-verified-pe-self-ask` | PE + Self-Ask clean proof snapshot on rebased SHA `3a03ab8`; later committed into-tree as `benchmarks/cell_Y_plan_execute/{config,summary}.json`. |
| 2026-04-21 ~00:19 | run `8857843_verified_pe_mcp_baseline_smoke` | `codex-fnd/issue-23-24-verified-pe-self-ask` | Verified PE clean proof snapshot on rebased SHA `3a03ab8`; later committed into-tree as `benchmarks/cell_Z_hybrid/{config,summary}.json`. |
| 2026-04-21 ~00:05 | merge `de11fd7` | `team13/main` | PR `#115` merged. Server hardening, path validation, and Insomnia-serving fixes are now on canonical mainline history. |
| 2026-04-20 ~21:35 | commit `dc61c5d` | `codex-fnd/issue-23-24-verified-pe-self-ask` | Fixes the remaining Verified PE smoke blocker by compacting verifier payloads and degrading verifier exceptions to `continue` instead of killing the scenario. Direct response to the `8854785` context-window failure. |
| 2026-04-20 ~21:20 | run `8854785_verified_pe_mcp_baseline_smoke` | `codex-fnd/issue-23-24-verified-pe-self-ask` | Verified PE improved to `1/2` on the latest pushed branch state. The remaining failed scenario was not a planner/tool-routing bug; it died when the verifier prompt exceeded the Llama-3.1-8B 32k context window after a huge sensor-readings payload was recycled into verification. |
| 2026-04-20 ~21:15 | run `8854783_pe_self_ask_mcp_baseline_smoke` | `codex-fnd/issue-23-24-verified-pe-self-ask` | PE + Self-Ask reached `2/2` on the two-scenario smoke slice. This is the first fully clean live smoke result on the repo-local AOB branch. |
| 2026-04-21 ~00:00 | PR `#115` approved | GH | Tanisha's server-hardening PR cleared review (reviewDecision: `APPROVED`, mergeable: `CLEAN`). Alex dismissed the prior `CHANGES_REQUESTED`; bot approval via "Manually auto-approve PR" workflow (after org setting `can_approve_pull_request_reviews` was flipped to `true`). Merged minutes later as `de11fd7`. |
| 2026-04-20 ~20:40 | branch `codex-fnd/issue-26-32-analysis-scaffold` | `team13/*` | Notebook 02/03 analysis scaffold lane was pushed and later updated to `4ed9bfa`, then opened as PR `#120`. |
| 2026-04-20 19:30 | commit `e4e4036` | `tanisha/server-hardening` | Fixes the latest two review findings on PR `#115`: served-model-name consistency and the profiling README's WandB linkage recipe. |
| 2026-04-20 ~19:20 | run `8853391_verified_pe_mcp_baseline_smoke` | `codex-fnd/issue-23-24-verified-pe-self-ask` | Verified PE rerun fails honestly (`0/2`) without the earlier suffix-replan crash. Remaining failures are real planner/tool-selection errors. |
| 2026-04-20 ~18:40 | run `8853022_pe_self_ask_mcp_baseline_smoke` | `codex-fnd/issue-23-24-verified-pe-self-ask` | PE + Self-Ask rerun also fails honestly (`0/2`), confirming the runner now surfaces tool errors instead of counting them as success. |
| 2026-04-20 18:59 | `#111` comment from `afan2g` | team13 issue | Aaron closes out items 1-8 + 10 of the Insomnia reconciliation, leaves item 9 to Alex, recommends issue stay open until a fresh end-to-end run passes. |
| 2026-04-20 14:59 | commit `b0f0d40` | `team13/main` | Ships the Insomnia reconciliation (`SETUP_MODE=all\|venv\|model`, `MODEL_REVISION` default = `main`, torch 2.6.0 pin, `short` partition/QoS, hf-hub CLI migration, submit-dir warnings). |
| 2026-04-20 14:29 | commit `77fc11d` | `team13/main` | `docs/gcp_fallback.md` — mechanically complete but **not yet end-to-end validated**. Emergency-only fallback; Insomnia-first remains the policy. |
| 2026-04-20 14:25 | commit `f2f3083` | `team13/main` | `docs/runbook.md` becomes the canonical top-level infra runbook; `insomnia_runbook.md` is now the cluster-specific companion. |
| 2026-04-20 14:20 | commit `91cb21e` | `team13/main` | Experiment 1 Cell A/B/C config skeletons + `mcp_servers/direct_adapter.py` (in-process shim for the 21 `@mcp.tool()` fns). Cell A ReAct runner still TODO. |
| 2026-04-20 14:13 | commit `01043c5` | `team13/main` | Profiling capture wrappers now back-link to the benchmark WandB run via `BENCHMARK_RUN_DIR`. |
| 2026-04-20 14:01 | commit `e15d856` | **local root only** | Adds `pm/backlog.md` entry to explore `claude_agent_sdk` (why AssetOpsBench imports it; should we mirror). **Not on any remote.** |
| 2026-04-20 08:19 UTC (~04:19 EDT) | PR `#115` review | GH | Alex's `8c26e3b` re-review: 0 Crit/High, 1 Med (NCCL env vars set unconditionally), 2 Low. Identifies merge conflict + missing CI run as non-code blockers. |
| 2026-04-20 05:37 | commit `5b719f4` | `codex-fnd/issue-23-24-verified-pe-self-ask` | Initial `#23` / `#24` runner landing: Verified PE + Self-Ask PE runners, example configs, docs, `docs/governance/model_registry.yaml`. Worktree: `codex-worktrees/codex-fnd-issues-23-24-verified-pe-self-ask/`. |
| 2026-04-20 05:22 | commit `0fea453` | `team13/main` | Project board reset: dates rolled to 2026-04-20/21, spillover moved to W4, review dir rename to `review/{codex,claude,local}-prompts/`. |
| 2026-04-20 05:12 | commit `e5a3943` | `codex-fnd/issue-26-32-analysis-scaffold` | Scaffolds `#26` (Notebook 02 latency analysis) and `#32` (Experiment 2) analysis lanes. |
| 2026-04-20 03:59 | PR `#118` merged | GH | `notebooks/01_data_exploration.ipynb` replaces the static smoke-test image; adds `results/` overview CSVs + figures. Closed `#117`. |
| 2026-04-20 03:41 | commit `8c26e3b` | `tanisha/server-hardening` | Addresses Alex's pre-merge review on PR `#115` (float coercion in DGA, WO WO-id + datetime UTC, iot error shape, long-context vLLM + test lock). |
| 2026-04-20 02:05 | PR `#116` merged | GH | `docs/ps_b_evaluation_methodology.md` + `docs/neurips_abstract_outline.md` (closes `#77`). |
| 2026-04-19 08:24 | commit `42e8ecc` | `origin/main` | Review dir renamed to the cross-agent convention (`review/<receiver>-prompts/`). |
| 2026-04-19 00:31 | commit `3f50c2c` | `origin/main` | Reframed `#23` from "Hybrid" → verifier-gated PE (`Plan-Execute-Verify-Replan`). Core comparison stays AaT vs PE; #23 is the optional third method. |
| 2026-04-18 23:19 | commit `f8ab65f` | `origin/main` | Apr-16 meeting audit sync (meeting notes, Apr-21/Apr-28 call prep, execution/synopsis/orchestration docs aligned). |

---

## 3. Current Technical State

### Remotes
- **`team13`** (`HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp`): shared team repo. `main` HEAD = `b08500e` (PR `#120` merged on top of `#114`, `#113`, `#119`, and `#115`).
- **`origin`** (`eggrollofchaos/hpml-assetopsbench-smart-grid-mcp`): Alex's fork. It should mirror the merged team-repo state for shared docs/governance updates unless there is an intentional divergence.
- Local root `main` is the staging point for small docs/governance follow-ups before they are synced to both remotes.

### Orchestration (`docs/orchestration_wiring.md`, `docs/experiment1_capture_plan.md`)
- **Plan-Execute (PE) on Smart Grid MCP servers is the one committed end-to-end runnable path** (on `team13/main`): `scripts/run_experiment.sh` → AssetOpsBench `plan-execute` CLI with `iot/fmsr/tsfm/wo` server overrides → WandB.
- **Agent-as-Tool (AaT)** infra is *partially* wired: config skeletons + `direct_adapter.py` exist; Cell A ReAct loop is still pseudocode in `docs/experiment1_capture_plan.md`. Cells B and C are planned to reuse the same loop with different tool dispatchers.
- **Verified PE (`#23`) and Self-Ask PE (`#24`)** are now merged on `team13/main` via PR `#119`. The live proof surface is split intentionally: committed `config.json` / `summary.json` snapshots in-tree, with raw logs and per-scenario JSONs archived off-repo on Insomnia and mirrored in W&B.
- **Notebook 02 / Notebook 03 analysis scaffolds** are now also merged on `team13/main` via PR `#120`, so the consumer-side parsing and preflight lane for `#26/#32` is canonical even though the real capture sets are still missing.
- **Hybrid** is deferred / future-work scope.

### Runtime & model stack (truth as of current `team13/main`, `b08500e`)
- Primary local model: **Llama-3.1-8B-Instruct** served by **vLLM 0.19.0** on Insomnia A6000 (pins in `requirements-insomnia.txt`: `torch==2.10.0`, `transformers==4.57.6`, `huggingface-hub==0.36.2`). **[V]**
- Serve script: `scripts/vllm_serve.sh` binds `--host 127.0.0.1`, `--served-model-name Llama-3.1-8B-Instruct`, `--max-model-len 32768`; Insomnia fabric overrides (`NCCL_SOCKET_IFNAME=eth0`, `NCCL_IB_DISABLE=1`) still applied unconditionally — flagged as PR `#115` Medium.
- `docs/governance/model_registry.yaml` is now on `team13/main`, so the model-ID / served-name / revision-contract story has a real canonical doc instead of living only in branch-local scripts.
- Notebooks: `notebooks/01_data_exploration.ipynb` (new) is the canonical reproducible dataset exploration; earlier static `docs/dataset_visualization.png` is now historical only.
- Judge model: Maverick-17B via WatsonX (see PR `#114` audit log work).
- GCP fallback: mechanically documented in `docs/gcp_fallback.md` but **unvalidated**; first real GCP execution will be a shakedown.

### Draft — distilled Apr-20 AOB / LiteLLM smoke lessons
- **Treat AssetOpsBench as a library slice, not a monolith.** For the repo-local PE family, the reliable path is to import the specific `plan_execute` pieces directly rather than package-level `__init__` surfaces that drag in unrelated runtime dependencies and obscure the actual execution path.
- **LiteLLM is the real adapter boundary for the local-Llama path.** The working chain is: repo-local runner → AOB LiteLLM client → OpenAI-compatible local vLLM server. The most important correctness checks were therefore model-name alignment, `/v1/models` validation, and prompt-size discipline, not exotic AOB internals.
- **The minimal dependency story is narrower than the whole AOB repo suggests.** For the repo-local PE path we actually exercised, the important external pieces were `litellm`, `mcp[cli]`, and the local vLLM stack. We did not need to mirror every AOB extra package just to run PE / Verified PE / Self-Ask PE.
- **Live MCP tool schemas matter.** Pulling tool names and signatures from the actual MCP servers, then adding planner guardrails / runtime repair on top, was much more effective than treating the planner prompt as a static generic interface description.
- **Do not recycle raw tool payloads back into verifier/planner prompts.** The remaining Verified PE failure after the orchestration fixes was a pure prompt-budget bug: one giant `get_sensor_readings` blob pushed verification over the 32k context window. Response compaction is part of the runner contract now, not an optional cleanup.
- **Tanisha's `#58/#115` work and today's `#23/#24` work are on the same general LiteLLM/vLLM lane.** Her branch proved the benchmark-facing self-hosted Llama path on Insomnia; today's work pushed that same runtime shape deeper into repo-local orchestration runners and failure-recovery debugging.

### Governance / planning (`pm/backlog.md`, `planning/`, `.agent-sessions/sessions.md`)
- Active `planning/` has only the Apr-21 and Apr-28 call agenda/prep docs + Apr-16 meeting record; older meeting docs are archived.
- `pm/backlog.md` has exactly **one** live entry: explore `claude_agent_sdk` (2026-04-20, Codex/user-pinned).
- Session registry is still noisy: many stale sessions from 2026-04-09/10 remain listed, and active-session counts should be treated as approximate until a cleanup pass lands.

### Review / audit trail conventions
- `review/codex-prompts/`, `review/claude-prompts/`, `review/local-prompts/` are now the canonical log dirs (renamed from older layout in commit `42e8ecc`).
- `docs/archive/cross_repo_review_remediation.md` + `..._spec.md` capture the completed PR `#107` review stream.

---

## 4. Active Findings / Known Problems

### Fixed in code and re-proven enough to trust the harness
- **[V]** `#23` Verified PE & `#24` PE + Self-Ask runners now surface failed tool calls and terminal failed steps honestly. The intermediate honest-failure runs (`8853022`, `8853391`) corrected the harness; the later rebased proof snapshots (`8857842`, `8857843`) then reached clean `2/2` smoke success.
- **[V]** The Verified PE suffix-replan crash (`Invalid dependency reference for step 1: #S1`) has been fixed and merged; the latest Verified PE reruns do not crash on that path.
- **[V]** PR `#115` is merged, so the earlier serve-path hardening review findings are now resolved on canonical history.

### Still open / follow-up
- **[V]** `#23/#24` are merged. The remaining orchestration follow-up is not publication anymore; it is the small post-merge docs/runtime reconciliation pass for `#111`.
- **[V]** PR `#112` still has `CHANGES_REQUESTED`. PRs `#113`, `#114`, and `#120` are merged, so they are no longer active review lanes.
- **[V]** Experiment 1 Cell A runner: absent. Without it, the `(B − A)` MCP-overhead delta cannot be measured, which is the whole point of `#25` and feeds `#26` (Notebook 02).
- **[V]** `docs/gcp_fallback.md`: runbook published, end-to-end path unvalidated.
- **[V]** `#111` is still open. The remaining question is deliberately narrow now: do one clean reconciled Insomnia proof pass on current `main`, then close it.

### Broader follow-up (do not mix into current branches)
- **[V]** `pm/backlog.md`: investigate why AssetOpsBench imports `claude_agent_sdk` and whether this repo should mirror it. Research task, not a coding task.
- **[V]** `#111` should no longer be treated as the home for Experiment 1 runner ownership questions. That work is now much more clearly living under `#25`.
- **[V]** `#26` and `#32` now have canonical consumer-side notebook scaffolds on `main`, but they still should not be described as partially "proved." The missing piece is execution data, not notebook structure.

---

## 5. Issues / PRs / Ownership Signals

### Merged in window (solid)
- **PR `#118`** (Alex, `codex-fnd/notebook01-data-exploration`) — Notebook 01 replaces static image. **Solid** — closed `#117`.
- **PR `#116`** (Alex, `codex-fnd/paper-methodology`) — PS B methodology + NeurIPS abstract outline. **Solid** — closed `#77`.

### Closures that look partial
- **`#111`** (Insomnia reconciliation) — technically still OPEN, but now it looks like a post-merge confirmation issue: align docs/scripts to the newer proven stack, do one clean run on `main`, then close.

### Recently merged
- **PR `#120`** (Alex, `codex-fnd/issue-26-32-analysis-scaffold`) — Notebook 02/03 analysis scaffolds for `#26/#32`. **Intentionally partial** — merged consumer-side structure, but `#26` and `#32` stay open pending real captures.
- **PR `#119`** (Alex, `codex-fnd/issue-23-24-verified-pe-self-ask`) — repo-local Verified PE + PE + Self-Ask runners plus clean smoke-proof snapshots. **Solid** — closes `#23` and `#24`.
- **PR `#114`** (Akshat, `akshat/issue20-judge-logs`) — Maverick-17B judge audit logs + path fix. **Solid** — closes `#20`.
- **PR `#113`** (Akshat, `akshat/replay-scenarios-harness`) — harness smoke run, six-dimension judge scorer, and Smart Grid trajectory artifact. **Solid** — closes `#3`, `#17`, and `#18`.

### Open PRs still in motion
| PR | Author | Branch | Status |
|---|---|---|---|
| `#112` | Copilot SWE Agent | `copilot/run-benchmark-scenario-end-to-end` | Local MCP smoke runner + SGT-009 evidence; still `CHANGES_REQUESTED` |

### Branches / worktrees (only those touching current coordination)
- `codex-worktrees/codex-fnd-issues-26-32-analysis-scaffold/` ← `#26/#32` analysis scaffolds. **Merged as PR `#120`**; the worktree may now only be needed for follow-up notebook work, not for the initial scaffold landing.
- `codex-worktrees/codex-fnd-orch-wandb/` ← older WandB orchestration stream (`484b167`, dormant).
- `codex-worktrees/codex-fnd-review-remediation/` ← post-merge follow-up for the `#107` remediation stream.
- `codex-worktrees/codex-fnd-scenario-realism/`, `codex-fnd-slurm-cheatsheet/`, `codex-fnd-wandb-schema/` ← older streams, check `git log` before reusing.
- Root worktree = `main` (local docs-only stream). Per global rule: do not `git switch` a non-main branch here.

---

## 6. Validation / Proof Ledger

| Date (EDT) | Run ID | Branch / SHA | Config | W&B | Status | Notes |
|---|---|---|---|---|---|---|
| 2026-04-21 | `8857843_verified_pe_mcp_baseline_smoke` | `codex-fnd/issue-23-24-verified-pe-self-ask` @ `3a03ab8…` (later merged as PR `#119`) | `configs/example_verified_pe.env` | `x65ej9e0` | **Clean smoke success proof snapshot** | Verified PE reached `2/2` on the rebased post-`#115` branch. Committed proof snapshots now live at `benchmarks/cell_Z_hybrid/{config,summary}.json`; raw logs remain archived off-repo. |
| 2026-04-21 | `8857842_pe_self_ask_mcp_baseline_smoke` | `codex-fnd/issue-23-24-verified-pe-self-ask` @ `3a03ab8…` (later merged as PR `#119`) | `configs/example_pe_self_ask.env` | `otkt77pj` | **Clean smoke success proof snapshot** | PE + Self-Ask reached `2/2` on the rebased branch. Committed proof snapshots now live at `benchmarks/cell_Y_plan_execute/{config,summary}.json`; raw logs remain archived off-repo. |
| 2026-04-20 | `8854785_verified_pe_mcp_baseline_smoke` | `codex-fnd/issue-23-24-verified-pe-self-ask` @ `7c13397…` | `configs/example_verified_pe.env` | `xoo73k1h` | **Near-clean proof; one harness bug left** | Verified PE improved to `1/2`. Scenario 2 succeeded. Scenario 1 failed because the verifier prompt exceeded the 32k context window after a huge sensor-readings payload was fed back into LiteLLM. This is what `dc61c5d` fixes. |
| 2026-04-20 | `8854783_pe_self_ask_mcp_baseline_smoke` | `codex-fnd/issue-23-24-verified-pe-self-ask` @ `7c13397…` | `configs/example_pe_self_ask.env` | `ncai1jfr` | **Earlier clean smoke success proof** | PE + Self-Ask reached `2/2` on the two-scenario smoke slice with truthful runner accounting. Later superseded by the rebased `8857842` proof snapshot. |
| 2026-04-20 | `8853391_verified_pe_mcp_baseline_smoke` | `codex-fnd/issue-23-24-verified-pe-self-ask` @ `79d3531…` | `configs/example_verified_pe.env` | — | **Truthful failure proof** | Verified PE now fails honestly (`0/2`) with explicit failed steps. No suffix-replan crash; remaining failures are planner/tool-selection quality problems. |
| 2026-04-20 | `8853022_pe_self_ask_mcp_baseline_smoke` | `codex-fnd/issue-23-24-verified-pe-self-ask` @ post-accounting-fix branch state | `configs/example_pe_self_ask.env` | — | **Truthful failure proof** | PE + Self-Ask also now fails honestly (`0/2`) rather than masking tool failures. Confirms the harness-level accounting fixes are working. |
| 2026-04-20 | `8850716_pe_self_ask_mcp_baseline_smoke` | `codex-fnd/issue-23-24-verified-pe-self-ask` @ `0591c75…` | `configs/example_pe_self_ask.env` | `y42u88h3` | **Historical integration proof — superseded** | Useful as first end-to-end evidence, but no longer the authoritative branch proof because later runs fixed the accounting layer. |
| 2026-04-20 | `8851966_verified_pe_mcp_baseline_smoke` | `codex-fnd/issue-23-24-verified-pe-self-ask` @ `0591c75…` | `configs/example_verified_pe.env` | `0v3a5jqi` | **Historical integration proof — superseded** | Same story as above: useful milestone, but not the authoritative proof after the later harness fixes. |
| 2026-04-16 | (committed artifacts now on `team13/main` via `#115`) | `team13/main` | — | — | **Real proof** | Self-hosted Llama-3.1-8B benchmark-path validation on Insomnia A6000; `--served-model-name Llama-3.1-8B-Instruct`, `--max-model-len 32768`. Embedded 8-step PE trajectory hits all 4 servers (iot/tsfm/fmsr/wo). |

Previously-authoritative artifacts to watch:
- **Static smoke image** `docs/dataset_visualization.png` → **superseded** by `notebooks/01_data_exploration.ipynb` (PR `#118`).
- **`benchmarks/validation_output.json`** on PR `#115` is a mixed stdout+JSON file; readable by hand but not clean for programmatic parsing (noted as Low in review).

---

## 7. Recommended Next Steps

### Current root `main` stream (small, reversible)
1. **Decide whether to push the local docs-only summary / housekeeping stream** up to `team13/main`.
2. **Re-check `#111` on current `main`**, do one clean end-to-end Insomnia run against the reconciled stack/docs path, then close it.

### Separate follow-up streams (do not mix)
3. **`#26/#32` after PR `#120`**:
   - consumer-side notebook scaffolds are now merged
   - execution-side progress still depends on real Cell A/B/C and B/Y/Z captures landing
4. **Experiment 1 Cell A runner** (`#25`): Aaron is now unblocked on the implementation direction. The remaining work is to build the local ReAct loop with AOB prompt/loop fidelity, then reuse the same loop for Cells B and C with different dispatchers.
5. **`#112`** still needs iteration; it is now the most obvious older open PR still lagging behind merged mainline work.
6. **GCP fallback shakedown** — treat the first real run on GCP as a validation-pass and update `docs/gcp_fallback.md` with actual-vs-documented deltas.
7. **Session registry hygiene** — many entries in `.agent-sessions/sessions.md` are stale (Apr 9-10, branches missing). A cleanup pass would reduce noise for future agents.

---

## 8. Key References

- Handoff entry point: `docs/live_repo_summary.md` (this file)
- Canonical infra: `docs/runbook.md`, `docs/insomnia_runbook.md`, `docs/gcp_fallback.md`
- Reproducibility: `docs/compute_plan.md`, `docs/validation_log.md`
- Experiment plan: `docs/execution_plan.md`, `docs/experiment1_capture_plan.md`, `docs/orchestration_wiring.md`
- Paper lane: `docs/ps_b_evaluation_methodology.md`, `docs/neurips_abstract_outline.md`
- Model/runtime: `requirements-insomnia.txt`, `scripts/vllm_serve.sh`, `scripts/run_experiment.sh`, `scripts/setup_insomnia.sh`, `docs/governance/model_registry.yaml`
- Active orchestration code: `mcp_servers/direct_adapter.py`, `mcp_servers/{iot,fmsr,tsfm,wo}_server/server.py`, `scripts/plan_execute_self_ask_runner.py`, `scripts/verified_pe_runner.py`, `scripts/orchestration_utils.py`
- Data / notebooks: `data/processed/`, `notebooks/01_data_exploration.ipynb`, `results/`
- Governance: `pm/backlog.md`, `CHANGELOG.md`, `.agent-sessions/sessions.md`, `planning/2026-04-21_call_prep.md`, `planning/2026-04-28_call_prep.md`
- Review artifacts: `review/codex-prompts/`, `review/claude-prompts/`, `review/local-prompts/`, `docs/archive/cross_repo_review_remediation.md`

---

## 9. Code-review findings — Aaron's 5 canonical-main commits (2026-04-20 post-review)

Claude review of the five Apr 20 commits (`01043c5`, `91cb21e`, `f2f3083`, `77fc11d`, `b0f0d40`) against `team13/main` and the `codex-fnd/issue-23-24-verified-pe-self-ask` branch. Verdicts agree with Codex's parallel read. Issue states:

| Issue | State | Verdict | Gap |
|---|---|---|---|
| `#25` | OPEN | not yet justified to close | Only Cell A/B/C scaffolding landed; no raw captures, no runner — remains correctly open |
| `#27` | CLOSED | partially justified | Mechanism wired, but `01043c5` was tested only against synthetic CSV; no live WandB dashboard proof yet |
| `#37` | CLOSED | justified, with small doc follow-ups | `runbook.md` exists and is well-structured. The remaining stale cross-references are small enough to fold into the next stack-reconciliation PR rather than treat as a closure problem. |
| `#38` | CLOSED | partially justified | Issue allows "mechanically complete"; closure defensible but comment didn't echo the doc's own §13 TODO |
| `#111` | OPEN | still reasonable to keep open briefly | Main now carries the newer 0.19.0 / Python 3.11 reality; the remaining work is the small post-merge docs/runbook cleanup plus one clean reconciled proof run on current main |

### Follow-up items posted as issue comments (2026-04-20 21:30 UTC)

All findings surfaced as follow-up comments on the 5 issues; none require reopens. Summary by issue:

- **`#27`** — posted follow-up covering M2 (one live profiling capture visible in the WandB run page, attachable to the next real run) and L2 (add `tests/test_log_profiling_to_wandb.py` covering no-URL, missing-dir, CSV parser).
- **`#37`** — posted follow-up covering H1/M1/L3, with the intended resolution now being: fold those small doc fixes into the next PR that moves the newer Insomnia stack forward.
- **`#38`** — posted follow-up noting the doc's own §13 "not yet validated end-to-end" TODO wasn't echoed in the closure comment.
- **`#111`** — posted follow-up confirming the call to leave open for one more pass, but only for the stack-reconciliation / proof-closeout reason, not for the Experiment 1 runner question.
- **`#25`** — Alex answered Aaron's 4 open questions at 2026-04-20 21:30: Cell A runner built locally with AOB prompt/loop fidelity as a hard constraint; multi_*.json slice (6 scenarios); 3 trials; latency-only for Notebook 02. Cell A runner implementation is now unblocked, and no extra issue is needed.

### Review-finding coverage

All H/M/L items from the review are now either tracked as issue comments (above) or resolved in-line. None stranded outside the 5 issues. No new issues created.

### Candidate doc-only cleanups for the post-merge `#111` follow-up

Now that `#23/#24` are merged and the stack direction has effectively settled, these three doc-only fixes are natural to fold into the small `#111` cleanup pass rather than open a separate stream:

1. **H1** — rewrite `docs/insomnia_runbook.md` lines 88-96 to match the 3.11 + 0.19.0 reality; demote the "Python 3.9 + vLLM 0.10+ silent crash" to a historical note.
2. **M1** — rewrite `docs/runbook.md` §5 troubleshooting row for "vLLM log is 0 bytes" so it describes current-stack hang modes (model download truncation, port conflict, cuDNN `LD_LIBRARY_PATH` miss).
3. **L3** — add "run on a compute node, not the login node" caveat next to `runbook.md` §2.2's `python -c "import vllm; ..."` command.

All three are 5-10 lines each. Landing them alongside the branch's runtime-contract update reinforces the branch as the canonical reconciliation and closes H2 at the same time.

Branch-scoped and unrelated to these doc-only fixes:
- The remaining `#23` / `#24` questions are now mostly about planner quality and PR framing, not harness-accounting correctness.

### Aaron's substantive comments on his 5 issues (all landed Apr 20 14:00-19:00 UTC-4)

- `#25` (OPEN, comment at 18:20 + Alex follow-up later that night): scaffolding landed in `91cb21e`; Aaron surfaced 4 design questions, and Alex answered them directly on-issue. **Cell A runner is still the explicit gating piece, but the ownership/design ambiguity is now much lower.**
- `#27` (CLOSED, comment at 18:13): wiring via `capture_around.sh` + `log_profiling_to_wandb.py`. Non-fatal design when WandB / URL missing.
- `#37` (CLOSED, comment at 18:25): `docs/runbook.md` structure detailed — preconditions, first-time setup, day-to-day workflow, profiling workflow, troubleshooting, related runbooks.
- `#38` (CLOSED, comment at 18:29): `docs/gcp_fallback.md` tactical structure detailed — when to use, prerequisites, instance selection, spin-up, env setup, benchmark/profiling invocation, artifact persistence, shutdown, spot handling, cost, GPU differences, §13 TODO.
- `#111` (OPEN, comment at 18:59): addressed items 1-8 + 10 from the issue. The remaining reason to keep it open is the final stack-reconciliation / proof-closeout pass after the newer branch direction lands.

### Coherence summary: main reading as a single source

Main is internally misleading in exactly two places — both small enough to fold into the next branch-forward PR rather than treat as their own cleanup stream:

1. `insomnia_runbook.md` Python-version section (H1 above)
2. `runbook.md` §5 troubleshooting cross-ref (M1 above)

Both are 2-3 line fixes that don't require reopening any closed issue.

---

## 10. Analysis-scaffold updates — `#26` / `#32` branch (2026-04-21)

`codex-fnd/issue-26-32-analysis-scaffold` was rebased onto `team13/main`, updated, pushed at `4ed9bfa`, and is now PR `#120`.

**Notebook 02 (`#26` — MCP overhead):**

- Scan expanded to read the real `summary.json` schema currently written by `scripts/run_experiment.sh` — latency p50/p95, tool/MCP latency, tool call counts, tool error count, success rate, judge fields (null until `#17` populates them). Validated against `benchmarks/cell_Y_plan_execute/summary.json` as the reference shape.
- Surfaces `meta.json` profiling linkage fields (`profiling_dir`, `profiling_artifact`, `profiling_summary`) added by `#27` / `01043c5` so profiling attachment per cell is visible at a glance.
- Adds MCP overhead decomposition computed from per-scenario `latencies.jsonl` (avoids the Simpson's-paradox trap of summary-of-averages): `(B − A)` transport overhead, `(B − C)` optimization delta, `(C − A)` net post-optimization — at both p50 and p95.
- Replaces the placeholder mean-only bar chart with a p50-bar + p95-cap figure.
- Graceful degradation: always writes `notebook02_cell_availability.preflight.csv`, skips aggregation / figures / decomposition when any cell is missing captures.

**Notebook 03 (`#32` — orchestration comparison, new scaffold):**

- Scans Cells B (AaT MCP-baseline), Y (PE), Z (Verified PE).
- Reads per-scenario JSONs for the `success` / `failed_steps` / `history` / `answer` / `verification.replans_used` shape produced by the AOB PE client and the repo-local PE-Self-Ask / Verified-PE runners on the `#23/#24` branch.
- Catches JSON error-payload masking by scanning `history[*].response.error` alongside `step.success=False` — per Codex's 2026-04-20 finding that scenario 1 of `8850716` had `fmsr/get_sensor_correlation` return `{"error": "Failure mode 'T-015' not found."}` while the runner counted the step as success.
- Aggregates success rate, mean failed steps, mean history length, mean tool errors, recovery rate per orchestration; hooks in `results/metrics/scenario_scores.jsonl` judge scores when they land via `#17`.
- Two-panel figure: success rate (bar) + latency (p50 bar / p95 cap) by orchestration.

**How much this closes:**

- **`#26` — Notebook 02:** ~60% done. Structure, parser, overhead math, and figure are production-ready. Remaining ~40%: run against real Cell A/B/C captures (gated on `#25`), write the prose, link the paper-facing figure.
- **`#32` — Experiment 2 execution:** ~15% done by this commit. This is an *execution* issue, not an *analysis* issue. What's new is the consumer (Notebook 03), not the producer. Real progress on `#32` requires live Cell B / Y / Z runs across N multi-domain scenarios — gated on Aaron's Cell A/B work (`#25`) and the actual Experiment 2 execution captures landing, not on unresolved `#23/#24` harness noise anymore.

**Known cleanup surfaced in the branch:**

Two parallel config sets exist in `configs/` after the rebase. Both target the same benchmark directories; pick one before first live Cell A/B/C run to avoid teammate confusion — see §5 "Broader follow-up" for details.

---

*Maintained by the agent producing each 48h refresh. If this doc is older than ~48h, verify against `git log --all --since="2 days ago"` before trusting its content.*
