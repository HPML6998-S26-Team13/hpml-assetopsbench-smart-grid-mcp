# Execution Plan: W2-W5

*Last updated: April 21, 2026*

How the team executes the remaining ~4 weeks of work, organized in two parts:

1. **Task dependency map** - which tasks block which, and what the critical path looks like
2. **Benchmarking operations** - what running experiments actually looks like (it's mostly async batch jobs, not synchronous coordination)

> **TL;DR:** The repo is no longer in pure setup mode. Canonical history now includes the first harness proof / judge / trajectory ladder (`#113`, `#114`), the merged Insomnia benchmark-Llama path (`#115`), the merged repo-local Verified PE / PE + Self-Ask runners with clean smoke proofs (`#119`), and the merged Notebook 02/03 consumer scaffolds (`#120`). The main remaining execution risk is now concentrated in `#111` (final post-merge proof run), `#25` (Cell A runner), and the still-missing real Experiment 1 / Experiment 2 capture sets that feed `#26` and `#32`.

## Status note (Apr 21, 2026)

What is now proven on canonical history:

- shared Insomnia A6000 vLLM smoke path
- self-hosted Llama-3.1-8B benchmark-path validation on Insomnia
- first visible WandB run
- first benchmark-facing Plan-Execute Smart Grid artifact flow via a WatsonX-hosted 70B / Mac smoke run with committed artifacts
- first canonical harness proof / judge / trajectory / judge-log ladder
- repo-local Verified PE and PE + Self-Ask runners with clean `2/2` smoke proofs
- Notebook 02 / Notebook 03 consumer-side scaffolds on canonical history
- resolved WO architecture decision (`#13`)
- closed "first WandB run" milestone (`#28`)

What still governs the near-term critical path:

- `#111` for the final post-merge Insomnia proof / closeout pass
- `#25` for the Cell A runner and the first real A/B/C capture chain
- `#26` and `#32` for actual experiment execution artifacts rather than just notebook scaffolds
- `#50 -> #2 -> #51` for the first believable Problem Statement B artifact chain

Most important nuance after the Apr 20-21 merge wave:

- The benchmark-facing proof story is now on canonical `main`, not just in PRs.
- The bottleneck has shifted from "can this stack run at all?" to "do we have the missing execution artifacts for the actual experiments?"

---

## Part 1: Task dependency map

### Critical path

```
Insomnia/vLLM up                 ┐
MCP server hardening             ├──► First end-to-end ladder ──► All experiment runs ──► Analysis ──► Paper
Eval harness end-to-end          │
WandB instrumentation + schema   ┘
```

The original W2 foundation tasks were a single bottleneck. As of Apr 21, that bottleneck has mostly broken: serving, benchmark-path validation, judge/trajectory artifacts, and the repo-local PE mitigation lane are all proven on canonical history. The remaining bottlenecks are the still-open execution issues listed in the status note above.

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
| Verified PE third-method prototype (`#23`; active optional follow-on, not core blocker) | Alex | Benchmark runner + PE baseline stable | Optional third-method evidence |
| Self-Ask clarification hook for active repo-local modes (`#24`) | Alex | Verified PE / PE runner plumbing | Quality of active conditions + mitigation work |
| 6-dimension LLM-as-Judge scoring in eval harness | Akshat | Eval harness running | Final scoring of all runs |
| First Smart Grid scenario runs end-to-end through MCP with trajectory artifact captured | Akshat | All Tier 1 done | Confidence to start Tier 3 |
| First judge-scored trajectory lands with logs / artifacts using Maverick-17B | Akshat | First Smart Grid trajectory + judge wiring | Confidence to start Tier 3 |

#### Tier 3 - Benchmark execution (W3-W4, fully async, anyone can submit)

| Task | Owner | Blocked by | Blocks |
|---|---|---|---|
| Experiment 1 runs (3 MCP conditions × N scenarios) | Aaron submits, Alex analyzes | Tier 1 + 2 complete | Final report |
| Experiment 2 runs (core AaT vs PE; optional third orchestration only if justified) | Alex submits | Tier 1 + 2 complete | Final report |
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

Important interpretation: **Cell C is one chosen optimized MCP condition**,
not a separate benchmark for every candidate optimization. The optimization
issues make Cell C real:

- `#29` proves a runnable INT8 serving path if the team chooses to use it
- `#30` picks the KV-cache setting the team will actually use
- `#31` implements the benchmark-side batching / scheduling behavior

Those tasks may each use small targeted sweeps or smoke comparisons, but the
main experiment result is still the A / B / C comparison rather than a full
"every scenario on every optimization variant" matrix.

**Experiment 2 - Orchestration comparison (2 committed cells, all on MCP-baseline):**

| Cell | Orchestration | MCP mode | Measures |
|---|---|---|---|
| **B (shared with Exp 1)** | **AaT** | **MCP baseline** | **Single-agent sequential, default pattern** |
| Y | Plan-Execute | MCP baseline | Planner + executor decomposition |

**Cell B is shared between both experiments** - it's the same set of runs, used to answer both research questions. So total unique committed cells = **4**, not 9.

**Active optional follow-on:** the repo now has a local Verified PE / `Plan-Execute-Verify-Replan` implementation path plus a PE + Self-Ask hook. These are real mitigation / third-method work items now, but they still do **not** replace the core AaT vs PE experiment story unless they earn that status through clean artifacts.

```
                  │ Direct (no MCP) │ MCP baseline │ MCP optimized │
──────────────────┼─────────────────┼──────────────┼───────────────┤
 Agent-as-Tool    │       run       │  run (shared)│      run      │
 Plan-Execute     │        -        │     run      │       -       │
```

We are **not** running the full 3×3 multiplicative grid. The full grid would let us ask "does MCP optimization affect different orchestrations differently?" - interesting but secondary, and not in our committed scope. If the core grid lands early and cleanly, we can still add optional follow-on cells later.

### Scenario-count policy

The team should treat experiment execution as a **two-pass process**:

1. **Best-effort / first-pass runs** on the current committed scenario set, so
   the cells, artifacts, and notebooks become real now.
2. **Final canonical runs** on the larger paper-scale scenario set once the
   scenario corpus expands.

So we do not need to wait for 30+ scenarios before starting Experiment 1 or
Experiment 2. The configs, batch runner, and notebooks are meant to be rerun
later on the larger corpus without a structural rewrite.

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
- **Interpreting old blocker lists** - some older issue dependency fields are
  best read as blockers for the **final canonical report-ready run set**, not
  as blockers for first execution. The near-term goal should be early
  best-effort artifact generation, then clean reruns once the later refinement
  tasks land.
- **Scenario realism and ground-truth tightening** - Dhaval has now answered the top-level realism question, but the team still needs to apply his "no analytic hints / preserve ideal sequence / record final value" guidance consistently.
- **First clean profiling capture path** - the real W3 question is no longer "can we serve a model?" but "when do profiler traces, GPU logs, WandB linkage, and teammate-usable instructions all meet in one artifact chain?"
- **Problem Statement B go-wide threshold** - the first believable generated batch still needs to prove it is strong enough to justify scale-up rather than another stabilization pass.
