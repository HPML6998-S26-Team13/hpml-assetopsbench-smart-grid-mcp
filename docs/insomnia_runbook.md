# Insomnia Runbook

*Last updated: 2026-04-28*
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

## Filesystem topology

Everything Team 13 owns on Insomnia lives under a single shared parent directory.
The canonical layout is:

```
/insomnia001/depts/edu/users/team13/
├── hpml-assetopsbench-smart-grid-mcp/   # canonical team checkout (root worktree on main)
│   ├── .venv-insomnia/                  # shared Python 3.11 env (uv-managed)
│   ├── scripts/                         # run_experiment.sh, vllm_serve.sh, setup_insomnia.sh, ...
│   ├── benchmarks/                      # Exp 1/2 capture trees (per-run JSONs, harness.log, vllm.log)
│   ├── profiling/traces/                # Torch profiler outputs (per RUN_ID)
│   └── logs/                            # exp_<jobid>.out Slurm output
├── worktrees/<branch-slug>/             # per-branch git worktrees, sibling of canonical checkout
└── AssetOpsBench/                       # upstream IBM clone (read-only, owner-only mode)
```

The parent directory is `drwxrws---` (`770 + setgid`) owned by `wax1:somedu`. The
setgid bit makes new files inherit the `somedu` group; see "Group permissions"
below for the `umask 002` convention that keeps everything group-writable.

The upstream `AssetOpsBench/` clone is intentionally left at owner-only mode —
do not chmod it. If you need a local change there, branch your own clone outside
the team root rather than mutating the shared copy.

To check your storage headroom on the edu scratch volume:

```bash
quota -s                                      # per-user usage and limits
df -h /insomnia001/depts/edu/users/team13     # team scratch capacity
```

### Worktrees on Insomnia

Per-branch work lives in `/insomnia001/depts/edu/users/team13/worktrees/<branch-slug>/`,
**sibling of the canonical checkout, not nested under it**. Create a worktree from
inside the canonical checkout:

```bash
cd /insomnia001/depts/edu/users/team13/hpml-assetopsbench-smart-grid-mcp
git fetch team13

# Local branch already exists:
git worktree add ../worktrees/<slug> <local-branch>

# Remote branch exists but no local branch yet — create the local branch in
# the worktree so commits aren't detached:
git worktree add -b <local-branch> ../worktrees/<slug> team13/<remote-branch>

# Brand-new branch off team13/main:
git worktree add -b <new-branch> ../worktrees/<slug> team13/main
```

**Do not pass a remote-tracking ref directly** (e.g.
`git worktree add ../worktrees/<slug> team13/foo`). Git interprets that as a
detached-HEAD checkout of the remote ref — commits land detached and `git push`
targets get murky. Always either reference an existing local branch or use
`-b <local-branch>` to create one.

Worktrees share the canonical `.venv-insomnia/` (one venv, multiple working trees).
`cd ../worktrees/<slug> && source ../../hpml-assetopsbench-smart-grid-mcp/.venv-insomnia/bin/activate`
works fine; do not create a per-worktree venv.

**Perms gotcha:** the `worktrees/` parent itself must be `drwxrws---` (group-writable
+ setgid), or teammates cannot create new worktrees under it. If `git worktree add`
fails with "Permission denied" on the parent, ask the directory owner to fix:

```bash
chmod g+rwxs /insomnia001/depts/edu/users/team13/worktrees
```

Submodules don't auto-populate in new worktrees. If the project pulls in submodules
(none today, but applies if added), run `git submodule update --init` after
`git worktree add`.

When done with a worktree, remove it from the canonical checkout:

```bash
cd /insomnia001/depts/edu/users/team13/hpml-assetopsbench-smart-grid-mcp
git worktree remove ../worktrees/<slug>
```

`git worktree remove --force` deletes untracked files inside the worktree without
warning; copy out anything you want to keep first.

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
- `mcp[cli]==1.27.0`
- `openai-agents==0.14.5`

`requirements-insomnia.txt` overlays the cluster-only stack on top of the base
file via `-r requirements.txt` at its head, so a single
`uv pip install -r requirements-insomnia.txt` resolves both layers together.

So if an Insomnia proof run dies with `ModuleNotFoundError: litellm` or
`ModuleNotFoundError: mcp`, the fix is usually not a bespoke `pip install` in
the moment — it is to refresh the shared env against
`requirements-insomnia.txt`. The matching model/runtime contract is now also
captured in [governance/model_registry.yaml](governance/model_registry.yaml).

### Trial output contract (PR #143)

`scripts/run_experiment.sh` post-processes every per-trial JSON to inject two
canonical fields:

- `data["scenario"]` — the **full source scenario JSON object** (with
  `scenario.id` as the key Notebook 03 consumes), copied from the scenario
  file referenced in `latencies.jsonl`. Already-populated objects with an
  `id` key are left alone (idempotent).
- `data["success"]` — boolean or `None`. If the runner already wrote a bool,
  it is preserved as-is. Otherwise `_derive_success` walks `history` first
  (falls back to `trajectory`); any failed step → `False`; if neither
  history/trajectory nor an answer exists → `None`; otherwise → `bool(answer)`.
  **Not** derived from harness exit status or judge pass rate.

Default `TRIALS=3`. Older captures predating PR #143 are missing these fields
and get classified as `legacy` by Notebook 03's `canonical_rows` gate. Retrofit
from the repo root:

```bash
# Dry-run sweep across all cells:
python3 scripts/backfill_canonical_scenario.py

# Apply to all cells:
python3 scripts/backfill_canonical_scenario.py --apply

# Apply to one cell only (A/B/C/Y/Z):
python3 scripts/backfill_canonical_scenario.py --apply --cell B

# Apply to a subset (--cell is repeatable via argparse action="append"):
python3 scripts/backfill_canonical_scenario.py --apply --cell B --cell Y
```

The script has no positional capture-dir argument — it walks
`benchmarks/cell_<X>/raw/<run_id>/` from the repo root for each selected cell.
Pass `--repo-root <path>` to point at a non-default checkout.

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

# Completions-only sanity serve (raw /v1/completions smoke tests only — do NOT
# use this as the basis for any captured benchmark / AaT / PE run):
python -u -m vllm.entrypoints.openai.api_server \
    --model models/Llama-3.1-8B-Instruct \
    --served-model-name Llama-3.1-8B-Instruct \
    --port 8000 --max-model-len 8192 --dtype float16
```

**Use the tool-call serve for any benchmark / AaT / PE reproduction.** As of
PR #144, `scripts/run_experiment.sh` defaults `VLLM_ENABLE_AUTO_TOOL_CHOICE=1`
and selects a model-family parser automatically (`llama3_json` for the team's
pinned Llama-3.1-8B-Instruct; see `run_experiment.sh:90-104`). The top-level
Cell A / Cell B configs (`configs/aat_direct.env`, `configs/aat_mcp_baseline.env`,
their `_smoke` and `_upstream_smoke` siblings) pin the values explicitly;
`configs/experiment2/*.env`, `configs/aat_mcp_optimized.env`, and the example
configs inherit the defaults. The wired flags become
`--enable-auto-tool-choice --tool-call-parser <parser>` (see
`run_experiment.sh:759-776`). Reproducing the serve manually without these
flags hits `tool_choice=auto requires --enable-auto-tool-choice` the moment
the harness makes its first tool-call request, regardless of cell.

The matching manual recipe — **source the target config first** so
`MAX_MODEL_LEN` matches what the harness expects (`32768` for Cell Y/Z PE
configs; `8192` for current Cell A/B AaT configs). Many configs intentionally
omit `VLLM_SERVED_MODEL_NAME`, `VLLM_ENABLE_AUTO_TOOL_CHOICE`, and
`VLLM_TOOL_CALL_PARSER` because they inherit defaults from
`scripts/run_experiment.sh:90-104`. Apply those defaults yourself before
launching:

```bash
# Pull MAX_MODEL_LEN, VLLM_MODEL_PATH, etc. from the cell's config.
set -a; source configs/experiment2/exp2_cell_Y_pe_mcp_baseline.env; set +a

# Apply the same defaults run_experiment.sh would. Adjust the parser case
# block if you point at a non-Llama-3 model.
VLLM_PORT="${VLLM_PORT:-8000}"
VLLM_MODEL_PATH="${VLLM_MODEL_PATH:-models/Llama-3.1-8B-Instruct}"
VLLM_SERVED_MODEL_NAME="${VLLM_SERVED_MODEL_NAME:-$(basename "$VLLM_MODEL_PATH")}"
VLLM_ENABLE_AUTO_TOOL_CHOICE="${VLLM_ENABLE_AUTO_TOOL_CHOICE:-1}"
case "${MODEL_ID:-}" in
  *llama-3*|*Llama-3*|*llama3*|*Llama3*) _DEFAULT_PARSER=llama3_json ;;
  *qwen*|*Qwen*) _DEFAULT_PARSER=hermes ;;
  *mistral*|*Mistral*) _DEFAULT_PARSER=mistral ;;
  *) _DEFAULT_PARSER=llama3_json ;;
esac
VLLM_TOOL_CALL_PARSER="${VLLM_TOOL_CALL_PARSER:-$_DEFAULT_PARSER}"

python -u -m vllm.entrypoints.openai.api_server \
    --model "$VLLM_MODEL_PATH" \
    --served-model-name "$VLLM_SERVED_MODEL_NAME" \
    --port "$VLLM_PORT" --max-model-len "$MAX_MODEL_LEN" --dtype float16 \
    --enable-auto-tool-choice --tool-call-parser "$VLLM_TOOL_CALL_PARSER"
```

Hard-coding `--max-model-len 8192` here is a known gotcha for any manual
replay against Cell Y/Z scenarios: PE and Verified PE multi-step plans
overflow the 8192 context window and either truncate or crash partway
through (see `docs/validation_log.md` for prior occurrences). The
`run_experiment.sh` harness sets `MAX_MODEL_LEN=32768` by default, so
manual recipes need to match that value.

**Replay phase is AaT-only.** `run_experiment.sh` runs the post-benchmark
torch-profiler replay only when `ORCHESTRATION=agent_as_tool` (Cell A, B, C).
For PE / Verified PE cells (Y, Z) the harness skips the replay phase
automatically because `replay_scenarios.sh` always drives `aat_runner.py`,
which would produce a misleading AaT-shaped trace under the cell's
directory. Profile coverage for non-AaT cells happens during the main
benchmark loop. See `docs/replay_phase_analysis.md` for the full design
rationale.

**Torch profiler flag changed.** vLLM 0.19.0 dropped the
`VLLM_TORCH_PROFILER_DIR` env var. Profiling is now enabled via a CLI flag with
an absolute path:

```bash
--profiler-config '{"profiler":"torch","torch_profiler_dir":"/abs/path/to/profiling/traces/<run-id>_torch"}'
```

`run_experiment.sh:783-785` builds this automatically when `TORCH_PROFILE=1`;
manual reproductions need to construct it explicitly. Output traces land under
`profiling/traces/${RUN_ID}_torch/`.

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
node hostname. GPU compute nodes follow the `ins0XX` pattern (e.g. `ins080`,
`ins082`, `ins103`). Read your assigned node from the interactive shell prompt,
or programmatically:

```bash
hostname              # e.g. ins080
echo "$SLURMD_NODENAME"   # same, set inside Slurm jobs
```

Then from a second login session:

```bash
ssh <UNI>@insomnia.rcs.columbia.edu
curl http://ins080:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"Llama-3.1-8B-Instruct","prompt":"A power transformer fails because","max_tokens":50}'
```

## Email notifications on job state

Queue waits can be hours. **Always attach mail flags when you submit** — the
default invocation pattern across the team is:

```bash
# One-time setup in ~/.bashrc on Insomnia:
export MAIL_USER="${USER}@columbia.edu"
```

Then every submit looks like:

```bash
sbatch --mail-type=BEGIN,END,FAIL --mail-user="$MAIL_USER" \
    scripts/run_experiment.sh configs/experiment2/exp2_cell_Y_pe_mcp_baseline.env
```

For interactive `srun` sessions:

```bash
srun -A edu -p short --qos=short \
    --gres=gpu:A6000:1 --time=00:30:00 \
    --mail-type=BEGIN,END,FAIL --mail-user="$MAIL_USER" \
    --pty bash
```

The committed scripts (`scripts/vllm_serve.sh`, `scripts/run_experiment.sh`)
deliberately omit `#SBATCH --mail-user` so teammates running shared scripts
don't get spammed with each other's job notifications. Pass the mail flags
on the `sbatch` CLI per invocation instead.

## Excluding bad nodes

Individual GPU nodes occasionally land in a bad state where vLLM/PyTorch can't
see the GPU, even though `sinfo` reports the node as Idle. Symptom in
`logs/exp_<jobid>.out` or `vllm.log`:

```
RuntimeError: CUDA unknown error - this may be due to an incorrectly set up environment ...
Setting the available devices to be zero.
```

When you hit this, identify the offending node from your job's
`$SLURMD_NODENAME` (or the prompt in an interactive shell — e.g. `ins082`) and
**re-submit with `--exclude=<node>`** so the scheduler routes around it:

```bash
sbatch --exclude=ins082 \
    --mail-type=BEGIN,END,FAIL --mail-user="$MAIL_USER" \
    scripts/run_experiment.sh "$cfg"
```

Multiple bad nodes: `--exclude=ins082,ins091`. The exclusion only affects this
submission; subsequent submits without the flag remain eligible for the node.

If a node stays bad across multiple submits over a day or more, file a ticket
with RCS (`rcs-support@columbia.edu`) — they can drain and reboot it. A node
that recovers on its own (typical) needs no follow-up.

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

Llama-3.1-8B at FP16 fits on every GPU type Insomnia exposes to the `edu`
account today (A6000 48 GB, L40/L40S 48 GB, H100 80 GB), so `--gres=gpu:1` is
the fastest path to a slot when the A6000 nodes are saturated. For the
authoritative live menu of partitions and GPU types:

```bash
sinfo -o '%P %.6D %.20G %N'      # partitions, node count, gres, nodelist
sinfo -p short --Format='Gres'   # just the gres column
```

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

- [runbook.md](runbook.md) — top-level reproducibility doc, including the
  WandB setup section (`wandb login` once per node, `WANDB_API_KEY` /
  `ENABLE_WANDB=1` / `WANDB_PROJECT` / `WANDB_ENTITY` / `WANDB_MODE` env vars
  honored by `run_experiment.sh`)
- [compute_plan.md](compute_plan.md) — phase-by-phase GPU allocation strategy
- [slurm_cheatsheet.md](slurm_cheatsheet.md) — quick command reference for submit/status/logging/cancel flows
- [governance/model_registry.yaml](governance/model_registry.yaml) — canonical model IDs, runtime pins, judge contract
- [scripts/setup_insomnia.sh](../scripts/setup_insomnia.sh) — one-shot env setup with pinned versions
- [scripts/vllm_serve.sh](../scripts/vllm_serve.sh) — Slurm job script for serving Llama-3.1-8B-Instruct
- [scripts/run_experiment.sh](../scripts/run_experiment.sh) — benchmark wrapper (vLLM serve + harness + WandB + canonical scenario contract)
- [scripts/backfill_canonical_scenario.py](../scripts/backfill_canonical_scenario.py) — retrofit pre-PR-#143 captures to canonical scenario/success contract
