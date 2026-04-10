# Project Synopsis -- Cold Start Guide

*Last updated April 9, 2026. Read time: ~10 minutes.*

## What is this project?

A 4-person team at Columbia University is building a performance benchmarking study for
an AI agent system applied to industrial equipment maintenance. The project sits at the
intersection of LLM-based AI agents, industrial operations, and high-performance ML
systems.

## The class

**COMS E6998: High Performance Machine Learning** (HPML), taught by Prof. Kaoutar El
Maghraoui at Columbia. The class focuses on optimizing ML workloads -- profiling where
time is spent (data loading, preprocessing, inference), applying optimization techniques
(quantization, caching, batching), and measuring the impact on GPU-accelerated
infrastructure. Every project must demonstrate measurable before/after performance
improvements using tools like PyTorch Profiler, NVIDIA Nsight, and Weights & Biases.

## The mentor and IBM connection

Our project is mentored by **Dr. Dhaval Patel** from IBM Research. IBM built an open-source
benchmark called **AssetOpsBench** that tests how well AI agents can handle industrial
maintenance tasks. Dhaval proposed four project ideas for HPML teams; we were assigned a
combination of two of them.

## Background: What is AssetOpsBench?

AssetOpsBench is a benchmark for evaluating AI agents on industrial asset operations and
maintenance (O&M). Think: a factory has hundreds of machines (turbines, chillers,
transformers). When something goes wrong -- a sensor spikes, a part degrades, a failure
mode appears -- an AI agent needs to:

1. **Read sensor data** (IoT telemetry -- temperature, vibration, gas levels)
2. **Diagnose the problem** (map symptoms to known failure modes using FMSR -- Failure
   Mode to Sensor Relation databases)
3. **Forecast** what will happen next (time-series forecasting with TSFM models)
4. **Create a work order** (WO -- assign a technician, set priority, schedule repair)

AssetOpsBench has four "tool domains" that correspond to these steps:

| Domain | What it does | Example |
|---|---|---|
| **IoT** | Sensor telemetry and asset metadata | "Get temperature readings for Chiller #4 over the last 24 hours" |
| **FMSR** | Maps failure modes to sensor patterns | "What failure mode correlates with high H2 and low C2H6?" |
| **TSFM** | Time-series forecasting and anomaly detection | "Predict remaining useful life for this transformer" |
| **WO** | Work order management | "Create a priority-1 work order for a high-voltage technician" |

An AI agent (powered by an LLM like Llama-3 or GPT-4) is given a maintenance scenario
and must use these tools to resolve it. The benchmark measures whether the agent picks
the right tools, calls them correctly, and reaches the right conclusion.

AssetOpsBench currently has 467 scenarios across 6 HuggingFace subsets on
[HuggingFace](https://huggingface.co/datasets/ibm-research/AssetOpsBench) (chillers, AHUs,
compressors, hydraulic pumps, bearings, boilers). Our job is to add a 7th: Smart Grid
power transformers.

## Background: What is MCP?

**Model Context Protocol (MCP)** is an open protocol (created by Anthropic) that
standardizes how LLMs interact with external tools. Instead of each LLM having its own
bespoke tool-calling format, MCP provides a universal JSON-RPC interface: the LLM sends
a structured request to an "MCP server," which executes the tool and returns results.

Think of it like a USB standard for AI tools -- any LLM that speaks MCP can use any MCP
server, regardless of who built either one.

For our project, this means wrapping all four AssetOpsBench tool domains (IoT, TSFM,
FMSR, WO) as MCP servers so that any LLM can call them through a standardized interface.
This adds a communication layer (JSON-RPC serialization/deserialization) that has
performance implications -- which is exactly what HPML wants us to measure and optimize.

## Background: What are Smart Grid transformers?

Power transformers are critical infrastructure in electrical grids. They step voltage
up/down for transmission and distribution. When a transformer fails, it can cause
blackouts and costs millions.

Transformer health is monitored through:
- **Dissolved Gas Analysis (DGA)**: Gases like H2, CH4, C2H2, C2H4 dissolve in
  transformer oil. Different gas ratios indicate different failure modes (partial
  discharge, overheating, arcing).
- **Winding temperature**: Overheating degrades insulation.
- **Load profiles**: How much power the transformer carries over time.

This is a natural fit for AssetOpsBench: the sensor data maps to IoT, the gas-to-fault
mapping maps to FMSR, predicting remaining useful life maps to TSFM, and scheduling
maintenance maps to WO.

## What we're actually doing

### Problem Statement

We extend AssetOpsBench by:
1. **Creating 30+ maintenance scenarios** for Smart Grid transformers using publicly
   available Kaggle telemetry data (DGA, temperature, load, fault records)
2. **Wrapping four AssetOpsBench tool domains** (IoT, TSFM, FMSR, WO) as MCP servers
3. **Profiling the LLM agent inference pipeline** end-to-end when executing scenarios
   through MCP
4. **Comparing two orchestration paradigms** -- Agent-as-Tool (ReAct-based, with
   reflection) and Plan-Execute (planner decomposes, executors run sequentially) -- on
   end-to-end multi-domain scenarios. Per Dhaval's lecture: Agent-as-Tool wins benchmarks
   (reflection gives self-correction) but Plan-Execute is preferred in practice
   (predictable resources, visibility, no infinite loops). IBM focuses on improving
   Plan-Execute. Exploratory direction: a hybrid with reflection checkpoints.

We use **Llama-3.1-8B-Instruct** served via **vLLM** on GPU infrastructure, profile with **PyTorch
Profiler**, and apply 2-3 optimization techniques:
- INT8 quantization (reduce model size and inference latency)
- KV-cache tuning (optimize memory for multi-turn tool-calling conversations)
- Batched tool-call scheduling (reduce round-trip overhead)

We also compare MCP-mediated tool calling against the existing direct function call
approach (AssetOpsBench's current ReAct-based implementation) to quantify the actual
cost of the standardization layer. This addresses a live industry debate about whether
MCP's interoperability benefits justify its overhead for simple tool-calling patterns.

We report before/after comparisons with full **WandB** experiment tracking.

### Why this problem statement works

Our mentor explicitly told us to keep scope realistic. This problem statement is
concrete and measurable -- every claim can be verified (count the scenarios, measure the
latency, compare before/after). It satisfies both the mentor's interest in extending
AssetOpsBench to new asset classes AND the class requirement for rigorous performance
profiling and optimization.

## The team

| Name | Role | Key strength |
|---|---|---|
| **Akshat Bhandari** | Scenario design, evaluation harness, judge integration | Published ML research (EACL 2026), multi-agent systems |
| **Aaron Fan** | Serving infrastructure, profiling capture, Problem Statement B generation pipeline | EE background, power systems research, embedded systems |
| **Tanisha Rathod** | MCP server implementation (all domains), data pipeline, Knowledge Plugin | Distributed systems at Caterpillar, AWS/SageMaker |
| **Wei Alexander Xin** | Project management, experiment design, profiling analysis, paper writing, WatsonX setup | 12+ yrs production data systems, project management |

## Related Work

- **FailureSensorIQ** (NeurIPS 2025): benchmarks sensor-failure reasoning, tests whether
  LLMs reason about sensors/assets/failure modes beyond data-driven correlations. Directly
  relevant to our FMSR domain.
- **"Why Do Multi-Agent LLM Systems Fail?"** (arXiv 2503.13657, Berkeley): failure taxonomy
  for multi-agent systems — specification, inter-agent, and task verification failures.
  Their "Self-Ask" fix (10 lines of code) significantly reduced "fail to ask for
  clarification" errors (10% of failures).

## Current status (April 9, 2026)

**Week 1 is complete, the mid-point was submitted Apr 6, and Week 2 is now focused on foundation bring-up plus planning cleanup.**

Completed:
- Problem statement finalized (four contributions: scenarios, MCP servers, profiling, orchestration comparison)
- Full research proposal drafted and shared with mentor via Overleaf (NeurIPS 2026 template)
- Mentor endorsed NeurIPS 2026 Datasets & Benchmarks submission (abstract May 4, paper May 6)
- Fork synced with upstream AssetOpsBench (new VibrationAgent, AgentRunner ABC, `src/workflow/` → `src/agent/` rename)
- Canonical GitHub repo is now the org repo: [HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp)
- WandB team created: wandb.ai/assetopsbench-smartgrid
- 5 candidate datasets identified (3 CC0, 2 restricted license)
- Compute confirmed: Insomnia (6x H100, ~100x A6000) + $500 GCP credits/person
- Compute plan committed (`docs/compute_plan.md`) mapping GPU needs per project phase
- WatsonX API access received from mentor Apr 5 and verified end-to-end; Llama-4-Maverick-17B (judge) and Llama-3.3-70B-instruct (scaling comparison) both benchmarked at interactive speeds (`docs/watsonx_access.md`)
- Data pipeline scripts plus tracked public-safe processed datasets landed (`data/processed/`: synthetic asset metadata, DGA records, failure modes, fault records, RUL labels, sensor readings for 20 transformers) while restricted-source Kaggle joins remain a local benchmarking path
- MCP server skeletons landed for all four domains (IoT, FMSR, TSFM, WO) on a shared base class with substantive domain logic (IEC 60599 Rogers Ratio DGA analysis, RUL forecast + z-score anomaly detection + OLS trend, work-order CRUD)
- Paper-ready `docs/data_pipeline.tex` section drafted
- **Mid-point report submitted** to Courseworks on Monday April 6 (see `reports/2026-04-06_midpoint_submission.pdf`)
- GitHub Projects reset as the canonical planning surface, with weekly iterations, workstream parent issues, and delivery-gate milestones

In progress (Week 2, Apr 7-13):
- Successful first Insomnia A6000 vLLM serve smoke test for Llama-3.1-8B-Instruct
- MCP server hardening, tests, and benchmark-path validation
- AssetOpsBench evaluation harness running end-to-end on the canonical repo
- First 15+ Smart Grid scenarios committed and validated
- First Smart Grid end-to-end MCP trajectory and first judge-scored artifact
- WandB metrics schema plus first experiment logs

Committed W3-W5 workstreams:
- Experiment 1: MCP overhead and optimization (Direct vs MCP-baseline vs MCP-optimized)
- Experiment 2: orchestration comparison and failure analysis
- Problem Statement B extension: generation pipeline, Knowledge Plugin, and validation methodology
- Paper flow: NeurIPS draft first, then class-report back-port

Open question awaiting mentor reply:
- Is **Hybrid Plan-Execute with reflection checkpoints** novel enough to add as a third orchestration condition alongside AaT and PE?

**Final deadline: May 4** (presentation + report + code)

## Key links

- AssetOpsBench: https://github.com/IBM/AssetOpsBench
- MCP: https://modelcontextprotocol.io/
- Our repo: https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp
- WandB: https://wandb.ai/assetopsbench-smartgrid
- Mentor: Dr. Dhaval Patel (pateldha@us.ibm.com)

## Timeline at a glance

```
Week 2 (Apr 7-13)    MCP servers + 15+ scenarios + baseline runs
Week 3 (Apr 14-20)   Baseline profiling on GPU infrastructure
Week 4 (Apr 21-27)   Apply optimizations, complete 30+ scenarios
Week 5 (Apr 28-May3) Final report + presentation + open-source PR
May 4                SUBMIT
```
