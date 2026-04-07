# Compute Plan

*Last updated: April 5, 2026*
*Owner: Aaron Fan (af3623)*

## Overview

This document describes the GPU compute resources available to the team, maps each
project phase to specific hardware, and provides a recommendation for when to use
the Insomnia cluster versus GCP.

**TL;DR:** Use Insomnia A6000 nodes for nearly all work (development, profiling,
optimization experiments). Reserve H100 for final scaling comparisons only. Fall
back to GCP A100 spot instances if Insomnia queues are congested or for long-running
unattended jobs that exceed the `short` partition time limit.

---

## 1. Insomnia Cluster (Primary)

### Available GPUs

| GPU | VRAM | Per Node | Nodes | Total GPUs | Partition(s) |
|-----|------|----------|-------|------------|--------------|
| **H100** | 80 GB HBM3 | 2 | 3 (ins048-050) | 6 | `short`, `burst` |
| **L40S** | 48 GB GDDR6 | 2 | 9 (ins038-039, 056-061, 063) | 18 | `short`, `burst` |
| **L40** | 48 GB GDDR6 | 2 | 3 (ins035-037) | 6 | `short`, `burst` |
| **A6000** | 48 GB GDDR6 | 8 | 13 (ins080-092) | 104 | `short`, `burst` |
| **A6000** | 48 GB GDDR6 | 4 | 2 (ins093-094) | 8 | `short`, `burst` |

### Partitions

| Partition | Time Limit | Notes |
|-----------|------------|-------|
| `short` | ~2 hours | General-access, all GPU types |
| `burst` | ~2 hours | Same nodes as `short`, preemptible |

Named partitions (e.g., `pmg1`, `morpheus1`) are group-dedicated and not available to us.

### Job Examples

```bash
# Interactive: 1x A6000 for development / debugging
srun --partition=short --gres=gpu:A6000:1 --mem=64G --time=02:00:00 --pty bash

# Interactive: 2x A6000 for vLLM serving (multi-GPU)
srun --partition=short --gres=gpu:A6000:2 --mem=128G --time=02:00:00 --pty bash

# Interactive: 1x H100 for scaling comparison
srun --partition=short --gres=gpu:h100:1 --mem=64G --time=02:00:00 --pty bash

# Batch job example (recommended for profiling runs)
# Note: profiling wrapper scripts will live in profiling/scripts/ once authored in W3.
sbatch profiling/scripts/run_profile.sh
```

---

## 2. Google Cloud Platform (Backup)

**Budget:** $500 credits per team member ($2,000 total)

| Instance | GPU | VRAM | Spot $/hr | On-demand $/hr |
|----------|-----|------|-----------|----------------|
| `a2-highgpu-1g` | 1x A100 40 GB | 40 GB | ~$1.81 | ~$3.67 |
| `a2-ultragpu-1g` | 1x A100 80 GB | 80 GB | ~$2.50 | ~$5.07 |

**When to use GCP:**
- Insomnia queue wait times are too long during peak hours
- Jobs need to run longer than the `short` partition 2-hour limit
- Reproducibility runs requiring a clean, isolated environment
- Parallel experiments when Insomnia GPU slots are saturated

**Budget estimate:** At spot pricing on A100-40GB, $500/person buys ~276 GPU-hours.
Even conservatively, the team has 1,000+ GPU-hours of GCP capacity.

---

## 3. GPU Needs per Project Phase

### Phase 1: MCP Server Development (Apr 7-13) -- Week 2

| Need | GPU | Duration | Where |
|------|-----|----------|-------|
| vLLM serving for Llama-3.1-8B (FP16, ~16 GB) | 1x A6000 | 1-2 hr sessions | Insomnia `short` |
| End-to-end agent trajectory testing through MCP | 1x A6000 | 1-2 hr sessions | Insomnia `short` |
| Dataset loading / preprocessing | CPU only | -- | Insomnia login node or local |

**Rationale:** Llama-3.1-8B at FP16 fits in ~16 GB. A single A6000 (48 GB) leaves
ample headroom for vLLM's KV-cache and batch buffers. A6000 nodes are plentiful
(112 GPUs total) so queue times should be minimal.

### Phase 2: Baseline Profiling (Apr 14-20) -- Week 3

| Need | GPU | Duration | Where |
|------|-----|----------|-------|
| Condition 1: Direct function calls (no MCP) | 1x A6000 | 2 hr | Insomnia `short` |
| Condition 2: MCP baseline (unoptimized) | 1x A6000 | 2 hr | Insomnia `short` |
| Condition 3: MCP optimized (INT8) | 1x A6000 | 2 hr | Insomnia `short` |
| PyTorch Profiler trace collection | same sessions | -- | -- |
| NVIDIA Nsight profiling | same sessions | -- | -- |
| nvidia-smi monitoring (GPU util, memory) | same sessions | -- | -- |

**Rationale:** Three separate profiling conditions, each fitting in a single 2-hour
`short` session on A6000. INT8-quantized model drops to ~8 GB, still well within A6000
capacity. Run profiling as batch jobs (`sbatch`) to avoid losing work on session timeout.

### Phase 3: Optimization Experiments (Apr 21-27) -- Week 4

| Need | GPU | Duration | Where |
|------|-----|----------|-------|
| INT8 quantization comparison | 1x A6000 | 2 hr | Insomnia `short` |
| KV-cache tuning sweeps | 1x A6000 | 2 hr x N | Insomnia `short` |
| Batched tool-call scheduling | 1x A6000 | 2 hr | Insomnia `short` |
| Orchestration comparison (AaT vs PE) | 1x A6000 | 2 hr x 2 | Insomnia `short` |
| *Scaling test: H100 comparison* | 1x H100 | 2 hr | Insomnia `short` |
| *Scaling test: multi-GPU vLLM* | 2x A6000 | 2 hr | Insomnia `short` |

**Rationale:** Most optimization experiments are parameter sweeps that fit in 2-hour
sessions. Run multiple sequential sessions or parallelize across A6000 nodes. Use
H100 for a single scaling comparison datapoint (same workload, different hardware)
to show performance portability.

### Phase 4: Final Runs + Report (Apr 28-May 3) -- Week 5

| Need | GPU | Duration | Where |
|------|-----|----------|-------|
| Reproducibility runs (all 30+ scenarios, 3 conditions) | 1x A6000 | 2 hr x 3-5 | Insomnia or GCP |
| LLM-as-Judge evaluation (Llama-4-Maverick-17B) | WatsonX API or 1x A100-80GB | varies | WatsonX or GCP |
| Any re-runs / gap-filling | 1x A6000 | as needed | Insomnia or GCP |

**Rationale:** Final reproducibility runs may need longer continuous sessions. If
Insomnia's 2-hour limit is constraining, use GCP A100 spot instances. Llama-4-Maverick-17B
for evaluation is large; prefer WatsonX API if available, otherwise run on GCP A100-80GB.

---

## 4. Model Memory Requirements

| Model | Precision | VRAM | Fits on |
|-------|-----------|------|---------|
| Llama-3.1-8B-Instruct | FP16 | ~16 GB | A6000 (48 GB), L40/L40S (48 GB), H100 (80 GB) |
| Llama-3.1-8B-Instruct | INT8 | ~8 GB | All GPUs |
| Llama-3.3-70B (optional scaling) | FP16 | ~140 GB | WatsonX API (preferred) |
| Llama-4-Maverick-17B (judge) | FP16 | ~34 GB | WatsonX API (preferred) |

---

## 5. Recommendation Summary

| Scenario | Use |
|----------|-----|
| **Default for all work** | Insomnia A6000 (`short` partition) |
| **Scaling comparison** | Insomnia H100 (`short` partition), 1-2 sessions only |
| **Long-running / unattended jobs** | GCP A100-40GB spot (~$1.81/hr) |
| **LLM-as-Judge (Maverick-17B)** | WatsonX API (preferred) or GCP A100-80GB spot |
| **Large model (70B, optional)** | WatsonX API (preferred) |
| **Insomnia queues full** | GCP A100-40GB spot as overflow |

### Why Insomnia over GCP

- **Cost:** Insomnia is free. GCP burns through credits at $1.81-5.07/hr per GPU.
  With ~30-50 GPU-hours needed, that's $55-250 on GCP vs $0 on Insomnia.
- **No spot preemption:** GCP spot instances can be reclaimed mid-job with 30 seconds
  notice, potentially losing an entire profiling run. Insomnia `short` jobs run to
  completion within the 2-hour window.
- **Lower latency:** Insomnia is on Columbia's campus network. No cloud egress fees,
  no data upload time for datasets, no SSH tunneling through NAT.
- **More GPU variety:** Insomnia has A6000, L40, L40S, and H100 all accessible from
  the same login node. On GCP, switching GPU types means creating a new instance.
- **HPML class alignment:** The course explicitly lists Insomnia as the recommended
  infrastructure. Using it demonstrates familiarity with university HPC resources,
  which is part of the grading criteria (GPU infrastructure + utilization metrics).
- **Credit conservation:** The $2,000 in GCP credits is a finite, non-renewable
  resource. Saving it for situations where Insomnia genuinely can't deliver (long jobs,
  queue saturation, large judge model) is better than spending it on work Insomnia
  handles fine.

GCP is the better choice only when: (1) a job needs to run longer than 2 hours
uninterrupted, (2) Insomnia queues are backed up and a deadline is approaching, or
(3) we need an A100-80GB for the Maverick-17B judge model that doesn't fit well
alongside vLLM overhead on a 48 GB A6000.

### Why A6000 over H100 for most work

- **Availability:** 112 A6000 GPUs vs 6 H100 GPUs. Far less queue contention.
- **Sufficiency:** Llama-3.1-8B at FP16 uses ~16 GB; A6000's 48 GB is more than enough.
- **Cost-equivalence:** Both are free on Insomnia. H100's extra bandwidth and compute
  are wasted on an 8B model that isn't compute-bound.
- **Reproducibility:** A6000 is more representative of typical deployment hardware.
  H100 results would be impressive but less generalizable.

H100 is valuable for one thing: a scaling comparison datapoint showing how the same
workload performs on different GPU tiers. Plan for 1-2 H100 sessions in Week 4.

### Budget Conservation

At current estimates, the project needs ~30-50 GPU-hours total across all phases.
Insomnia covers this entirely at zero cost. GCP credits ($2,000 total) should be
treated as insurance, not the primary compute source. Estimated GCP spend: $0-50
under normal conditions, up to $200 if Insomnia has extended downtime.
