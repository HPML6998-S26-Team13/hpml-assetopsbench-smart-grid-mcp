# MCP-Based Industrial Agent Benchmarking for Smart Grid Operations

**COMS E6998: High Performance Machine Learning -- Final Project**  
Columbia University, Spring 2026

**Team 13 / District 1101:** Akshat Bhandari (ab6174), Aaron Fan (af3623), Tanisha Rathod (tr2828), Wei Alexander Xin (wax1)  
**Mentor:** Dr. Dhaval Patel, IBM Research

## Overview

<p align="center">
  <img src="docs/images/power-transformer-substation.jpg" alt="Power transformer substation" width="600">
</p>

This project extends IBM's [AssetOpsBench](https://github.com/IBM/AssetOpsBench) industrial
AI agent benchmark (467 scenarios across 6 HuggingFace subsets) by adding a 7th domain -- Smart
Grid power transformers:

1. Creating 30+ maintenance scenarios for **Smart Grid transformers** using public telemetry data
2. Wrapping four AssetOpsBench tool domains (IoT, TSFM, FMSR, WO) as **MCP servers**
3. Profiling and optimizing the **LLM agent inference pipeline** when operating through MCP
4. Comparing two **orchestration paradigms** (Agent-as-Tool vs Plan-Execute) on end-to-end multi-domain scenarios

We serve Llama-3.1-8B-Instruct via vLLM, profile end-to-end with PyTorch Profiler, apply 2-3
optimization techniques (INT8 quantization, KV-cache tuning, batched tool-call scheduling),
and compare MCP-mediated tool calling against direct function calls to quantify protocol
overhead. All experiments tracked with WandB.

### Datasets

| Dataset | Rows | Primary Agent | License | Source |
|---|---|---|---|---|
| [Power Transformers FDD & RUL](https://www.kaggle.com/datasets/yuriykatser/power-transformers-fdd-and-rul) | 3,000 files x 420 | TSFM, IoT | CC0 | Kaggle |
| [DGA Fault Classification](https://www.kaggle.com/datasets/bantipatel20/dissolved-gas-analysis-of-transformer) | 201 | FMSR | CC0 | Kaggle |
| [Transformer Health Index](https://www.kaggle.com/datasets/easonlai/sample-power-transformers-health-condition-dataset) | 470 | FMSR | ODbL | Kaggle |
| [Current & Voltage Monitoring](https://www.kaggle.com/datasets/sreshta140/ai-transformer-monitoring) | 19,352 | IoT, TSFM | © Authors | Kaggle |
| [Smart Grid Fault Records](https://www.kaggle.com/datasets/ziya07/power-system-faults-dataset) | 506 | WO | CC0 | Kaggle |

Only CC0 datasets will be used in any open-source contributions back to AssetOpsBench.

### Why Llama-3.1-8B-Instruct?

| Model | Params | FP16 VRAM | Tool-calling support | Fit for this project |
|---|---|---|---|---|
| **Llama-3.1-8B-Instruct** | 8B | ~16GB | Good, well-documented, strong vLLM support | Best -- fits A6000, enables rapid iteration, INT8 optimization is meaningful (16→8GB) |
| Phi-4-14B | 14B | ~28GB | Strong reasoning, less proven for tool calling | Reasonable but less community tooling |
| Mistral-Small-24B | 24B | ~48GB | Good | Needs A100, fewer experiment iterations per dollar |
| Gemma-3-27B | 27B | ~54GB | Good | Needs A100 80GB, overkill for benchmarking |

We select Llama-3.1-8B-Instruct for its favorable profiling characteristics: it fits comfortably on
an A6000 with room for KV-cache experiments, and INT8 quantization produces a meaningful
memory reduction. We optionally compare against Llama-3.3-70B (AssetOpsBench's default model)
via WatsonX API to assess scaling effects.

## Repository Structure

```
.
├── README.md
├── README.md                     # This file — project overview, current status, structure
├── requirements.txt              # Python dependencies (ibm-watsonx-ai, pandas, etc)
├── .github/workflows/            # CI (Black formatting check)
│
├── data/                         # Data pipeline + processed datasets — see data/README.md
│   ├── build_processed.py        #   Downloads + joins 5 Kaggle datasets via synthesized transformer_id
│   ├── generate_synthetic.py     #   Offline synthetic equivalent (no Kaggle needed)
│   ├── processed/                #   6 joined CSVs tracked in git (asset_metadata, dga_records, …)
│   ├── scenarios/                #   AssetOpsBench-format scenario files — see data/scenarios/README.md
│   └── raw/                      #   GITIGNORED raw Kaggle downloads
│
├── mcp_servers/                  # 4 MCP servers on shared base — see mcp_servers/README.md
│   ├── base.py                   #   Shared data loader + utilities
│   ├── iot_server/               #   Sensor reads, asset metadata
│   ├── fmsr_server/              #   Failure search, IEC 60599 Rogers Ratio DGA analysis
│   ├── tsfm_server/              #   RUL forecast, z-score anomaly, OLS trend
│   └── wo_server/                #   Work order CRUD, downtime estimation
│
├── scripts/                      # Utility scripts
│   ├── verify_watsonx.py         #   WatsonX access verification + latency benchmarking
│   └── benchmark_prompts/        #   Prompt templates for latency tests
│
├── benchmarks/                   # Raw latency/throughput runs — see benchmarks/README.md
│   ├── baseline/                 #   Pre-optimization (direct Python, MCP baseline)
│   └── optimized/                #   Post-optimization (int8, kv_cache, batched)
│
├── notebooks/                    # Jupyter notebooks — see notebooks/README.md
├── profiling/                    # PyTorch Profiler + Nsight — see profiling/README.md
├── results/                      # Curated metrics + figures — see results/README.md
│
├── docs/                         # Living authored documentation — see docs/README.md
├── planning/                     # Meeting agendas + working notes
└── reports/                      # Frozen deliverables (PDFs, PPTXs) — see reports/README.md
    └── archive/                  #   Superseded drafts
```

## Setup

### Prerequisites

- Python 3.12+
- Docker (for CouchDB)
- CUDA-capable GPU (16GB+ VRAM recommended)
- Access to Columbia Insomnia cluster or Google Cloud GPU instance
- WatsonX API key (via [Codabench](https://www.codabench.org/competitions/10206/))

### Installation

```bash
git clone https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp.git
cd hpml-assetopsbench-smart-grid-mcp
pip install -r requirements.txt
```

### Running Experiments

*Instructions will be added as the project progresses.*

## Experiment Tracking

WandB dashboard: https://wandb.ai/assetopsbench-smartgrid

## Current Status

*Last updated: Apr 9, 2026 - W2 foundation work in progress, planning system reset complete.*

**Week 1 (complete):**
- [x] Problem statement finalized (four contributions)
- [x] Research proposal drafted and shared with mentor via Overleaf; mentor endorsed NeurIPS 2026 Datasets & Benchmarks track
- [x] GitHub repo scaffolded, WandB team created, **repo now public** (Apr 7)
- [x] 5 Kaggle datasets identified, AssetOpsBench forked and reviewed
- [x] Compute confirmed (Insomnia cluster + GCP credits) and compute plan committed (`docs/compute_plan.md`)
- [x] WatsonX API access received from mentor (Apr 5) and verified end-to-end — 6 Llama models available; Llama-4-Maverick-17B and Llama-3.3-70B-instruct benchmarked (`docs/watsonx_access.md`)
- [x] Data pipeline + processed Kaggle datasets landed (`data/processed/` with asset_metadata, dga_records, failure_modes, fault_records, rul_labels, sensor_readings — 97k+ rows, synthesized `transformer_id` key across 20 transformers)
- [x] MCP server skeletons landed for all four domains (IoT, FMSR, TSFM, WO) on a shared base class with substantive domain logic (IEC 60599 Rogers Ratio DGA analysis, RUL forecast, anomaly detection, work-order CRUD)
- [x] `docs/data_pipeline.tex` paper section drafted
- [x] **Mid-point report submitted** (`reports/2026-04-06_midpoint_submission.pdf`) to Courseworks on Mon Apr 6

**Week 2 (in progress, Apr 7-13):**
- [x] GitHub Projects reset as the canonical planning surface, with weekly iterations, workstream parent issues, and delivery-gate milestones
- [ ] Successful first Insomnia A6000 vLLM serve smoke test for Llama-3.1-8B-Instruct
- [ ] AssetOpsBench evaluation harness running end-to-end on the canonical repo
- [ ] Smart Grid MCP validation through the benchmark Llama path, not only Claude Desktop
- [ ] First 15+ Smart Grid scenarios committed and validated in the canonical repo
- [ ] First Smart Grid end-to-end MCP trajectory and first judge-scored artifact

**Committed W3-W5 tracks:**
- Experiment 1: MCP overhead and optimization (Direct vs MCP-baseline vs MCP-optimized)
- Experiment 2: orchestration comparison and failure analysis
- Problem Statement B extension: scenario generation pipeline, Knowledge Plugin, and validation methodology
- NeurIPS 2026 draft first, then back-port to the class IEEE report format

**Open question awaiting mentor reply:** is **Hybrid Plan-Execute with reflection checkpoints** novel enough to add as a third orchestration condition alongside vanilla Agent-as-Tool and vanilla Plan-Execute?

## Key Dates

| Date | Milestone |
|---|---|
| Mon Apr 6 | Mid-point report due (Courseworks, 11:59pm) |
| Sun May 4 | Final presentation + project due |
| Sun May 4 | NeurIPS 2026 Datasets & Benchmarks abstract deadline |
| Wed May 6 | NeurIPS 2026 full submission deadline |

## References and Resources

- [AssetOpsBench](https://github.com/IBM/AssetOpsBench) -- IBM's industrial AI agent benchmark
- [AssetOpsBench on HuggingFace](https://huggingface.co/datasets/ibm-research/AssetOpsBench)
- [AssetOpsBench competition](https://www.codabench.org/competitions/10206/)
- [Model Context Protocol](https://modelcontextprotocol.io/) -- open protocol for LLM tool integration
- [vLLM](https://github.com/vllm-project/vllm) -- High-throughput LLM serving
- [PyTorch Profiler](https://pytorch.org/tutorials/recipes/recipes/profiler_recipe.html)
- [Weights & Biases](https://wandb.ai/site)

See also: [docs/project_reference.md](docs/project_reference.md) for class requirements, grading, and mentor guidance.

## Acknowledgments

We acknowledge the use of AI tools, including Claude, during the development of this project.

## License

MIT
