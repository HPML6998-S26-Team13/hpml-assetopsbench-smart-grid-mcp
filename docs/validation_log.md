# Validation Log

*Last updated: 2026-04-21*

Canonical log for live serve / benchmark / profiling proofs. Use this file for
concrete run records, not the runbooks.

## Convention

For each proof entry, record:

- date
- scope
- branch / git SHA
- config or command path
- run id / Slurm job id
- primary artifacts
- what the run proves
- caveats / follow-ups

## 2026-04-16 — Insomnia benchmark-path validation (`#58`, PR `#115`)

- **Scope:** self-hosted Llama-3.1-8B benchmark-path validation on Insomnia
- **Branch / state:** PR `#115` branch (not yet canonical `main` at the time of validation)
- **Key runtime shape:** `--served-model-name Llama-3.1-8B-Instruct`, `--max-model-len 32768`, local vLLM OpenAI-compatible path
- **Primary artifacts:** committed validation artifacts referenced from PR `#115`

What this proves:

- the long-context benchmark-facing serve path worked on an Insomnia A6000 node
- the benchmark path needed the served-model-name / OpenAI-client alignment
- the successful proof used the longer `32768` context lane rather than the lighter `8192` smoke-path default

Caveats / follow-ups:

- the validated shape still needed to be folded back into shared scripts/docs on canonical history
- startup-time expectations from that run informed the later timeout cleanup

## 2026-04-20 — PE + Self-Ask integration proof (`#24`)

- **Scope:** repo-local PE + Self-Ask runner on Insomnia
- **Branch / git SHA:** historical pre-accounting-fix branch state (around `0591c75`, pre-rebase)
- **Config:** `configs/example_pe_self_ask.env`
- **Run id / Slurm job id:** `8850716_pe_self_ask_mcp_baseline_smoke`
- **W&B:** `y42u88h3`
- **Primary artifacts:** historical live-run artifacts in the Insomnia worktree + W&B `y42u88h3`

What this proves:

- the repo-local Self-Ask PE runner executed end-to-end on Insomnia
- local `vllm==0.19.0`, Smart Grid MCP servers, LiteLLM/OpenAI-compatible local serving, and WandB upload all worked together in one live run

Caveats / follow-ups:

- this was an **integration proof**, not yet a clean method-quality proof
- one scenario still ended with a terminal failed step (`Unknown server 'none'`) even though the benchmark wrapper counted the run as completed
- that accounting bug is now fixed on the branch; rerun after the fix is required before treating this as final PR evidence

## 2026-04-20 — Verified PE integration proof (`#23`)

- **Scope:** repo-local Verified PE runner on Insomnia
- **Branch / git SHA:** historical pre-accounting-fix branch state (around `0591c75`, pre-rebase)
- **Config:** `configs/example_verified_pe.env`
- **Run id / Slurm job id:** `8851966_verified_pe_mcp_baseline_smoke`
- **W&B:** `0v3a5jqi`
- **Primary artifacts:** historical live-run artifacts in the Insomnia worktree + W&B `0v3a5jqi`

What this proves:

- the repo-local Verified PE workflow also executes end-to-end on Insomnia with live verifier / retry behavior
- the runtime stack is the same working local-serving path as the PE + Self-Ask run

Caveats / follow-ups:

- this run also happened before the benchmark-wrapper success-accounting fix
- the raw scenario outputs show semantic failures even though the wrapper summary reported `pass=2`, so rerun on the fixed branch is required

## 2026-04-21 — PE + Self-Ask clean smoke proof snapshot (`#24`)

- **Scope:** repo-local PE + Self-Ask runner on Insomnia
- **Branch / git SHA:** `codex-fnd/issue-23-24-verified-pe-self-ask` at `3a03ab83b7714c1d0f3aed2bc4899ef63fe5511c`
- **Config:** `configs/example_pe_self_ask.env`
- **Run id / Slurm job id:** `8857842_pe_self_ask_mcp_baseline_smoke`
- **W&B:** [otkt77pj](https://wandb.ai/assetopsbench-smartgrid/assetopsbench-smartgrid/runs/otkt77pj)
- **Primary artifacts:**
  - committed snapshot: `benchmarks/cell_Y_plan_execute/config.json`
  - committed snapshot: `benchmarks/cell_Y_plan_execute/summary.json`
  - live raw artifacts: archived in the Insomnia worktree under run id `8857842_pe_self_ask_mcp_baseline_smoke`

What this proves:

- the repo-local PE + Self-Ask runner reached a full `2 / 2` smoke success on the two multi-domain scenarios on the rebased post-`#115` branch
- the live path was clean end-to-end: local vLLM, LiteLLM/OpenAI-compatible serving, Smart Grid MCP servers, benchmark wrapper, and WandB upload
- the committed `config.json` / `summary.json` snapshot now gives the PR an in-tree proof surface without requiring the full raw log bundle in git

Caveats / follow-ups:

- the full raw logs and per-scenario JSONs are intentionally not committed in this branch; they remain archived on Insomnia and externally reflected in W&B
- earlier `8854783_pe_self_ask_mcp_baseline_smoke` remains useful historical evidence, but `8857842` is the committed snapshot aligned to the current rebased branch state

## 2026-04-21 — Verified PE clean smoke proof snapshot (`#23`)

- **Scope:** repo-local Verified PE runner on Insomnia
- **Branch / git SHA:** `codex-fnd/issue-23-24-verified-pe-self-ask` at `3a03ab83b7714c1d0f3aed2bc4899ef63fe5511c`
- **Config:** `configs/example_verified_pe.env`
- **Run id / Slurm job id:** `8857843_verified_pe_mcp_baseline_smoke`
- **W&B:** [x65ej9e0](https://wandb.ai/assetopsbench-smartgrid/assetopsbench-smartgrid/runs/x65ej9e0)
- **Primary artifacts:**
  - committed snapshot: `benchmarks/cell_Z_hybrid/config.json`
  - committed snapshot: `benchmarks/cell_Z_hybrid/summary.json`
  - live raw artifacts: archived in the Insomnia worktree under run id `8857843_verified_pe_mcp_baseline_smoke`

What this proves:

- the repo-local Verified PE runner reached a full `2 / 2` smoke success on the rebased post-`#115` branch
- verifier-time prompt overflows, summarization overflows, and oversized execution-context recycling are all fixed enough for a clean live proof
- the committed `config.json` / `summary.json` snapshot now gives the PR an in-tree proof surface for the Verified PE lane as well

Caveats / follow-ups:

- this is the current authoritative Verified PE smoke snapshot for the PR
- the full raw logs and per-scenario JSONs are intentionally not committed in this branch; they remain archived on Insomnia and externally reflected in W&B
