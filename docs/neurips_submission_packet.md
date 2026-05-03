# NeurIPS 2026 Submission Packet

*Created: 2026-05-02*
*Owner: Alex Xin*
*Issues: #5, #39, #47, #48*

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
| Full-paper deadline | 2026-05-06 23:59 AOE |
| Overleaf project | https://www.overleaf.com/project/69f5a380e638a31066dc0bd1 |
| Template status | Official NeurIPS 2026 template ingested in Overleaf Git commit `7e361de` |
| Template source | https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip |
| LaTeX mode | anonymous `eandd` via `\usepackage[eandd]{neurips_2026}` |
| Checklist | `checklist.tex` added to Overleaf; content still needs final answers |
| Overleaf transfer plan | `docs/neurips_overleaf_transfer_plan.md` |

## Working Title

**SmartGridBench: MCP-Based Industrial Agent Benchmarking for Smart Grid
Transformer Operations**

## Abstract Candidate

Industrial-agent benchmarks under-cover Smart Grid transformer diagnostics and
maintenance, even though these workflows require exactly the kind of multi-tool
reasoning that industrial LLM agents are expected to perform: telemetry
inspection, fault diagnosis, degradation forecasting, and work-order planning.
We present SmartGridBench, a Smart Grid transformer-maintenance extension of
AssetOpsBench that adds transformer scenarios, public-data-backed asset
records, and four tool domains exposed through the Model Context Protocol
(MCP). The benchmark is designed to make two usually conflated systems choices
measurable: the transport cost of MCP relative to direct tool invocation, and
the behavioral effect of orchestration strategies such as Agent-as-Tool,
Plan-Execute, and Verified Plan-Execute when the tool surface is held fixed.
Current artifacts show a runnable end-to-end benchmark path with committed
scenario outputs, profiling links, Weights & Biases runs, LLM-as-judge scores,
and failure-taxonomy exports. Preliminary six-trial captures show that MCP
standardization introduces measurable overhead in direct comparisons, that
persistent optimized MCP sessions can reduce steady-state latency but do not by
themselves improve answer quality, and that PE-family mitigations such as
Self-Ask and verification can materially change judged quality. We also treat
scenario realism, generated-scenario circularity, and failure accounting as
first-class benchmark artifacts rather than post-hoc notes. SmartGridBench
therefore contributes both a new industrial benchmark domain and an auditable
systems study of protocol and orchestration choices in tool-using agents.

## Claim Tiers

| Tier | Claim | Evidence now | Paper stance |
|---|---|---|---|
| Safe | SmartGridBench adds a Smart Grid transformer-maintenance lane over AssetOpsBench. | `data/`, `mcp_servers/`, `data/scenarios/`, `docs/data_pipeline.tex` | Main contribution. |
| Safe | The repo has direct-tool, MCP-baseline, and optimized-MCP AaT paths with committed artifacts. | A/B job `8979314`; C job `9071639`; Notebook 02 exports | Report as preliminary six-trial evidence until final reruns freeze. |
| Safe | The repo has Plan-Execute, Verified PE, and PE-family Self-Ask follow-ons with judge outputs. | jobs `8998340` through `8998343`; Notebook 03 exports | Main orchestration result, with small-sample caveat. |
| Safe | Failure analysis is artifact-backed. | `failure_evidence_table.csv`, taxonomy SVGs, mitigation inventory | Main reliability/evaluation contribution. |
| Pending | Scenario floor reaches 30 validated scenarios. | `team13/main` has 11 main scenarios; PR #156 adds 10 hand-authored scenarios; Akshat generator acceptance remains needed for 30 floor | Mention as deadline blocker until merged/validated. |
| Pending | Mitigation ladder improves outcomes. | Detection guard, repair/replan, and adjudication implementation landed; `mitigation_before_after.csv` has header only | Describe as implemented mitigation ladder pending rerun evidence. |
| Optional | 70B and context-window appendix strengthens generality. | local branch evidence exists outside canonical main | Appendix only if published before final paper freeze. |

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
3. Insert the current results tables from this packet with captions labeled as
   first six-trial captures.
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
third. Do not claim measured mitigation improvement until before/after rows
exist.

## Figure and Table Transfer Checklist

- [ ] Insert Experiment 1 latency figure from `results/figures/notebook02_latency_comparison.png`.
- [ ] Insert Experiment 2 orchestration figure from `results/figures/notebook03_orchestration_comparison.png`.
- [ ] Insert PE-family follow-on figure from `results/figures/notebook03_pe_family_follow_on.png` if it fits the page budget.
- [ ] Insert failure taxonomy count figure from `results/figures/failure_taxonomy_counts.svg`.
- [ ] Insert failure stage heatmap from `results/figures/failure_stage_cell_heatmap.svg`.
- [ ] Add artifact ledger table using `docs/validation_log.md` and `results/metrics/experiment_matrix_summary.csv`.
- [ ] Add scenario corpus table once PR #156 and generator-accepted scenarios settle.

## Final Submission Blockers

| Blocker | Owner | Deadline posture |
|---|---|---|
| Compile in Overleaf with official 2026 template | Alex | Must clear before abstract/full-paper upload. |
| Fill NeurIPS checklist | Alex + factual inputs from team | Must clear before full-paper upload. |
| Reach and document 30 validated scenarios | Akshat/Tanisha, Alex shepherd | Must clear before final claims. |
| Freeze final result table captions | Alex, Aaron, Akshat | Can use current six-trial captures if final reruns do not land. |
| Decide whether to include mitigation rerun rows | Alex | Include only if `mitigation_before_after.csv` has real rows. |
| Final references and citations | Alex | Must clear before full-paper upload. |

## Teammate Fact Asks

- Aaron: final sentence on Insomnia/vLLM/profiling setup and whether Cell C
  should be described as persistent MCP session reuse, prefix caching, or both.
- Tanisha: final sentence on MCP server/data scope and any caveat around
  Smart Grid data realism.
- Akshat: final scenario count, generated-scenario validation disposition, and
  one sentence on judge-score methodology.
