# Execution Plan: W2-W5

*Last updated: April 7, 2026*

How the team executes the remaining ~4 weeks of work, organized in two parts:

1. **Task dependency map** — which tasks block which, and what the critical path looks like
2. **Benchmarking operations** — what running experiments actually looks like (it's mostly async batch jobs, not synchronous coordination)

> **TL;DR:** Once W2 setup is done (vLLM up, MCP servers hardened, eval harness wired, WandB instrumented, Slurm template written), W3-W4 benchmark runs are submit-and-walk-away. Nobody needs to be online during runs. The team coordinates during W2 setup and during analysis discussions — not during the experiments themselves.

---

## Part 1: Task dependency map

### Critical path

```
Insomnia/vLLM up           ┐
MCP server hardening       ├──► First baseline trajectory ──► All experiment runs ──► Analysis ──► Paper
Eval harness end-to-end    │
WandB instrumentation      ┘
```

The four foundation tasks above form a single bottleneck: **all four must complete before any benchmark runs can start**. Each is owned by a different person, so they can run in parallel during W2 — but downstream work is blocked until the slowest of the four lands.

### Task tiers

#### Tier 1 — Foundation (W2, must complete to unblock everything else)

| Task | Owner | Blocked by | Blocks |
|---|---|---|---|
| Insomnia/vLLM environment up + Llama-3.1-8B-Instruct serving | Aaron | (nothing) | All local GPU work, all experiment runs |
| MCP server hardening (4 servers, tests, edge cases) | Tanisha | (nothing) | Eval harness integration, all benchmarks |
| Eval harness end-to-end on existing scenarios | Akshat | Tanisha's hardened MCP, Aaron's vLLM | All benchmarks, all scoring |
| 15+ Smart Grid scenarios authored | Akshat | (nothing — can write in parallel) | All benchmarks (the test set) |
| Profiling harness scripts (PyTorch Profiler wrappers) | Aaron | vLLM up | Experiment 1 capture |
| WandB instrumentation (metrics schema in MCP servers + eval harness) | Alex | Tanisha's MCP, Akshat's harness | All experiment logging |
| Slurm batch script template | Aaron | vLLM, harness, MCP, WandB | Async benchmarking |

#### Tier 2 — Experimental design (W2-W3, depends on Tier 1)

| Task | Owner | Blocked by | Blocks |
|---|---|---|---|
| Orchestration wiring (AaT + PE on team's MCP servers) | Alex | Tier 1 complete | Experiment 2 |
| Hybrid orchestration prototype implementation | Alex | Tier 1 + mentor novelty check reply | Experiment 2 condition Z |
| Self-Ask integration (~10 LOC, addresses "Fail to Ask for Clarification" failures) | Alex | Alex's orchestrations exist | Quality of all 3 conditions |
| 6-dimension LLM-as-Judge scoring in eval harness | Akshat | Eval harness running | Final scoring of all runs |
| First baseline trajectory through MCP (the integration moment) | Akshat + Tanisha + Alex | All Tier 1 done | Confidence to start Tier 3 |

#### Tier 3 — Benchmark execution (W3-W4, fully async, anyone can submit)

| Task | Owner | Blocked by | Blocks |
|---|---|---|---|
| Experiment 1 runs (3 MCP conditions × N scenarios) | Aaron submits, Alex analyzes | Tier 1 + 2 complete | Final report |
| Experiment 2 runs (3 orchestrations × N multi-domain scenarios) | Alex submits | Tier 1 + 2 complete | Final report |
| INT8 quantization experiment | Aaron | vLLM + Slurm template | MCP-optimized condition |
| KV-cache tuning experiment | Aaron | vLLM + Slurm template | MCP-optimized condition |
| Batched tool-call scheduling implementation + experiment | Akshat | Eval harness + MCP | MCP-optimized condition |
| 30+ scenarios completed | Akshat | (none — ongoing authoring through W4) | Final benchmark coverage |

#### Tier 4 — Analysis (W4, depends on Tier 3 results)

| Task | Owner | Blocked by | Blocks |
|---|---|---|---|
| Notebook 02: latency analysis (MCP overhead) | Alex | Experiment 1 results in WandB | Paper section on overhead |
| Notebook 03: orchestration comparison | Alex | Experiment 2 results in WandB | Paper section on orchestration |
| Failure mode taxonomy analysis (Berkeley failure paper applied to our results) | Alex | Experiment 2 results | Paper analysis section |

#### Tier 5 — Writing (W4-W5, Alex drives, others contribute facts)

| Task | Owner | Blocked by | Blocks |
|---|---|---|---|
| NeurIPS draft (sole author: Alex; format: Datasets & Benchmarks Track) | Alex | Notebook results | Final submission |
| Class final report (back-port of NeurIPS draft to IEEE template) | Alex | NeurIPS draft | May 4 submission |
| Methodology + Data content brief (1-page bullet list of facts) | Tanisha → Alex | (nothing — can hand off any time) | NeurIPS draft |
| Scenarios + Eval content brief | Akshat → Alex | (nothing) | NeurIPS draft |
| Infrastructure + Profiling content brief | Aaron → Alex | (nothing) | NeurIPS draft |

### Critical-path implications

- **Tier 1 is the bottleneck.** Until all four foundation tasks land, no benchmark runs can start. Three of the four are owned by different people, so they can progress in parallel — but the slowest sets the schedule.
- **The first baseline trajectory** (Akshat + Tanisha + Alex jointly verifying that an agent can run a scenario end-to-end through MCP) is the integration moment that unlocks all experiment runs. It requires all four Tier 1 tasks to be done.
- **Tier 3 can run in parallel and async** — once the foundation is in place, multiple experiment cells can be submitted as independent Slurm jobs, each running unattended.
- **Tier 5 (writing) can begin during Tier 3** — Alex can draft outline, intro, methodology, related work in parallel with experiments running. Only Results and Discussion need to wait for Tier 4 analysis.

---

## Part 2: Benchmarking operations

### The async batch workflow (this is what running experiments actually looks like)

Once Tier 1 setup is in place, running an experiment cell is **submit-and-walk-away**:

```
1. Author writes a config file:
   scenarios=smartgrid_v1
   orchestration=plan_execute
   mcp_mode=baseline
   trials=5
   model=llama-3.1-8b-instruct

2. Author submits to Slurm:
   sbatch scripts/run_experiment.sh configs/exp_PE_baseline.yaml

3. Slurm allocates a GPU, spins up vLLM + MCP servers + eval harness
   inside the job's process tree.

4. Eval harness loops through all 30+ scenarios × 5 trials = 150 runs.
   Each run:
     - Sends scenario prompt to the agent (orchestrated via the chosen
       orchestration: AaT, PE, or Hybrid)
     - Agent makes tool calls to the team's MCP servers (running
       in-process or over local socket)
     - Captures: per-tool latency, total wall-clock, tokens consumed,
       completion success (LLM-as-Judge score), trajectory log
     - Logs all metrics to WandB

5. Job completes (1-3 hours later). Results live in WandB.

6. Author opens analysis notebook the next morning, reads from WandB,
   computes statistics, generates figures.

NOBODY was online during steps 3-5.
```

### Role clarifications

The async workflow above implies specific roles that may differ from the team's intuition:

| Role | NOT this | IS this |
|---|---|---|
| **Akshat (eval harness owner)** | Manually runs `python run_scenario.py 1`, watches output, runs `python run_scenario.py 2`, etc. | **Authors scenarios + builds the harness that loops through them automatically.** Once authored, scenarios live in `data/scenarios/*.json` and the harness consumes them in batch. |
| **Aaron (infrastructure owner)** | Babysits WandB during runs, watches metrics, intervenes on failures | **Writes Slurm templates + profiling capture wrappers + ensures vLLM is reliably servable.** Once the template is written, anyone can submit jobs. |
| **Tanisha (MCP server owner)** | Responds to MCP requests interactively while teammates run scenarios | **Hardens her MCP servers so they run as long-lived processes inside Slurm jobs without intervention.** Once hardened, the servers are hands-off. |
| **Alex (experiment + analysis owner)** | Manually compares orchestrations by running each one and watching | **Designs experiment configs, submits Slurm jobs, then analyzes WandB results offline in notebooks.** |

**Practical implication:** the team's W3-W4 collaboration mode is *"submit jobs, then meet to discuss results"* — not *"gather to run experiments together."*

### Experimental grid (5 cells, not 9)

Two experimental tracks share infrastructure but answer different research questions:

**Experiment 1 — MCP overhead (3 cells, all on ReAct/AaT orchestration):**

| Cell | Orchestration | MCP mode | Measures |
|---|---|---|---|
| A | ReAct/AaT | Direct (no MCP) | Pure tool execution + LLM inference |
| B | ReAct/AaT | MCP baseline | Adds JSON-RPC serialization + network |
| C | ReAct/AaT | MCP optimized (batched, connection reuse) | Optimization recovery |

Delta (B − A) = raw cost of MCP standardization. Delta (C − A) = residual cost after optimization.

**Experiment 2 — Orchestration comparison (3 cells, all on MCP-baseline):**

| Cell | Orchestration | MCP mode | Measures |
|---|---|---|---|
| **B (shared with Exp 1)** | **AaT** | **MCP baseline** | **Single-agent sequential, default pattern** |
| Y | Plan-Execute | MCP baseline | Planner + executor decomposition |
| Z | Hybrid (PE + reflection checkpoints) | MCP baseline | PE structure with self-correction (conditional on mentor novelty check) |

**Cell B is shared between both experiments** — it's the same set of runs, used to answer both research questions. So total unique cells = **5**, not 9.

```
                  │ Direct (no MCP) │ MCP baseline │ MCP optimized │
──────────────────┼─────────────────┼──────────────┼───────────────┤
 Agent-as-Tool    │       run       │  run (shared)│      run      │
 Plan-Execute     │        —        │     run      │       —       │
 Hybrid           │        —        │   run (cond.)│       —       │
```

We are **not** running the full 3×3 multiplicative grid. The full grid would let us ask "does MCP optimization affect different orchestrations differently?" — interesting but secondary, and not in our scope. If the analysis surfaces a strong reason to investigate, we can add cells in W4.

### Cost reality

- **Per scenario per cell**, on Insomnia A6000 with Llama-3.1-8B-Instruct: ~1-3 minutes (multi-turn agent, ~5-15 LLM calls)
- **Per cell** (30 scenarios × 5 trials): 2.5-7.5 hours of GPU time
- **Full 5-cell grid:** ~12-37 hours of GPU time = ~1-2 days of compute, free on Insomnia

The widely-cited "$4000-5000 per benchmark run" figure for AssetOpsBench refers to running their full 467-scenario suite with frontier models (GPT-4 class). Our subset of ~30 Smart Grid scenarios on Llama-3.1-8B is essentially free because we use free academic compute and a much smaller model on a much smaller scenario set. **Worth a sentence in the paper as a cost-conscious design choice.**

### Implementation notes for the Slurm template

Aaron's Slurm template should:

- Allocate `--gres=gpu:a6000:1 --mem=64G --time=02:00:00` (A6000 has no 2-hour cap unlike H100)
- Activate the team's `.venv-insomnia` (separate from local `.venv`)
- Set CUDA paths directly (the `module load cuda` is broken on Insomnia per the README's verified config notes — use `export PATH=/usr/local/cuda/bin:$PATH` instead)
- Launch vLLM as a background process, wait for it to be ready (~60 seconds)
- Launch the MCP servers (in-process or as subprocesses)
- Run the eval harness with the config file as argument
- Stream all output to a per-job log file in `logs/`
- Wait for the harness to finish before exiting

Once the template works for one cell, every other cell is just a different config file.

---

## Open questions

- **Mentor novelty check on Hybrid orchestration** — pending response. If green-lit, Hybrid is added as Experiment 2 cell Z. If not, Experiment 2 reduces to 2 cells (AaT vs PE) and the total grid is 4 cells.
- **Problem Statement B / Future Work stretch track** (auto-scenario generation pipeline) — go/no-go decision deferred to the April 14 call. Activated only if Tier 1 is on track and someone has the bandwidth to own the pipeline.
- **First baseline trajectory date** — depends on Tier 1 completion. Target: by end of W2 (April 13). This is the integration milestone everything else depends on.
