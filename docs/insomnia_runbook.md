# Insomnia Runbook

*Last updated: 2026-04-24*
*Owner: Aaron Fan (af3623)*

Verified setup notes, gotchas, and debugging recipes for the Columbia Insomnia
HPC cluster. Read [compute_plan.md](compute_plan.md) first for the higher-level
hardware strategy (which GPU for which phase, Insomnia vs GCP), and
[runbook.md](runbook.md) for the end-to-end reproducibility story. This doc
covers the cluster-specific operational details that aren't obvious from the
official RCS documentation. For the current model names, repo-facing model
IDs, and runtime pins that this runbook assumes, see
[governance/model_registry.yaml](governance/model_registry.yaml).

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

## Group permissions: keep the team checkout group-writable

Every file or directory that any teammate needs to edit must be group-readable
*and* group-writable. The shared parent at
`/insomnia001/depts/edu/users/team13/` is owned by `wax1:somedu` with mode
`drwxrws---` (770 + setgid). The setgid bit makes new files inherit the
`somedu` group automatically; the `g+w` bit is what lets teammates push
commits, edit configs, or run `git pull` into a worktree they didn't create.

The default sshd `umask` on Insomnia is `0027`, which writes new files as
`-rw-r-----` and new directories as `drwxr-x---`. That's the opposite of what
we want for shared work — only the file's owner can edit it, even though the
group is correct. **Set your interactive umask to `002`** so new artifacts
land as `-rw-rw----` and `drwxrws---`:

```bash
# one-time, in ~/.bashrc:
echo "umask 002" >> ~/.bashrc
```

Slurm jobs inherit the submitting shell's umask, so this also fixes job-emitted
logs, `.out` files, and write-from-Python artifacts.

If you encounter a tree where the perms have already drifted (typical sign:
`git pull` works but `git checkout` of a teammate's branch fails with
"unable to unlink"), repair it from the team root:

```bash
cd /insomnia001/depts/edu/users/team13
# Recursive group rwx, capital X = exec only on dirs/already-exec files.
# Skip git internals, venvs, and __pycache__.
find <tree> \( -path "*/.git" -o -path "*/.git/*" \
              -o -path "*/.venv*" -o -path "*/__pycache__/*" \) -prune \
            -o -print0 | xargs -0 chmod g+rwX
# Ensure setgid on every dir so future writes inherit somedu.
find <tree> \( -path "*/.git" -o -path "*/.git/*" -o -path "*/.venv*" \) -prune \
            -o -type d -print0 | xargs -0 chmod g+s
```

The upstream `AssetOpsBench/` clone under the same parent is intentionally
left at owner-only mode; if you need to make a local change there, branch it
into your own clone rather than mutating the shared copy.

Two kinds of residue are expected after the sweep and not problems to chase:

- **Worktree `.git` stub files** (e.g.
  `worktrees/<name>/.git`) — these are owned by whoever created the worktree
  and are deliberately excluded by the `*/.git` prune. Teammates never need
  to write them.
- **Slurm output files** (`logs/exp_*.out`) — owned by the user who
  submitted the job. `chmod` requires being the file's owner, so each
  teammate needs to run the recipe (or just `find . -user "$USER" ! -perm
  -g+w -exec chmod g+rwX {} +`) once from their own account. Adding the
  `umask 002` line above prevents this drift on all future writes.

## Persistent ssh-agent: type your GitHub passphrase once per node

By default the cluster does not start ssh-agent, so every `git push` /
`git pull` / `ssh github.com` re-prompts for the passphrase on
`~/.ssh/id_ed25519`. The fix is a small `~/.ssh/config` block plus a
bashrc snippet that starts an agent on first login and reuses it across
subsequent logins on the same login node. Net result: one passphrase
prompt per login-node-reboot (typically weeks apart).

There is no Linux equivalent of macOS `UseKeychain`, so the passphrase
cannot be persisted across reboots — `ssh-agent` only caches it in
process memory.

**Step 1 — `~/.ssh/config` GitHub block:**

```bash
cat >> ~/.ssh/config <<'EOF'

Host github.com
  IdentityFile ~/.ssh/id_ed25519
  IdentitiesOnly yes
  AddKeysToAgent yes
EOF
chmod 600 ~/.ssh/config
```

`IdentitiesOnly yes` prevents the agent from offering every loaded key to
GitHub (which can hit the server's `MaxAuthTries` and produce
`Too many authentication failures`). `AddKeysToAgent yes` auto-loads the
key into the agent on first use.

**Step 2 — `~/.bashrc` snippet for persistent agent:**

```bash
cat >> ~/.bashrc <<'EOF'

# Persistent ssh-agent: reuse an existing agent across logins on this node.
# First ssh prompts for passphrase once; subsequent ssh ops are passphrase-free
# until the agent dies (typically only at login-node reboot).
SSH_ENV="$HOME/.ssh/agent-environment"
__ssh_agent_start() {
  ssh-agent -s | grep -v '^echo' > "$SSH_ENV"
  chmod 600 "$SSH_ENV"
}
[ -f "$SSH_ENV" ] && . "$SSH_ENV" > /dev/null
if [ -z "${SSH_AGENT_PID:-}" ] || ! kill -0 "$SSH_AGENT_PID" 2>/dev/null; then
  __ssh_agent_start
  . "$SSH_ENV" > /dev/null
fi
unset -f __ssh_agent_start
EOF
```

**Watch out for the `kill -0 0` trap.** An earlier draft of this snippet
used `${SSH_AGENT_PID:-0}` as the default. On Linux, `kill -0 0` targets
the caller's *process group* and always succeeds — so the "is agent
alive?" check passed even when no agent was running, and the start branch
was never taken. The version above tests the variable for emptiness
first.

**Step 3 — prime the agent (one passphrase prompt, ever per node reboot):**

```bash
exec bash -l                # or: source ~/.bashrc
ssh -T git@github.com       # prompts for passphrase, caches the key
ssh-add -l                  # confirms the ed25519 key is loaded
```

After this, `git push`/`git pull` from Insomnia in any shell on this node
runs without prompting until the agent dies.

**Caveats:**

- Login nodes are a small pool with DNS round-robin (`2402-login-001`,
  `2402-login-002`, …). Each node has its own agent process. You will
  re-enter the passphrase the first time you land on a node where the
  agent isn't running yet.
- Slurm jobs do not inherit your interactive agent. If a job needs to
  `git push` it has to authenticate some other way (HTTPS token, separate
  passphrase-less deploy key, etc.). For our workflow jobs only write
  artifacts, and humans push from interactive sessions, so this hasn't
  come up.

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
captured in [governance/model_registry.yaml](governance/model_registry.yaml).

The repo-standard local Llama checkpoint revision is:

```bash
MODEL_REVISION=0e9e39f249a16976918f6564b8830bc894c89659
```

`scripts/setup_insomnia.sh` uses that SHA by default. Override
`MODEL_REVISION` only for an intentional checkpoint refresh or validation
rerun, and record the override in the run artifact / issue comment.

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
[validation_log.md](validation_log.md). Keep this runbook for operational
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

- [compute_plan.md](compute_plan.md) — phase-by-phase GPU allocation strategy
- [slurm_cheatsheet.md](slurm_cheatsheet.md) — quick command reference for submit/status/logging/cancel flows
- [scripts/setup_insomnia.sh](../scripts/setup_insomnia.sh) — one-shot env setup with pinned versions
- [scripts/vllm_serve.sh](../scripts/vllm_serve.sh) — Slurm job script for serving Llama-3.1-8B-Instruct
