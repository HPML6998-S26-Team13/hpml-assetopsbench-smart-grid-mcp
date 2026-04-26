# Live Repo Summary — Active State

*Last updated: 2026-04-26 06:20 EDT*
*Configured emphasis window: 48 hours by default for this repo; widen or shrink the window by repo cadence.*
*Current emphasis window: 2026-04-24 06:20 EDT -> 2026-04-26 06:20 EDT, with older still-live blockers retained as needed.*
*Window update convention: when `Last updated` changes, slide this window to match unless the start point is intentionally anchored; if anchored, say so explicitly here.*
*Audience: incoming coding agent. Use this for current state. Older or removed detail lives in `docs/coordination/repo_summary_history.md`; do not evict material solely because it is older than the configured window.*

> Legend: **[V]** verified from code/git/GitHub/logs • **[I]** inference • **[?]** unresolved.

---

## 1. Executive Snapshot

- **[V]** Current canonical remote history is `team13/main@c61538e`, carrying
  Aaron's three squashed AaT commits with author/committer metadata aligned
  after the Apr 26 attribution rewrite. Alex's root `main` is local-only ahead by
  two coordination/model-revision commits (`2726482`, `0ef5304`); do not push
  root `main` unless Alex asks.
- **[V]** Apr 21 Team check-in #4 now has a repo meeting record at
  `planning/2026-04-21_meeting_notes.md`. The Apr 28 agenda/prep docs point at
  that record while preserving current truth: #104 is proof-backed but awaits
  PR/review and human closure, and #25 remains the full-capture gate.
- **[V]** AaT Cell A/B smoke and upstream parity proof are now real on branch
  `codex-fnd/aat-smoke-fix`: Cell A job `8962310_aat_direct_smoke_104`
  completed `1 / 1` on `9541e26`, and Cell B job
  `8969519_aat_mcp_baseline_smoke_104` completed `1 / 1` on `a10d092`.
  Upstream AOB `OpenAIAgentRunner` parity job
  `8970383_aat_mcp_baseline_upstream_smoke_104` completed `1 / 1` on
  `e43cba3` with Slurm elapsed `00:11:18`; repeat parity job
  `8970468_aat_mcp_baseline_upstream_smoke_104` also completed `1 / 1` with
  Slurm elapsed `00:09:05`. These used self-hosted
  `openai/Llama-3.1-8B-Instruct` on Insomnia and emitted canonical raw
  artifacts under `benchmarks/cell_{A_direct,B_mcp_baseline}/`. This clears
  the `#104` runner/MCP-bootstrap/upstream-parity proof boundary and gives
  `#25` an A/B smoke anchor; full `multi_*.json` / 3-trial A/B/C captures still
  remain.
- **[V]** The former local root-main coordination stack is now merged as PR
  `#126`. The branch `codex-fnd/root-main-coordination` was deleted remotely
  and local root `main` was reset to the squash merge.
- **[V]** The heavier `#26` / `#32` / `#34` notebook-and-config staging work
  remains isolated on draft PR `#123`, not on this cleanup stack.
- **[V]** Draft PR `#124` is the separate staging lane for `#35` / `#64` /
  `#36` / `#5`: a docs-only stack carrying the experiment-framing prerequisites
  plus `docs/failure_analysis_scaffold.md` and `docs/neurips_draft.md`.
  `black` passed; the PR remains draft and is not in review yet.
- **[V]** `#104` is repurposed as "Wire vanilla Agent-as-Tool to MCP-baseline stack (runner + harness + smoke + docs)" — the former mid-point PowerPoint task is folded into `#80`. Metadata: parent `#73 WS5 Orchestration comparison`, milestone `M5`, Project Status `Todo`, **assigned Aaron** (reassigned from Alex on 2026-04-22 so the AaT wiring lands alongside Aaron's Exp 1 runner work in `#25` — Cells A/B/C all sit on the ReAct/AaT surface and Cell B is shared with Exp 2). Outline comment posted with the wrapper plan (scripts/aat_runner.py on the openai-agent Python API), recommended upstream runner, first-run target (SGT-009 on Watsonx then Insomnia), and open questions.
- **[V]** `docs/orchestration_wiring.md` Agent-as-Tool section is corrected: upstream AssetOpsBench exposes `claude-agent` and `openai-agent` as first-class AaT CLIs (both MCP-wired via stdio, LiteLLM-routed, `server_paths` on their Python runner constructors). The real plumbing gap is that neither AaT CLI exposes a `--server NAME=PATH` override, so the Smart Grid MCP servers need a thin team-repo wrapper to be reachable.
- **[V]** Short coordination docs now live under `docs/coordination/`.
  - tracked: `docs/coordination/shift_coordination_note_template.md`
  - local/untracked per-agent notes: `docs/coordination/shift_coordination_note__*.md`
  They are meant to stay much shorter than `docs/coordination/live_repo_summary.md` and carry only the current delta / coordination signal.
- **[V]** Shift notes now have an explicit compaction trigger. When a per-agent
  note grows past roughly 600 words / 20 bullets, or when commits / PRs /
  issues / logs already preserve the detailed work, the agent should rewrite the
  note in place: keep active deltas and open loops, promote settled current truth
  here, summarize only otherwise-unrecoverable context into history, and drop
  transcript-level minutiae.
- **[V]** The repo-local orchestration lane is now merged and proven:
  - PR `#119` landed repo-local **PE + Self-Ask** and **Verified PE** runners.
  - clean smoke proofs exist for both on the rebased branch:
    - `8857842_pe_self_ask_mcp_baseline_smoke`
    - `8857843_verified_pe_mcp_baseline_smoke`
- **[V]** The analysis scaffold lane is merged:
  - PR `#120` landed Notebook 02 / Notebook 03 consumer-side scaffolds for `#26` / `#32`.
  - `#26` and `#32` remain open because they still need real experiment captures, not because the notebook structure is missing.
- **[V]** The follow-up after `#120` now makes the staged execution story explicit:
  - on the shared-doc side, Notebook 02 / Notebook 03 are now documented as staged rather than all-or-nothing
  - on the draft PR `#123` side, the concrete config/notebook staging for `#26` / `#32` / `#34` continues in isolation
  - current canonical artifact state:
    - Cell Y has a canonical PE config and proof snapshot
    - PE + Self-Ask and Verified PE are smoke-proven runner paths
    - Cell Z / Self-Ask follow-ons still need promoted canonical Experiment 2 configs and raw scenario JSONs before Notebook 03 can treat them as analysis-ready
- **[V]** Team issue bodies no longer carry the duplicated planning boilerplate.
  - the single-source explanation now lives in `docs/README.md`
  - archived planning tracker/spec references remain documented there, not repeated on every issue
- **[V]** `#25` has moved past the missing-runner gate for Cells A/B. The
  remaining gap is full Experiment 1 capture material: agreed `multi_*.json`
  slice, 3 trials, and Cell C after the optimized MCP lane is ready.
- **[V]** `#111` is closed after PR `#125` landed the final Insomnia HF CLI fix and
  the shared Insomnia checkout was verified on `main@b480604`.
- **[V]** `#112` is the main older open PR still lagging. It still has `CHANGES_REQUESTED`; the remaining work is in Akshat’s lane.

---

## 2. Recent Timeline

| When (EDT) | Ref | Where | Why it matters |
|---|---|---|---|
| 2026-04-26 06:10 | `team13/main@c61538e`, PR branch `b8f4e52` | `team13/main` + `codex-fnd/aat-smoke-fix` | Rewrote published commit metadata at Alex's explicit override so the six squash commits no longer show a second GitHub "committed by" identity: PR `#126`/Alex commits now have Alex as committer, and Aaron's AaT squash stack now has Aaron as committer. Trees/messages are unchanged; backup refs exist locally under `refs/backup/pre-attribution-rewrite-*20260426_060931`. |
| 2026-04-26 05:30 | `codex-fnd/aat-smoke-fix` | feature branch | Ported the local Apr 21 meeting-note/call-prep commit onto the AaT smoke-fix PR branch so the PR can carry the local root-main coordination commits plus the runtime proof branch together. |
| 2026-04-25/26 | `46edc87` + Slurm `8962310`, `8969519`, `8970383`, `8970468` | feature branch / Insomnia | AaT Cell A, team-runner Cell B, and upstream AOB `OpenAIAgentRunner` parity are all smoke-proven on the SGT-009 / T-015 scenario; the parity path now has two successful runs. |
| 2026-04-24 evening | `c61538e` | `team13/main` | Aaron's AaT runner stack was squashed into three shared-main commits: shared runner, Cell A/B configs/smokes, and design docs. The feature branch now carries the follow-up fixes/proofs on top. |
| 2026-04-24 evening | `planning/2026-04-21_meeting_notes.md` | local `main` -> feature branch | Ported the Apr 21 Team check-in #4 notes from the stale local reconciliation branch, then updated Apr 28 agenda/prep to point at the meeting record while preserving current issue truth. |
| 2026-04-24 13:08 | PR `#126` / `8548b8a` | `team13/main` | Root coordination/docs stack merged after review feedback was addressed: live-summary window sync, AaT runner design CHANGELOG entry, orchestration heading cleanup, and a clean squash body replacing the malformed intermediate commit message. |
| 2026-04-22 01:42 | `7bd2165` | local `main` | Refreshed the live summary to state explicitly that PE already uses thin repo-local wrappers around the AOB `PlanExecuteRunner` path, while vanilla AaT still needs the analogous wrapper around `OpenAIAgentRunner`. |
| 2026-04-22 03:09 | local `#26/#32/#34` staging pass | draft PR `#123` branch | Tightened the experiment-matrix story into actual scaffolding on the staging branch: added Y/Z baseline Self-Ask configs, replaced the stale Z legacy-hybrid config there, updated Notebook 03 to support staged Y/Z then B/Y analysis, and updated Notebook 02 to treat the first Cell B artifact as a shared-anchor milestone. Those concrete config/notebook edits are not part of PR `#125`. |
| 2026-04-22 03:15 | local Notebook 02 / 03 execution | draft PR `#123` branch | Notebook execution confirmed the staged logic compiles and runs on the staging branch. Current canonical repo-state result: Y has the canonical baseline surface; Z / Self-Ask follow-ons are smoke-proven but not yet canonical-analysis-ready because the promoted configs and raw scenario JSONs are not merged. |
| 2026-04-22 morning | `f1a3241`, `bb0d45e` | local `main` | Added the short coordination-note template/current note and a teammate-facing AOB dependency note to `docs/orchestration_wiring.md`. |
| 2026-04-22 00:15 | `#104` reassigned Alex → Aaron | team GitHub | AaT wiring consolidated with Aaron's Exp 1 runner work (`#25`) since Cells A/B/C all ride on the ReAct/AaT surface and Cell B is shared with Exp 2. One runner, two experiments. Casual handoff comment posted. |
| 2026-04-21 23:55 | `#104` repurpose + `docs/orchestration_wiring.md` correction + local squash (9→7 commits) + Apr 13 Watsonx PE smoke entry added to `docs/validation_log.md` | local `main` | Repurposed `#104` from the closed mid-point PPT task into the vanilla AaT wiring issue (runner wrapper + harness dispatch + first smoke + docs), with full metadata set and outline comment posted. Fixed the stale `docs/orchestration_wiring.md` claim that upstream lacks an AaT CLI. Squashed two repo-summary refreshes and the AaT-pair commits into cleaner units. |
| 2026-04-21 evening | issue-body cleanup | team GitHub issues | Removed duplicated “Canonical task source … / Historical planning snapshots …” boilerplate from the team issue bodies; `docs/README.md` is now the single source for that guidance. |
| 2026-04-21 12:49 | `3609321` | historical `team13/main` | Former shared-main baseline before the Apr 21-22 merge wave and PR `#122`; no longer current. |
| 2026-04-21 morning | `8859928_issue111_main_proof` | temp Insomnia worktree on `main` + local shell fix | `2/2` clean proof for `#111` after patching the Slurm spool-path bug. Useful validation, but not final canonical proof because the fix is still local/uncommitted. |
| 2026-04-21 morning | job `8859923` | shared Insomnia `main` checkout | First `#111` proof attempt failed immediately. Root cause: `insomnia_env.sh` sourced via `BASH_SOURCE[0]` under `sbatch`. |
| 2026-04-21 ~02:27 | merge `b08500e` | `team13/main` | PR `#120` merged. Notebook 02/03 scaffolds are on canonical history. |
| 2026-04-21 ~02:10 | merge `152627b` | `team13/main` | PR `#114` merged. Maverick judge audit logs + path fix landed. |
| 2026-04-21 ~02:09 | merge `01fa799` | `team13/main` | PR `#113` merged. Harness smoke proof, six-dimension judge scorer, and SGT trajectory artifact landed. |
| 2026-04-21 ~01:58 | merge `3a3004f` | `team13/main` | PR `#119` merged. Repo-local PE + Self-Ask / Verified PE runners landed; `#23` and `#24` closed. |
| 2026-04-21 ~00:25 | run `8857842_pe_self_ask_mcp_baseline_smoke` | rebased `#119` branch | Clean PE + Self-Ask smoke proof. |
| 2026-04-21 ~00:19 | run `8857843_verified_pe_mcp_baseline_smoke` | rebased `#119` branch | Clean Verified PE smoke proof. |
| 2026-04-21 ~00:05 | merge `de11fd7` | `team13/main` | PR `#115` merged. Server hardening and self-hosted benchmark path fixes landed. |
| 2026-04-20 afternoon-evening | `01043c5` → `b0f0d40` | `team13/main` | Aaron’s 5-commit infra/docs/scaffold series landed: profiling↔W&B wiring, Experiment 1 A/B/C scaffolding, canonical runbook, GCP fallback, `#111` setup reconciliation. Historical review notes moved to `docs/coordination/repo_summary_history.md`. |

---

## 3. Current Technical State

### Runtime / stack

- **[V]** Canonical current direction on `main` is the newer Insomnia stack:
  - Python 3.11
  - `vllm==0.19.0`
  - `transformers==4.57.6`
  - `huggingface-hub==0.36.2`
- **[V]** `docs/runbook.md` and `docs/insomnia_runbook.md` already reflect the three `#37` follow-up doc changes:
  - compute-node-only `import vllm` verification
  - updated 3.11 / 0.19.0 troubleshooting language
  - login-node verification framed as metadata-only

### Orchestration state

- **[V]** The repo-local PE family now treats AssetOpsBench as a **library slice**:
  - import the actual `plan_execute` surfaces directly
  - use LiteLLM / OpenAI-compatible serving as the model boundary
  - avoid package-level imports that drag in unrelated SDK dependencies
- **[V]** In practice, PE already uses the same general pattern AaT will use:
  - thin repo-local wrappers around the AOB runtime slice
  - explicit team `server_paths` overrides pointing at this repo's Smart Grid MCP servers
  - shared harness/logging/artifact plumbing in `scripts/run_experiment.sh`
  The difference is that PE-family wrappers already exist (`plan_execute_self_ask_runner.py`, `verified_pe_runner.py`), while vanilla AaT still needs its wrapper (`#104`).
- **[V]** The main orchestration runner code is now:
  - `scripts/plan_execute_self_ask_runner.py`
  - `scripts/verified_pe_runner.py`
  - `scripts/orchestration_utils.py`
- **[V]** The mainline proof snapshots committed in-tree are:
  - `benchmarks/cell_Y_plan_execute/{config.json,summary.json}`
  - `benchmarks/cell_Z_hybrid/{config.json,summary.json}`
- **[V]** Vanilla **Agent-as-Tool is smoke-tested for Cells A/B** on
  `codex-fnd/aat-smoke-fix`. The team wrapper uses one OpenAI Agents SDK loop
  with the pinned AOB prompt; Cell A supplies direct callables and Cell B
  supplies MCP stdio servers. Proof anchors: Cell A Slurm job `8962310`,
  Cell B Slurm job `8969519`, and upstream AOB `OpenAIAgentRunner` parity
  Slurm jobs `8970383` and `8970468`. `docs/validation_log.md` records these
  proof anchors. Remaining
  AaT work is PR/review closeout, Cell C once the optimized MCP lane lands,
  and the full `#25` capture slice.

### Active execution lanes

- **[V]** The experiment-matrix cleanup stack is scoped as a small docs +
  Insomnia HF-login fix, not as the heavier Notebook 03 staging lane.
- **[V]** Draft PR `#123` remains the concrete config/notebook staging lane for
  `#26` / `#32` / `#34`.
- **[V]** Draft PR `#124` is the current staging lane for the
  failure-analysis / paper docs (`#35` / `#64` / `#36` / `#5`). It is
  intentionally docs-only and does not close the underlying issues because the
  missing artifact-backed reruns and final results are still outstanding.
- **[V]** The `#111` Insomnia setup reconciliation is closed. The final verification
  checked `scripts/setup_insomnia.sh` syntax, the shared `.venv-insomnia` package
  metadata, and the corrected `huggingface_cli login` command shape on Insomnia.

---

## 4. Active Findings / Open Loops

1. **`#25` Cell A runner**
   - **[V]** Config scaffolds, direct adapter, profiling↔W&B plumbing, and the
     shared AaT runner are now present on the active fix branch.
   - **[V]** Cell A smoke succeeded on Insomnia as job `8962310`; this is no
     longer a missing-runner issue.
   - **[?]** Remaining `#25` work is the full capture set, not the smoke proof:
     `multi_*.json`, 3 trials, A/B first, and Cell C after the optimized MCP
     stack is ready.

2. **`#26` / `#32` need execution data**
   - **[V]** Notebook scaffolds are merged.
   - **[V]** Remaining blocker is real capture generation:
     - Experiment 1: Cell A / B / C
     - Experiment 2: Cell B / Y / Z
   - **[V]** Important nuance after the local Apr 22 staging pass:
     - Y is the canonical PE baseline
     - PE + Self-Ask and Verified PE have smoke-proven runner paths
     - Z / Self-Ask follow-ons still need promoted canonical configs and raw artifacts before they are analysis-ready
     - Cell B now has a one-scenario AaT smoke anchor; the honest Experiment 2
       core claim still needs the agreed raw run set

3. **`#112` still needs another pass**
   - **[V]** Still open with `CHANGES_REQUESTED`.
   - **[V]** Earlier guidance already given to Akshat; no new blocker surfaced in this pass.

4. **`#104` vanilla AaT wiring (owned by Aaron, adjacent to `#25`)**
   - **[V]** Issue repurposed from the closed mid-point PPT task; parent `#73`, milestone `M5`, outline comment posted; reassigned to Aaron 2026-04-22 so the AaT runner is built once and reused across Exp 1 Cells A/B/C and the Exp 2 AaT arm.
   - **[V]** Core runner/proof is now done on `codex-fnd/aat-smoke-fix`:
     `scripts/aat_runner.py` uses the OpenAI Agents SDK directly, Cell A/B tool
     names match, local vLLM routing is explicit, and Insomnia smoke artifacts
     exist for A (`8962310`) and B (`8969519`).
   - **[V]** Upstream parity is now proven by
     `8970383_aat_mcp_baseline_upstream_smoke_104`: AOB
     `OpenAIAgentRunner` Python API, same Smart Grid MCP servers/scenario,
     `1 / 1` success, Slurm elapsed `00:11:18`, 4 MCP tool calls.
     Repeat job `8970468_aat_mcp_baseline_upstream_smoke_104` also completed
     `1 / 1` successfully, Slurm elapsed `00:09:05`, 4 MCP tool calls.
   - **[?]** Remaining closeout is process, not implementation proof: PR/review,
     issue comment/update, and then a human decision to close `#104`.

---

## 5. Issues / PRs / Ownership Signals

### Recently merged and effectively settled

- **PR `#113`** → closes `#3`, `#17`, `#18`
- **PR `#114`** → closes `#20`
- **PR `#115`** → closes `#9`, `#10`, `#11`, `#12`, `#58`
- **PR `#119`** → closes `#23`, `#24`
- **PR `#120`** → updates `#26`, `#32` but intentionally does not close them

### Still-open issues that matter most

| Issue | Owner signal | Current state |
|---|---|---|
| `#25` | Aaron implementation lane | A/B smoke artifacts exist; full `multi_*.json` / 3-trial A/B/C capture still pending |
| `#26` | analysis/results lane | Notebook 02 scaffold merged; needs real captures |
| `#32` | analysis/results lane | Notebook 03 scaffold merged; Y can start when raw PE artifacts exist; Cell B now has an AaT smoke anchor, but final Experiment 2 raw run set is still pending |
| `#104` | Aaron implementation lane (reassigned from Alex 2026-04-22) | Team AaT runner plus A/B smoke and upstream `OpenAIAgentRunner` parity proof exist; PR/review and issue closeout remain |

### Older open PR

| PR | Author | Status | Notes |
|---|---|---|---|
| `#112` | Copilot SWE Agent | `CHANGES_REQUESTED` | Needs the earlier requested fixes; no new dependency from today’s work |

### Active draft PRs

| PR | Author | Status | Notes |
|---|---|---|---|
| `#123` | Alex / Codex staging branch | draft, `black` green | Notebook/config staging for `#26` / `#32` / `#34`; keeps the staged Experiment 2 analysis lane isolated while AaT artifacts are still missing |
| `#124` | Alex / Codex staging branch | draft, `black` green | Failure-analysis / paper staging for `#35` / `#64` / `#36` / `#5`; docs-only stack with experiment-framing prerequisites plus the scaffold docs |

---

## 6. Validation / Proof Ledger

| Date (EDT) | Run ID | Branch / SHA | Config | W&B | Status | Notes |
|---|---|---|---|---|---|---|
| 2026-04-26 | `8970468_aat_mcp_baseline_upstream_smoke_104` | `codex-fnd/aat-smoke-fix@e43cba3` | `configs/aat_mcp_baseline_upstream_smoke.env` | disabled | **AaT upstream parity repeat success** | AOB `OpenAIAgentRunner` Python API, same Smart Grid MCP servers/scenario, Slurm `COMPLETED 0:0` in `00:09:05`, `run_status: success`, `1/1`, latency 31.48s, `tool_call_count_total=4`. |
| 2026-04-26 | `8970383_aat_mcp_baseline_upstream_smoke_104` | `codex-fnd/aat-smoke-fix@e43cba3` | `configs/aat_mcp_baseline_upstream_smoke.env` | disabled | **AaT upstream parity success** | AOB `OpenAIAgentRunner` Python API, same Smart Grid MCP servers/scenario, Slurm `COMPLETED 0:0` in `00:11:18`, `run_status: success`, `1/1`, latency 36.18s, `tool_call_count_total=4`. |
| 2026-04-26 | `8969519_aat_mcp_baseline_smoke_104` | `codex-fnd/aat-smoke-fix@a10d092` | `configs/aat_mcp_baseline_smoke.env` | disabled | **AaT Cell B smoke success** | `run_status: success`, `1/1`, latency 91.78s, `tool_call_count_total=4`; all four MCP servers bootstrapped/initialized and vLLM accepted sequential tool-call turns with `parallel_tool_calls=false`. |
| 2026-04-25 | `8962310_aat_direct_smoke_104` | `codex-fnd/aat-smoke-fix@9541e26` | `configs/aat_direct_smoke.env` | disabled | **AaT Cell A smoke success** | `run_status: success`, `1/1`, latency 12.09s, `tool_call_count_total=4`; direct callable path exercised the same SGT-009 / T-015 scenario as Cell B. |
| 2026-04-13 | `local-20260413-003914_pe_mcp_baseline_watsonx_smoke` | canonical `main` at the time | Watsonx `llama-3-3-70b-instruct` on SGT-009 / T-015 | `9d4442ja` | **Earliest committed PE proof** | `run_status: success`, `pass: 1`, `fail: 0`, wall-clock 93.6s. 8-step plan, all steps OK. Raw artifacts live at `benchmarks/cell_Y_plan_execute/raw/local-20260413-003914_*`. Just added to `docs/validation_log.md` so the earliest benchmark-path proof is explicitly in the log ladder. |
| 2026-04-21 | `8859928_issue111_main_proof` | temp Insomnia worktree based on `main@3609321` + local shell fix | `configs/issue111_main_proof.env` | disabled | **Validated fix** | `2/2` success after patching the Slurm spool-path bug. Useful proof of the fix, but not final canonical proof because the committed SHA does not yet contain the fix. |
| 2026-04-21 | `8859923` | shared Insomnia `main@3609321` | `configs/issue111_main_proof.env` | disabled | **Immediate failure** | Exposed the `insomnia_env.sh` sourcing bug under `sbatch`. |
| 2026-04-21 | `8857843_verified_pe_mcp_baseline_smoke` | rebased `#119` branch @ `3a03ab8…` | `configs/example_verified_pe.env` | `x65ej9e0` | **Clean smoke success** | Verified PE `2/2`; proof snapshot committed in-tree at `benchmarks/cell_Z_hybrid/`. |
| 2026-04-21 | `8857842_pe_self_ask_mcp_baseline_smoke` | rebased `#119` branch @ `3a03ab8…` | `configs/example_pe_self_ask.env` | `otkt77pj` | **Clean smoke success** | PE + Self-Ask `2/2`; proof snapshot committed in-tree at `benchmarks/cell_Y_plan_execute/`. |
| 2026-04-20 | `8854785_verified_pe_mcp_baseline_smoke` | `#119` branch @ `7c13397…` | `configs/example_verified_pe.env` | `xoo73k1h` | **Near-clean, one bug left** | Verifier/context-window failure that directly motivated the final payload-compaction fixes. |
| 2026-04-20 | `8854783_pe_self_ask_mcp_baseline_smoke` | `#119` branch @ `7c13397…` | `configs/example_pe_self_ask.env` | `ncai1jfr` | **Earlier clean success** | Earlier PE success, later superseded by the rebased `8857842` proof. |

---

## 7. Recommended Next Steps

1. **Close out `#104` through process.**
   - Core A/B smoke proof is present (`8962310`, `8969519`) and upstream
     `OpenAIAgentRunner` parity proof is present twice (`8970383`, `8970468`).
     Remaining work is PR/review, issue comment/update, and human closure.
2. **Proceed to `#25` full capture planning.**
   - Use the proven A/B smoke path for the real `multi_*.json`, 3-trial
     capture set. Keep Cell C gated on the optimized MCP workstream.
3. **Use Cell B smoke artifacts to unblock Notebook 02/03 contract checks.**
4. **Triage `#112` only if Akshat wants another pass or it starts blocking other work.**

---

## 8. Key References

- Infra / runtime:
  - `docs/runbook.md`
  - `docs/insomnia_runbook.md`
  - `docs/gcp_fallback.md`
  - `scripts/run_experiment.sh`
  - `scripts/vllm_serve.sh`
  - `scripts/setup_insomnia.sh`
  - `docs/governance/model_registry.yaml`
- Orchestration:
  - `scripts/plan_execute_self_ask_runner.py`
  - `scripts/verified_pe_runner.py`
  - `scripts/orchestration_utils.py`
  - `mcp_servers/direct_adapter.py`
- Validation / proof:
  - `docs/validation_log.md`
  - `benchmarks/cell_Y_plan_execute/`
  - `benchmarks/cell_Z_hybrid/`
- Experiment / analysis:
  - `docs/experiment1_capture_plan.md`
  - `docs/orchestration_wiring.md`
  - `notebooks/01_data_exploration.ipynb`
  - `notebooks/02_latency_analysis.ipynb`
  - `notebooks/03_orchestration_comparison.ipynb`
- Governance / handoff:
  - `pm/backlog.md`
  - `CHANGELOG.md`
  - `.agent-sessions/sessions.md`
  - `docs/coordination/repo_summary_history.md`

---

## 9. Historical Notes Pointer

- Older detail that was removed from this live summary now belongs in `docs/coordination/repo_summary_history.md`.
- That includes:
  - the long-form review treatment of Aaron’s Apr 20 five-commit series
  - earlier stale “candidate cleanup” notes that are now already reflected in docs
  - milestone transitions from the first version of this live summary through the merged PR wave on Apr 21

---

*If this doc starts carrying stale or purely historical material again, move it into `docs/coordination/repo_summary_history.md` rather than letting the live summary become an archive. The configured window is an emphasis guide, not an automatic eviction rule.*
