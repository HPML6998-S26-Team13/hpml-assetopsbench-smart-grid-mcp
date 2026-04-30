# Spec: extraction from team repo into Alex's AOB fork

*Companion spec to [aob-extraction.md](aob-extraction.md). Captures design rationale, edge cases, decision rationale, and later-phase concerns. Plan stays lean; this carries the why.*

## Phase 0 sign-off (2026-04-28)

| Question | Locked answer | Confidence | Awaiting external? |
|---|---|---|---|
| Q-NAMING | Sub-namespace `src/servers/smart_grid/{iot,fmsr,tsfm,wo}/` | High | No (Dhaval ack-of-record only) |
| Q-SCENARIOS | Convert team-repo single-file JSONs to AOB array format. Negative checks → sibling array file `smart_grid_negative_checks.json`. | High | No |
| Q-EVAL-PARITY | Behavioral parity at agreement threshold ≥ 95%, `score_6d ≥ 0.6` classification, Cohen's κ ≥ 0.8. | High | No |
| Q-UPSTREAM-PR-CADENCE | Hybrid: Phase 1 standalone PR; Phases 2 + 3 combined as a "Smart Grid Bench domain" PR. | Medium | Yes (Dhaval preference) |
| Q-DHAVAL-COORDINATION | Phases 1-3 in Alex's fork need no upstream ack. Phase 4 PR(s) gated on Dhaval. AOB `feat/evaluation-module` merge ETA pending Dhaval Apr 28 reply. | High | Yes (merge ETA) |

Phase 0 deliverable status: **complete** — Phase 1 may begin. Q-UPSTREAM-PR-CADENCE and the AOB merge ETA will be confirmed (or revised) via Dhaval's Apr 28 email reply; revising them mid-flight does not block Phase 1 work because Phase 1 lands entirely in Alex's fork.

---


## Document scope

This spec covers:
- Design decisions called out as `Q-*` in the plan, with the options
  considered and the recommended answer.
- Edge cases each phase needs to handle.
- AOB README delta — how the 7th-domain claim is framed in upstream prose.
- Authorship + attribution mechanics.
- Eval parity findings (filled in during Phase 1).
- AOB upstream merge timing — what we depend on, what's in our control.
- Later-phase concerns (post-paper).

---

## Design Decisions

### Q-NAMING — Smart Grid namespace alongside AOB's existing servers

**Background.** AOB upstream `main` has `src/servers/{fmsr,iot,tsfm,wo,utilities,vibration}/`. Each is a general-purpose MCP server (not Smart-Grid-specific). Our team repo has `mcp_servers/{iot,fmsr,tsfm,wo}_server/server.py` — Smart-Grid-specific implementations sharing names but with different code (transformer T-015 nameplate, DGA dissolved-gas analysis, RUL forecasting, work order workflow).

**Options:**

1. **Sub-namespace**: `src/servers/smart_grid/{iot,fmsr,tsfm,wo}/`. Preserves the AOB convention (one dir per server) within a Smart-Grid namespace. Imports become `src.servers.smart_grid.iot.main`. Cleanest mental model: Smart Grid is the 7th domain, not a fork of AOB's existing 4 servers.

2. **Domain-rename**: `src/servers/transformer_iot/`, `transformer_fmsr/`, etc. Avoids any apparent collision but loses the cross-domain pattern (an `iot` reader thinks "general IoT" not "transformer IoT").

3. **Top-level rename**: `src/sg_servers/{iot,fmsr,tsfm,wo}/`. Maximum separation; suggests SG is its own platform. Diverges from AOB's `src/servers/` convention.

**Recommended:** **Option 1** (`src/servers/smart_grid/`). Mirrors how AOB already separates `src/scenarios/{local,huggingface}/` namespaces. Keeps AOB's "one dir per server" DNA. Direct adapter becomes `src/agent/<adapter-location>/smart_grid_direct_adapter.py` and references `src.servers.smart_grid.<server>` cleanly.

**Open dependency:** confirm with Dhaval before landing — if AOB has plans to refactor `src/servers/` into a different namespace shape (e.g., domain-grouped), we should align.

### Q-SCENARIOS — file-per-scenario vs array-per-file

**Background.** Team repo: `data/scenarios/multi_01_*.json` is one scenario per file. AOB upstream: `src/scenarios/local/vibration_utterance.json` is an array of scenarios (one file per domain or topic).

**Options:**

1. **Convert to array format on extraction**: bundle all 11 Smart Grid scenarios into `src/scenarios/local/smart_grid.json` as a single array. Matches AOB convention.

2. **Keep file-per-scenario in a sub-dir**: `src/scenarios/local/smart_grid/multi_01_*.json` etc. Diverges from AOB convention but keeps team-repo file structure aligned for diff-friendliness.

3. **Both**: ship the array form for AOB compatibility AND keep the per-file form in a subdir for tooling that prefers individual files.

**Recommended:** **Option 1** (array format). AOB's `loader.py` and `Scenario.from_raw` are written for array files; matching that convention reduces friction. Loader code in spec § "Scenario shape mapping" below.

**Edge case:** team-repo `data/scenarios/negative_checks/` — Phase 2 extraction must decide whether negative-check scenarios go in the same `smart_grid.json` array (with a `category: "negative"` tag) or a sibling `smart_grid_negative_checks.json` file. Recommend sibling for clarity.

### Q-EVAL-PARITY — what does "parity" mean for retiring `judge_trajectory.py`

**Background.** Backlog pin (b) says "retire `scripts/judge_trajectory.py` once parity is proven." Need a concrete definition.

**Options:**

1. **Tight parity**: same prompt template, same rubric, same model → identical scores within ε on all 36 trials. Highest bar; easiest to verify; least flexible.

2. **Behavioral parity**: same model, same rubric (semantic), but allow prompt-template differences. Score agreement at threshold (e.g. `score_6d ≥ 0.6` classification agreement ≥ 95%). Looser; what we likely need.

3. **Statistical parity**: same model, possibly different rubric, but per-cell ranking preserved (Z+SA > Z > Y+SA > B > A > Y stays the same direction). Loosest; closest to "research conclusions don't change."

**Recommended:** **Option 2** (behavioral parity at agreement threshold ≥ 95%, threshold = `score_6d ≥ 0.6` for "judge-pass"). Cohen's κ for inter-rater agreement; aim for κ ≥ 0.8.

**Edge case:** if AOB's `feat/evaluation-module` rubric is materially different (e.g. 4 criteria instead of 6), document the gap in the parity report and decide:
- Port our 6-criterion rubric upstream (preferred if Dhaval agrees).
- Adopt AOB's rubric and re-score our captures (may invalidate the headline table).
- Keep both side-by-side until upstream parity is reached.

### Q-UPSTREAM-PR-CADENCE — single combined PR or per-phase

**Options:**

1. **One PR per phase**: evaluation adapter, then Smart Grid domain, then orchestration runners. Smaller diffs, easier review, faster iteration.

2. **One combined PR with staged commits**: single review surface, lets reviewer see the full vision. Bigger diff (~5-10k LOC).

3. **Hybrid**: Phase 1 (evaluation adapter) as standalone PR (short blast radius); Phases 2+3 combined as a single "Smart Grid Bench domain" PR.

**Recommended:** **Option 3 (hybrid)**. Phase 1 has natural standalone value (helps any AOB user, not just Smart Grid). Phases 2+3 are coherent Smart-Grid Bench landing.

**Open dependency:** Dhaval's preference. Default to recommended unless Dhaval pushes back.

### Q-DHAVAL-COORDINATION — what needs upstream maintainer go-ahead

| Action | Needs Dhaval ack? | Reason |
|---|---|---|
| Phase 1 in Alex's fork | No | Pure local refactor on `eggrollofchaos/AssetOpsBench` |
| Phase 2 in Alex's fork | No | Same — local refactor |
| Phase 3 in Alex's fork | No | Same — local refactor |
| Q-NAMING decision | Yes (informally) | If AOB plans a `src/servers/` reorg, align |
| Q-SCENARIOS array conversion | No | Established AOB convention |
| Phase 4 upstream PR(s) | Yes | Required for any merge to `IBM/AssetOpsBench` |
| Retiring `scripts/judge_trajectory.py` from team repo | No | Internal team-repo decision once parity proven |
| `feat/evaluation-module` merge timing in AOB | Asked, awaiting answer | Affects Phase 1 dependency surface |

---

## Scenario shape mapping (Q-SCENARIOS reference)

Team repo single-file scenario:
```json
{
  "id": "SGT-009",
  "type": "transformer_fault",
  "text": "Transformer T-015 shows rising load and intermittent over-temperature alerts. Investigate...",
  "category": "multi_step",
  "characteristic_form": "Multi-step end-to-end fault response",
  "asset_id": "T-015",
  "expected_tools": ["list_assets", "get_asset_metadata", "get_sensor_readings", "..."],
  "ground_truth": "...",
  "difficulty": "medium",
  "domain_tags": ["iot", "fmsr", "tsfm", "wo"]
}
```

AOB array element shape (`Scenario.from_raw` accepts):
```json
{
  "id": "SGT-009",
  "type": "transformer_fault",
  "text": "...",
  "category": "multi_step",
  "characteristic_form": "Multi-step end-to-end fault response"
  // extra fields preserved via ConfigDict(extra='allow')
}
```

`asset_id`, `expected_tools`, `ground_truth`, `difficulty`, `domain_tags`
survive the round-trip via `extra='allow'`. Conversion script for Phase 2:

```python
import json
from pathlib import Path

scenarios = [
    json.loads(p.read_text())
    for p in sorted(Path("data/scenarios").glob("*.json"))
    if p.is_file() and not p.name.startswith("_")
]
Path("smart_grid.json").write_text(json.dumps(scenarios, indent=2))
```

---

## AOB README delta

AOB's README claims "4 domain-specific agents." Adding Smart Grid bumps that to 5 (or possibly more, depending on `feat/vibration-mcp-server` merge state).

**Suggested wording for AOB README:**

> AssetOpsBench is a unified framework for developing, orchestrating, and evaluating
> domain-specific AI agents in industrial asset operations and maintenance.
>
> - **5 domain-specific agents** covering: rotating-equipment vibration analysis,
>   IoT sensor monitoring, failure-mode and symptom retrieval (FMSR), time-series
>   forecasting and remaining useful life (TSFM/RUL), and Smart Grid transformer
>   operations.

If `feat/vibration-mcp-server` and other in-flight branches add more domains
between today and our PR, adjust the count accordingly. Don't over-claim.

---

## Authorship + attribution

Code authored by team members (Aaron, Tanisha, Akshat) needs attribution preserved on extraction:

- **Aaron**: most of `scripts/aat_runner.py`, `scripts/aat_tools_*.py`, `scripts/aat_system_prompt.py` (Phase 3).
- **Tanisha**: parts of `mcp_servers/iot_server/` (Phase 2).
- **Akshat**: most of `scripts/aat_runner.py` batch mode (PR `#134` v4 — Phase 3), parts of `scripts/judge_trajectory.py` (Phase 1).
- **Alex**: `scripts/plan_execute_self_ask_runner.py`, `scripts/verified_pe_runner.py`, `scripts/orchestration_utils.py`, most docs.

**Mechanism:** when extracting code, preserve git history via `git filter-repo` or per-commit cherry-pick. Alternative: a single squash commit with a `Co-Authored-By:` trailer for each contributor (per CLAUDE.md hard rule 3 — but rule 3 forbids `Co-Authored-By: Claude` AI attribution; human co-authorship is fine).

**Coordination requirement:** Aaron, Tanisha, Akshat must be aware before any extraction PR lands in Alex's fork. Recommend a short async note + acknowledgment before Phase 2 starts.

**Open question for Phase 0:** does the team want to be co-authors on the upstream AOB PR(s), or is "the Smart Grid Bench team at Columbia" sufficient as a paper citation? Different mechanics:
- Per-commit `Co-Authored-By:` if team consents to GitHub-visible commit attribution.
- A `CONTRIBUTORS.md` block + paper-side acknowledgment if they prefer.

---

## Eval parity findings (filled in during Phase 1)

*(Placeholder — populated by the parity report deliverable.)*

| Trial | AOB rubric score | Team rubric score | Agreement at ≥0.6? | Disagreement reason |
|---|---|---|---|---|
| (filled in) | | | | |

Cohen's κ: TBD.
Final verdict: TBD.
Remediation if κ < 0.8: TBD.

---

## AOB upstream merge timing

`feat/evaluation-module` is at `fcff318` (2026-04-27 commit by Shuxin Lin) but **not merged to AOB main** as of today. Two scenarios:

**Scenario A — branch merges to AOB main before our Phase 1 starts.**
We adopt the merged version directly; Phase 1 becomes "vendor `src/evaluation/` + write the SG adapter." Smaller blast radius.

**Scenario B — branch is still open when we start Phase 1.**
Two sub-options:
- B1: cherry-pick the eight files from the branch into our fork's `aob/sg-evaluation-adapter` feature branch. Carry the diff ourselves until upstream merges, then rebase. Adds carry-cost but unblocks us.
- B2: wait for upstream merge before starting Phase 1. Adds calendar dependency on Shuxin Lin / Dhaval.

**Recommended:** Scenario B1 if upstream merge hasn't happened by the time we want to start. Scenario A is pure-luck preferred.

**Action:** Dhaval Apr 28 email asks for the merge ETA. Use the answer to decide.

---

## Edge cases per phase

### Phase 1 edge cases

- **Trajectory shape mismatch.** Our per-trial JSON has `data["history"]` as a list of step dicts; AOB's `PersistedTrajectory.trajectory: Any` accepts anything but downstream metrics expect `{"turns": [...]}` (SDK shape) or step list (PE shape). The shape-agnostic judge from PR `#144` already handles both; the adapter just needs to pass through the right shape based on runner.
- **`scenario_id` type.** Our IDs are strings (e.g., `SGT-009`); AOB's `vibration_utterance.json` uses integers. `Scenario.from_raw` already handles both via `str(d["id"])`. No action.
- **Run-id derivation.** AOB expects `run_id` to be unique across the corpus. Our `RUN_ID = ${SLURM_JOB_ID}_${EXPERIMENT_NAME}` is already globally unique within our captures. Use as-is.
- **Missing `answer` field.** Some legacy runs have `answer = ""`. AOB's `PersistedTrajectory.answer: str` is required-not-Optional. Coerce empty → `""` (already does).

### Phase 2 edge cases

- **`mcp_servers/base.py` shared base class.** AOB doesn't have a unified base; each server uses `mcp.server.fastmcp.FastMCP` directly. Either keep `base.py` as Smart-Grid-namespaced helper OR refactor servers to use FastMCP directly. Decide in Phase 0.
- **Direct-mode tool registry.** Our `mcp_servers/direct_adapter.py` exposes 21 callables. AOB's direct-mode pattern is per-runner. Map to a single callable registry that the AOB direct-mode runner can consume.
- **Domain-tag overlap.** Our scenarios use `domain_tags: ["iot", "fmsr", "tsfm", "wo"]` to mark multi-domain. If AOB's metrics layer treats these as filters into AOB's general iot/fmsr/etc. servers, we get cross-talk. Either tag with `domain_tags: ["smart_grid_iot", ...]` or namespace differently. Decide in Q-NAMING.

### Phase 3 edge cases

- **AaT `parallel_tool_calls`** (PR `#134` v4). AOB's `OpenAIAgentRunner` doesn't expose this knob. Port adds a constructor arg. Default `False` for backward-compat with AOB callers.
- **MCP connection reuse** (PR `#134` v4 batch mode). AOB's runner spawns/teardowns MCP per-call. Our batch mode keeps connections alive. Port preserves this as opt-in via a new `reuse_mcp_connections=True` flag.
- **Verified PE replan loop.** AOB's `PlanExecuteRunner` doesn't have replan. Adding `VerifiedPlanExecuteRunner` introduces `verification.replans_used` to trajectories. AOB metrics layer must accommodate (or expose as opaque field via `extra='allow'`).
- **Self-Ask parent-clarification.** AOB plan_execute has a planner+executor split. Self-Ask hooks into the planner. Port preserves the AOB hook surface.

### Phase 4 edge cases

- **Test failures on AOB CI.** We don't know what AOB CI runs. Plan: dry-run AOB's full test suite locally on our feature branch before opening any upstream PR.
- **Branch protection / force-push prohibition.** Upstream AOB main may have branch protection. Our PR(s) must accommodate.
- **License compatibility.** AOB is Apache-2.0 (per `~/coding/AssetOpsBench/LICENSE`). Team repo doesn't currently have an explicit LICENSE file (Columbia coursework default). Confirm before extraction.

---

## Later-phase concerns (post-paper)

Items that don't block May 6 deadline but should be tracked:

- **Team-repo `mcp_servers/` removal.** Once Phase 4 lands upstream, the team repo can either keep its own copy (research artifact) or switch to depending on AOB. The latter is cleaner long-term but adds an external dependency to the paper-final repo.
- **Notebook 02/03 portability.** If a researcher wants to reproduce our analysis from an AOB checkout, the notebooks need to either move to AOB or be made path-portable. Not a Phase 0-4 task.
- **`scripts/run_experiment.sh` Slurm harness.** Genuinely repo-cluster-specific (Insomnia/Columbia). Stays in team repo; AOB readers run AOB's own benchmark CLI.
- **Cell C smoke artifact upstream.** Once PR `#134` lands in team repo with smoke artifact, that artifact + the corresponding `aat_runner` batch mode is upstream-able. Phase 3 of this plan captures the runner; the smoke artifact itself is paper-evidence and stays with the paper.
- **Future scenarios.** If we add scenarios beyond the current 11 during the final 5×6 capture push, those flow into AOB via the same Phase 2 mechanism (extend `smart_grid.json` array).
- **Failure-taxonomy classifications** (`#35`/`#64`/`#65`/`#66`). Once classified per `Final_Project/notes/2026-04-28_failure_taxonomy_plan.md`, those classifications could become AOB-side test cases for runners. Out of scope here.

---

## Cross-references

- Plan: [aob-extraction.md](aob-extraction.md)
- Backlog pin (b): `pm/backlog.md` 2026-04-27
- AOB upstream: https://github.com/IBM/AssetOpsBench
- Alex's fork: https://github.com/eggrollofchaos/AssetOpsBench
- AOB feat/evaluation-module branch tip: `fcff318`
- Live state context: `docs/coordination/live_repo_summary.md`
- Dhaval coordination: `Final_Project/planning/Dhaval_Email_Thread.md` (personal repo)
- Replay-phase analysis (separate but related): `docs/replay_phase_analysis.md`
- Y baseline 3.12 disclosure (separate but related): `docs/methods_python_version_disclosure.md`
