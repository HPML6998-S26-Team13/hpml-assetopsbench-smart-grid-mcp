# Execution Plan: W2-W5

*Last updated: April 18, 2026*

How the team executes the remaining ~4 weeks of work, organized in two parts:

1. **Task dependency map** - which tasks block which, and what the critical path looks like
2. **Benchmarking operations** - what running experiments actually looks like (it's mostly async batch jobs, not synchronous coordination)

> **TL;DR:** The repo is no longer in pure setup mode. Insomnia smoke proof, the first real WandB run, and the first Plan-Execute Smart Grid benchmark-facing artifact flow all landed on Apr 13. That canonical proof is specifically a WatsonX-hosted 70B / Mac 1-scenario smoke run under `benchmarks/cell_Y_plan_execute/`, not yet the primary self-hosted 8B benchmark lane. The Apr 16 post-call audit resolved the WO architecture decision plus the first-WandB-run milestone. The remaining execution risk is now concentrated in overdue W2 closeout (canonical benchmark proof, MCP hardening / benchmark-path validation, profiling wrappers, scenario / judge artifacts) plus W3 profiling and PS B deliverables. Tanisha's PR `#115` now adds a real Insomnia A6000 / Llama-3.1-8B benchmark-path proof for `#58`, but it is still in review rather than on canonical history.

## Status note (Apr 18, 2026)

What is now proven on canonical history:

- shared Insomnia A6000 vLLM smoke path
- first visible WandB run
- first benchmark-facing Plan-Execute Smart Grid artifact flow via a WatsonX-hosted 70B / Mac smoke run with committed artifacts
- resolved WO architecture decision (`#13`)
- closed "first WandB run" milestone (`#28`)

What still governs the near-term critical path:

- `#3` canonical benchmark scenario proof on the AssetOpsBench stack
- `#9-#12` and `#58` for MCP hardening / benchmark-path confidence
- `#7`, `#59`, `#25`, `#27`, `#37`, and `#111` for profiler / GPU capture and runbook usability
- `#15`, `#17`, `#18`, and `#20` for scenario-count, judge, and first-trajectory evidence
- `#50 -> #2 -> #51` for the first believable Problem Statement B artifact chain

Most important nuance after Tanisha's Apr 16 ET validation:

- PR `#115` now contains a real Insomnia A6000 Plan-Execute proof that reaches `iot`, `fmsr`, `tsfm`, and `wo` with self-hosted Llama-3.1-8B-Instruct, plus evidence that the successful validation used a `32768` context-length invocation while the shared script still lagged behind that longer benchmark path.
- That materially lowers uncertainty around `#58`, but it does **not** remove the "proof must land on canonical `main`" rule, and it does **not** yet fix the profiling README mismatch noted in review.

---

## Part 1: Task dependency map

### Critical path

```
Insomnia/vLLM up                 ┐
MCP server hardening             ├──► First end-to-end ladder ──► All experiment runs ──► Analysis ──► Paper
Eval harness end-to-end          │
WandB instrumentation + schema   ┘
```

The original W2 foundation tasks were a single bottleneck. As of Apr 14, that bottleneck has partially broken: serving, WandB, and a first Plan-Execute benchmark path are now proven. The remaining bottlenecks are the still-open W2 closeout issues listed in the status note above.

### Task tiers

#### Tier 1 - Foundation (W2, must complete to unblock everything else)

| Task | Owner | Blocked by | Blocks |
|---|---|---|---|
| Successful first Insomnia A6000 vLLM serve smoke test for Llama-3.1-8B-Instruct | Aaron | (nothing) | All local GPU work, all experiment runs |
| MCP server hardening (4 servers, tests, edge cases) | Tanisha | (nothing) | Eval harness integration, all benchmarks |
| Run one existing benchmark scenario end-to-end on the canonical stack | Akshat | Tanisha's hardened MCP, Aaron's vLLM | All benchmarks, all scoring |
| 15+ Smart Grid scenarios authored | Akshat | (nothing - can write in parallel) | All benchmarks (the test set) |
| Profiling harness scripts (PyTorch Profiler wrappers) | Aaron | vLLM up | Experiment 1 capture |
| WandB instrumentation (metrics schema in MCP servers + eval harness; schema in `docs/wandb_schema.md`) | Alex | Tanisha's MCP, Akshat's harness | All experiment logging |
| Generic Slurm experiment template | Aaron | vLLM, harness, MCP, WandB | Async benchmarking |

#### Tier 2 - Experimental design (W2-W3, depends on Tier 1)

| Task | Owner | Blocked by | Blocks |
|---|---|---|---|
| Orchestration wiring (AaT + PE on team's MCP servers) | Alex | Tier 1 complete | Experiment 2 |
| Hybrid orchestration prototype implementation | Alex | AaT vs PE comparison stable + spare bandwidth | Optional follow-on only |
| Self-Ask integration (~10 LOC, addresses "Fail to Ask for Clarification" failures) | Alex | Proven active orchestration modes | Quality of active conditions + mitigation work |
| 6-dimension LLM-as-Judge scoring in eval harness | Akshat | Eval harness running | Final scoring of all runs |
| First Smart Grid scenario runs end-to-end through MCP with trajectory artifact captured | Akshat | All Tier 1 done | Confidence to start Tier 3 |
| First judge-scored trajectory lands with logs / artifacts using Maverick-17B | Akshat | First Smart Grid trajectory + judge wiring | Confidence to start Tier 3 |

#### Tier 3 - Benchmark execution (W3-W4, fully async, anyone can submit)

| Task | Owner | Blocked by | Blocks |
|---|---|---|---|
| Experiment 1 runs (3 MCP conditions × N scenarios) | Aaron submits, Alex analyzes | Tier 1 + 2 complete | Final report |
| Experiment 2 runs (3 orchestrations × N multi-domain scenarios) | Alex submits | Tier 1 + 2 complete | Final report |
| INT8 quantization experiment | Aaron | vLLM + Slurm template | MCP-optimized condition |
| KV-cache tuning experiment | Aaron | vLLM + Slurm template | MCP-optimized condition |
| Batched tool-call scheduling implementation + experiment | Akshat | Eval harness + MCP | MCP-optimized condition |
| 30+ scenarios completed | Akshat | (none - ongoing authoring through W4) | Final benchmark coverage |

#### Tier 4 - Analysis (W4, depends on Tier 3 results)

| Task | Owner | Blocked by | Blocks |
|---|---|---|---|
| Notebook 02: latency analysis (MCP overhead) | Alex | Experiment 1 results in WandB | Paper section on overhead |
| Notebook 03: orchestration comparison | Alex | Experiment 2 results in WandB | Paper section on orchestration |
| Failure taxonomy classification + evidence table | Alex | Experiment 2 results | Failure analysis section |
| Failure taxonomy visuals + mitigation plan | Alex | Classification table | Mitigation implementation |
| Implement chosen mitigation(s), including Self-Ask if selected | Alex | Mitigation plan | Before/after reruns |
| Re-run affected benchmark cells and compare before/after | Alex | Mitigation implementation | Final analysis section |

#### Tier 5 - Writing (W4-W5, Alex drives, others contribute facts)

| Task | Owner | Blocked by | Blocks |
|---|---|---|---|
| NeurIPS draft (sole author: Alex; format: Datasets & Benchmarks Track) | Alex | Notebook results | Final submission |
| Class final report (back-port of NeurIPS draft to IEEE template) | Alex | NeurIPS draft | May 4 submission |
| Methodology + Data content brief (1-page bullet list of facts) | Tanisha → Alex | (nothing - can hand off any time) | NeurIPS draft |
| Scenarios + Eval content brief | Akshat → Alex | (nothing) | NeurIPS draft |
| Infrastructure + Profiling content brief | Aaron → Alex | (nothing) | NeurIPS draft |

### Critical-path implications

- **The critical path has narrowed.** Benchmark-facing proof now exists, so the team should stop talking as if “nothing can run yet.” The current blockers are the open W2 closeout issues that gate broader profiling, judge, and scenario-scale work.
- **The first end-to-end ladder** is now explicit:
  1. one existing benchmark scenario runs on the canonical stack
  2. one Smart Grid scenario runs end-to-end through MCP with a saved trajectory artifact
  3. one judge-scored trajectory lands with logs / artifacts
  This replaces the earlier vague "first baseline trajectory" milestone and is the integration moment that unlocks all experiment runs.
- **The committed experiment grid is now the four-cell core, not the earlier five-cell conditional grid.** Hybrid is parked as optional follow-on scope rather than treated as a silent required condition.
- **Tier 3 can run in parallel and async** - once the foundation is in place, multiple experiment cells can be submitted as independent Slurm jobs, each running unattended.
- **Tier 5 (writing) can begin during Tier 3** - Alex can draft outline, intro, methodology, related work in parallel with experiments running. Only Results and Discussion need to wait for Tier 4 analysis.
- **Problem Statement B is now committed work**, not a stretch toggle. It runs in parallel across W3-W5: Tanisha owns the Knowledge Plugin, Aaron owns the generation pipeline, Akshat owns validation, and Alex owns evaluation methodology plus the write-up.

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

All WandB config / summary fields for that run should conform to
`docs/wandb_schema.md`, so the benchmark config, run logs, and exported results
stay joinable.
```

### Role clarifications

The async workflow above implies specific roles that may differ from the team's intuition:

| Role | NOT this | IS this |
|---|---|---|
| **Akshat (eval harness owner)** | Manually runs `python run_scenario.py 1`, watches output, runs `python run_scenario.py 2`, etc. | **Authors scenarios + builds the harness that loops through them automatically.** Once authored, scenarios live in `data/scenarios/*.json` and the harness consumes them in batch. |
| **Aaron (infrastructure owner)** | Babysits WandB during runs, watches metrics, intervenes on failures | **Writes Slurm templates + profiling capture wrappers + ensures vLLM is reliably servable.** Once the template is written, anyone can submit jobs. |
| **Tanisha (MCP server owner)** | Responds to MCP requests interactively while teammates run scenarios | **Hardens her MCP servers so they run as long-lived processes inside Slurm jobs without intervention.** Once hardened, the servers are hands-off. |
| **Alex (experiment + analysis owner)** | Manually compares orchestrations by running each one and watching | **Designs experiment configs, submits Slurm jobs, then analyzes WandB results offline in notebooks.** |

**Practical implication:** the team's W3-W4 collaboration mode is *"submit jobs, then meet to discuss results"* - not *"gather to run experiments together."*

### Experimental grid (4 committed cells, not 9)

Two experimental tracks share infrastructure but answer different research questions. The committed class-project grid is the four-cell core below; Hybrid is no longer counted inside the active grid.

**Experiment 1 - MCP overhead (3 cells, all on ReAct/AaT orchestration):**

| Cell | Orchestration | MCP mode | Measures |
|---|---|---|---|
| A | ReAct/AaT | Direct (no MCP) | Pure tool execution + LLM inference |
| B | ReAct/AaT | MCP baseline | Adds JSON-RPC serialization + network |
| C | ReAct/AaT | MCP optimized (batched, connection reuse) | Optimization recovery |

Delta (B − A) = raw cost of MCP standardization. Delta (C − A) = residual cost after optimization.

**Experiment 2 - Orchestration comparison (2 committed cells, all on MCP-baseline):**

| Cell | Orchestration | MCP mode | Measures |
|---|---|---|---|
| **B (shared with Exp 1)** | **AaT** | **MCP baseline** | **Single-agent sequential, default pattern** |
| Y | Plan-Execute | MCP baseline | Planner + executor decomposition |

**Cell B is shared between both experiments** - it's the same set of runs, used to answer both research questions. So total unique committed cells = **4**, not 9.

**Optional follow-on only:** a Hybrid cell Z (PE + reflection checkpoints) remains available as backlog / future-work scope if the core AaT vs PE comparison becomes stable early enough to justify it.

```
                  │ Direct (no MCP) │ MCP baseline │ MCP optimized │
──────────────────┼─────────────────┼──────────────┼───────────────┤
 Agent-as-Tool    │       run       │  run (shared)│      run      │
 Plan-Execute     │        -        │     run      │       -       │
```

We are **not** running the full 3×3 multiplicative grid. The full grid would let us ask "does MCP optimization affect different orchestrations differently?" - interesting but secondary, and not in our committed scope. If the core grid lands early and cleanly, we can still add optional follow-on cells later.

### Working model choice

- **Primary local benchmark model:** Llama-3.1-8B-Instruct on Insomnia via vLLM
- **Judge model:** WatsonX-hosted Maverick-17B
- **Scaling spot-check only:** WatsonX-hosted Llama-3.3-70B-instruct

This is now an explicit planning choice. We are not duplicating the full benchmark grid across both 8B and 70B. The 70B path is reserved for selective comparison runs that help contextualize the local 8B results without doubling the operational burden.

### Cost reality

- **Per scenario per cell**, on Insomnia A6000 with Llama-3.1-8B-Instruct: ~1-3 minutes (multi-turn agent, ~5-15 LLM calls)
- **Per cell** (30 scenarios × 5 trials): 2.5-7.5 hours of GPU time
- **Full 4-cell committed grid:** ~10-30 hours of GPU time = ~1-2 days of compute, free on Insomnia

The widely-cited "$4000-5000 per benchmark run" figure for AssetOpsBench refers to running their full 467-scenario suite with frontier models (GPT-4 class). Our subset of ~30 Smart Grid scenarios on Llama-3.1-8B is essentially free because we use free academic compute and a much smaller model on a much smaller scenario set. **Worth a sentence in the paper as a cost-conscious design choice.**

### Implementation notes for the Slurm template

Aaron's Slurm template should:

- Allocate `--gres=gpu:a6000:1 --mem=64G --time=02:00:00` (A6000 has no 2-hour cap unlike H100)
- Activate the team's `.venv-insomnia` (separate from local `.venv`)
- Set CUDA paths directly (the `module load cuda` is broken on Insomnia per the README's verified config notes - use `export PATH=/usr/local/cuda/bin:$PATH` instead)
- Launch vLLM as a background process, wait for it to be ready (~60 seconds)
- Launch the MCP servers (in-process or as subprocesses)
- Run the eval harness with the config file as argument
- Stream all output to a per-job log file in `logs/`
- Wait for the harness to finish before exiting

Once the template works for one cell, every other cell is just a different config file.

---

## Open questions

- **Exact AaT readiness date** - the four-cell committed grid assumes AaT becomes truly runnable soon enough for fair comparison, but that is still not proven on canonical history today.
- **Scenario realism and ground-truth tightening** - Dhaval has now answered the top-level realism question, but the team still needs to apply his "no analytic hints / preserve ideal sequence / record final value" guidance consistently.
- **First clean profiling capture path** - the real W3 question is no longer "can we serve a model?" but "when do profiler traces, GPU logs, WandB linkage, and teammate-usable instructions all meet in one artifact chain?"
- **Problem Statement B go-wide threshold** - the first believable generated batch still needs to prove it is strong enough to justify scale-up rather than another stabilization pass.
