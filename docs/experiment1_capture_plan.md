# Experiment 1 Capture Plan

*Last updated: 2026-04-26*
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
  vLLM plumbing already wired; Agent-as-Tool dispatch now defaults to
  `scripts/aat_runner.py`, with `AAT_RUNNER_TEMPLATE` kept as an override for
  parity or variant runs (see `docs/orchestration_wiring.md`).
- `profiling/scripts/{sample_nvidia_smi,run_nsight,run_vllm_torch_profile,capture_around}.sh`
  — capture wrappers that link to the benchmark's WandB run via
  `log_profiling_to_wandb.py` when `BENCHMARK_RUN_DIR` is set.
- `configs/aat_{direct,mcp_baseline,mcp_optimized}.env` — cell config
  skeletons with the metadata fields filled in. The direct and MCP-baseline
  configs now use first-class Agent-as-Tool dispatch.

## Current smoke status and remaining capture gaps

The Cell A/B runner gate is no longer open. `scripts/aat_runner.py` now
provides the shared OpenAI Agents SDK loop, with the AOB prompt pinned by SHA
and the tool source selected by cell:

| Cell | Dispatcher | Smoke status |
|---|---|---|
| A | `mcp_servers.direct_adapter` direct callables | Slurm job `8962310_aat_direct_smoke_104`, `1 / 1` success, 4 tool calls |
| B | MCP stdio to the four Smart Grid servers | Slurm job `8969519_aat_mcp_baseline_smoke_104`, `1 / 1` success, 4 MCP tool calls |
| B parity | Upstream AOB `OpenAIAgentRunner` Python API with Smart Grid server paths | Slurm job `8970383_aat_mcp_baseline_upstream_smoke_104`, `1 / 1` success, Slurm elapsed `00:11:18` |
| C | optimized MCP transport | waits on the optimized MCP lane |

What remains for `#25` is the report-facing capture set, not the smoke runner:

- run A/B across the agreed `multi_*.json` slice with 3 trials first
- add Cell C when the optimized MCP implementation is behaviorally ready
- decide whether raw scenario JSONs are committed, summarized in-tree with
  validation-log references, or kept on Insomnia with live artifact paths
- keep Notebook 02 parser checks moving on the smoke artifacts while the full
  capture set runs

## Dependencies across the team

| Cell | Remaining blocker | Who | Status |
|---|---|---|---|
| A | full `multi_*.json` / 3-trial capture | Aaron | smoke-proven, capture pending |
| A | WandB/profiling link | Aaron | done in `01043c5` |
| B | full `multi_*.json` / 3-trial capture | Aaron | smoke-proven, capture pending |
| C | optimized MCP transport chosen and wired into the Cell C config | Akshat / Tanisha / Aaron | pending optimized lane |

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

## Recommended run sequence

| Order | Work | Cells |
|---|---|---|
| 1 | Use the smoke-proven configs to capture A and B over the agreed `multi_*.json` slice with 3 trials | A, B |
| 2 | Check artifact size and decide retention: committed summaries plus validation-log/live Insomnia paths by default, full raw only if manageable | A, B |
| 3 | Run Notebook 02 parser/availability checks against the A/B outputs and the existing smoke artifacts | A, B |
| 4 | Add Cell C once the optimized MCP lane is ready enough to provide a stable config and comparable tool surface | C |
| 5 | Rerun A/B/C as the final matched set if Cell C changes shared runner/config assumptions | A, B, C |

This is the **first usable run sequence**, not the only one. Once the larger
scenario corpus exists, rerun the same cells with the same configs and notebook
pipeline to produce the final report-ready results.

## Open decisions

1. **Scenario slice** — current default is `data/scenarios/multi_*.json`
   (6-ish multi-domain scenarios). Is that the scenario slice you want for
   Notebook 02, or should we include the single-domain `iot_`, `fmsr_`,
   `tsfm_`, `wo_` files too?
2. **Trials** — configs default to 3 trials/scenario. For the overhead
   comparison you'll want enough samples to fit a distribution; 3 feels thin
   but keeps the time budget small. Bump to 5 if compute allows.
3. **Scoring** — do Notebook 02 parsers need judge scores, or is this purely
   latency analysis? If latency-only, we can defer LLM-as-Judge scoring out of
   the Experiment 1 critical path.

## Notebook 02 expectations

`#26` does not need to wait for the final paper-scale run set before analysis
starts. The expected cadence is:

1. preflight and parser validation can now start from the AaT smoke artifacts:
   Cell A job `8962310_aat_direct_smoke_104` and Cell B job
   `8969519_aat_mcp_baseline_smoke_104`; upstream parity proof is job
   `8970383_aat_mcp_baseline_upstream_smoke_104`
2. shared-Cell-B contract checks can now use the Cell B smoke artifact:
   - scenario IDs and trial indices match the Experiment 2 join keys
   - latency rows are present in the expected `latencies.jsonl` shape
   - `CONTRIBUTING_EXPERIMENTS` correctly marks Cell B as dual-use
3. early best-effort analysis on the first complete A / B / C run set
4. final publishable figures/tables after the chosen Cell C stack and the
   larger scenario corpus are rerun

## References

- `docs/execution_plan.md` — core grid, staged follow-on policy, async batch workflow
- `docs/orchestration_wiring.md` — why AaT uses first-class harness dispatch
  plus a separate upstream parity wrapper
- `docs/wandb_schema.md` — field names used in config/summary JSON
- `profiling/README.md` — capture wrapper usage + WandB linkage contract
- Issues: `#25` (this), `#26` (Alex's notebook), `#31` (batched scheduling),
  `#72` (WS4 parent), `#85`-`#88` (MCP hardening)
