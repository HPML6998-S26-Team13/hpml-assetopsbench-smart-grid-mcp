# Experiment 1 Capture Plan

*Last updated: 2026-04-18*
*Owner: Aaron Fan (af3623)*

Plan for producing the raw profiling + benchmark artifacts for Experiment 1
(MCP overhead), issue `#25`. Notebook 02 (`#26`, Alex) consumes those
artifacts to compute the `Direct → MCP-baseline → MCP-optimized` delta.

## Experimental cells

| Cell | Orchestration | MCP mode | Tool invocation | Config |
|---|---|---|---|---|
| **A** | Agent-as-Tool (ReAct) | direct | In-process Python call via `mcp_servers/direct_adapter.py` | `configs/aat_direct.env` |
| **B** | Agent-as-Tool (ReAct) | baseline | MCP JSON-RPC over stdio, default server config | `configs/aat_mcp_baseline.env` |
| **C** | Agent-as-Tool (ReAct) | optimized | MCP JSON-RPC with batched tool calls + connection reuse | `configs/aat_mcp_optimized.env` |

Fairness contract: **all three cells use the same underlying 21 tool
functions, the same scenarios, the same prompt template, the same model and
decoding parameters.** The only variable is the transport between the ReAct
agent and the tool. This is what makes `(B - A)` a meaningful measurement of
MCP overhead rather than a mix of algorithmic differences.

Interpretation note: **Cell C is the chosen optimized MCP bundle**, not a
separate standalone benchmark for each candidate optimization. The optimization
issues feed Cell C as follows:

- `#29` — stand up an INT8 serving option if the team chooses to include it
- `#30` — choose the KV-cache setting the team will actually use
- `#31` — implement the batched / scheduled MCP behavior that makes the
  optimized transport materially different from baseline

Those tasks may use small targeted sweeps or smoke checks. The Experiment 1
headline result remains A / B / C.

Shared cell B: it also doubles as the AaT baseline for Experiment 2
(orchestration comparison) — `CONTRIBUTING_EXPERIMENTS` on its config
reflects that.

## What's in place

- `mcp_servers/direct_adapter.py` — registry of the 21 `@mcp.tool()`
  functions as plain Python callables, plus a helper that emits a compact
  JSON-schema-ish description list for LLM prompting. Used by Cell A.
- `scripts/run_experiment.sh` — generic runner with the benchmark / WandB /
  vLLM plumbing already wired; it has an `AAT_RUNNER_TEMPLATE` hook for
  Agent-as-Tool paths (see `docs/orchestration_wiring.md`).
- `profiling/scripts/{sample_nvidia_smi,run_nsight,run_vllm_torch_profile,capture_around}.sh`
  — capture wrappers that link to the benchmark's WandB run via
  `log_profiling_to_wandb.py` when `BENCHMARK_RUN_DIR` is set.
- `configs/aat_{direct,mcp_baseline,mcp_optimized}.env` — cell config
  skeletons with the metadata fields filled in; `AAT_RUNNER_TEMPLATE` is
  intentionally blank pending the runner work below.

## What's missing — the Cell A runner

The gating piece is a ReAct loop that uses the direct adapter. Cells B and C
then reuse the **same ReAct loop** with different tool dispatchers. Shape:

```python
# Pseudocode — not yet implemented
for step in range(max_steps):
    resp = llm.chat(messages)
    action = parse_react_action(resp)  # "Thought / Action / Action Input"
    if action.name == "final_answer":
        break
    result = tool_dispatcher.call(action.name, **action.args)
    messages.append(react_observation(result))
```

The `tool_dispatcher` is the only thing that changes across cells:

| Cell | Dispatcher |
|---|---|
| A | `mcp_servers.direct_adapter.get_tool(name)(**args)` |
| B | MCP JSON-RPC client → stdio to `mcp_servers/<domain>_server/server.py` |
| C | Same MCP client + batching wrapper + persistent stdio connections |

### Cell A runner requirements

To make the runner comparable to AOB's canonical ReAct (so the "Direct vs
MCP" story reads as an apples-to-apples), it needs:

1. **ReAct prompt template** close to AOB's. Upstream AOB uses a Thought /
   Action / Action Input / Observation format; the Cell A runner should
   match exactly so the model-side prompt isn't a confound.
2. **Tool schema** fed via `direct_adapter.list_tool_specs_for_llm()` —
   same 21 tools, same descriptions, same parameter shapes as the MCP path.
3. **Stopping criteria** — max steps, token budget, loop detection.
4. **Per-step latency logging** to `latencies.jsonl` in the run dir (matches
   the shape Alex's PE smoke run already writes, so Notebook 02 parses both
   identically).
5. **Error handling** for tool exceptions — surface as `Observation:
   <error>` so the agent can recover, but flag in the trajectory so
   Notebook 02 can filter failed runs.

**Design decision still needed (escalate to Alex):** do we reimplement the
ReAct loop in this repo, or fork AOB's ReAct runner and run it against the
direct adapter + our scenarios? Options:

- **Reimplement (~200-400 LOC).** Clean control, uses our adapter natively,
  no AOB fork needed. Risk: our prompt drifts from AOB's and the comparison
  becomes about prompt quality rather than transport.
- **Fork AOB ReAct.** Prompt fidelity is guaranteed. Risk: couples us to
  an unreleased AOB internal API, and AOB doesn't expose a stable top-level
  AaT CLI per `docs/orchestration_wiring.md`.

Recommendation: reimplement, but copy AOB's prompt template verbatim and
cite it in the runner's docstring so the choice is auditable.

## Dependencies across the team

| Cell | Blocker | Who | Target | Status |
|---|---|---|---|---|
| A | Cell A ReAct runner + AOB prompt review | Aaron (impl), Alex (review) | Apr 21 | Not started |
| A | WandB/profiling link | Aaron | ✅ done | `01043c5` |
| B | MCP server hardening (IoT/TSFM/FMSR/WO) | Tanisha | Apr 20-21 | `#85` in progress, `#86`/`#87`/`#88` Todo |
| B | Cell A runner (reused) | Aaron | Apr 21 | Not started |
| C | Batched tool-call scheduling | Akshat | Apr 22 | `#31` Todo |
| C | Cell B working (prerequisite for the optimization delta) | Tanisha + Aaron | Apr 21 | — |

These blockers are mostly for the **final canonical A / B / C capture set**.
The team can still start best-effort runs on the current scenario slice as soon
as a cell becomes runnable, rather than waiting for every downstream refinement
task to finish.

## Capture pipeline per cell

Once a cell's runner config can execute, each run does:

```bash
RUN_ID="${CELL_NAME}_$(date +%Y%m%d_%H%M%S)"
BENCH=benchmarks/cell_${CELL}/raw/$RUN_ID
OUT=profiling/traces/$RUN_ID

# Phase 1 — benchmark run (vLLM + ReAct loop + scenarios). Writes BENCH/.
sbatch --wait --mail-type=BEGIN,END,FAIL --mail-user=$MAIL_USER \
    scripts/run_experiment.sh configs/${CELL_CONFIG}.env

# Phase 2 — profiling capture around a replay of the same prompts.
# BENCHMARK_RUN_DIR triggers the WandB linkage.
BENCHMARK_RUN_DIR=$BENCH \
    bash profiling/scripts/capture_around.sh "$OUT" \
        -- bash scripts/replay_scenarios.sh "$BENCH"
```

Open: whether profiling should wrap the live benchmark run or a deterministic
replay. Wrapping the live run gives a single-shot capture but couples to
scheduler noise; replay lets us isolate the model-forward cost from the
scenario loop. Default plan: replay, because `capture_around.sh` already
produces matched `capture_meta.json` that can be joined to the benchmark run
via `run_id`. (`scripts/replay_scenarios.sh` TBD; trivial wrapper that iterates
`BENCH/*.json` and reissues each prompt against the same vLLM endpoint.)

## Proposed run sequence

| Date | Work | Cells |
|---|---|---|
| Apr 18-20 | Cell A runner impl; validate against 2 scenarios locally via `DRY_RUN=1` then a short Slurm slot | A (dry) |
| Apr 20 evening | Tanisha lands IoT hardening → Cell B unblocked | — |
| Apr 21 | Cell A + B full captures against the multi-domain smoke set; first artifacts land in `benchmarks/cell_{A,B}*/raw/` | A, B |
| Apr 21-22 | Akshat lands batched scheduling → Cell C unblocked | — |
| Apr 22 | Cell C capture + all three cells committed with matched `latencies.jsonl` + profiling traces + WandB run URLs | A, B, C |
| Apr 23 | Hand off to Alex for Notebook 02 parsing; `#25` closes | — |

This is the **first usable run sequence**, not the only one. Once the larger
scenario corpus exists, rerun the same cells with the same configs and notebook
pipeline to produce the final report-ready results.

## Open questions for Alex

1. **Cell A runner ownership** — I'll implement if you're OK with a from-scratch
   ReAct loop that copies AOB's prompt template, OR you'd rather we fork AOB's
   runner (more invasive, higher prompt fidelity).
2. **Scenario slice** — current default is `data/scenarios/multi_*.json`
   (6-ish multi-domain scenarios). Is that the scenario slice you want for
   Notebook 02, or should we include the single-domain `iot_`, `fmsr_`,
   `tsfm_`, `wo_` files too?
3. **Trials** — configs default to 3 trials/scenario. For the overhead
   comparison you'll want enough samples to fit a distribution; 3 feels thin
   but keeps the time budget small. Bump to 5 if compute allows.
4. **Scoring** — do Notebook 02 parsers need judge scores, or is this purely
   latency analysis? If latency-only, we can defer LLM-as-Judge scoring out of
   the Experiment 1 critical path.

## Notebook 02 expectations

`#26` does not need to wait for the final paper-scale run set before analysis
starts. The expected cadence is:

1. preflight and parser validation as soon as any A / B / C artifacts exist
2. shared-Cell-B contract checks as soon as `#104` / the first AaT artifact
   makes Cell B real:
   - scenario IDs and trial indices match the Experiment 2 join keys
   - latency rows are present in the expected `latencies.jsonl` shape
   - `CONTRIBUTING_EXPERIMENTS` correctly marks Cell B as dual-use
3. early best-effort analysis on the first complete A / B / C run set
4. final publishable figures/tables after the chosen Cell C stack and the
   larger scenario corpus are rerun

## References

- `docs/execution_plan.md` — core grid, staged follow-on policy, async batch workflow
- `docs/orchestration_wiring.md` — why AaT needs an explicit runner template
- `docs/wandb_schema.md` — field names used in config/summary JSON
- `profiling/README.md` — capture wrapper usage + WandB linkage contract
- Issues: `#25` (this), `#26` (Alex's notebook), `#31` (batched scheduling),
  `#72` (WS4 parent), `#85`-`#88` (MCP hardening)
