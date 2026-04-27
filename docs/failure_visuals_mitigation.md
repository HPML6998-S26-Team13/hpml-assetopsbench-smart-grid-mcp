# Failure Visuals + Mitigation Plan for `#64`

*Last updated: 2026-04-27*
*Owner: Alex Xin (strategy lane stays here for `#64`)*
*Issue: `#64`*

This doc carries the visuals plan, figure-ready aggregation contract,
mitigation ranking rubric, the initial Apr 22 mitigation ranking, and the
mitigation-experiment promotion gate for `#64` (failure taxonomy visuals +
mitigation plan). Companion docs are `docs/failure_taxonomy_evidence.md` for
`#35` (taxonomy + populated evidence pass) and
`docs/failure_analysis_scaffold.md` for `#36` (before/after metric pack and
export contract). This file used to live as one of three sections inside the
combined `docs/failure_analysis_scaffold.md`; it was split into its own
surface on 2026-04-27 so each issue has its own reviewable PR.

## Primary inputs

- `results/metrics/failure_evidence_table.csv` — primary table behind
  taxonomy and stage figures (owned by `#36` export contract; populated by
  `#35`)
- `results/metrics/mitigation_run_inventory.csv` — primary table behind the
  mitigation priority figure
- `results/metrics/mitigation_before_after.csv` — primary table behind the
  before/after comparison figure
- `docs/failure_taxonomy_evidence.md` — labels and pattern reads that justify
  each mitigation rank
- `docs/validation_log.md` — canonical run-history index for the rerun pairs

## Apr 27 status refresh

The canonical `team13/main` lane has advanced since the Apr 26 refresh:

- Cell A direct AaT smoke and Cell B MCP baseline AaT smoke succeeded;
  upstream AOB parity smoke succeeded twice.
- Notebook 02 partial-readiness mode landed in PR `#123`; Notebook 03
  preliminary mode landed in PR `#136`.
- Experiment 1 A/B canonical captures landed in PR `#130` with WandB +
  `nvidia-smi` + `torch.profiler` integration.

These are figure-readiness anchors for downstream visuals: the canonical Cell
A/B captures are the first artifacts where a mitigation rerun can plausibly
land in the same scenario set that the figures cite.

## Visuals scaffold

Recommended outputs:

| Output | Purpose |
|---|---|
| failure taxonomy count bar chart | which failure classes dominate |
| failure stage x cell heatmap | where each orchestration fails in the pipeline |
| mitigation priority table | what we fix first and why |
| before/after comparison figure | whether the chosen mitigation changed outcomes |

Recommended narrative structure:

1. what failed most often
2. what was cheapest / most credible to fix
3. what we implemented
4. what improved after rerun

### Figure-ready aggregation contract

Each visual should have one explicit source table so the notebook and paper
lane do not quietly diverge:

| Figure / table | Source table | Row grain |
|---|---|---|
| failure taxonomy count bar chart | `results/metrics/failure_evidence_table.csv` | one row per `(run_name, scenario_id, trial_index)` evidence item |
| failure stage x cell heatmap | `results/metrics/failure_evidence_table.csv` | one row per evidence item with `cell` and `failure_stage` populated |
| mitigation priority table | `results/metrics/mitigation_run_inventory.csv` | one row per mitigation lane |
| mitigation before/after figure | `results/metrics/mitigation_before_after.csv` | one row per `(lane, phase, run_name)` |

Each figure renders from one named CSV and no other source. This avoids the
common failure where a figure pulls from raw run JSON for a few cases and
the exported table for the rest, producing inconsistent counts between the
notebook and the paper.

## Mitigation ranking rubric

Use these four questions:

| Question | Why it matters |
|---|---|
| Does this failure happen often enough to matter? | avoid chasing one-off noise |
| Does it damage correctness or benchmark credibility? | prioritize real risk |
| Is there a bounded mitigation we can implement this week? | keep scope realistic |
| Would the paper story get stronger if we fixed it? | connect code work to deliverable value |

Initial candidate mitigations already visible in repo history:

- Self-Ask clarification for PE-family runners
- verifier-gated retries / suffix replanning in Verified PE
- better transport path through MCP optimization
- stronger runtime / tool-error normalization in runner outputs
- context compaction / prompt-size controls for verifier-heavy runs

## Initial mitigation ranking (Apr 22)

| Rank | Mitigation | Why it matters | Status |
|---|---|---|---|
| 1 | strict success accounting + atomic error promotion | prevents the benchmark from silently counting broken runs as clean evidence | partly landed; keep as required baseline |
| 2 | final-answer evidence consistency check | closes the most dangerous correctness gap now visible in committed Y-cell artifacts | not yet explicit |
| 3 | unknown-server / invalid-routing hard fail | turns orchestration-contract bugs into obvious failures instead of muddled completions | partly visible in rerun history; should remain enforced |
| 4 | Self-Ask on ambiguous PE-family tasks | cheap clarification hook for under-specified reasoning tasks | implemented as follow-on mitigation in `scripts/plan_execute_self_ask_runner.py` |
| 5 | verifier-gated retry / suffix replan | helps recover from bad intermediate steps without restarting the whole run | implemented in Z lane in `scripts/verified_pe_runner.py` |
| 6 | MCP-optimized transport for PE-family follow-ons | worthwhile after correctness/verification fixes, but not the first mitigation to prioritize | future follow-on |

### Why this order

- Ranks 1-3 are about **trusting the artifacts at all**.
- Ranks 4-5 are about **improving agent behavior once the accounting surface
  is honest**.
- Rank 6 is valuable, but it should not outrank correctness and verification
  fixes.

## Mitigation experiment card

Every mitigation promoted from `#64` into `#65` / `#66` should be written as
one bounded experiment card before implementation or rerun:

| Field | What to write |
|---|---|
| `mitigation_name` | short stable name |
| `target_pattern` | which failure pattern it addresses |
| `hypothesis` | one-sentence expected effect |
| `before_run` | concrete run ID or run family used as the baseline |
| `after_run_plan` | which rerun should prove the change |
| `primary_metric` | one metric that decides success |
| `secondary_metrics` | supporting metrics only |
| `stop_condition` | what result means the mitigation is not worth scaling |

### Promotion gate into `#65` / `#66`

Only promote a mitigation into implementation / rerun when all of these are
true:

1. the failure pattern is at least **recurring** or is an **illustrative**
   correctness bug severe enough to threaten benchmark trust
2. there is one bounded implementation point rather than a fuzzy prompt
   rewrite
3. there is a like-for-like rerun lane that keeps the comparison honest
4. the paper can explain the mitigation in one sentence without inventing a
   new benchmark axis

### Test of boundedness (criterion 2)

A mitigation is **bounded** when it can be expressed as either:

- one named function added to one named runner module, with a single call
  site (e.g., a `check_evidence_consistency()` helper called from one
  `_finalize_answer()` path), or
- a typed config knob already present in the runner, plus one if-branch
  that consumes it (e.g., raise `tool_error` when `routing_strict=True`),

and the rerun command line that invokes the mitigation is identical to the
baseline command line except for one flag, one config file, or one env
variable.

A mitigation is **fuzzy** (and therefore not promotable under criterion 2)
when it requires:

- editing a free-form prompt without a deterministic check that the edit
  did what was intended, or
- changing the runner's behavior in ways that touch more than one tool /
  step / verifier surface at once, or
- a rerun command line that diverges from the baseline in a way the
  diff-against-baseline cannot show in one line.

## Worked card: rank-2 first promotion

The first concrete mitigation card under the rubric above. Targets the
dominant `task verification failure` pattern surfaced by PR `#138`'s
populated evidence pass.

| Field | Value |
|---|---|
| `mitigation_name` | `final_answer_evidence_consistency_check` |
| `target_pattern` | answer/tool inconsistency: final answer or work order disagrees with the deciding tool's named output (PR #138 rows 1 and 2) |
| `hypothesis` | adding a deterministic check that compares the chosen fault label against the formal diagnostic tool's named output before final answer / WO emission will eliminate the answer/tool inconsistency pattern in PE-family runs |
| `before_run` | `local-20260413-003914_pe_mcp_baseline_watsonx_smoke` and `issue18-smartgrid-smoke` (both Y-cell, plan_execute, baseline; both currently `must-fix` priority) |
| `after_run_plan` | rerun the same scenario set under PE-baseline with the consistency check enabled; capture into `benchmarks/cell_Y_plan_execute/raw/<job>_pe_evidence_consistency_check/` |
| `primary_metric` | count of rows whose taxonomy_label flips from `task verification failure` (final answer stage) to clean on the after-side of `failure_evidence_table.csv` |
| `secondary_metrics` | `success_rate`, `judge_pass_rate` if judge data exists, `latency_seconds_mean` (cost of the check) |
| `stop_condition` | the mitigation does not flip at least the two named runs to clean, OR `latency_seconds_mean` rises by more than 25% on the after-side |

Boundedness: implements as one helper function in
`scripts/plan_execute_runner.py` (or a new wrapper module) called from one
finalize-answer path; rerun command differs from the baseline by one
config flag (e.g. `--enable-evidence-consistency-check`). Passes the
boundedness test.

Promotion gate check:

1. `recurring` evidence grade — yes (rows 1 and 2 in PR #138's pass)
2. one bounded implementation point — yes (see boundedness above)
3. like-for-like rerun lane — yes (same scenario set, same runner, one
   config flag toggles the mitigation)
4. paper-explainable in one sentence — yes ("the runner refuses to emit a
   final answer whose chosen fault label is not supported by the deciding
   diagnostic tool's named output")

Recommended owner: aligns with `#65` (Implement chosen mitigations); after
W5 reassignment proposal, that issue is owned by Akshat. The boundedness
condition keeps the implementation small enough that #65 can absorb it
without changing scope.

## Minimum deliverable definition

For `#64`:

- one visual summary of failure classes
- one written mitigation priority list with rationale

## Paper handoff note

The paper should separate:

- **baseline comparison findings** from the core experiment matrix
- **mitigation findings** from the failure-analysis lane

That keeps the story honest. Self-Ask or verifier improvements should read
as measured follow-on fixes, not as something silently baked into the
baseline.

## Next fill targets

The artifact gap that still bounds this lane:

1. populated rows on `failure_evidence_table.csv` (schema owned by `#36`
   export contract; populated rows produced under `#35`) so the taxonomy
   bar chart and the stage-by-cell heatmap have real counts, not
   illustrative placeholders
2. one matched mitigation rerun pair where both the before and after rows are
   populated end-to-end on `mitigation_before_after.csv` so the comparison
   figure is `comparison_ready` (per `#36` status labels)
3. agreement on which one mitigation goes first into `#65` / `#66` (current
   recommendation: rank 2, final-answer evidence consistency check, since it
   targets the dominant `task verification failure` pattern)
