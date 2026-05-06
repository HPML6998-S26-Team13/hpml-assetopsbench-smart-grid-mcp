# NeurIPS 2026 Submission Packet

*Last updated: 2026-05-05*
*Owner: Alex Xin*
*Issues: #5, #39, #47, #48, #88, #181, #182*

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
| Abstract submission status | External OpenReview receipt not stored in repo; verify receipt before full-paper upload. |
| Full-paper deadline | 2026-05-06 23:59 AOE |
| Overleaf project | https://www.overleaf.com/project/69f5a380e638a31066dc0bd1 |
| Template status | Official NeurIPS 2026 template ingested in Overleaf Git commit `7e361de` |
| Content status | First real paper draft populated in Overleaf commit `4a85633` |
| Template source | https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip |
| LaTeX mode | anonymous `eandd` via `\usepackage[eandd]{neurips_2026}` |
| Checklist | `checklist.tex` added to Overleaf; content still needs final answers |
| Overleaf transfer plan | `docs/neurips_overleaf_transfer_plan.md` |

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
| Safe | The repo has direct-tool, MCP-baseline, and optimized-MCP AaT paths with committed artifacts. | Post-PR175 paper-grade rows in `results/metrics/evidence_registry.csv`, `results/metrics/gcp_post175_core31_summary.csv`, and `results/metrics/gcp_post175_final_summary.csv` | Main 31-scenario core evidence for A/B/C. |
| Safe | The repo has Plan-Execute, Verified PE, and PE-family Self-Ask follow-ons with judge outputs. | Post-PR175 paper-grade rows in `results/metrics/evidence_registry.csv`, `results/metrics/gcp_post175_core31_summary.csv`, and `results/metrics/gcp_post175_final_summary.csv` | Main 31-scenario orchestration result for Y/YS/Z/ZS, plus 15-scenario follow-on/extra rows. |
| Safe | Failure analysis is artifact-backed. | `failure_evidence_table.csv`, taxonomy SVGs, mitigation inventory | Main reliability/evaluation contribution. |
| Safe | The LLM judge has a small manual sanity audit. | `results/metrics/manual_judge_audit.csv` has 12 stratified mitigation trajectories from the now-superseded post-PR180 cohort with 12/12 judge/manual pass-label agreement | Use only as a judge-calibration sanity check; current paper-grade mitigation evidence is the post-PR175 cohort. |
| Safe | Scenario floor reaches 31 validated scenarios. | PR #175 merged over PR #180 at `team13/main@1913c6e4703425f735d8cb8297cb890ba66bbeff`; core rows cover 31 scenarios x 5 trials | Use "all validated scenarios" for core 8B claims. |
| Safe with caveat | Mitigation ladder has post-PR175 before/after evidence. | `results/metrics/evidence_registry.csv` marks `mitigation15_4tier` rows as paper-grade; `results/metrics/gcp_post175_mitigation_4tier_summary.csv` has the matched 15-scenario x 5-trial ladder | Report mixed effects. The ladder is evidence-backed but does not support a universal mitigation-lift claim. |
| Safe with caveat | Hosted WatsonX 70B rows strengthen generality. | `results/metrics/evidence_registry.csv` marks the post-PR175 70B rows as paper-grade; `results/metrics/gcp_post175_70b_summary.csv` summarizes 15-scenario main/top-up rows | Core scaling evidence exists for 15 scenarios; all-31 70B remains future extension work. |

## Section Plan

| Section | Draft content to transfer |
|---|---|
| 1. Introduction | Benchmark gap, Smart Grid maintenance stakes, protocolized tool-use cost, and why transport/orchestration must be separated. |
| 2. Benchmark Extension | Dataset sources, shared `transformer_id`, four tool domains, scenario schema, realism controls, and 30-scenario target status. |
| 3. System Design | MCP servers, direct adapter for Cell A, persistent MCP path for Cell C, run artifact contract, WandB/profiler linkage. |
| 4. Experimental Design | Experiment 1 A/B/C transport axis; Experiment 2 B/Y/Z orchestration axis; PE-family Self-Ask/Verified follow-ons. |
| 5. Results | Notebook 02 latency summary, Notebook 03 orchestration/judge table, failure taxonomy counts, and mitigation status. |
| 6. Limitations | Small six-trial first captures, scenario-count pending work, generated-scenario circularity, and guarded-rerun incompleteness. |
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
4. Add TODO markers for final scenario count, repeated transport distribution,
   mitigation before/after rows, references, checklist answers, and compile
   proof.
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

| Failure class | Rows | Percent |
|---|---:|---:|
| Task verification failure | 18 | 51.4% |
| Inter-agent / orchestration failure | 13 | 37.1% |
| Specification failure | 4 | 11.4% |

Interpretation for draft prose: the largest failure class is not transport or
execution plumbing; it is evidence verification and unsupported finalization.
This justifies the implemented mitigation ladder as benchmark reliability work:
detection first, repair/replan second, and explicit fault/risk adjudication
third. The post-PR175 mitigation cohort should be described as mixed evidence rather than a
blanket mitigation win: `ZS_REPAIR` is the only row with a clear positive lift
over its baseline in the post-PR175 paper-grade mitigation CSV.

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
- [ ] Insert failure taxonomy count figure from `results/figures/failure_taxonomy_counts.svg`.
- [ ] Insert failure stage heatmap from `results/figures/failure_stage_cell_heatmap.svg`.
- [ ] Add manual judge audit table/footnote from `results/metrics/manual_judge_audit.csv`.
- [ ] Add artifact ledger table using `docs/validation_log.md` and `results/metrics/experiment_matrix_summary.csv`.
- [ ] Add scenario corpus table once PR #156 and generator-accepted scenarios settle.

## Final Submission Blockers

| Blocker | Owner | Deadline posture |
|---|---|---|
| Compile in Overleaf with official 2026 template | Alex | Must clear before abstract/full-paper upload. |
| Fill NeurIPS checklist | Alex + factual inputs from team | Must clear before full-paper upload. |
| Reach and document 30 validated scenarios | Akshat/Tanisha, Alex shepherd | Must clear before final claims. |
| Freeze final result table captions | Alex, Aaron, Akshat | Can use current six-trial captures if final reruns do not land. |
| Decide final wording for mitigation rerun rows | Alex | Include the post-PR175 rows only as mixed follow-on evidence; avoid universal-lift wording. |
| Wire judge audit caveat into paper | Alex | Use `manual_judge_audit.csv` as a small sanity check, not a full human-eval claim. |
| Final references and citations | Alex | Must clear before full-paper upload. |

## Teammate Fact Asks

- Aaron: final sentence on Insomnia/vLLM/profiling setup and whether Cell C
  should be described as persistent MCP session reuse, prefix caching, or both.
- Tanisha: final sentence on MCP server/data scope and any caveat around
  Smart Grid data realism.
- Akshat: final scenario count, generated-scenario validation disposition, and
  one sentence on judge-score methodology.
