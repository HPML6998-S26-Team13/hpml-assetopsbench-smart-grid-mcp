# Failure Taxonomy + Evidence Table for `#35`

*Last updated: 2026-04-30*
*Owner: Alex Xin (lane), Akshat Bhandari (Round 1 reassignment for evidence
fill-in)*
*Issue: `#35`*

This doc carries the classification rules, taxonomy decision ladder, evidence
schema, and the populated evidence pass for `#35` (failure taxonomy
classification + evidence table). Its companion docs are
`docs/failure_visuals_mitigation.md` for `#64` (visuals + mitigation rubric)
and `docs/failure_analysis_scaffold.md` for `#36` (before/after metric pack).
This file used to live as one of three sections inside the combined
`docs/failure_analysis_scaffold.md`; it was split into its own surface on
2026-04-27 so each issue has its own reviewable PR.

## Primary inputs

- `benchmarks/cell_*/raw/<run-id>/` — raw run-level failures, trajectories,
  latencies
- `benchmarks/cell_*/summary.json` — aggregate per-run metrics
- `results/metrics/scenario_scores.jsonl` — judge score and pass-rate joins
  when populated
- `results/metrics/failure_evidence_table.csv` — current classified failure
  table, one row per judge-failed trial
- `docs/validation_log.md` — canonical proof runs and caveats
- `notebooks/03_orchestration_comparison.ipynb` — orchestration-level failure
  summaries
- `scripts/run_exp1_ab_capture.sh`, `scripts/replay_scenarios.sh` — A/B
  capture wrapper and profiler replay helper
- W&B runs / artifacts — preserved run context and profiling linkage

## Apr 27 status refresh

The canonical `team13/main` lane has advanced since the Apr 26 refresh:

- Cell A direct AaT smoke (`8962310_aat_direct_smoke_104`) and Cell B MCP
  baseline AaT smoke (`8969519_aat_mcp_baseline_smoke_104`) succeeded.
- Upstream AOB `OpenAIAgentRunner` parity smoke succeeded twice
  (`8970383_aat_mcp_baseline_upstream_smoke_104`,
  `8970468_aat_mcp_baseline_upstream_smoke_104`).
- Notebook 02 partial-readiness mode landed in PR `#123`; Notebook 03
  preliminary mode landed in PR `#136`.
- Experiment 1 A/B canonical captures landed in PR `#130`. Job `8979314`
  produced both `8979314_aat_direct` and `8979314_aat_mcp_baseline` over
  scenario set `smartgrid_multi_domain` on `Llama-3.1-8B-Instruct`. Both
  sides hit `success_rate=1.0` over 6 scenarios, so neither produced new
  failure evidence rows; their value to `#35` is the per-trial latency,
  tool-call, and `tool_error_count=0` baseline that any future PE-family
  rerun will be classified against.

These are readiness anchors, not final taxonomy evidence. They prove the AaT
A/B paths can execute and emit artifacts; they do not yet replace the
matched-trial `B/Y` or mitigation rerun evidence needed for final taxonomy
counts and before/after claims. The `under-constrained fault selection`
pattern stays at evidence grade `illustrative` until a second Y-cell
artifact reproduces it.

## Apr 30 status refresh

The taxonomy lane now has a first real CSV export:
`results/metrics/failure_evidence_table.csv`.

That file classifies the **35 judge-failed rows** in
`results/metrics/scenario_scores.jsonl` across the currently scored cells:
A, B, C, D, Y, Z, and ZSD. The export is still a judge-derived taxonomy pass,
not a hand-audited final paper table; its labels come from the six judge
dimensions, judge suggestions, and representative trajectory checks where the
failure class was ambiguous.

Current top-level counts:

| Taxonomy label | Rows | Read |
|---|---:|---|
| task verification failure | 18 | missing or empty evidence is not treated as a stop condition before final answer / work-order emission |
| inter-agent / orchestration failure | 13 | tool sequencing, tool-argument, or routing contracts break the intended execution path |
| specification failure | 4 | fault/risk adjudication remains under-specified even when some evidence is available |

Current symptom counts:

| Symptom | Rows | Candidate mitigation |
|---|---:|---|
| missing-evidence final answer | 18 | block final answers and work orders when required evidence retrieval fails or returns empty |
| tool routing or argument-contract failure | 7 | validate tool arguments and aliases before calls; hard-fail bad routing as explicit step errors |
| tool-call sequencing failure | 6 | require evidence acquisition before inference, risk estimation, or work-order creation |
| under-constrained fault/risk adjudication | 4 | add an explicit adjudication step that cites the deciding tool evidence |

Cell distribution in the current export:

| Cell | Failed rows classified |
|---|---:|
| Y | 9 |
| C | 6 |
| A | 5 |
| D | 5 |
| B | 4 |
| Z | 3 |
| ZSD | 3 |

The important read is not "C/D are bad" or "ZSD solves it." The sharper read
is that **clean execution and judge-quality success are separable**. Several
runs finish `success=True` while still failing the judge because they proceed
with missing evidence, wrong tool order, or under-justified fault
adjudication. That is exactly the failure-analysis story this table should
feed.

The representative-row audit gate is accepted for the current scaffold: every
row has a concrete artifact path, and representative rows from each symptom
class were checked against their judge-log artifacts before rendering the first
summary figures. If final reruns add or replace judge rows, rerun the renderer
and refresh this section rather than editing the counts by hand.

## Classification rule

Use the Berkeley categories as the top-level taxonomy:

- **Specification failure**: the agent misunderstood the task, failed to ask
  for clarification, or pursued the wrong goal
- **Inter-agent / orchestration failure**: the planner, executor, verifier, or
  tool-calling loop lost coordination or passed stale / bad context
- **Task verification failure**: the system failed to validate whether an
  action actually worked or whether the observed result was trustworthy

Do not classify from vibes. Every label must point back to a concrete run
artifact and a quoted or paraphrased trajectory symptom.

## Taxonomy decision ladder

Use the narrowest label that explains the failure while still matching the
concrete artifact symptom.

| If the concrete failure is mainly that... | Use this label |
|---|---|
| the run pursued the wrong task framing, wrong fault hypothesis, or wrong success criterion before downstream execution even had a fair chance | specification failure |
| the planner / executor / verifier / tool-routing layer lost coordination, passed bad context, called the wrong surface, or hid a routing-contract break | inter-agent / orchestration failure |
| the system observed contradictory or weak evidence, but still emitted an unearned confident answer or success bit | task verification failure |

### Tie-break rule

When more than one label looks plausible:

1. identify the **latest irreversible mistake** visible in the artifact
2. label the row from that point of failure
3. mention upstream contributors in `evidence_note`, not as separate labels

This avoids double-counting one bad run under every category it touched.

### Failure-stage assignment rule

Use the earliest stage where the run becomes observably unrecoverable:

- `planning`: the plan is already wrong or under-constrained
- `tool selection`: wrong tool or wrong evidence source chosen
- `tool execution`: the tool call itself fails, routes incorrectly, or
  returns unusable output that the wrapper mishandles
- `verification`: the run has enough evidence to notice a conflict or failed
  action, but the check is missing or ignored
- `final answer`: the run reaches the answer / work-order layer with
  unresolved contradictions or unearned confidence

## Evidence table schema

This is the table `#35` should eventually fill.

| Column | Meaning |
|---|---|
| `run_name` | stable run identifier from benchmark / W&B |
| `cell` | `A`, `B`, `C`, `Y`, `Z` |
| `orchestration_mode` | `agent_as_tool`, `plan_execute`, `verified_pe` |
| `mcp_mode` | `direct`, `baseline`, `optimized` |
| `scenario_id` | scenario identifier or scenario filename |
| `trial_index` | repeated-run index |
| `failure_stage` | planning, tool selection, tool execution, verification, final answer |
| `taxonomy_label` | Berkeley category |
| `symptom` | short human-readable description |
| `artifact_path` | raw JSON / log / W&B artifact used as evidence |
| `evidence_note` | the concrete reason for the label |
| `candidate_mitigation` | likely fix or guardrail |
| `priority` | `must-fix`, `should-fix`, `watch` |

Historical validation-only rows may temporarily use `n/a` for `scenario_id`
or `trial_index` when the raw scenario JSON is not committed in-tree. The
final exported CSV for notebook joins should backfill concrete values
wherever the raw benchmark artifacts exist. Rows in the populated pass below
that show `n/a` for these columns are historical-only entries from
`docs/validation_log.md`; treat any row with concrete `scenario_id` /
`trial_index` as paper-citable, and any row with `n/a` as discussion-only
until a matched canonical capture lands.

The CSV target is `results/metrics/failure_evidence_table.csv` (schema owned
by `#36` export contract; populated rows produced under `#35`; see
`docs/failure_analysis_scaffold.md`). As of 2026-04-30 it contains 35
judge-failed rows. The next pass should manually audit representative rows
before the paper cites exact category counts.

## Initial evidence pass (Apr 22)

This is the historical first populated pass using artifacts already available on
canonical history or explicitly cited in `docs/validation_log.md`. It is
enough to start the mitigation discussion without pretending the full
experiment matrix is already captured.

| run_name | cell | orchestration_mode | mcp_mode | scenario_id | trial_index | failure_stage | taxonomy_label | symptom | artifact_path | evidence_note | candidate_mitigation | priority |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `local-20260413-003914_pe_mcp_baseline_watsonx_smoke` | Y | `plan_execute` | `baseline` | `multi_01_end_to_end_fault_response` | `1` | final answer | task verification failure | final answer and work order choose low-temperature overheating even though `analyze_dga` returned `Normal / Inconclusive` | `benchmarks/cell_Y_plan_execute/raw/local-20260413-003914_pe_mcp_baseline_watsonx_smoke/2026-04-13_Y_llama-3-3-70b-instruct_plan_execute_baseline_multi_01_end_to_end_fault_response_run01.json` | Step 5 returns dataset `fault_label = Low-temperature overheating`, Step 6 returns IEC diagnosis `Normal / Inconclusive`, and the answer never resolves the conflict before writing the work order | add explicit conflict-resolution / evidence-consistency check before final answer and WO creation | must-fix |
| `issue18-smartgrid-smoke` | Y | `plan_execute` | `baseline` | `sgt003_t012_dga` | `1` | final answer | task verification failure | the scenario answer locks onto low-temperature overheating even though the formal DGA tool again returns `Normal / Inconclusive` | `benchmarks/cell_Y_plan_execute/raw/issue18-smartgrid-smoke/sgt003_t012_dga_run01.json` | The runner uses the dataset label and keyword search path after Step 2 contradicts the formal diagnostic output, which suggests a recurring failure mode rather than a one-off | require the chosen fault mode to cite the deciding tool output, not just any supporting label-like field | must-fix |
| `validation_8760652` | Y | `plan_execute` | `baseline` | `n/a` | `n/a` | planning | specification failure | the plan ships without an explicit fault-selection adjudication step, and the run later drifts to `Partial Discharge` | `benchmarks/validation_output.json; benchmarks/validation_8760652.log` | The plan lists `list_failure_modes -> search_failure_modes -> get_sensor_correlation` without a clear explicit adjudication step before downstream tool selection. Per the failure-stage rule (earliest stage where the run becomes observably unrecoverable), the unrecoverable point is at `planning` — the missing adjudication step is what causes the later `tool selection` to drift. Final answer converges on `FM-001 Partial Discharge` even though the task began from a thermal-overload symptom description | tighten PE prompts so probable-fault selection must be justified from named tool evidence before downstream actions | should-fix |
| `8850716_pe_self_ask_mcp_baseline_smoke` | Y | `plan_execute` | `baseline` | `n/a` | `n/a` | tool execution | inter-agent / orchestration failure | one scenario ends with terminal `Unknown server 'none'` while the wrapper still reports the run as completed | `docs/validation_log.md` | This is a concrete routing-contract failure between the runner and the tool layer; the validation log cites the failed terminal step and W&B run `y42u88h3` even though the raw per-scenario JSON is not committed in-tree | hard-fail unknown-server / bad-routing conditions and normalize them into explicit step errors | must-fix |
| `8851966_verified_pe_mcp_baseline_smoke` | Z | `verified_pe` | `baseline` | `n/a` | `n/a` | verification | task verification failure | wrapper summary reports `pass=2` even though raw scenario outputs contain semantic failures | `docs/validation_log.md` | The benchmark accounting layer masked a real failure; the validation log cites the semantic mismatch and links the historical W&B run `0v3a5jqi` even though the raw per-scenario JSON is not committed in-tree | keep atomic error-promotion + success-accounting normalization in the runner and verify reruns against raw outputs | must-fix |

### Initial pattern read

This first pass already shows a useful shape:

- **Task verification failures dominate** the initial evidence set.
- The most dangerous pattern is **answer/tool inconsistency**: the run
  gathers evidence that conflicts internally, then still produces a
  clean-sounding final answer.
- The second dangerous pattern is **wrapper-level masking**: tool-routing or
  semantic failures are easy to undercount if the benchmark summary trusts
  the top-level success bit too much.
- We have at least one plausible **specification failure** pattern as well:
  fault selection can become under-constrained when the prompt/plan does not
  force an explicit adjudication step between competing candidate
  mechanisms.

### Evidence standard for paper use

Use three evidence grades so the paper does not overstate what the repo has
actually shown:

| Grade | Standard | How to use it in prose |
|---|---|---|
| illustrative | one concrete artifact-backed example | "we observed an example of..." |
| recurring | at least two distinct artifact-backed examples with the same pattern | "a recurring failure mode was..." |
| mitigated | a recurring pattern plus an explicit before/after rerun pair | "the mitigation reduced..." |

Current grade by pattern:

- missing-evidence final answer: **recurring** (18 judge-failed rows)
- tool routing or argument-contract failure: **recurring** (7 judge-failed rows)
- tool-call sequencing failure: **recurring** (6 judge-failed rows)
- under-constrained fault / risk adjudication: **recurring with cautious
  wording** (4 judge-failed rows)

That means the paper can safely say the current scored artifact set shows
repeated **evidence-grounding** and **orchestration-contract** failures. The
specification/adjudication pattern is also repeated in the judge-derived table,
but should still be phrased more cautiously than the dominant evidence-grounding
pattern because it is lower-count and more interpretation-heavy.

### Paper-safe wording guide

Use wording that matches the evidence grade rather than the severity of the
story we wish we had:

| Grade | Safe wording |
|---|---|
| illustrative | "we observed an example where..." |
| recurring | "we repeatedly observed..." / "a recurring failure mode was..." |
| mitigated | "after applying the mitigation, the rerun artifacts show..." |

Do **not** use frequency words like "often", "most", or "typically" unless
the exported table actually supports that count on comparable artifacts.

## Classification workflow

1. Pull failed or weak runs from the latest comparable cell artifacts.
2. Read the raw scenario JSON and relevant history / error fields.
3. Assign a failure stage first.
4. Assign the Berkeley taxonomy label second.
5. Capture one concrete evidence note, not just a label.
6. Group repeated symptoms before proposing mitigations.

The goal is not a giant spreadsheet. The goal is a defensible set of
recurring failure patterns we can cite in the paper and act on in code.

## Artifact readiness ledger

Track successful readiness proofs separately from classified failures so the
paper does not mix "runner is alive" with "failure pattern was observed."

| run_name | cell | status | What it supports | What it does not support yet |
|---|---|---|---|---|
| `8962310_aat_direct_smoke_104` | A | smoke success | direct-tool AaT path and artifact contract are runnable | final A-cell latency distribution or failure rates |
| `8969519_aat_mcp_baseline_smoke_104` | B | smoke success | MCP-baseline AaT path and shared Cell B artifact shape are runnable | final shared `B/Y` orchestration comparison |
| `8979314_aat_direct` | A | canonical capture | 6/6 scenario success on canonical scenario set; baseline latency / tool-call / tool-error metrics for any future PE-family or mitigation classification against this scenario set | judge-score, MCP latency, token, and profiling sample dims still NULL on the capture |
| `8979314_aat_mcp_baseline` | B | canonical capture | 6/6 scenario success on canonical scenario set; baseline metrics for AaT MCP baseline against the same scenario set as `8979314_aat_direct` | same NULL columns as `8979314_aat_direct`; no failure rows produced (success_rate=1.0) |
| `8970383_aat_mcp_baseline_upstream_smoke_104` | B parity | smoke success | upstream AOB runner parity against Smart Grid MCP servers | final performance comparison |
| `8970468_aat_mcp_baseline_upstream_smoke_104` | B parity | repeat smoke success | parity result is repeatable on the same smoke scenario | final performance comparison |
| `9071639_aat_mcp_optimized` | C | canonical capture | optimized MCP Cell C executes 6/6 and supports the first real `(B-C)` transport comparison | judge pass remains 0/6; taxonomy rows show execution success does not imply answer quality |
| `9073472_aat_mcp_model_optimized` | D | exploratory capture | optimized-serving AaT arm executes 6/6 with INT8/BF16/fp8-KV proof | exploratory only; judge pass 1/6 and not part of clean A/B/C fairness contract |
| `9074775_exp2_cell_ZSD_verified_pe_self_ask_mcp_model_optimized` | ZSD | exploratory capture | Verified PE + Self-Ask + optimized MCP + optimized serving executes 6/6; judge mean is 0.611 | best-engineered ablation, not a clean core-matrix cell |

## Minimum deliverable definition

For `#35`:

- one populated evidence table with the dominant failure patterns
- each cited paper failure mode grounded in at least one concrete artifact

## Next fill targets

The artifact gap that still bounds this lane:

1. keep `failure_evidence_table.csv` refreshed if final scenario/rerun sweeps
   add judge rows
2. use `results/figures/failure_taxonomy_counts.svg` and
   `results/figures/failure_stage_cell_heatmap.svg` for the first #64 figure
   pass
3. implement or explicitly defer the selected `#65/#66` mitigation lane:
   `missing_evidence_final_answer_guard`
