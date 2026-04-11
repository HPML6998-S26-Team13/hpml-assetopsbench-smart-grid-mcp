# configs/

Experiment configs consumed by [`scripts/run_experiment.sh`](../scripts/run_experiment.sh). Each file describes one cell of the experimental grid (an orchestration × MCP-mode combination across a scenario set), and is sourced as bash so the schema is just env vars.

## Naming

Use the cell name from [`docs/execution_plan.md`](../docs/execution_plan.md) — the 5-cell unique grid:

| Cell | Orchestration | MCP mode | Suggested config name |
|---|---|---|---|
| A | Agent-as-Tool (ReAct) | direct | `aat_direct.env` |
| B | Agent-as-Tool (ReAct) | baseline | `aat_mcp_baseline.env` *(shared across both experiments)* |
| C | Agent-as-Tool (ReAct) | optimized | `aat_mcp_optimized.env` |
| Y | Plan-Execute | baseline | `pe_mcp_baseline.env` |
| Z | Hybrid (PE + reflection) | baseline | `hybrid_mcp_baseline.env` *(conditional)* |

## Schema

See [`example_baseline.env`](example_baseline.env) for the full schema with comments. Required keys:

- `EXPERIMENT_NAME` — short label, becomes part of the run ID
- `SCENARIOS_GLOB` — glob of scenario JSON files relative to repo root
- `MODEL_ID` — `<provider>/<model>` (`watsonx/...` or `openai/...`)

Optional keys (with defaults) cover orchestration, MCP mode, trial count, vLLM launch knobs, and the path to the AssetOpsBench harness checkout.

## Running

```bash
sbatch scripts/run_experiment.sh configs/aat_mcp_baseline.env
```

Outputs land in `logs/exp_<jobid>_<EXPERIMENT_NAME>/`:
- `meta.json` — full run metadata + summary stats
- `vllm.log` — vLLM server output
- `harness.log` — aggregated harness stderr
- `<scenario>_t<N>.json` — one file per scenario × trial

## Status

Skeleton config + skeleton runner — see the TODOs in [`scripts/run_experiment.sh`](../scripts/run_experiment.sh) for the wiring that depends on Akshat (harness model-id routing, orchestration flags), Tanisha (MCP server launch contract), and Alex (WandB schema).
