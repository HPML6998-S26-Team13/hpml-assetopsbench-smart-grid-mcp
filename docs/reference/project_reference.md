# Project Reference

*Last updated: April 18, 2026*

**Course:** COMS E6998 - High Performance Machine Learning, Spring 2026  
**Instructor:** Prof. Kaoutar El Maghraoui  
**Mentor:** Dr. Dhaval Patel (pateldha@us.ibm.com), Shuxin Lin (shuxin.lin@ibm.com)

## Mentor Guidance (Mar 5, 2026 Intro Call)

- Keep scope realistic and achievable -- this is a class project, not research
- Problem statement must be concrete and measurable
- Example structure: study dataset X, create N scenarios, benchmark performance, report
- Use existing tools (W&B, MLflow) rather than building from scratch
- Success = learning something new + discoverable findings that excite readers
- Avoid risky claims (no "10% improvement through fine-tuning")

## HPML Class Requirements

All projects must include:

1. **Profiling** -- PyTorch Profiler and/or NVIDIA Nsight to break down time in data
   preprocessing, loading, and inference
2. **Optimization** -- at least 1-3 techniques (quantization, LoRA, vLLM, async execution,
   KV-cache, etc.)
3. **GPU Infrastructure** -- Insomnia cluster or Google Cloud with GPU utilization metrics
4. **Experiment Tracking** -- WandB dashboard with all metrics logged
5. **Comparative Analysis** -- before/after optimization with compute, memory, I/O,
   latency, throughput insights

## Deliverables and Grading

| Deliverable | Format | Weight |
|---|---|---|
| Project proposal | (submitted Feb 22) | 5% |
| Code + profiling + docs + reproducibility | GitHub repo, Python/Jupyter | 25% |
| GitHub commit tracking | Individual participation evaluated via commit history | (part of 25%) |
| WandB experiments + dashboard | wandb.ai link | 20% |
| Technical contributions, novelty, performance methodology, analysis of results | -- | 25% |
| Final presentation + Q/A | PowerPoint (class template) | 10% |
| Final report | LaTeX (IEEE format, Overleaf) | 15% |
| Bonus: blog post, open-source PR, novel/publishable results, public repos | -- | up to 10% |

## Final Report Sections (Required)

**Class final report (IEEE format):**
- Abstract
- Introduction (background and motivation)
- Models and Data Description
- Training and Profiling Methodology
- Performance Tuning Methodology
- Experimental Results (before/after, visualizations)
- Conclusion (findings, limitations, future work)

**NeurIPS 2026 Datasets & Benchmarks submission (parallel target, 9 pages max):**
- Abstract
- Introduction and Problems in the Current Systems
- Our Ideas and Plan (contributions)
- System Design (architecture, orchestration, optimization)
- Evaluation Plan (metrics, baselines, methodology)
- Implementation Roadmap
- Core Integration Plan (dataset documentation, reproducibility)
- References

### Section Mapping: Class Report <-> NeurIPS 2026

| Class (IEEE) | NeurIPS 2026 | Notes |
|---|---|---|
| Abstract | Abstract | Same content, NeurIPS limited to 1 paragraph |
| Introduction | Introduction + Our Ideas and Plan | NeurIPS splits motivation from contributions |
| Models and Data Description | System Design + Core Integration Plan | NeurIPS separates architecture from dataset docs |
| Training and Profiling Methodology | System Design (Sec 3.3) | Optimization techniques section |
| Performance Tuning Methodology | System Design (Sec 3.3) | Same section, different framing |
| Experimental Results | Evaluation Plan + Results | NeurIPS: plan first, results section added later |
| Conclusion | Conclusion | Same, NeurIPS emphasizes reproducibility |
| -- | Implementation Roadmap | NeurIPS-only, shows project timeline |
| -- | References | Both require refs, NeurIPS has specific citation style |

## Team Strengths

| Name | UNI | Role | Key Strengths |
|---|---|---|---|
| Alex Xin | wax1 | Project management, experiment design, profiling analysis, report writing | Production data systems, agentic AI, project management |
| Akshat Bhandari | ab6174 | Scenario design, evaluation harness, judge integration | Multi-agent LLM systems, evaluation harnesses, published VLM research |
| Tanisha Rathod | tr2828 | MCP server implementation, data pipeline, Knowledge Plugin | Distributed systems, AWS/SageMaker, high-perf APIs, LoRA |
| Aaron Fan | af3623 | Serving infrastructure, profiling capture, scenario-generation pipeline | Real-time embedded systems, EE background (power systems), low-level APIs |
