# Mid-Point Report -- Slide Content

Template: HPML_Mid_Report_Template.pptx (5 slides)

---

## Slide 1: Title

HPML Project Mid-point Progress
Team 13 / District 1101
Alex Xin (wax1), Akshat Bhandari (ab6174), Tanisha Rathod (tr2828), Aaron Fan (af3623)

---

## Slide 2: Project Summary

**Project Title:** MCP-Based Industrial Agent Benchmarking for Smart Grid Transformer Operations

**Project Goals:**
- Extend IBM's AssetOpsBench benchmark with 30+ Smart Grid transformer maintenance scenarios
- Wrap all four tool domains (IoT, FMSR, TSFM, WO) as MCP servers for standardized, model-agnostic LLM tool calling
- Profile and optimize the end-to-end LLM agent inference pipeline through the MCP communication layer
- Compare two orchestration paradigms (Agent-as-Tool vs Plan-Execute) on end-to-end multi-domain scenarios
- Contribute scenarios and MCP servers back to the AssetOpsBench open-source project via pull request

**AI Model(s):**
- Llama-3.1-8B-Instruct (primary, served via vLLM)
- Llama-4-Maverick-17B (LLM-as-Judge for evaluation, via WatsonX)
- Optional: Llama-3.3-70B via WatsonX API for scaling comparison (AssetOpsBench's default model)

**Dataset(s):**
- [Power Transformers FDD & RUL](https://www.kaggle.com/datasets/yuriykatser/power-transformers-fdd-and-rul) (3,000 files x 420 rows, CC0)
- [DGA Fault Classification](https://www.kaggle.com/datasets/bantipatel20/dissolved-gas-analysis-of-transformer) (201 rows, CC0)
- [Smart Grid Fault Records](https://www.kaggle.com/datasets/ziya07/power-system-faults-dataset) (506 rows, CC0)
- [Transformer Health Index](https://www.kaggle.com/datasets/easonlai/sample-power-transformers-health-condition-dataset) (470 rows, ODbL)
- [Current & Voltage Monitoring](https://www.kaggle.com/datasets/sreshta140/ai-transformer-monitoring) (19,352 rows)

**Performance Optimization Techniques/Methodology:**
- INT8 quantization (FP16 -> INT8 via vLLM, ~16GB -> ~8GB memory)
- KV-cache tuning (optimize block size and memory allocation for multi-turn tool calling)
- Batched tool-call scheduling (parallelize independent MCP requests)
- Compare MCP-mediated vs direct function calls to quantify protocol overhead
- Orchestration comparison: Agent-as-Tool (single LLM, sequential) vs Plan-Execute (planner + executor) on multi-domain scenarios

**Profiling/Performance Analysis Tools:**
- PyTorch Profiler (end-to-end pipeline traces)
- NVIDIA Nsight / nvidia-smi (GPU utilization)
- Weights & Biases (experiment tracking and dashboards)
- vLLM built-in metrics (token throughput, latency)

---

## Slide 3: Current Progress

**GitHub:** https://github.com/eggrollofchaos/hpml-assetopsbench-smart-grid-mcp

**WandB:** https://wandb.ai/assetopsbench-smartgrid

**Results obtained so far:**
- Finalized problem statement combining Proposals 1 and 4 from mentor (MCP standardization + Smart Grid scenario generation)
- Held intro meeting with mentor Dr. Dhaval Patel (Mar 5); aligned on scope and constraints
- Problem statement and full research proposal drafted and shared with mentor via Overleaf
- Forked AssetOpsBench; reviewed scenario structure, evaluation harness, and MCP server patterns
- Identified and documented 5 candidate Kaggle datasets covering all 4 agent domains (IoT, FMSR, TSFM, WO)
- Confirmed compute infrastructure: Insomnia cluster (6x H100, ~100x A6000) + $500 GCP credits/person
- Set up GitHub repo with scaffolded project structure, CI (Black formatting), documentation
- Set up WandB team project for experiment tracking
- Requested WatsonX API access for running AssetOpsBench evaluation pipeline

---

## Slide 4: Work in Progress

- Implementing four MCP servers (IoT, FMSR, TSFM, WO) for Smart Grid transformer data
- Designing and authoring first batch of Smart Grid scenarios (targeting 15+ by Apr 13, 30+ by Apr 27)
- Synthesizing common `transformer_id` key across datasets to enable cross-domain scenarios
- Getting AssetOpsBench evaluation harness running end-to-end with existing scenarios
- Deploying Llama-3.1-8B-Instruct via vLLM on Insomnia cluster for baseline inference runs
- Preparing profiling methodology: PyTorch Profiler instrumentation for tool-call latency, GPU utilization, memory bandwidth
- Designing orchestration comparison: Agent-as-Tool vs Plan-Execute on end-to-end scenarios
- Awaiting WatsonX API key for access to Llama-4-Maverick-17B judge model

---

## Slide 5: Blockers and Limitations

- **WatsonX API access pending:** Required for running AssetOpsBench's LLM-as-Judge evaluation (Llama-4-Maverick-17B). We've registered on Codabench and contacted our mentor directly. Without it, we can still build and test MCP servers and scenarios, but cannot run the official evaluation pipeline.
- **No single dataset covers all agent domains:** We need to combine 3-5 Kaggle datasets using a synthesized key. Ensuring cross-domain consistency (e.g., a transformer's sensor data aligns with its fault history) requires careful data engineering, e.g. creating a fleet of N fictional transformers spanning all 4 agentic domains, mapped to specific attributes accordingly.
- **Licensing restrictions on 2 of 5 datasets:** Transformer Health Index (ODbL) and Current & Voltage Monitoring (author copyright) may not be redistributable in an open-source PR. We plan to use only CC0 datasets for any public contribution.
- **Insomnia H100 time limit:** 2-hour session cap on H100 nodes. Mitigated by using A6000 or A100 for most work; H100 reserved for final profiling comparisons if needed.
