# IEEE Class Final Report Draft

*Created: 2026-05-02*
*Owner: Alex Xin*
*Issues: #40, #78; source paper lane: #5, #39*

This is the first content-bearing IEEE report draft. It is intentionally a
Markdown drafting surface, not the final LaTeX artifact. The final report should
be transferred into the class IEEE Overleaf template after the NeurIPS source is
stable, with this file used as the section-by-section content and claim ledger.

## Abstract

Industrial-agent benchmarks under-cover Smart Grid transformer diagnostics and
maintenance, even though these workflows require multi-tool reasoning across
telemetry inspection, fault diagnosis, degradation forecasting, and work-order
planning. We extend IBM's AssetOpsBench benchmark with SmartGridBench, a Smart
Grid transformer-maintenance domain backed by public transformer data, a
shared asset-key design, and four Model Context Protocol (MCP) tool domains:
IoT, FMSR, TSFM, and work orders. We use this extension to study two HPML
questions: the latency/profiling cost of MCP-mediated tool access relative to
direct Python tool calls, and the quality/latency effects of orchestration
strategies such as Agent-as-Tool, Plan-Execute, and Verified Plan-Execute. The
current artifact set includes runnable benchmark captures, Weights & Biases
tracking, PyTorch profiling hooks, LLM-as-judge scores, and failure-taxonomy
exports. Preliminary six-trial evidence shows that optimized persistent MCP
sessions can improve steady-state latency but do not automatically improve
answer quality, while PE-family reasoning mitigations such as Self-Ask and
verification can materially change judged quality. We conclude that protocol
choice, orchestration structure, and evidence accounting all affect benchmark
interpretation, and that industrial-agent evaluations should report them as
first-class variables rather than implementation details.

## I. Introduction

Power transformers are high-value grid assets whose failures can cause outages,
equipment damage, and expensive emergency maintenance. Diagnosing these assets
requires combining telemetry, dissolved-gas analysis, degradation forecasting,
and maintenance planning. That makes Smart Grid transformer operations a natural
test case for industrial LLM agents: the agent must not simply answer a
question, but decide which evidence to retrieve, how to interpret conflicting
signals, and when to create or defer a maintenance action.

AssetOpsBench already provides an industrial-agent benchmark framework with
tool-using maintenance tasks, but its default asset coverage does not focus on
Smart Grid transformers. Our project extends the benchmark with a new Smart
Grid domain while also exposing the tool layer through MCP. This lets us ask a
systems question that matters for HPML: what cost do we pay for a standardized
tool protocol, and what can we recover through batching, persistent sessions,
prefix caching, and careful runner design?

The class project therefore has two coupled contributions. First, it contributes
a benchmark extension: Smart Grid data, scenarios, tool wrappers, and validation
docs. Second, it contributes a performance and reliability study: direct tools
versus MCP transport, Agent-as-Tool versus Plan-Execute family orchestration,
and failure taxonomy analysis over committed benchmark artifacts.

## II. Models and Data Description

SmartGridBench uses public transformer-related data sources and reconciles them
around a shared synthetic `transformer_id` key. This lets a single scenario
span multiple domains: IoT telemetry, failure-mode reasoning, time-series
forecasting, and work-order planning. The scenario format follows the
AssetOpsBench utterance contract while adding Smart Grid-specific fields such as
`asset_id`, `expected_tools`, `ground_truth`, `difficulty`, and `domain_tags`.

The benchmark currently exposes four Smart Grid tool domains:

| Domain | Role in the report | Representative task |
|---|---|---|
| IoT | Retrieve transformer sensor readings and operating context. | Check recent voltage, current, temperature, and load behavior. |
| FMSR | Diagnose DGA and transformer fault modes. | Map gas patterns to plausible electrical or thermal fault classes. |
| TSFM | Forecast remaining useful life or detect time-series anomalies. | Decide whether a transformer can stay in service through a planning window. |
| WO | Create or reason about maintenance work orders. | Recommend inspection, corrective action, priority, and safety notes. |

The final report should be careful about scenario counts. On canonical
`team13/main`, the main scenario directory contains 11 positive scenario files
and 5 negative validation fixtures. PR #156 adds 10 additional hand-authored
scenarios, and the final-week plan expects Akshat's generator-accepted batch to
clear the 30-scenario floor promised in the proposal. The report should claim
30 validated scenarios only after those files are merged and validated.

## III. Training and Profiling Methodology

This project does not train a new model. The "Training and Profiling
Methodology" section should therefore describe inference serving, profiling,
and experiment reproducibility. Our primary local model is
`openai/Llama-3.1-8B-Instruct`, served through vLLM on Insomnia GPU resources.
The benchmark runner records trial-level outputs, latency JSONL, summary JSON,
configuration JSON, harness logs, and optional profiler traces under
`benchmarks/cell_<X>/`.

The benchmark matrix separates two variables:

| Experiment | Cells | Question |
|---|---|---|
| Experiment 1: transport | A direct tools, B MCP baseline, C optimized MCP | What latency cost does MCP introduce, and what does optimized MCP recover? |
| Experiment 2: orchestration | B Agent-as-Tool MCP, Y Plan-Execute, Z Verified PE | What happens when orchestration changes while transport remains MCP-based? |

This split avoids a full orchestration-by-transport grid that would be too
large for the deadline and harder to interpret. It also makes the shared B cell
important: B is both the MCP transport baseline in Experiment 1 and the
Agent-as-Tool baseline in Experiment 2.

## IV. Performance Tuning Methodology

The main optimization lane is Cell C, which keeps the Agent-as-Tool task surface
but optimizes MCP execution. The current successful Cell C capture uses
persistent MCP sessions and vLLM prefix caching. A separate exploratory Cell D
adds optimized model serving choices such as compressed INT8 weights, BF16
execution, and fp8 KV cache; this is useful as an ablation, but it changes more
than MCP transport and should not replace the cleaner A/B/C comparison.

The report should separate three types of tuning:

| Tuning type | Evidence status | Report stance |
|---|---|---|
| MCP session/prefix-cache optimization | Cell C job `9071639` exists | Core transport optimization evidence, with first-trial cold-start caveat. |
| Model-side optimized serving | Cell D job `9073472` exists | Exploratory ablation, not the main fair transport comparison. |
| PE-family mitigation | Self-Ask/Verified rows exist; missing-evidence guard reruns pending | Quality/reliability follow-on, not raw transport optimization. |

The missing-evidence guard has been implemented and documented, but its
before/after CSV currently has no outcome rows. In the final report, it should
be described as an implemented mitigation pending guarded rerun evidence unless
`results/metrics/mitigation_before_after.csv` is populated before report freeze.

## V. Experimental Results

### Experiment 1: Transport Latency

The current first-capture Experiment 1 table is:

| Cell | Meaning | Run | Trials | p50 latency | p95 latency | Judge mean | Judge pass |
|---|---|---|---:|---:|---:|---:|---:|
| A / AT-I | Agent-as-Tool direct Python tools | `8979314_aat_direct` | 6 | 12.15s | 17.29s | 0.167 | 1/6 |
| B / AT-M | Agent-as-Tool MCP baseline | `8979314_aat_mcp_baseline` | 6 | 13.09s | 16.27s | 0.278 | 2/6 |
| C / AT-TP | Optimized MCP transport + prefix cache | `9071639_aat_mcp_optimized` | 6 | 7.40s | 47.93s | 0.167 | 0/6 |

The paired A/B run shows a modest MCP overhead in mean latency and total wall
clock, while Cell C shows a lower p50 but a high p95 because the first optimized
trial pays a large cold-start/setup cost. The key class-report point is not
"MCP always wins" or "MCP always loses." The result is more nuanced: optimized
transport can reduce steady-state latency, but answer quality must be measured
separately because the optimized transport row still has poor judge scores.

### Experiment 2: Orchestration and Quality

The current first-capture orchestration table is:

| Cell | Meaning | Run | Success rate | p50 latency | Judge mean | Judge pass |
|---|---|---|---:|---:|---:|---:|
| B / AT-M | Agent-as-Tool MCP baseline | `8979314_aat_mcp_baseline` | 1.0 | 13.09s | 0.278 | 2/6 |
| Y / PE-M | Plan-Execute MCP baseline | `8998340_exp2_cell_Y_pe_mcp_baseline` | 0.5 | 52.06s | 0.111 | 0/6 |
| Z / V-M | Verified PE MCP baseline | `8998342_exp2_cell_Z_verified_pe_mcp_baseline` | 1.0 | 119.64s | 0.639 | 4/6 |
| YS / PE-S-M | Plan-Execute + Self-Ask | `8998341_exp2_cell_Y_pe_self_ask_mcp_baseline` | 1.0 | 59.00s | 0.444 | 3/6 |
| ZS / V-S-M | Verified PE + Self-Ask | `8998343_exp2_cell_Z_verified_pe_self_ask_mcp_baseline` | 1.0 | 33.78s | 0.833 | 5/6 |

Vanilla Plan-Execute is weak in this first capture, but the PE-family rows are
scientifically useful because they show how clarification and verification
change outcomes. The strongest current row is Verified PE + Self-Ask, with mean
judge score `0.833` and `5/6` judge pass. The report should frame this as a
quality/reliability follow-on rather than evidence that every PE variant is
better than Agent-as-Tool.

### Failure Taxonomy

The failure taxonomy export currently classifies 35 judge-failed rows:

| Failure class | Rows | Percent |
|---|---:|---:|
| Task verification failure | 18 | 51.4% |
| Inter-agent / orchestration failure | 13 | 37.1% |
| Specification failure | 4 | 11.4% |

This is one of the strongest report contributions. The largest failure class is
task verification: agents often produce final answers without sufficiently
grounding required evidence. That directly motivates the missing-evidence guard
and makes the final discussion stronger than a simple latency chart.

## VI. Conclusion

SmartGridBench extends AssetOpsBench into a high-stakes Smart Grid transformer
domain and turns protocol choice, orchestration choice, and failure accounting
into measurable benchmark variables. The current evidence shows that MCP can be
made operationally viable, that optimized transport improves some latency
behavior without solving semantic quality, and that PE-family quality depends
heavily on clarification, verification, and evidence grounding. The report's
main conclusion should stay disciplined: this is not a claim of universal agent
superiority, but a reproducible benchmark extension and an artifact-backed
systems study of industrial tool-using agents.

The remaining work before submission is to merge/validate the final 30-scenario
corpus, freeze figure captions, decide whether guarded mitigation reruns are
paper-grade, and transfer the final content into the IEEE LaTeX template.

## Report Figure Checklist

- [ ] Experiment 1 latency chart: `results/figures/notebook02_latency_comparison.png`.
- [ ] Experiment 2 orchestration chart: `results/figures/notebook03_orchestration_comparison.png`.
- [ ] PE-family follow-on chart, if space permits: `results/figures/notebook03_pe_family_follow_on.png`.
- [ ] Failure taxonomy counts: `results/figures/failure_taxonomy_counts.svg`.
- [ ] Failure stage heatmap: `results/figures/failure_stage_cell_heatmap.svg`.
- [ ] Artifact ledger table from `docs/validation_log.md` and `results/metrics/experiment_matrix_summary.csv`.
