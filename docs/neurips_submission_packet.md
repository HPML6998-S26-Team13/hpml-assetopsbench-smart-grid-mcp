---
status: active-draft
scope: team-repo deliverable drafting
owner: Team 13
canonical: true
---

# NeurIPS 2026 Submission Packet

*Last updated: 2026-05-07. Stale-overlay refresh: 2026-05-10.*
*Owner: Alex Xin*
*Issues: #5, #39, #47, #48, #88, #181, #182*

> **Stale-overlay 2026-05-10 (post-NeurIPS submission, post-PR #199):** Body
> below is the May 7 submission-packet snapshot. NeurIPS submission landed on
> 2026-05-07 (OpenReview `scKKXyNaQG`; #182 closed). Repo state has moved
> since:
>
> - **Paper-grade canonical corpus stays at 36** scenarios (31 hand-authored +
>   5 promoted generated) + 5 negative fixtures. Frozen at 2026-05-07 NeurIPS
>   submission. The submitted paper claims 36; the hosted reviewer artifact
>   snapshot `d606d10765e1ec97e97e3683f6a3794ecf64bb17` matches the same
>   paper-grade corpus.
> - **Repo current corpus**: `data/scenarios/` now has 61 scenario files
>   because PR #199 (#55 batch A and B) ported in 25 additional scenarios
>   post-submission. Those 25 are NOT judged/validated and are deliberately
>   excluded from paper, deck, and CourseWorks claims.
> - **Result-table evidence floor stays 31 hand-authored, post-PR175** —
>   unchanged from May 7.
> - **Rows below that say "scenario floor reaches 36" / "use 36 validated
>   scenarios"** still hold for the submitted paper; the additional 25 in the
>   repo do not change submitted claims.
>
> Do not edit the May 7 body to "update" the corpus number — keep snapshot
> intact and rely on this overlay for current truth.

---

This packet is the deadline-facing control surface for the NeurIPS 2026
Evaluations & Datasets submission. It summarizes what can already go into the
paper, what still needs a final evidence pass, and where the LaTeX submission
surface lives. NeurIPS previously used the Datasets & Benchmarks track name for
this submission lane.

## Submission Surface

| Field | Current value |
|---|---|
| Venue | NeurIPS 2026 Evaluations & Datasets Track (formerly Datasets & Benchmarks) |
| Abstract deadline | 2026-05-04 23:59 AOE |
| Abstract submission status | Submitted on OpenReview: https://openreview.net/forum?noteId=scKKXyNaQG |
| Full-paper deadline | 2026-05-06 23:59 AOE |
| Overleaf project | https://www.overleaf.com/project/69f5a380e638a31066dc0bd1 |
| Template status | Official NeurIPS 2026 template ingested in Overleaf Git commit `7e361de` |
| Content status | First real paper draft populated in Overleaf commit `4a85633` |
| Template source | https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip |
| LaTeX mode | anonymous `eandd` via `\usepackage[eandd]{neurips_2026}` |
| Checklist | `checklist.tex` added to Overleaf; content still needs final answers |
| Overleaf transfer plan | `docs/neurips_overleaf_transfer_plan.md` |
| Reviewer artifact URL | https://huggingface.co/datasets/garn-garn/smartgridbench-review-artifact |
| OpenReview Code URL | https://huggingface.co/datasets/garn-garn/smartgridbench-review-artifact/tree/main/code |
| Croissant metadata URL | https://huggingface.co/datasets/garn-garn/smartgridbench-review-artifact/resolve/main/croissant.json |
| Hosted artifact SHA | `881f9f27fa216519f4af54336323609be31ae486` |
| Team repo SHA before artifact-ledger doc update | `c5e051ee751d3876d543395dc4887b3d7f7791d3` |
| Artifact source snapshot SHA | `9dece6a16daa9b68398d140993e3b02d4dcd83e4` |
| Anonymous code snapshot SHA | `64ce4792ab83ebebbc6c1c24013ed177c667ddef` |
| Artifact import SHA | `4b3523cca79aa119ab7fccb51e4ce9ce0f868749` |
| Evidence capture floor SHA | `1913c6e4703425f735d8cb8297cb890ba66bbeff` |
| Artifact license | CC BY 4.0 for reviewer artifact data/docs/scenarios; project code remains MIT |
| Final PDF SHA-256 | Pending final PDF export |
| Full submission URL | Pending final full-paper upload |

## Reviewer Artifact Record

The anonymous reviewer artifact is hosted on Hugging Face at
https://huggingface.co/datasets/garn-garn/smartgridbench-review-artifact. It
currently contains the 31-scenario catalog, canonical scenario JSON files, negative
schema fixtures, paper-grade evidence registry, 37-row-group summary tables,
2,420 compact judge-score rows, the 12-row manual judge audit, a file manifest,
provenance notes, validation notes, manual Croissant metadata, and an
anonymized executable code package under
https://huggingface.co/datasets/garn-garn/smartgridbench-review-artifact/tree/main/code.

Use the artifact SHA
`881f9f27fa216519f4af54336323609be31ae486` as the hosted snapshot identifier in
the submission ledger. The artifact package was assembled from source snapshot
`9dece6a16daa9b68398d140993e3b02d4dcd83e4`, includes the artifact import commit
`4b3523cca79aa119ab7fccb51e4ce9ce0f868749`, includes anonymous executable code
from team snapshot `64ce4792ab83ebebbc6c1c24013ed177c667ddef`, and traces the
main evidence captures to floor SHA `1913c6e4703425f735d8cb8297cb890ba66bbeff`.

If the final paper cites the post-PR195 36-scenario corpus or the current
failure-taxonomy figure, refresh this hosted artifact before final upload or
explicitly caveat the artifact as the 31-scenario reviewer snapshot.

OpenReview Code URL to use during double-blind review:
https://huggingface.co/datasets/garn-garn/smartgridbench-review-artifact/tree/main/code.
Do not point reviewers at the non-anonymous Team 13 GitHub repo during
double-blind review.

## Working Title

**SmartGridBench: MCP-Based Industrial Agent Benchmarking for Smart Grid
Transformer Operations**

## Submission-Ready Abstract Candidate

Word count: 182 words. Use this exact text for the NeurIPS abstract submission
unless a final evidence gate changes before upload.

Industrial-agent benchmarks under-cover Smart Grid transformer diagnostics and
maintenance, even though these workflows require multi-tool reasoning across
telemetry inspection, fault diagnosis, degradation forecasting, and work-order
planning. We present SmartGridBench, a Smart Grid transformer-maintenance
extension of AssetOpsBench with transformer scenarios, public-data-backed asset
records, and four tool domains exposed through the Model Context Protocol
(MCP). The benchmark makes two usually conflated systems choices measurable:
the transport cost of MCP relative to direct tool invocation, and the
behavioral effect of Agent-as-Tool, Plan-Execute, and Verified Plan-Execute
orchestration when the tool surface is held fixed. Current artifacts show a
runnable end-to-end benchmark path with committed scenario outputs, profiling
links, Weights & Biases runs, LLM-as-judge scores, and failure-taxonomy
exports. Preliminary six-trial captures show measurable MCP overhead in direct
comparisons, steady-state latency reductions from persistent optimized MCP
sessions, and quality shifts from PE-family mitigations such as Self-Ask and
verification. We also treat scenario realism, generated-scenario circularity,
and failure accounting as first-class benchmark artifacts rather than post-hoc
notes. SmartGridBench therefore contributes both a new industrial benchmark
domain and an auditable systems study of protocol and orchestration choices in
tool-using agents.

## Claim Tiers

| Tier | Claim | Evidence now | Paper stance |
|---|---|---|---|
| Safe | SmartGridBench adds a Smart Grid transformer-maintenance lane over AssetOpsBench. | `data/`, `mcp_servers/`, `data/scenarios/`, `docs/data_pipeline.tex` | Main contribution. |
| Safe | The repo has direct-tool, MCP-baseline, and optimized-MCP AaT paths with committed artifacts. | Post-PR175 paper-grade rows in `results/metrics/evidence_registry.csv`, `results/metrics/gcp_post175_core31_summary.csv`, and `results/metrics/gcp_post175_final_summary.csv` | Main 31-scenario core evidence for A/B/C; scenario catalog now contains 36 validated rows after PR #195. |
| Safe | The repo has Plan-Execute, Verified PE, and PE-family Self-Ask follow-ons with judge outputs. | Post-PR175 paper-grade rows in `results/metrics/evidence_registry.csv`, `results/metrics/gcp_post175_core31_summary.csv`, and `results/metrics/gcp_post175_final_summary.csv` | Main 31-scenario orchestration result for Y/YS/Z/ZS, plus 15-scenario follow-on/extra rows. |
| Safe | Failure analysis is artifact-backed. | `results/metrics/failure_taxonomy_current.csv`, `results/metrics/failure_taxonomy_current_auto_label_counts.csv`, and `results/figures/failure_taxonomy_current_auto_label_counts.svg` | Main reliability/evaluation contribution; older 35-row `failure_evidence_table.csv` is historical only. |
| Safe | The LLM judge has a small manual sanity audit. | `results/metrics/manual_judge_audit.csv` has 12 stratified mitigation trajectories from the now-superseded post-PR180 cohort with 12/12 judge/manual pass-label agreement | Use only as a judge-calibration sanity check; current paper-grade mitigation evidence is the post-PR175 cohort. |
| Safe | Scenario floor reaches 36 validated scenarios. | PR #195 promoted five bounded-edit generated scenarios on top of the 31-scenario post-PR175 corpus; `python3 data/scenarios/validate_scenarios.py` passes 36 scenarios + 5 negative fixtures | Use "36 validated scenarios" for benchmark-corpus claims; keep result-table claims scoped to the 31-scenario post-PR175 evidence floor where appropriate. |
| Safe with caveat | Mitigation ladder has post-PR175 before/after evidence. | `results/metrics/evidence_registry.csv` marks `mitigation15_4tier` rows as paper-grade; `results/metrics/gcp_post175_mitigation_4tier_summary.csv` has the matched 15-scenario x 5-trial ladder | Report mixed effects. The ladder is evidence-backed but does not support a universal mitigation-lift claim. |
| Safe with caveat | Hosted WatsonX 70B rows strengthen generality. | `results/metrics/evidence_registry.csv` marks the post-PR175 70B rows as paper-grade; `results/metrics/gcp_post175_70b_summary.csv` summarizes 15-scenario main/top-up rows | Core scaling evidence exists for 15 scenarios; all-36/all-50 70B remains future extension work. |

## Section Plan

| Section | Draft content to transfer |
|---|---|
| 1. Introduction | Benchmark gap, Smart Grid maintenance stakes, protocolized tool-use cost, and why transport/orchestration must be separated. |
| 2. Benchmark Extension | Dataset sources, shared `transformer_id`, four tool domains, scenario schema, realism controls, 36 validated scenarios, and generated-scenario disposition/promotion rules. |
| 3. System Design | MCP servers, direct adapter for Cell A, persistent MCP path for Cell C, run artifact contract, WandB/profiler linkage. |
| 4. Experimental Design | Experiment 1 A/B/C transport axis; Experiment 2 B/Y/Z orchestration axis; PE-family Self-Ask/Verified follow-ons. |
| 5. Results | Notebook 02 latency summary, Notebook 03 orchestration/judge table, failure taxonomy counts, and mitigation status. |
| 6. Limitations | Result tables scoped to the 31-scenario post-PR175 evidence floor, generated-scenario circularity, all-36/all-50 70B future work, and mixed mitigation effects. |
| 7. Reproducibility | Artifact ledger, run IDs, repo paths, Overleaf source, and NeurIPS checklist. |

## Immediate Overleaf Population Plan

This is the next practical writing block. We can populate Overleaf now without
waiting for final reruns:

1. Paste the title, abstract candidate, and contribution paragraph.
2. Paste Introduction, Benchmark Extension, System Design, Experimental Design,
   Results Skeleton, Failure Analysis, Limitations, and Reproducibility from
   `docs/neurips_draft.md`.
3. Insert the paper-final core table from
   `results/metrics/gcp_post175_core31_summary.csv` for A/B/C/Y/YS/Z/ZS.
   The earlier six-trial notebook tables can remain as preliminary calibration
   or appendix material only, with explicit `n=6` disclosure.
4. Add TODO markers for artifact refresh, repeated transport distribution,
   mitigation caveats, references, checklist answers, and compile proof.
5. Insert figures only after captions include source CSV paths or run IDs.

The detailed copy order and caveats live in
`docs/neurips_overleaf_transfer_plan.md`. Issue #39 tracks the Overleaf content
transfer; issue #40 / #78 track the later IEEE report back-port.

## Current Results Snapshot

### Experiment 1 - Transport Axis

| Cell | Meaning | Run | Trials | p50 latency | p95 latency | Judge mean | Judge pass |
|---|---|---|---:|---:|---:|---:|---:|
| A / AT-I | Agent-as-Tool direct Python tools | `8979314_aat_direct` | 6 | 12.15s | 17.29s | 0.167 | 1/6 |
| B / AT-M | Agent-as-Tool MCP baseline | `8979314_aat_mcp_baseline` | 6 | 13.09s | 16.27s | 0.278 | 2/6 |
| C / AT-TP | Optimized MCP transport + prefix cache | `9071639_aat_mcp_optimized` | 6 | 7.40s | 47.93s | 0.167 | 0/6 |

Interpretation for draft prose: optimized persistent MCP improves steady-state
latency after the first cold trial, but quality does not automatically improve
with transport optimization. Keep Cell C quality caveats prominent.

### Experiment 2 - Orchestration Axis

| Cell | Meaning | Run | Success rate | p50 latency | Judge mean | Judge pass |
|---|---|---|---:|---:|---:|---:|
| B / AT-M | Agent-as-Tool MCP baseline | `8979314_aat_mcp_baseline` | 1.0 | 13.09s | 0.278 | 2/6 |
| Y / PE-M | Plan-Execute MCP baseline | `8998340_exp2_cell_Y_pe_mcp_baseline` | 0.5 | 52.06s | 0.111 | 0/6 |
| Z / V-M | Verified Plan-Execute MCP baseline | `8998342_exp2_cell_Z_verified_pe_mcp_baseline` | 1.0 | 119.64s | 0.639 | 4/6 |
| YS / PE-S-M | Plan-Execute + Self-Ask | `8998341_exp2_cell_Y_pe_self_ask_mcp_baseline` | 1.0 | 59.00s | 0.444 | 3/6 |
| ZS / V-S-M | Verified PE + Self-Ask | `8998343_exp2_cell_Z_verified_pe_self_ask_mcp_baseline` | 1.0 | 33.78s | 0.833 | 5/6 |

Interpretation for draft prose: vanilla PE is weak on current evidence, but
structured PE-family variants become more competitive when clarification and
verification are added. This supports a nuanced enterprise-readiness story:
structure helps auditability, but only if the runner also handles missing
evidence and final-answer grounding.

Source note: the core `B/Y/Z` rows trace to
`results/metrics/notebook03_orchestration_comparison.csv`; the `YS/ZS`
Self-Ask rows trace to `results/metrics/notebook03_self_ask_ablation.csv` and
`results/metrics/experiment_matrix_summary.csv`. These are the legacy
six-trial smoke/calibration rows. The paper-final orchestration table should
lead with `results/metrics/gcp_post175_core31_summary.csv`, which aggregates
the post-PR175 31-scenario x 5-trial core evidence: B `57/155` pass, Y
`76/155`, YS `78/155`, Z `86/155`, and ZS `80/155`.

### Failure Taxonomy

Current citation targets:

- `results/metrics/failure_taxonomy_current.csv`
- `results/metrics/failure_taxonomy_current_auto_label_counts.csv`
- `results/metrics/failure_taxonomy_current_failed_dim_counts.csv`
- `results/metrics/failure_taxonomy_current_manual_audit_counts.csv`
- `results/figures/failure_taxonomy_current_auto_label_counts.svg`

| Auto label | Rows | Percent of paper-grade failures |
|---|---:|---:|
| `low_task_completion` | 944 | 74.0% |
| `low_data_retrieval_accuracy` | 182 | 14.3% |
| `low_agent_sequence_correct` | 78 | 6.1% |
| `low_generalized_result_verification` | 72 | 5.6% |

Interpretation for draft prose: the largest failure class is not transport or
execution plumbing; it is evidence verification and unsupported finalization.
This justifies the implemented mitigation ladder as benchmark reliability work:
detection first, repair/replan second, and explicit fault/risk adjudication
third. The post-PR175 mitigation cohort should be described as mixed evidence rather than a
blanket mitigation win: `ZS_REPAIR` is the only row with a clear positive lift
over its baseline in the post-PR175 paper-grade mitigation CSV.

The older 35-row `failure_evidence_table.csv` / `failure_taxonomy_counts.svg`
pair is preliminary-historical. Do not use those counts as current paper/deck
numbers.

### Judge Sanity Audit

The current manual audit samples 12 trajectories across baseline, guard,
repair, and adjudication rows from the now-superseded post-PR180 mitigation
cohort. Manual labels agree with the 6D judge pass/fail label on all 12 sampled
rows (`7/12` pass, `5/12` fail). This is a judge-calibration sanity check, not
claim-grade mitigation evidence; current mitigation claims should cite the
post-PR175 paper-grade cohort in
`results/metrics/gcp_post175_mitigation_4tier_summary.csv`.

Source: `results/metrics/manual_judge_audit.csv`.

## Figure and Table Transfer Checklist

- [ ] Insert Experiment 1 latency figure from `results/figures/notebook02_latency_comparison.png`.
- [ ] Insert Experiment 2 orchestration figure from `results/figures/notebook03_orchestration_comparison.png`.
- [ ] Insert PE-family follow-on figure from `results/figures/notebook03_pe_family_follow_on.png` if it fits the page budget.
- [ ] Insert current failure taxonomy count figure from `results/figures/failure_taxonomy_current_auto_label_counts.svg`.
- [ ] Insert failure stage heatmap from `results/figures/failure_stage_cell_heatmap.svg`.
- [ ] Add manual judge audit table/footnote from `results/metrics/manual_judge_audit.csv`.
- [ ] Add artifact ledger table using `docs/validation_log.md` and `results/metrics/experiment_matrix_summary.csv`.
- [ ] Add scenario corpus table once PR #156 and generator-accepted scenarios settle.

## Final Submission Blockers

| Blocker | Owner | Deadline posture |
|---|---|---|
| Compile in Overleaf with official 2026 template | Alex | Must clear before abstract/full-paper upload. |
| Fill NeurIPS checklist | Alex + factual inputs from team | Must clear before full-paper upload. |
| Refresh reviewer artifact or caveat artifact snapshot | Alex | Required if final paper cites the 36-scenario corpus or current failure-taxonomy figure while the hosted artifact still exposes the 31-scenario snapshot. |
| Freeze final result table captions | Alex, Aaron, Akshat | Lead with post-PR175 result tables; use six-trial captures only as historical calibration or appendix material. |
| Decide final wording for mitigation rerun rows | Alex | Include the post-PR175 rows only as mixed follow-on evidence; avoid universal-lift wording. |
| Wire judge audit caveat into paper | Alex | Use `manual_judge_audit.csv` as a small sanity check, not a full human-eval claim. |
| Final references and citations | Alex | Must clear before full-paper upload. |

## Teammate Fact Asks

- Aaron: final sentence on Insomnia/vLLM/profiling setup and whether Cell C
  should be described as persistent MCP session reuse, prefix caching, or both.
- Tanisha: final sentence on MCP server/data scope and any caveat around
  Smart Grid data realism.
- Akshat: generated-scenario validation disposition and one sentence on
  judge-score methodology.
