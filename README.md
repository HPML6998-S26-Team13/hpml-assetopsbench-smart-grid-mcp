# MCP-Based Industrial Agent Benchmarking for Smart Grid Operations

**COMS E6998: High Performance Machine Learning -- Final Project**
Columbia University, Spring 2026

**Team 13:** Alex Xin (wax1), Akshat Bhandari (ab6174), Tanisha Rathod (tr2828), Aaron Fan (af3623)
**Mentor:** Dr. Dhaval Patel, IBM Research

## Overview

This project extends IBM's [AssetOpsBench](https://github.com/IBM/AssetOpsBench) industrial
AI agent benchmark by:

1. Creating 30+ maintenance scenarios for **Smart Grid transformers** using public telemetry data
2. Wrapping AssetOpsBench tool domains as **MCP (Model Context Protocol) servers**
3. Profiling and optimizing the **LLM agent inference pipeline** when operating through MCP

We serve Llama-3-8B via vLLM, profile end-to-end with PyTorch Profiler, apply 2-3
optimization techniques (INT8 quantization, KV-cache tuning, batched tool-call scheduling),
and report before/after comparisons with full WandB experiment tracking.

## Repository Structure

```
.
├── README.md
├── data/                  # Smart Grid datasets and scenario definitions
│   ├── raw/               # Raw Kaggle data
│   ├── processed/         # Cleaned data for scenario generation
│   └── scenarios/         # Generated AssetOpsBench scenarios
├── mcp_servers/           # MCP server implementations
│   ├── iot_server/        # IoT telemetry MCP server
│   └── tsfm_server/       # Time-series forecasting MCP server
├── benchmarks/            # Benchmark scripts and configurations
│   ├── baseline/          # Baseline (no optimization) runs
│   └── optimized/         # Runs with optimization techniques applied
├── profiling/             # PyTorch Profiler traces and analysis
├── notebooks/             # Jupyter notebooks for analysis and visualization
├── docs/                  # Project documentation
│   └── mid_checkpoint.md  # Mid-point progress report
├── results/               # Experiment results and figures
└── requirements.txt       # Python dependencies
```

## Setup

### Prerequisites

- Python 3.10+
- CUDA-capable GPU (16GB+ VRAM recommended)
- Access to Columbia Insomnia cluster or Google Cloud GPU instance

### Installation

```bash
git clone https://github.com/eggrollofchaos/hpml-assetopsbench-smart-grid-mcp.git
cd hpml-assetopsbench-smart-grid-mcp
pip install -r requirements.txt
```

### Running Experiments

*Instructions will be added as the project progresses.*

## Experiment Tracking

WandB dashboard: https://wandb.ai/assetopsbench-smartgrid

## Key Dates

| Date | Milestone |
|---|---|
| Apr 6 | Mid-point progress checkpoint |
| May 4 | Final presentation + project due |

## References and Resources

- [AssetOpsBench](https://github.com/IBM/AssetOpsBench) -- IBM's industrial AI agent benchmark
- [AssetOpsBench on HuggingFace](https://huggingface.co/datasets/ibm-research/AssetOpsBench)
- [AssetOpsBench competition](https://www.codabench.org/competitions/10206/)
- [Model Context Protocol](https://modelcontextprotocol.io/) -- Anthropic's open protocol for LLM tool integration
- [vLLM](https://github.com/vllm-project/vllm) -- High-throughput LLM serving
- [PyTorch Profiler](https://pytorch.org/tutorials/recipes/recipes/profiler_recipe.html)
- [Weights & Biases](https://wandb.ai/site)

See also: [docs/project_reference.md](docs/project_reference.md) for class requirements, grading, and mentor guidance.

## License

MIT
