# scripts/

*Last updated: 2026-04-21*

Executable entrypoints and helper utilities for the repo. If you know roughly
what you want to do but not which command to run, start here.

## Primary entrypoints

| Script | Use it when… | Notes |
|---|---|---|
| [`run_experiment.sh`](run_experiment.sh) | You want to run a benchmark cell or smoke config on the canonical SmartGridBench path | Main entrypoint for Plan-Execute, PE + Self-Ask, and Verified PE runs |
| [`setup_insomnia.sh`](setup_insomnia.sh) | You need to bootstrap or refresh the shared Insomnia environment | Cluster-oriented setup script; read [`../docs/insomnia_runbook.md`](../docs/insomnia_runbook.md) first |
| [`vllm_serve.sh`](vllm_serve.sh) | You want to launch the local vLLM server directly | Pairs with [`test_inference.sh`](test_inference.sh) |
| [`test_inference.sh`](test_inference.sh) | You want a quick sanity check against a live vLLM endpoint | Useful after serving changes or model swaps |
| [`run_harness_smoke.cmd`](run_harness_smoke.cmd) | You want the Windows AssetOpsBench harness smoke path | Referenced from [`../docs/eval_harness_readme.md`](../docs/eval_harness_readme.md) |

## Model / environment validation

| Script | Purpose |
|---|---|
| [`verify_watsonx.py`](verify_watsonx.py) | List or benchmark available WatsonX models |
| [`validate_llama_path.py`](validate_llama_path.py) | Sanity-check the local Llama path / model availability assumptions |
| [`insomnia_env.sh`](insomnia_env.sh) | Shared environment exports consumed by the cluster scripts |

## Orchestration runners

| Script | Purpose |
|---|---|
| [`plan_execute_self_ask_runner.py`](plan_execute_self_ask_runner.py) | Repo-local PE + Self-Ask runner |
| [`verified_pe_runner.py`](verified_pe_runner.py) | Repo-local Verified PE runner |
| [`orchestration_utils.py`](orchestration_utils.py) | Shared planning / execution / summarization helpers used by the runners |

## Evaluation / analysis helpers

| Script | Purpose |
|---|---|
| [`judge_trajectory.py`](judge_trajectory.py) | LLM-as-Judge scoring helper for trajectory artifacts |
| [`tmux_watch_run.sh`](tmux_watch_run.sh) | Convenience watcher for long-running jobs or logs |

## Related indexes

- [`../configs/README.md`](../configs/README.md) - which configs feed `run_experiment.sh`
- [`../docs/runbook.md`](../docs/runbook.md) - canonical reproducibility workflow
- [`../profiling/README.md`](../profiling/README.md) - profiling wrappers under `profiling/scripts/`
- [`../data/scenarios/README.md`](../data/scenarios/README.md) - scenario authoring and validation
