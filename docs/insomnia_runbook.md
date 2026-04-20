# Insomnia Runbook

*Last updated: 2026-04-21*
*Owner: Aaron Fan (af3623)*

Verified setup notes, gotchas, and debugging recipes for the Columbia Insomnia
HPC cluster. Read [`compute_plan.md`](compute_plan.md) first for the higher-level
hardware strategy (which GPU for which phase, Insomnia vs GCP), and
[`runbook.md`](runbook.md) for the end-to-end reproducibility story. This doc
covers the cluster-specific operational details that aren't obvious from the
official RCS documentation. For the current model names, repo-facing model
IDs, and runtime pins that this runbook assumes, see
[`governance/model_registry.yaml`](governance/model_registry.yaml).

## Two runbooks, one project

`docs/runbook.md` is the top-level reproducibility doc (preconditions,
setup, day-to-day cell submission, troubleshooting decision tree). This
file (`insomnia_runbook.md`) is the cluster-specific gotcha reference that
`runbook.md` links into. Start with `runbook.md` when onboarding;
come back here when you hit a weird Slurm/CUDA/vLLM behavior.

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

## Storage: use the shared team directory

**Home directory is capped at 50 GB**, which isn't enough for a vLLM venv
(~6 GB) plus the Llama-3.1-8B weights (~16 GB) plus profiling traces.

Instead, the team operates out of a single shared checkout in edu scratch:

```
/insomnia001/depts/edu/users/team13/hpml-assetopsbench-smart-grid-mcp
```

All Slurm jobs, profiling runs, and vLLM serves should cd into this directory
rather than per-user clones. The `.venv-insomnia/` under it is the canonical
team venv — do not delete or recreate it without coordinating with the team
owner (wax1), or you'll break everyone else's running jobs.

Day-to-day usage:

```bash
cd /insomnia001/depts/edu/users/team13/hpml-assetopsbench-smart-grid-mcp
source .venv-insomnia/bin/activate
git pull                                   # stay current
sbatch scripts/run_experiment.sh configs/<cell>.env
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
handles this by installing the pinned `torch` stack from
`requirements-insomnia.txt`, which in turn pulls a compatible
`nvidia-cudnn-cu12` wheel transitively. `scripts/vllm_serve.sh` adds the cuDNN
lib path to `LD_LIBRARY_PATH` at runtime. You shouldn't need to do anything
manual unless you're building your own venv.

## Python version: use the shared 3.11 env

Insomnia ships only **Python 3.9.18** system-wide (`/usr/bin/python3.9`); there
is no newer Python module available (`module avail python` returns nothing).
Any venv created with `python3 -m venv` inherits 3.9, which is **not** the path
we use anymore. The team-standard env is the shared `.venv-insomnia/` created
via `uv` with **Python 3.11**.

As of Apr 21, 2026, the reconciled shared-stack target is:

- `torch==2.10.0`
- `transformers==4.57.6`
- `huggingface-hub==0.36.2`
- `vllm==0.19.0`

Those pins match the actual shared-env direction we are standardizing around,
not the older `vllm==0.8.5` / Python 3.9 story. **Do not bump the vLLM or
torch pins casually without re-verifying the whole Insomnia stack.**

### Recreate the shared env when needed

Install Python 3.11 via `uv` (no admin needed; `uv` ships its own Python
interpreters), then recreate the venv:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env

cd /insomnia001/depts/edu/users/team13/hpml-assetopsbench-smart-grid-mcp
deactivate 2>/dev/null || true
rm -rf .venv-insomnia          # slow on networked FS, can take 1-2 min
uv venv .venv-insomnia --python 3.11
source .venv-insomnia/bin/activate
uv pip install -r requirements-insomnia.txt
```

**Note:** `.venv-insomnia/` under the team directory is shared across
teammates. Only recreate it after pinging the team — an in-flight `rm -rf`
will take down any running jobs that depend on it.

`requirements-insomnia.txt` is the canonical pinned serving overlay: it layers
the cluster-only `vllm` / cuDNN stack on top of the portable base
`requirements.txt`.

That base now also carries the portable AssetOpsBench PE-client slice used by
our repo-local Self-Ask PE / Verified PE runners:

- `litellm==1.81.13`
- `mcp[cli]>=1.26.0`

So if an Insomnia proof run dies with `ModuleNotFoundError: litellm` or
`ModuleNotFoundError: mcp`, the fix is usually not a bespoke `pip install` in
the moment — it is to refresh the shared env against
`requirements-insomnia.txt`. The matching model/runtime contract is now also
captured in [`governance/model_registry.yaml`](governance/model_registry.yaml).

For quick login-node verification, stick to metadata-only checks:
```bash
python --version                                    # should be 3.11.x
python - <<'PY'
from importlib.metadata import version
for pkg in ("torch", "vllm", "transformers", "huggingface-hub", "litellm", "mcp"):
    print(f"{pkg}: {version(pkg)}")
PY
```

If you want to verify a real `import vllm` or `import torch`, do that only from a
compute node:
```bash
srun --account=edu --partition=short --qos=short --gres=gpu:1 \
     --mem=64G --time=01:00:00 --pty bash
cd /insomnia001/depts/edu/users/team13/hpml-assetopsbench-smart-grid-mcp
source .venv-insomnia/bin/activate
python -c "import vllm; print(vllm.__version__)"
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
cd /insomnia001/depts/edu/users/team13/hpml-assetopsbench-smart-grid-mcp
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

Concrete proof runs and benchmark-path validation notes live in
[`validation_log.md`](validation_log.md). Keep this runbook for operational
instructions; keep proof records there.

## Watching live runs with tmux

If you want a quick 2x2 dashboard instead of manually opening four shells, use:

```bash
bash scripts/tmux_watch_run.sh --job-id 8848287
```

or:

```bash
bash scripts/tmux_watch_run.sh --run-id 8848287_pe_self_ask_mcp_baseline_smoke
```

The helper opens:

- top-left: repo shell with run metadata
- bottom-left: `logs/exp_<jobid>.out` when `--job-id` is provided
- top-right: `harness.log`
- bottom-right: `vllm.log` (or `nvidia-smi` if no vLLM log exists)

If you're SSHing from Ghostty, either start the SSH session with
`TERM=xterm-256color ssh insomnia` or run `export TERM=xterm-256color` before
launching `tmux`.

To test inference, open a second SSH session and `curl` against the compute
node hostname (visible in your interactive shell prompt, e.g. `ins080`):

```bash
ssh <UNI>@insomnia.rcs.columbia.edu
curl http://ins080:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"Llama-3.1-8B-Instruct","prompt":"A power transformer fails because","max_tokens":50}'
```

## Email notifications on job state

Queue waits can be hours, so always attach mail flags when you submit. Pattern:

```bash
sbatch \
    --mail-type=BEGIN,END,FAIL \
    --mail-user=<UNI>@columbia.edu \
    scripts/vllm_serve.sh
```

For interactive `srun` sessions:

```bash
srun \
    -A edu -p short --qos=short \
    --gres=gpu:A6000:1 \
    --time=00:30:00 \
    --mail-type=BEGIN,END,FAIL \
    --mail-user=<UNI>@columbia.edu \
    --pty bash
```

Convenience: `export MAIL_USER=<UNI>@columbia.edu` in your shell profile
(`~/.bashrc` on Insomnia), then `sbatch --mail-type=BEGIN,END,FAIL --mail-user="$MAIL_USER" ...`.

The committed scripts (`scripts/vllm_serve.sh`, `scripts/run_experiment.sh`)
deliberately omit `#SBATCH --mail-user` so teammates running shared scripts
don't get spammed with each other's job notifications. Pass the mail flags
on the `sbatch` CLI per invocation instead.

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
- [`slurm_cheatsheet.md`](slurm_cheatsheet.md) — quick command reference for submit/status/logging/cancel flows
- [`scripts/setup_insomnia.sh`](../scripts/setup_insomnia.sh) — one-shot env setup with pinned versions
- [`scripts/vllm_serve.sh`](../scripts/vllm_serve.sh) — Slurm job script for serving Llama-3.1-8B-Instruct
