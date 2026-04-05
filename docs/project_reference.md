# Project Reference

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
| WandB experiments + dashboard | wandb.ai link | 20% |
| Technical contributions + methodology + analysis | -- | 25% |
| Final presentation | PowerPoint (class template) | 10% |
| Final report | LaTeX (IEEE format, Overleaf) | 15% |
| Bonus: open-source PR, blog post, novel results | -- | up to 10% |

## Final Report Sections (Required)

- Abstract
- Introduction (background and motivation)
- Models and Data Description
- Training and Profiling Methodology
- Performance Tuning Methodology
- Experimental Results (before/after, visualizations)
- Conclusion (findings, limitations, future work)

## Team Strengths

| Name | UNI | Primary Strengths |
|---|---|---|
| Alex Xin | wax1 | Production data systems, agentic AI, project management |
| Akshat Bhandari | ab6174 | Multi-agent LLM systems, evaluation harnesses, published VLM research |
| Tanisha Rathod | tr2828 | Distributed systems, AWS/SageMaker, high-perf APIs, LoRA |
| Aaron Fan | af3623 | Real-time embedded systems, EE background (power systems), low-level APIs |
