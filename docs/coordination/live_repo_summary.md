# Live Repo Summary — Active State

*Last updated: 2026-04-23 15:20 EDT*
*Window emphasized: 2026-04-19 00:00 EDT → 2026-04-23 15:20 EDT*
*Audience: incoming coding agent. Use this for current state. Older or removed detail lives in `docs/coordination/repo_summary_history.md`.*

> Legend: **[V]** verified from code/git/GitHub/logs • **[I]** inference • **[?]** unresolved.

---

## 1. Executive Snapshot

- **[V]** Current canonical remote history includes PR `#122`'s knowledge-plugin
  merge (`0865f67`). Do not use the older `999667d` pre-`#122` baseline as
  current truth.
- **[V]** The small experiment-matrix / Insomnia-HF cleanup stack has been
  isolated from the older local root-main history so it can land independently
  of the heavier staging lanes.
- **[V]** The heavier `#26` / `#32` / `#34` notebook-and-config staging work
  remains isolated on draft PR `#123`, not on this cleanup stack.
- **[V]** `#104` is repurposed as "Wire vanilla Agent-as-Tool to MCP-baseline stack (runner + harness + smoke + docs)" — the former mid-point PowerPoint task is folded into `#80`. Metadata: parent `#73 WS5 Orchestration comparison`, milestone `M5`, Project Status `Todo`, **assigned Aaron** (reassigned from Alex on 2026-04-22 so the AaT wiring lands alongside Aaron's Exp 1 runner work in `#25` — Cells A/B/C all sit on the ReAct/AaT surface and Cell B is shared with Exp 2). Outline comment posted with the wrapper plan (scripts/aat_runner.py on the openai-agent Python API), recommended upstream runner, first-run target (SGT-009 on Watsonx then Insomnia), and open questions.
- **[V]** `docs/orchestration_wiring.md` Agent-as-Tool section is corrected: upstream AssetOpsBench exposes `claude-agent` and `openai-agent` as first-class AaT CLIs (both MCP-wired via stdio, LiteLLM-routed, `server_paths` on their Python runner constructors). The real plumbing gap is that neither AaT CLI exposes a `--server NAME=PATH` override, so the Smart Grid MCP servers need a thin team-repo wrapper to be reachable.
- **[V]** Short coordination docs now live under `docs/coordination/`.
  - tracked: `docs/coordination/shift_coordination_note_template.md`
  - local/untracked per-agent notes: `docs/coordination/shift_coordination_note__*.md`
  They are meant to stay much shorter than `docs/coordination/live_repo_summary.md` and carry only the current delta / coordination signal.
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
- **[V]** `#25` remains gated on the missing **Cell A runner**. Aaron has the design answers he needed; the remaining gap is implementation, not decision-making.
- **[V]** `#111` is now down to one concrete last-mile fix:
  - first proof run on canonical `main` failed because `scripts/run_experiment.sh` and `scripts/vllm_serve.sh` source `insomnia_env.sh` via `BASH_SOURCE[0]`, which points into Slurm’s spool dir under `sbatch`
  - a local 2-line fix was validated on Insomnia in a temporary proof worktree
  - that fix still needs to be committed on `main`, then rerun once on the matching committed SHA
- **[V]** `#112` is the main older open PR still lagging. It still has `CHANGES_REQUESTED`; the remaining work is in Akshat’s lane.

---

## 2. Recent Timeline

| When (EDT) | Ref | Where | Why it matters |
|---|---|---|---|
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
- **[V]** Vanilla **Agent-as-Tool is not yet smoke-tested.** `benchmarks/cell_B_mcp_baseline/raw/` is empty, and `docs/validation_log.md` contains PE-family proofs only (Apr 13 Watsonx PE smoke, Apr 16 Insomnia PE benchmark path, Apr 20/21 PE + Self-Ask and Verified PE). Upstream AssetOpsBench does expose `claude-agent` and `openai-agent` as first-class AaT runners (MCP-wired via stdio, LiteLLM-routed, with `server_paths` parity on their Python constructors) — the actual gap is that neither AaT CLI supports a `--server NAME=PATH` override, so the Smart Grid MCP servers need a thin team-repo wrapper. That wiring work is now tracked under `#104`.

### Active execution lanes

- **[V]** The experiment-matrix cleanup stack is scoped as a small docs +
  Insomnia HF-login fix, not as the heavier Notebook 03 staging lane.
- **[V]** Draft PR `#123` remains the concrete config/notebook staging lane for
  `#26` / `#32` / `#34`.
- **[V]** The `#111` Slurm shell fix remains a separate closeout: the local
  proof job `8859928` validated the fix, but the matching committed-SHA rerun is
  still the gating step before clean closure.

---

## 4. Active Findings / Open Loops

1. **`#111` last-mile shell fix**
   - **[V]** Real bug found.
   - **[V]** Local fix validated by job `8859928`.
   - **[?]** Still needs commit + one rerun on the matching committed SHA before the issue can be cleanly closed.

2. **`#25` Cell A runner**
   - **[V]** Config scaffolds, direct adapter, and profiling↔W&B plumbing are already on `main`.
   - **[V]** Missing piece is still the actual Cell A ReAct / Agent-as-Tool runner.

3. **`#26` / `#32` need execution data**
   - **[V]** Notebook scaffolds are merged.
   - **[V]** Remaining blocker is real capture generation:
     - Experiment 1: Cell A / B / C
     - Experiment 2: Cell B / Y / Z
   - **[V]** Important nuance after the local Apr 22 staging pass:
     - Y is the canonical PE baseline
     - PE + Self-Ask and Verified PE have smoke-proven runner paths
     - Z / Self-Ask follow-ons still need promoted canonical configs and raw artifacts before they are analysis-ready
     - the honest Experiment 2 core claim still waits on Cell B

4. **`#112` still needs another pass**
   - **[V]** Still open with `CHANGES_REQUESTED`.
   - **[V]** Earlier guidance already given to Akshat; no new blocker surfaced in this pass.

5. **`#104` vanilla AaT wiring (owned by Aaron, adjacent to `#25`)**
   - **[V]** Issue repurposed from the closed mid-point PPT task; parent `#73`, milestone `M5`, outline comment posted; reassigned to Aaron 2026-04-22 so the AaT runner is built once and reused across Exp 1 Cells A/B/C and the Exp 2 AaT arm.
   - **[?]** Implementation still to land: `scripts/aat_runner.py` around `OpenAIAgentRunner` with team `server_paths`, default harness dispatch for `ORCHESTRATION=agent_as_tool`, first smoke run (SGT-009 on Watsonx then Insomnia), canonical `benchmarks/cell_B_mcp_baseline/raw/<run-id>/` artifacts, and a `docs/validation_log.md` entry.
   - **[?]** Open questions on Codex-side: does `openai-agent --json` output mesh with `judge_trajectory.py`, is our local AssetOpsBench venv synced cleanly with the LiteLLM refactor, and should `claude-agent` also get a parallel smoke for symmetry.

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
| `#111` | shared infra follow-up | one local shell fix + one matching-SHA rerun |
| `#25` | Aaron implementation lane | Cell A runner still missing |
| `#26` | analysis/results lane | Notebook 02 scaffold merged; needs real captures |
| `#32` | analysis/results lane | Notebook 03 scaffold merged; Y can start when raw PE artifacts exist; Z / Self-Ask follow-ons need promoted canonical configs and raw artifacts; the honest B/Y core still needs Cell B |
| `#104` | Aaron implementation lane (reassigned from Alex 2026-04-22) | Vanilla AaT wiring — wrapper + harness dispatch + first smoke + docs. Metadata set; outline posted; not started. Pairs with `#25` so one AaT runner covers Cells A/B/C and the Exp 2 AaT arm. |

### Older open PR

| PR | Author | Status | Notes |
|---|---|---|---|
| `#112` | Copilot SWE Agent | `CHANGES_REQUESTED` | Needs the earlier requested fixes; no new dependency from today’s work |

---

## 6. Validation / Proof Ledger

| Date (EDT) | Run ID | Branch / SHA | Config | W&B | Status | Notes |
|---|---|---|---|---|---|---|
| 2026-04-13 | `local-20260413-003914_pe_mcp_baseline_watsonx_smoke` | canonical `main` at the time | Watsonx `llama-3-3-70b-instruct` on SGT-009 / T-015 | `9d4442ja` | **Earliest committed PE proof** | `run_status: success`, `pass: 1`, `fail: 0`, wall-clock 93.6s. 8-step plan, all steps OK. Raw artifacts live at `benchmarks/cell_Y_plan_execute/raw/local-20260413-003914_*`. Just added to `docs/validation_log.md` so the earliest benchmark-path proof is explicitly in the log ladder. |
| 2026-04-21 | `8859928_issue111_main_proof` | temp Insomnia worktree based on `main@3609321` + local shell fix | `configs/issue111_main_proof.env` | disabled | **Validated fix** | `2/2` success after patching the Slurm spool-path bug. Useful proof of the fix, but not final canonical proof because the committed SHA does not yet contain the fix. |
| 2026-04-21 | `8859923` | shared Insomnia `main@3609321` | `configs/issue111_main_proof.env` | disabled | **Immediate failure** | Exposed the `insomnia_env.sh` sourcing bug under `sbatch`. |
| 2026-04-21 | `8857843_verified_pe_mcp_baseline_smoke` | rebased `#119` branch @ `3a03ab8…` | `configs/example_verified_pe.env` | `x65ej9e0` | **Clean smoke success** | Verified PE `2/2`; proof snapshot committed in-tree at `benchmarks/cell_Z_hybrid/`. |
| 2026-04-21 | `8857842_pe_self_ask_mcp_baseline_smoke` | rebased `#119` branch @ `3a03ab8…` | `configs/example_pe_self_ask.env` | `otkt77pj` | **Clean smoke success** | PE + Self-Ask `2/2`; proof snapshot committed in-tree at `benchmarks/cell_Y_plan_execute/`. |
| 2026-04-20 | `8854785_verified_pe_mcp_baseline_smoke` | `#119` branch @ `7c13397…` | `configs/example_verified_pe.env` | `xoo73k1h` | **Near-clean, one bug left** | Verifier/context-window failure that directly motivated the final payload-compaction fixes. |
| 2026-04-20 | `8854783_pe_self_ask_mcp_baseline_smoke` | `#119` branch @ `7c13397…` | `configs/example_pe_self_ask.env` | `ncai1jfr` | **Earlier clean success** | Earlier PE success, later superseded by the rebased `8857842` proof. |

---

## 7. Recommended Next Steps

1. **Commit the `#111` shell fix on `main`.**
   - Files:
     - `scripts/run_experiment.sh`
     - `scripts/vllm_serve.sh`
2. **Rerun the same `#111` proof on the matching committed SHA.**
   - Then close `#111`.
3. **Execute `#104` vanilla AaT wiring.**
   - `scripts/aat_runner.py` around `OpenAIAgentRunner` with team `server_paths` (mirror `plan_execute_self_ask_runner.py` structure).
   - `run_experiment.sh` default dispatch for `ORCHESTRATION=agent_as_tool`, `AAT_RUNNER_TEMPLATE` kept as override.
   - First smoke on SGT-009 / T-015 under Watsonx, then Insomnia; artifacts under `benchmarks/cell_B_mcp_baseline/raw/<run-id>/`.
   - `docs/validation_log.md` entry recording the run.
4. **Wait on / review Aaron’s `#25` Cell A runner work.**
5. **After Cell A lands, start real Experiment 1 / 2 capture generation for `#26` / `#32`.**
6. **Triage `#112` only if Akshat wants another pass or it starts blocking other work.**

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

*If this doc starts carrying stale or purely historical material again, move it into `docs/coordination/repo_summary_history.md` rather than letting the live summary become an archive.*
