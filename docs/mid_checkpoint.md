# Mid-Point Progress Report -- Team 13

**Project:** MCP-Based Industrial Agent Benchmarking for Smart Grid Operations
**Date:** April 6, 2026
**Team:** Alex Xin (wax1), Akshat Bhandari (ab6174), Tanisha Rathod (tr2828), Aaron Fan (af3623)
**Mentor:** Dr. Dhaval Patel, IBM Research

## Problem Statement

We extend IBM's AssetOpsBench industrial AI agent benchmark by (1) creating 30+
maintenance scenarios for Smart Grid transformers using publicly available Kaggle
telemetry data, (2) wrapping two AssetOpsBench tool domains (IoT and TSFM) as MCP
servers, and (3) conducting a systematic performance study of LLM agent inference when
executing these scenarios through the MCP protocol.

Using Llama-3-8B served via vLLM, we profile the end-to-end agent pipeline with PyTorch
Profiler and measure task completion rate, tool-call latency, token efficiency, and GPU
utilization. We then apply 2-3 optimization techniques (INT8 quantization, KV-cache
tuning, and batched tool-call scheduling) and report before/after comparisons with full
WandB experiment tracking.

## Progress to Date

### Completed

- Reviewed all four mentor proposals and identified project direction (Proposal 1 + 4)
- Held intro meeting with mentor Dr. Dhaval Patel (March 5) and aligned on scope
- Finalized problem statement following mentor guidance to keep scope concrete and measurable
- Set up project GitHub repository with scaffolded structure
- Set up WandB team project for experiment tracking
- Forked AssetOpsBench and reviewed existing scenario format and agent pipeline
- Identified candidate Smart Grid datasets on Kaggle
- Verified compute infrastructure access (Insomnia cluster / GPU availability)
- Read MCP documentation and understand protocol architecture

### In Progress

- Implementing IoT MCP server for Smart Grid telemetry data
- Creating initial Smart Grid transformer scenarios (targeting 30+)
- Setting up vLLM serving for Llama-3-8B on Insomnia cluster
- Establishing baseline profiling methodology

## Methodology

### Data

We use publicly available Smart Grid transformer datasets from Kaggle containing dissolved
gas analysis (DGA), winding temperature readings, and load profile data. These are
processed into AssetOpsBench-compatible scenario format covering fault detection,
preventive maintenance scheduling, and work order creation.

### Architecture

```
┌──────────────────┐     MCP (JSON-RPC)     ┌────────────────┐
│   LLM Agent      │ ◄──────────────────────► │  IoT MCP       │
│   (Llama-3-8B    │                          │  Server        │
│    via vLLM)     │ ◄──────────────────────► │  TSFM MCP      │
│                  │                          │  Server        │
└──────────────────┘                          └────────────────┘
        │
        ▼
  PyTorch Profiler + WandB Logging
```

### Optimization Techniques (Planned)

1. **INT8 Quantization** -- Reduce model memory footprint and inference latency
2. **KV-Cache Tuning** -- Optimize cache allocation for multi-turn tool-calling sequences
3. **Batched Tool-Call Scheduling** -- Reduce round-trip overhead for sequential tool calls

### Metrics

| Metric | Tool |
|---|---|
| Task completion rate | Custom evaluation harness |
| Tool-call latency (ms) | PyTorch Profiler |
| Token efficiency (tokens/task) | vLLM logs |
| GPU utilization (%) | NVIDIA Nsight / nvidia-smi |
| Memory bandwidth usage | PyTorch Profiler |
| End-to-end time-to-solution | WandB |

## Timeline (Remaining)

| Week | Dates | Deliverable |
|---|---|---|
| 2 | Apr 7-13 | MCP servers complete, 15+ scenarios, WandB project live |
| 3 | Apr 14-20 | Baseline profiling complete, first WandB dashboard |
| 4 | Apr 21-27 | All optimizations applied, 30+ scenarios, before/after data |
| 5 | Apr 28-May 3 | Final report, presentation, open-source PR to AssetOpsBench |
| -- | May 4 | Final submission and presentation |

## Team Roles

| Member | Primary | Secondary |
|---|---|---|
| Alex Xin | Project management, WandB, report, scenario design | MCP integration testing |
| Akshat Bhandari | LLM agent pipeline, evaluation harness, profiling analysis | Report methodology |
| Tanisha Rathod | MCP server implementation, cloud infrastructure | Optimization techniques |
| Aaron Fan | Smart Grid data pipeline, IoT MCP server, profiling tools | Systems optimization |

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Smart Grid data quality insufficient for realistic scenarios | Identified multiple Kaggle datasets as fallbacks |
| Llama-3-8B insufficient for complex tool-calling | Can fall back to API-based model (WatsonX access from mentor) |
| MCP overhead too small to meaningfully optimize | Pivot to direct comparison study (MCP vs native tool calling) |
| Insomnia cluster availability issues | Google Cloud backup with GPU quota |

## Repository

https://github.com/eggrollofchaos/hpml-assetopsbench-smart-grid-mcp
