# Mid-Point Report -- Slide Content

Template: HPML_Mid_Report_Template.pptx (5 slides)

---

## Slide 1: Title

HPML – SmartGridBench  
Team 13 / District 1101  
Midpoint Progress Report  
Akshat Bhandari (ab6174), Aaron Fan (af3623), Tanisha Rathod (tr2828), Wei Alexander Xin (wax1)

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

**GitHub:** https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp

**WandB:** https://wandb.ai/assetopsbench-smartgrid

**Results obtained so far:**

- **Project setup complete:** mentor-aligned problem statement (Proposals 1 + 4: MCP standardization + Smart Grid scenario generation), full research proposal shared with Dhaval via Overleaf, team repo with CI/docs/WandB tracking, compute plan committed (Insomnia 6x H100 + ~100x A6000, $500/person GCP, WatsonX API)

- **Data pipeline landed:** 5 Kaggle datasets joined via synthesized `transformer_id` key (T-001–T-020 stratified across 4 health tiers); 97k+ rows processed and tracked in `data/processed/`

- **MCP servers built for all four domains** on shared base class: IoT (sensor reads, asset metadata), FMSR (failure search, **IEC 60599 Rogers Ratio DGA analysis**), TSFM (RUL forecast, z-score anomaly detection, OLS trend), WO (work-order CRUD, downtime estimation) — ~2k Python lines landed

- **WatsonX Llama models verified and benchmarked end-to-end** *(see `docs/reference/watsonx_access.md`)*:
  - Llama-4-Maverick-17B (judge): ~84 tok/s, tight variance (warm 1.4-1.6s, cold ≈ warm) — interactive-speed
  - Llama-3.3-70B-instruct (scaling): ~19-34 tok/s, high cold-call variance (short-prompt warm range 1.6-16.3s)
  - **Maverick is ~2.3x faster than 70B** on matched 1,400-token code-review prompts (6.4s warm vs 14.8s warm); both correctly identified key bugs in the smoke test

---

## Slide 4: Work in Progress

- Fleshing out MCP server implementations on top of the skeletons for all four domains (IoT, FMSR, TSFM, WO)
- Designing and authoring first batch of Smart Grid scenarios (targeting 15+ by Apr 13, 30+ by Apr 27)
- Getting AssetOpsBench evaluation harness running end-to-end with existing scenarios
- Deploying Llama-3.1-8B-Instruct via vLLM on Insomnia cluster for baseline inference runs
- Preparing profiling methodology: PyTorch Profiler instrumentation for tool-call latency, GPU utilization, memory bandwidth
- Designing orchestration comparison: Agent-as-Tool vs Plan-Execute on end-to-end scenarios
- Finalizing two-repo strategy: team repo for R&D, AssetOpsBench fork as staging area for eventual upstream PR contribution

---

## Slide 5: Blockers and Limitations

- **No single dataset covers all agent domains — being addressed:** Combined 5 Kaggle datasets via synthesized `transformer_id` key (T-001–T-020 stratified across 4 health tiers), giving each fictional transformer a consistent cross-domain narrative.
Still in progress: validating that queries return coherent stories across domains (e.g., a transformer's sensor anomalies align with its fault and failure-mode history), and expanding beyond the initial 20-transformer fleet as scenarios grow.
- **Licensing gap for the IoT domain:** 3 of 5 source datasets are CC0 (FDD&RUL, DGA, Fault Records — covering TSFM, FMSR, WO), but Transformer Health Index (ODbL) and Current & Voltage Monitoring (author copyright) are non-redistributable. These feed IoT's asset metadata and sensor readings, so without a fix, the public PR would ship 3 of 4 domains with real data.
**Mitigation:** Tanisha's `generate_synthetic.py` already produces a synthetic 20-transformer fleet with sensor time series; we plan to ship this as the default IoT data source for the public PR so all 4 domains are covered end-to-end, while continuing to search for CC0 real replacements (HuggingFace, data.gov) to strengthen the contribution.
- **Insomnia H100 time limit:** 2-hour session cap on H100 nodes. Mitigated by using A6000 or A100 for most work; H100 reserved for final profiling comparisons if needed.

---

# Archive

## Slide 3 items

**Results obtained so far:**
- Held intro meeting with mentor Dr. Dhaval Patel; aligned on scope and constraints
- Forked AssetOpsBench for eventual PR; reviewed scenario structure, evaluation harness, and MCP server patterns
- Finalized problem statement combining Proposals 1 and 4 from mentor (MCP standardization + Smart Grid scenario generation)
- Identified and documented 5 candidate Kaggle datasets covering all 4 agent domains (IoT, FMSR, TSFM, WO)
- Set up GitHub repo with scaffolded project structure, CI (Black formatting), documentation
- Set up WandB team project for experiment tracking
- Problem statement and full research proposal drafted and shared with mentor via Overleaf
- Data pipeline + 6 processed Kaggle datasets landed in `data/processed/`
- Confirmed compute infrastructure: Insomnia cluster (6x H100, ~100x A6000) + $500 GCP credits/person
- MCP server skeletons landed for all four domains (IoT, FMSR, TSFM, WO) on a shared base class
- Compute plan committed (GPU needs per phase, Insomnia vs GCP)
- Synthesizing common `transformer_id` key across datasets to enable cross-domain scenarios
- WatsonX API access verified; Maverick-17B (judge) and Llama-3.3-70B (scaling) benchmarked end-to-end

## Slide 5 items

**Blockers and Limitations** *(pre-Apr 6 version, preserved for reference)*:

- **No single dataset covers all agent domains:** We need to combine 3-5 Kaggle datasets using a synthesized key. Ensuring cross-domain consistency (e.g., a transformer's sensor data aligns with its fault history) requires careful data engineering, e.g. creating a fleet of N fictional transformers spanning all 4 agentic domains, mapped to specific attributes accordingly.
- **Licensing restrictions on 2 of 5 datasets:** Transformer Health Index (ODbL) and Current & Voltage Monitoring (author copyright) may not be redistributable in an open-source PR. We plan to use only CC0 datasets for any public contribution.
- **Insomnia H100 time limit:** 2-hour session cap on H100 nodes. Mitigated by using A6000 or A100 for most work; H100 reserved for final profiling comparisons if needed.
- **WatsonX API access pending:** Required for running AssetOpsBench's LLM-as-Judge evaluation (Llama-4-Maverick-17B). We've registered on Codabench and contacted our mentor directly. Without it, we can still build and test MCP servers and scenarios, but cannot run the official evaluation pipeline.
