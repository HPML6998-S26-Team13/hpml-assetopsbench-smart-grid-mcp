# Compute Environment Discrepancies

*Last updated: 2026-05-03*
*Owner: Alex Xin*

This note records the hardware/runtime discrepancy discovered while comparing
the first Insomnia Experiment 2 captures against the GCP A100 final-six runs.
It is an evidence-quality note, not a replacement for the current final matrix
in `docs/experiment_matrix.md`.

## Insomnia first-capture hardware

The first Experiment 2 PE-family capture was not a single-hardware cohort. The
Slurm wrapper at the time requested a generic GPU (`--gres=gpu:1`), so the
scheduler was free to allocate any eligible GPU type on the `short` partition.

| Cell | Run ID | Node | GPU | vLLM attention | KV cache |
|---|---|---|---|---|---|
| Y | `8998340_exp2_cell_Y_pe_mcp_baseline` | `ins083` | NVIDIA RTX A6000 | FlashAttention 2 | 221,824 tokens |
| YS | `8998341_exp2_cell_Y_pe_self_ask_mcp_baseline` | `ins084` | NVIDIA RTX A6000 | FlashAttention 2 | 221,824 tokens |
| Z | `8998342_exp2_cell_Z_verified_pe_mcp_baseline` | `ins084` | NVIDIA RTX A6000 | FlashAttention 2 | 221,824 tokens |
| ZS | `8998343_exp2_cell_Z_verified_pe_self_ask_mcp_baseline` | `ins050` | NVIDIA H100 NVL | FlashAttention 3 | 545,456 tokens |

This explains the otherwise surprising observation that the historical ZS 2x3
run reported FlashAttention 3 while the nearby Insomnia rows reported
FlashAttention 2. It was not a package downgrade or repo change; it was a
different Slurm allocation.

## GCP final-six hardware

The final-six GCP matrix was a consistent A100 cohort. The summary pullback in
`benchmarks/gcp_a100_final_20260503/summary/README.md` records an
`a2-highgpu-1g` Spot VM with one NVIDIA A100-SXM4-40GB GPU. Those vLLM logs use
FlashAttention 2 and report a smaller KV-cache pool, for example the ZS row:

- run: `final5x6_a100_20260503T090200Z_ZS_final5x6_exp2_cell_Z_verified_pe_self_ask_mcp_baseline`
- GPU: NVIDIA A100-SXM4-40GB
- vLLM attention: FlashAttention 2
- available KV cache memory: 19.92 GiB
- GPU KV cache size: 163,168 tokens

The final matrix should therefore be interpreted as GCP A100 evidence. The
historical Insomnia first-capture table is useful for debugging and narrative
context, but it should not be used as a same-hardware comparison against the
GCP A100 matrix without explicit labels.

## How to reproduce the 2x3 hardware comparison

To compare the old Z and ZS behavior on Insomnia, run the same 2-scenario x
3-trial slice on each requested GPU class:

- Z and ZS on H100: submit with `--gres=gpu:h100:1`.
- Z and ZS on A6000: submit with `--gres=gpu:A6000:1`.
- Use a temporary config copy that pins `SCENARIOS_GLOB` to the original two
  multi-domain scenarios, e.g. `data/scenarios/multi_0[12]_*.json`, because
  the current `multi_*.json` glob now matches more than two files.
- Keep `TRIALS=3`, `MAX_MODEL_LEN=32768`, `TEMPERATURE=0.0`, and the same
  `openai/Llama-3.1-8B-Instruct` model path.

For future evidence runs where hardware must be controlled, rely on typed GPU
requests. As of 2026-05-03 the committed Insomnia batch defaults request
A6000 explicitly; H100 or generic-GPU runs should be requested deliberately
from the `sbatch` command line and labeled as hardware-comparison or
hardware-flexible evidence.

## Current Insomnia writable-path check

On 2026-05-03, a login-node filesystem check found:

- `/insomnia001` exists but is root-owned and not writable.
- `/insomnia001/depts/edu/users/team13` was not present from the login node.
- `/tmp`, `/dev/shm`, and `/run/user/43118` are writable tmpfs locations; use
  only for ephemeral probes, not durable benchmark artifacts.
- `/manitou-home/rcs` is writable and `mkdir` succeeded for a temporary probe,
  but the mounted filesystem was 99% full (`8.0T` available of `581T`) and the
  directory is world-writable rather than a clean team scratch area.

Recommendation: ask RCS to restore or create an intended durable team scratch
directory before launching new artifact-heavy Insomnia runs. If we must run
before that is resolved, use a small explicitly named subdirectory under
`/manitou-home/rcs` only after confirming it is acceptable for course-team
work and keep large artifacts pruned or moved promptly.
