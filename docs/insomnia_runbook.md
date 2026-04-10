# Insomnia Runbook

*Last updated: 2026-04-10*
*Owner: Aaron Fan (af3623)*

Verified setup notes, gotchas, and debugging recipes for the Columbia Insomnia
HPC cluster. Read [`compute_plan.md`](compute_plan.md) first for the higher-level
hardware strategy (which GPU for which phase, Insomnia vs GCP). This doc covers
the cluster-specific operational details that aren't obvious from the official
RCS documentation.

## Slurm: account, partition, QoS

The instructor's example uses `--partition=gpu` — **this partition does not
exist** on Insomnia. The verified working settings for our class account:

```bash
--account=edu
--partition=short    # or burst
--qos=short          # must match partition
```

`short` and `burst` use the same physical nodes; `burst` is preemptible. Both
have a 12-hour walltime cap on `short`-partition nodes (the older "2 hour"
number you may see floating around is incorrect for `short`/`burst`).

Check your associations:
```bash
sacctmgr show associations user=<UNI> format=Account%20,Partition%20,QOS%30
```

## Storage: clone into scratch, not $HOME

**Home directory is capped at 50 GB.** A vLLM venv (~6 GB) plus the
Llama-3.1-8B weights (~16 GB) plus profiling traces will fill it. Always clone
the team repo into your edu scratch directory:

```bash
mkdir -p /insomnia001/depts/edu/users/<UNI>
cd /insomnia001/depts/edu/users/<UNI>
git clone git@github.com:HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp.git
```

Scratch is **1 TB shared** across the edu account and **not backed up** — but
everything important is in git or re-downloadable from HuggingFace.

## CUDA: don't use `module load cuda`

Insomnia's `cuda/12.3` module is broken — it points at `/usr/local/cuda-12.3/`
which no longer exists. The actual installed version is **CUDA 12.9** at
`/usr/local/cuda/`. Set the paths directly in your job scripts:

```bash
export PATH=/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
```

## cuDNN: not installed system-wide

There is no system cuDNN on Insomnia. The team's `scripts/setup_insomnia.sh`
handles this by pip-installing `nvidia-cudnn-cu12` into the venv, and
`scripts/vllm_serve.sh` adds the cuDNN lib path to `LD_LIBRARY_PATH` at runtime.
You shouldn't need to do anything manual unless you're building your own venv.

## Python version: vLLM versions matter

Insomnia ships only **Python 3.9.18** system-wide (`/usr/bin/python3.9`); there
is no newer Python module available (`module avail python` returns nothing).
Any venv created with `python3 -m venv` inherits 3.9.

**vLLM 0.10+ requires Python 3.10+** (it uses PEP 604 `X | None` union syntax),
so newer vLLM releases will not import on a stock Insomnia venv. This is why
`scripts/setup_insomnia.sh` pins `vllm==0.8.5` — that release still supports
Python 3.9. **Do not bump the vLLM pin without also installing a newer Python.**

### Failure mode (verified Apr 10, 2026)

If you accidentally end up on a vLLM that requires 3.10+ (e.g., by running an
older unpinned version of the setup script, or by running `pip install vllm`
manually), you get a **silent crash inside imports** that is extremely hard to
diagnose:

```
File ".../vllm/model_executor/models/registry.py", line 442, in _LazyRegisteredModel
    module_hash: str) -> _ModelInfo | None:
TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'
```

When launched as a backgrounded process inside a Slurm script with redirected
stdout/stderr, the crash produces **zero output**. Symptoms:

- `nvidia-smi` shows 0 MiB GPU usage
- The vLLM server log file is 0 bytes
- The Slurm job log shows only "Waiting for vLLM server to start..."
- No traceback anywhere
- Job eventually times out in the health-check loop

If you ever see this combination, **don't keep resubmitting Slurm jobs** —
foreground vLLM in an interactive session and you'll see the real error
immediately. See "Debugging: foreground vLLM" below.

### If you need a newer vLLM

Install Python 3.11 via `uv` (no admin needed; `uv` ships its own Python
interpreters), then recreate the venv:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env

cd /insomnia001/depts/edu/users/<UNI>/hpml-assetopsbench-smart-grid-mcp
deactivate 2>/dev/null || true
rm -rf .venv-insomnia          # slow on networked FS, can take 1-2 min
uv venv .venv-insomnia --python 3.11
source .venv-insomnia/bin/activate
uv pip install vllm torch transformers huggingface-hub nvidia-cudnn-cu12
```

Verify before submitting any Slurm jobs:
```bash
python --version                                    # should be 3.11.x
python -c "import vllm; print(vllm.__version__)"    # should print without error
```

## Login node etiquette

The Insomnia RCS team has explicitly warned (Apr 2026) that **heavy work on
login nodes will be terminated**. Even `import vllm` is enough to draw a
warning email — the import pulls in torch and CUDA libs, which is enough load
to upset the shared head node.

Always grab a compute node first:

```bash
srun --account=edu --partition=short --qos=short --gres=gpu:1 \
     --mem=64G --time=01:00:00 --pty bash
```

Editing files, submitting Slurm jobs, and `git` operations are fine on the
login node. Anything that imports torch/vllm/transformers belongs on a
compute node.

## Debugging: foreground vLLM

When a Slurm job hangs without producing logs, **don't keep resubmitting**.
Grab an interactive shell and run vLLM in the foreground so you see all output
live:

```bash
srun --account=edu --partition=short --qos=short --gres=gpu:1 \
     --mem=64G --time=01:00:00 --pty bash

# Once you're on the compute node:
cd /insomnia001/depts/edu/users/<UNI>/hpml-assetopsbench-smart-grid-mcp
source .venv-insomnia/bin/activate
export PATH=/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH

# Quick sanity check (should print version, not crash)
python -c "import vllm; print(vllm.__version__)"

# Foreground vLLM
python -u -m vllm.entrypoints.openai.api_server \
    --model models/Llama-3.1-8B-Instruct \
    --port 8000 --max-model-len 8192 --dtype float16
```

Expect 1-3 minutes to "Uvicorn running on http://0.0.0.0:8000" — Python
imports take ~30 seconds, model load to GPU another minute, CUDA graph capture
another minute. If you see no output at all within 30 seconds, vLLM is crashing
on import and you need to investigate that first.

To test inference, open a second SSH session and `curl` against the compute
node hostname (visible in your interactive shell prompt, e.g. `ins080`):

```bash
ssh <UNI>@insomnia.rcs.columbia.edu
curl http://ins080:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"models/Llama-3.1-8B-Instruct","prompt":"A power transformer fails because","max_tokens":50}'
```

## Queue waits

The `edu` class account has lower priority than dedicated research groups, so
expect queue waits during weekday business hours. Some heuristics:

- **Off-peak (evenings, weekends):** jobs typically start within minutes
- **Peak (weekday afternoons):** can be 30 min to several hours
- **`ReqNodeNotAvail`** in `squeue` reason column means the requested nodes
  are reserved — try a different GPU type (`--gres=gpu:1` instead of
  `--gres=gpu:A6000:1`) to give the scheduler more flexibility
- **`Priority`** just means you're in line; check estimated start with
  `squeue -u <UNI> --start`

Llama-3.1-8B at FP16 fits on every GPU type Insomnia has (A6000 48 GB, L40/L40S
48 GB, H100 80 GB), so `--gres=gpu:1` is the fastest path to a slot when the
A6000 nodes are saturated.

## SSH multiplexing (avoid repeated Duo 2FA)

Add to `~/.ssh/config` on your local machine:

```
Host insomnia
  HostName insomnia.rcs.columbia.edu
  User <UNI>
  ControlMaster auto
  ControlPath ~/.ssh/sockets/%r@%h-%p
  ControlPersist 4h
```

Then `mkdir -p ~/.ssh/sockets`. First `ssh insomnia` needs Duo; subsequent
`ssh`/`scp` reuse the connection for 4 hours. This is purely a convenience
feature — it has nothing to do with login-node policy or job execution.

## See also

- [`compute_plan.md`](compute_plan.md) — phase-by-phase GPU allocation strategy
- [`scripts/setup_insomnia.sh`](../scripts/setup_insomnia.sh) — one-shot env setup with pinned versions
- [`scripts/vllm_serve.sh`](../scripts/vllm_serve.sh) — Slurm job script for serving Llama-3.1-8B-Instruct
