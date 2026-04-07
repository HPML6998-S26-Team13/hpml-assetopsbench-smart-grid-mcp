Insomnia or GCP Environment

## Task

**vLLM serving Llama-3.1-8B-Instruct on Insomnia and successfully responding to a test prompt**

That's the foundational milestone — until it works, no MCP experiments, no profiling, no benchmarks.

Here's the concrete checklist of what needs to happen:

## Guidelines

What "ready" actually looks like

| Step | What | Command/artifact | Done? |
|---|---|---|---|
| 1 | SSH access to Insomnia working | `ssh insomnia` connects (Duo + Columbia creds) | We should already have this from class HW |
| 2 | Team repo cloned on Insomnia | `git clone ...hpml-assetopsbench-smart-grid-mcp.git` in his home dir | — |
| 3 | Python env on Insomnia (separate from local laptop venv) | `uv venv .venv-insomnia && source .venv-insomnia/bin/activate` | — |
| 4 | vLLM + torch + transformers installed | `uv pip install vllm torch transformers` | — |
| 5 | Llama-3.1-8B-Instruct downloaded | `huggingface-cli download meta-llama/Llama-3.1-8B-Instruct` (~16GB; Llama is gated, needs HF token + Meta access approval) | — |
| 6 | Slurm batch script that launches vLLM | `scripts/vllm_serve.sh` with `#SBATCH --gres=gpu:a6000:1 --mem=64G --time=02:00:00` | — |
| 7 | First successful job submission | `sbatch scripts/vllm_serve.sh`; job runs without crashing | — |
| 8 | Test inference returns a sensible completion | `curl http://localhost:8000/v1/completions -d '{"model":"...","prompt":"Test","max_tokens":50}'` returns a real response | — |
| 9 | GPU memory + tokens/sec recorded | `nvidia-smi` during the run shows ~16GB used; vLLM logs show throughput | — |

## Slurm

**The Slurm script we need to write looks roughly like this:**

```bash
#!/bin/bash
#SBATCH --partition=short
#SBATCH --gres=gpu:a6000:1
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=logs/vllm_%j.out

source .venv-insomnia/bin/activate

# Don't use `module load cuda` — it's broken on Insomnia (see README)
export PATH=/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH

python -m vllm.entrypoints.openai.api_server \
  --model ./models/Llama-3.1-8B-Instruct \
  --port 8000 \
  --max-model-len 8192 &

sleep 60  # wait for vLLM to load model

curl http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "./models/Llama-3.1-8B-Instruct", "prompt": "Smart Grid transformers fail because", "max_tokens": 100}'

wait
```

## Notes

- I have a personal "Verified Insomnia Configuration (March 25, 2026)" doc that might be helpful.
- **`module load cuda/12.3` is broken** (points to nonexistent path) — workaround is to set `PATH` and `LD_LIBRARY_PATH` directly to `/usr/local/cuda/`
- **CUDA 12.9** is the actual installed version
- **No system-wide cuDNN** — install via pip in the venv
- **2-hour session cap on H100 nodes** — use A6000 instead for development
- **Slurm partition + account** specifics that are already documented