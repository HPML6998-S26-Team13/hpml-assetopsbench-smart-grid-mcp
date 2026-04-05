# Project Roadmap

*Last updated: April 1, 2026 (post-team call)*

## Timeline

| Week | Dates | Focus | Key Deliverables |
|---|---|---|---|
| 0 | Apr 1-2 | Setup and alignment | Problem statement, repo, WandB, datasets identified, Dhaval contacted |
| 1 | Apr 3-6 | **Mid-checkpoint + implementation start** | Mid-point PowerPoint submitted, Overleaf shared with Dhaval, AssetOpsBench running, initial scenario drafting |
| 2 | Apr 7-13 | MCP servers + scenarios | IoT MCP server, TSFM MCP server implemented; 15+ Smart Grid scenarios; baseline agent runs |
| 3 | Apr 14-20 | Baseline profiling | Llama-3-8B on Insomnia via vLLM; PyTorch Profiler traces; first WandB experiment logs |
| 4 | Apr 21-27 | Optimizations | INT8 quantization, KV-cache tuning, batched tool-call scheduling; 30+ scenarios; before/after data |
| 5 | Apr 28-May 3 | Report + presentation | Final report (LaTeX/Overleaf), presentation (PPT), WandB dashboard polish, open-source PR |
| -- | May 4 | Submission | Final presentation + all deliverables |

## Work Distribution

| Member | Primary | Secondary |
|---|---|---|
| Alex | Project coordination, mid-point report, profiling analysis | Report writing |
| Akshat | Scenario design, evaluation harness | Agent pipeline |
| Tanisha | MCP server implementation (all domains), dataset compilation, Overleaf | Cloud infrastructure |
| Aaron | Scenario design, compute plan + infrastructure | Data pipeline |

## Datasets

See [docs/hpml_datasets.pdf](hpml_datasets.pdf) for full details.

Primary datasets (all CC0 licensed):
- **Power Transformers FDD & RUL** -- 3,000 files x 420 rows, fault labels + RUL (TSFM, IoT)
- **DGA Fault Classification** -- 201 rows, gas concentrations + fault types (FMSR)
- **Smart Grid Fault Records** -- 506 rows, fault type + maintenance status + downtime (WO)

## Problem Statement

We extend IBM's AssetOpsBench industrial AI agent benchmark by (1) creating 30+
maintenance scenarios for Smart Grid transformers using publicly available Kaggle
telemetry data, (2) wrapping four AssetOpsBench tool domains (IoT, TSFM, FMSR, WO) as MCP
servers, and (3) conducting a systematic performance study of LLM agent inference when
executing these scenarios through the MCP protocol. Using Llama-3-8B served via vLLM, we
profile the end-to-end agent pipeline with PyTorch Profiler and measure task completion
rate, tool-call latency, token efficiency, and GPU utilization. We then apply 2-3
optimization techniques (INT8 quantization, KV-cache tuning, and batched tool-call
scheduling) and report before/after comparisons with full WandB experiment tracking.
