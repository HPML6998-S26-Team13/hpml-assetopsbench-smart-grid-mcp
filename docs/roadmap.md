# Project Roadmap

*Last updated: April 5, 2026*

## Timeline

| Week | Dates | Focus | Key Deliverables |
|---|---|---|---|
| 0 | Apr 1-2 | Setup and alignment | Problem statement, repo, WandB, datasets identified, Dhaval contacted, research proposal drafted |
| 1 | Apr 3-6 | **Mid-checkpoint + implementation start** | Mid-point PowerPoint submitted (Mon Apr 6), Overleaf shared with Dhaval, AssetOpsBench evaluation harness running, initial scenario drafting |
| 2 | Apr 7-13 | MCP servers + scenarios | All four MCP servers implemented (IoT, FMSR, TSFM, WO); 15+ Smart Grid scenarios; first baseline agent runs through MCP |
| 3 | Apr 14-20 | Baseline profiling | Llama-3.1-8B-Instruct on Insomnia via vLLM; PyTorch Profiler traces across all 3 conditions (direct, MCP baseline, MCP optimized); orchestration comparison design; first WandB experiment logs |
| 4 | Apr 21-27 | Optimizations + orchestration | INT8 quantization, KV-cache tuning, batched tool-call scheduling; Agent-as-Tool vs Plan-Execute comparison; 30+ scenarios; before/after data collected |
| 5 | Apr 28-May 3 | Report + presentation | Final report (LaTeX/Overleaf), presentation (PPT), WandB dashboard polish, open-source PR to AssetOpsBench |
| -- | May 4 | Submission | Final presentation + all deliverables |
| -- | May 4 | NeurIPS (stretch) | Datasets & Benchmarks abstract deadline |
| -- | May 6 | NeurIPS (stretch) | Full paper submission deadline |

## Work Distribution

| Member | Primary | Secondary |
|---|---|---|
| Alex | Project coordination, profiling analysis, report writing | Mid-point report |
| Akshat | Scenario design, evaluation harness, agent pipeline | MCP integration |
| Tanisha | MCP server implementation (all domains), dataset compilation, Overleaf | Cloud infrastructure |
| Aaron | Scenario design, compute plan + infrastructure, environment setup | Data pipeline |

## Datasets

See [docs/hpml_datasets.pdf](hpml_datasets.pdf) for full details.

Primary datasets (CC0 licensed):
- [Power Transformers FDD & RUL](https://www.kaggle.com/datasets/yuriykatser/power-transformers-fdd-and-rul) -- 3,000 files x 420 rows, fault labels + RUL (TSFM, IoT)
- [DGA Fault Classification](https://www.kaggle.com/datasets/bantipatel20/dissolved-gas-analysis-of-transformer) -- 201 rows, gas concentrations + fault types (FMSR)
- [Smart Grid Fault Records](https://www.kaggle.com/datasets/ziya07/power-system-faults-dataset) -- 506 rows, fault type + maintenance status + downtime (WO)

## Problem Statement

We extend IBM's AssetOpsBench industrial AI agent benchmark by (1) creating 30+
maintenance scenarios for Smart Grid transformers using publicly available Kaggle
telemetry data, (2) wrapping four AssetOpsBench tool domains (IoT, TSFM, FMSR, WO) as
MCP servers, (3) conducting a systematic performance study of LLM agent inference when
executing these scenarios through the MCP protocol, and (4) comparing two orchestration
paradigms (Agent-as-Tool vs Plan-Execute) on end-to-end multi-domain scenarios.

Using Llama-3.1-8B-Instruct served via vLLM, we profile the end-to-end agent pipeline with PyTorch
Profiler, apply 2-3 optimization techniques (INT8 quantization, KV-cache tuning, batched
tool-call scheduling), and compare MCP-mediated tool calling against the existing direct
function call baseline to quantify protocol overhead. All experiments tracked with WandB.
