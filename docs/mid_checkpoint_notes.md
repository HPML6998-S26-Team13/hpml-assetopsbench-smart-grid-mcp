# Mid-Point Progress Report (Long-form notes) -- Team 13 / District 1101

**Project:** MCP-Based Industrial Agent Benchmarking for Smart Grid Operations
**Date:** April 6, 2026
**Team:** Alex Xin (wax1), Akshat Bhandari (ab6174), Tanisha Rathod (tr2828), Aaron Fan (af3623)
**Mentor:** Dr. Dhaval Patel, IBM Research

## Problem Statement

We extend IBM's AssetOpsBench industrial AI agent benchmark by (1) creating 30+
maintenance scenarios for Smart Grid transformers using publicly available Kaggle
telemetry data, (2) wrapping four AssetOpsBench tool domains (IoT, TSFM, FMSR, WO) as
MCP servers, (3) conducting a systematic performance study of LLM agent inference when
executing these scenarios through the MCP protocol, and (4) comparing two orchestration
paradigms (Agent-as-Tool vs Plan-Execute) on end-to-end multi-domain scenarios.

We select Llama-3.1-8B-Instruct for its favorable profiling characteristics (~16GB FP16), enabling
rapid iteration on optimization experiments. We serve it via vLLM, profile the end-to-end
agent pipeline with PyTorch Profiler, and apply 2-3 optimization techniques (INT8
quantization, KV-cache tuning, and batched tool-call scheduling). We also compare
MCP-mediated tool calling against the existing direct function call baseline (ReAct with
native tool calls) to quantify the cost of the MCP standardization layer. All experiments
are tracked with WandB. Evaluation uses AssetOpsBench's LLM-as-Judge pipeline
(Llama-4-Maverick-17B) scoring across six dimensions.

## Progress to Date

### Completed

- Reviewed all four mentor proposals and identified project direction (Proposal 1 + 4)
- Held intro meeting with mentor Dr. Dhaval Patel (March 5) and aligned on scope
- Finalized problem statement with four contributions (scenarios, MCP servers, profiling/optimization, orchestration comparison)
- Full research proposal drafted and shared with mentor via Overleaf (NeurIPS 2026 template)
- Set up project GitHub repository with scaffolded structure and CI (Black formatting)
- Set up WandB team project for experiment tracking
- Forked AssetOpsBench and reviewed existing scenario format, agent pipeline, and evaluation harness
- Identified and documented 5 candidate Kaggle datasets covering all 4 agent domains
- Verified compute infrastructure access (Insomnia cluster: 6x H100, ~100x A6000; plus $500 GCP credits/person)
- Read MCP documentation and understand protocol architecture
- Compute plan committed documenting GPU needs per phase and Insomnia vs GCP recommendation (`docs/compute_plan.md`)
- Received WatsonX API access from mentor, verified 6 Llama foundation models available, benchmarked Maverick-17B (~80 tok/s steady) and Llama-3.3-70B (~34 tok/s) end-to-end against a realistic code review prompt (`docs/watsonx_access.md`)
- Data pipeline scripts landed along with processed Kaggle datasets (`data/processed/`: asset metadata, DGA records, failure modes, fault records, RUL labels, sensor readings)
- MCP server skeletons landed for all four domains (IoT, FMSR, TSFM, WO) on shared base class

### In Progress

- Fleshing out four MCP server implementations on top of the skeletons
- Creating initial Smart Grid transformer scenarios following AssetOpsBench format
- Synthesizing common `transformer_id` key across datasets for cross-domain scenarios
- Getting AssetOpsBench evaluation harness running end-to-end
- Setting up vLLM serving for Llama-3.1-8B-Instruct on Insomnia cluster
- Designing orchestration comparison (Agent-as-Tool vs Plan-Execute)
- Establishing baseline profiling methodology

## Methodology

### Data

We use publicly available Smart Grid transformer datasets from Kaggle containing dissolved
gas analysis (DGA), winding temperature readings, load profiles, fault classification,
and maintenance records. These are processed into AssetOpsBench-compatible scenario format
covering all four agent domains: sensor data retrieval (IoT), failure mode diagnosis
(FMSR), time-series forecasting (TSFM), and work order creation (WO). A synthesized
`transformer_id` key links records across datasets for cross-domain scenarios.

### Architecture

```
User Query
    |
    v
LLM Agent (Llama-3.1-8B-Instruct via vLLM)
    |
    | MCP / JSON-RPC
    v
+----------+----------+----------+----------+
| IoT MCP  | FMSR MCP | TSFM MCP |  WO MCP  |
| Server   | Server   | Server   |  Server  |
+----------+----------+----------+----------+
    |
    v
Smart Grid Datasets (Kaggle)
    |
    v
PyTorch Profiler + WandB Logging
```

### Optimization Techniques (Planned)

1. **INT8 Quantization** -- Reduce model memory footprint (~16GB to ~8GB) and inference latency
2. **KV-Cache Tuning** -- Optimize cache allocation for multi-turn tool-calling sequences
3. **Batched Tool-Call Scheduling** -- Parallelize independent MCP requests within a trajectory

### Experimental Comparisons

- **MCP overhead:** ReAct + direct function calls (existing baseline) vs ReAct + MCP (unoptimized) vs ReAct + MCP (optimized)
- **Orchestration:** Agent-as-Tool (single LLM, sequential) vs Plan-Execute (planner + executor) on end-to-end scenarios

### Orchestration Design Tradeoffs

Per Dhaval's lecture (Mar 2) and AssetOpsBench benchmark results:

- **Agent-as-Tool** consistently outperforms Plan-Execute on benchmarks because ReAct
  gives it reflection/self-correction — the agent can detect and recover from errors
- **Plan-Execute** is preferred in production despite lower benchmark scores:
  predictable resource usage, execution visibility, no risk of infinite loops, ability
  to reserve hardware (e.g., GPU for TSFM fine-tuning)
- IBM's competition teams focus exclusively on improving Plan-Execute
- Exploratory direction: hybrid approach adding reflection checkpoints to Plan-Execute
  — combining the predictability of PE with the self-correction of AaT

Related work:
- FailureSensorIQ (NeurIPS 2025): benchmarks sensor-failure reasoning for FMSR domain
- "Why Do Multi-Agent LLM Systems Fail?" (arXiv 2503.13657): failure taxonomy —
  specification, inter-agent, task verification. "Self-Ask" fix reduced clarification
  failures by addressing 10% of failure cases

### Metrics

| Metric | Tool |
|---|---|
| Task completion rate (6-dimension rubric) | LLM-as-Judge (Llama-4-Maverick-17B) |
| Tool-call latency (ms) | PyTorch Profiler |
| Token efficiency (tokens/task) | vLLM logs |
| GPU utilization (%) | NVIDIA Nsight / nvidia-smi |
| Memory bandwidth usage | PyTorch Profiler |
| End-to-end time-to-solution (s) | WandB |

## Timeline (Remaining)

| Week | Dates | Deliverable |
|---|---|---|
| 2 | Apr 7-13 | All four MCP servers implemented, 15+ scenarios, first baseline agent runs |
| 3 | Apr 14-20 | Baseline profiling complete (all 3 conditions), first WandB dashboard |
| 4 | Apr 21-27 | Optimizations applied, orchestration comparison, 30+ scenarios, before/after data |
| 5 | Apr 28-May 3 | Final report, presentation, open-source PR to AssetOpsBench |
| -- | May 4 | Final submission and presentation |

## Team Roles

| Member | Primary | Secondary |
|---|---|---|
| Alex Xin | Project coordination, profiling analysis, report writing | Mid-point report |
| Akshat Bhandari | Scenario design, evaluation harness, agent pipeline | MCP integration |
| Tanisha Rathod | MCP server implementation (all domains), dataset compilation, Overleaf | Cloud infrastructure |
| Aaron Fan | Scenario design, compute plan + infrastructure, data pipeline | Environment setup |

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Smart Grid data quality insufficient for realistic scenarios | Multiple Kaggle datasets identified as fallbacks; can synthesize additional data |
| Llama-3.1-8B-Instruct insufficient for complex tool-calling | Compare against API-based WatsonX runs with larger models |
| MCP overhead too small to meaningfully optimize | The "direct vs MCP" comparison is a valid finding either way |
| Insomnia cluster availability issues | Google Cloud backup with $500 GPU credits/person |
| Dataset licensing blocks open-source PR | Use only CC0 datasets for public contribution |

## Repository

https://github.com/eggrollofchaos/hpml-assetopsbench-smart-grid-mcp
