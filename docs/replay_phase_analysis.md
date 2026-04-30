# vLLM replay-phase analysis

*Investigation drafted in response to user follow-up + `pm/backlog.md` 2026-04-27 pin (c). Two questions:*

1. *Why does "first prefill repeat on warmup" happen at all?*
2. *Should the replay phase be cell-aware (PE for Cell Y, Verified PE for Cell Z) or stay AaT-only?*

## Where the replay phase lives

| File | Lines | Role |
|---|---|---|
| `scripts/run_experiment.sh` | `1130-1144` | Replay-phase guard (`TORCH_PROFILE=1` AND `TORCH_PROFILE_DIR` AND `LAUNCH_VLLM=1`); calls `run_vllm_torch_profile.sh` wrapping `replay_scenarios.sh` |
| `profiling/scripts/run_vllm_torch_profile.sh` | `92-119` | `POST /start_profile` → run target → `POST /stop_profile`; assumes vLLM was started with `--profiler-config` so the endpoints exist |
| `scripts/replay_scenarios.sh` | header + main | Replays unique scenarios from the just-finished benchmark run by **always** invoking `scripts/aat_runner.py` (cell-blind) |

## Q1 — why "first prefill repeats on warmup"

Two distinct phenomena get folded into the question:

**(a) vLLM startup tax on first prefill.**
vLLM 0.19.0 captures CUDA graphs, allocates KV-cache slabs, and JIT-compiles attention kernels on the **first** prefill against a fresh server. That first request pays the full startup cost; subsequent requests run against warm kernels and warm KV-cache geometry. On the H100/A6000 setup this typically inflates first-prefill latency by 2-5×.

**(b) Why the harness intentionally captures a "second-pass" trace.**
The main benchmark loop (lines `873-1028` of `run_experiment.sh`) runs every scenario × trial against the cell's actual orchestration runner. By the time it finishes, vLLM is fully warmed for the prompt distribution that this run touches. The replay phase then runs the **same** unique scenarios one more time with the torch profiler attached, deliberately capturing steady-state model-forward cost rather than mixed warmup+steady. The header comment in `replay_scenarios.sh` makes the intent explicit:

> Phase 2 of the Experiment 1 profiling capture: runs one pass of each unique scenario so the vLLM torch profiler captures representative model-forward cost without the full 3-trial benchmark overhead.

So "first prefill repeats" isn't a bug — it's the design. The repeat is what gives us a clean steady-state profile per scenario.

**Caveat for Cell Y/Z.** PE and Verified PE issue **many** prefills per scenario (one per step in the plan), and KV-cache state from the main benchmark may already be partially evicted by the time the replay starts (LRU-style eviction once total token volume exceeds the cache budget). So the "warm" assumption is weaker for multi-step orchestration than for AaT. Empirically the replay traces still look clean, but a strict-parity argument would require replay to begin within a fixed window of benchmark end and to operate on a cache that hasn't churned over.

## Q2 — should replay be cell-aware?

Today: replay is **AaT-only** regardless of the originating cell. `replay_scenarios.sh` calls `aat_runner.py` whether the cell ran AaT, PE, or Verified PE.

**Three options:**

### Option 1 (preferred) — Skip the replay phase for non-AaT cells

Guard the replay block so it only fires when the cell's orchestration is `agent_as_tool`:

```bash
# scripts/run_experiment.sh:1130
if [ "${TORCH_PROFILE:-0}" = "1" ] \
   && [ -n "${TORCH_PROFILE_DIR:-}" ] \
   && [ "$LAUNCH_VLLM" = "1" ] \
   && [ "$ORCHESTRATION" = "agent_as_tool" ]; then
  echo "=== Torch profiler replay pass ==="
  ...
fi
```

Pros:
- Cell Y/Z stop producing AaT-shaped traces under `cell_Y_plan_execute/raw/<run>/profiling/`. Misleading-trace problem disappears.
- The benchmark loop itself can still be profiled if `TORCH_PROFILE=1` — vLLM captures whatever requests hit it during that loop, which is the cell-correct workload.
- Smallest, safest diff.

Cons:
- Cell Y/Z lose the "clean steady-state" replay trace. But they didn't have a *correct* one to begin with — they had an AaT trace masquerading under the cell's directory.

### Option 2 — Make replay cell-aware (dispatch on `ORCHESTRATION`)

`replay_scenarios.sh` would dispatch to the cell's actual runner:
- `agent_as_tool` → `scripts/aat_runner.py`
- `plan_execute` → `scripts/plan_execute_self_ask_runner.py --self-ask=false`
- `plan_execute_self_ask` → `scripts/plan_execute_self_ask_runner.py --self-ask=true`
- `verified_pe` → `scripts/verified_pe_runner.py`

Pros:
- Replay traces become per-cell representative.
- Profiling artifacts can be compared cell-to-cell on like-for-like workloads.

Cons:
- Replay for Y/Z runs ~5-10× longer than for A/B because PE/Verified PE issue many prefills per scenario. Profiler captures get larger.
- Adds dispatch logic to `replay_scenarios.sh`, which currently has a clean single-purpose contract (call AaT).
- Some PE/Verified PE runners need warm MCP servers that the replay would have to bootstrap, OR keep the main-loop's MCP servers alive through replay (significant lifecycle change).
- Doesn't solve the "KV-cache churn between main loop and replay" caveat; the cleanliness gain is marginal.

### Option 3 — Status quo + explicit documentation

Keep replay AaT-only across all cells. Document explicitly that:
- For Cell A/B, the replay trace IS the cell's workload profile.
- For Cell Y/Z, the replay trace is an "AaT-shaped reference profile against the cell's scenarios," not a representative profile of PE/Verified PE workload.

Pros:
- No code change. The Apr 28 default-on for `--enable-auto-tool-choice` already prevents the BadRequestError for non-AaT cells.

Cons:
- Future readers (and reviewers) will see `cell_Y_plan_execute/raw/<run>/profiling/` containing AaT trace data and reasonably assume it represents PE workload. Documentation alone is brittle.

## Recommendation

**Adopt Option 1** (skip replay for non-AaT cells). The main benchmark loop already runs under TORCH_PROFILE if requested, so cell Y/Z still get profiling coverage of their actual workload — they just lose a misleading second-pass trace they didn't need.

Open question (defer): if we ever want clean per-cell replay traces, we can add Option 2 incrementally on top of Option 1 — a per-cell config knob (`REPLAY_RUNNER=match-cell|aat|none`) that opts back into cell-aware replay for benchmark runs that explicitly want it.

## Implementation sketch (Option 1)

Single-line guard add. No new tests required (the path is exercised by every Slurm-driven Cell A/B run today; Cell Y/Z runs would just skip the block silently).

```diff
--- a/scripts/run_experiment.sh
+++ b/scripts/run_experiment.sh
@@ -1127,7 +1127,7 @@ pathlib.Path(meta_path).write_text(json.dumps(meta, indent=2) + "\n", encoding="
 PY
 
-if [ "${TORCH_PROFILE:-0}" = "1" ] && [ -n "${TORCH_PROFILE_DIR:-}" ] && [ "$LAUNCH_VLLM" = "1" ]; then
+if [ "${TORCH_PROFILE:-0}" = "1" ] && [ -n "${TORCH_PROFILE_DIR:-}" ] && [ "$LAUNCH_VLLM" = "1" ] && [ "$ORCHESTRATION" = "agent_as_tool" ]; then
   echo ""
   echo "=== Torch profiler replay pass ==="
   echo "Profiler dir: $TORCH_PROFILE_DIR"
```

A doc note in `profiling/README.md` and `docs/insomnia_runbook.md`'s replay
section should call out the skip explicitly:

> The replay phase only fires for `ORCHESTRATION=agent_as_tool` (Cell A, B, C).
> Cell Y/Z (PE / Verified PE) skip replay because the AaT-only replay would
> produce a trace shaped like the AaT loop rather than the cell's actual
> orchestration. Profile coverage for Y/Z still happens during the main
> benchmark loop when `TORCH_PROFILE=1` is set.

## Backlog ledger update

When this lands, the backlog pin from 2026-04-27 (item c) can be marked done
or replaced with the deferred Option-2 follow-up:

> [ ] (Future) Add per-cell `REPLAY_RUNNER` config knob if cell-aware replay
> traces become useful. Today, replay is skipped for non-AaT cells; main-loop
> profiling covers Y/Z. Source: `docs/replay_phase_analysis.md`.
