# Team 13 Call - April 14, 2026 (Tuesday, 2:45 PM ET)

*Weekly team sync. Goal: truthfully assess W2 status, lock the first end-to-end ladder, and assign clean W3 handoffs.*

## Agenda (35 min)

**0:00-0:05 - W2 status reality check**
- What is merged to the org repo `main` branch vs still only local?
- Which W2 foundation tasks are done, in progress, or blocked?
- Are we still targeting first end-to-end artifacts by Apr 13-14, or has that slipped?

**0:05-0:12 - Foundation bring-up review**
- Aaron: Insomnia A6000 vLLM smoke test status
- Tanisha: benchmark-Llama-path validation for MCP servers
- Akshat: canonical harness status plus scenario count already pushed
- Alex: WandB schema / instrumentation and orchestration wiring status

**0:12-0:18 - Lock the first end-to-end ladder**
- Step 1: one existing benchmark scenario runs on the canonical stack
- Step 2: one Smart Grid scenario runs end-to-end through MCP with a trajectory artifact
- Step 3: one judge-scored trajectory lands with logs / artifacts using Maverick-17B
- Confirm exact owners and handoff order for each step

**0:18-0:24 - W3 experiment plan**
- Experiment 1: Direct vs MCP-baseline vs MCP-optimized
- Experiment 2: Agent-as-Tool vs Plan-Execute, plus Hybrid only if approved
- Profiling capture split: Aaron authors capture wrappers, Alex owns experiment design and analysis
- Confirm whether the generic Slurm experiment template is still missing

**0:24-0:29 - Failure analysis and mitigation lane**
- Confirm failure taxonomy work is a real multi-step lane, not a single catch-all task
- Decide what counts as the first useful failure-analysis artifact
- Decide whether Self-Ask is the first mitigation to implement once failure evidence exists

**0:29-0:34 - Problem Statement B and writing**
- PS B is committed W3-W5 work, not a stretch placeholder
- Tanisha: Knowledge Plugin
- Aaron: scenario-generation pipeline
- Akshat: generated-scenario validation
- Alex: evaluation methodology plus NeurIPS / class-report write-up

**0:34-0:35 - Blockers and next actions**
- What is the single biggest blocker for each person this week?
- What needs to land before the Apr 21 call?

---

## Decisions needed

1. If Dhaval has not replied on Hybrid, do we default W3 to AaT vs PE only?
2. What is the exact handoff contract between Tanisha's servers and Akshat's harness?
3. What evidence is enough to mark Aaron's serving work as truly done?
4. Which open items look partially done but still need canonical proof before we close them?
