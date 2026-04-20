# Slurm Cheatsheet

*Created: 2026-04-12*  
*Last updated: 2026-04-20*

Quick command-first reference for common Slurm operations on Insomnia.
Use this when you just want to submit a job, get an interactive GPU shell,
watch a running allocation, or recover from common `sbatch` / `srun`
confusion.

For Insomnia-specific setup and serving guidance, see
[`insomnia_runbook.md`](insomnia_runbook.md). For the higher-level workflow,
see [`runbook.md`](runbook.md).

## Mental model

- `sbatch script.sh` submits a batch job and returns immediately with a job ID.
- `srun --pty bash` waits for an allocation, then gives you an interactive
  shell on the compute node.
- `srun bash -lc '...'` waits for an allocation, then runs a command
  non-interactively.
- `srun --jobid=<JOBID> --overlap --pty bash` drops you into an already-running
  job allocation.
- `squeue` shows live jobs.
- `sacct` shows completed or historical jobs.

Two important realities on Insomnia:

- **Anything that imports `torch` / `vllm` / `transformers` belongs on a compute
  node, not the login node.**
- **Slurm log paths are resolved relative to the submit directory**
  (`$SLURM_SUBMIT_DIR`), so submit from the repo root or use `--chdir=...`.

## Submit a batch script

Use this when you do not want to sit and wait for the allocation.

From the repo root:

```bash
cd <repo-root-or-worktree>
sbatch scripts/vllm_serve.sh
```

Or from anywhere, explicitly:

```bash
sbatch \
  --chdir=<repo-root-or-worktree> \
  scripts/vllm_serve.sh
```

Capture the job ID:

```bash
JOBID=$(sbatch scripts/vllm_serve.sh | awk '{print $4}')
echo "$JOBID"
```

With email notifications:

```bash
sbatch \
  --mail-type=BEGIN,END,FAIL \
  --mail-user=<UNI>@columbia.edu \
  scripts/vllm_serve.sh
```

## Run an ad hoc command when allocation starts

Use this for a one-off command, **not** for scripts that already contain
`#SBATCH` headers.

```bash
sbatch \
  --account=edu \
  --partition=short \
  --qos=short \
  --gres=gpu:A6000:1 \
  --time=00:20:00 \
  --wrap='hostname && nvidia-smi'
```

If you are running `scripts/vllm_serve.sh` or `scripts/run_experiment.sh`,
submit the script directly with `sbatch`, because those scripts already carry
their own Slurm settings.

## Ask for an interactive GPU shell

Use this when you want to debug manually on the compute node.

```bash
srun \
  --account=edu \
  --partition=short \
  --qos=short \
  --gres=gpu:A6000:1 \
  --time=00:30:00 \
  --chdir=<repo-root-or-worktree> \
  --pty bash
```

Minimal generic GPU request:

```bash
srun \
  --account=edu \
  --partition=short \
  --qos=short \
  --gres=gpu:1 \
  --time=00:05:00 \
  --pty bash
```

## Attach to an already-running job

Use this when the batch job is already running and you want a shell in the same
allocation.

```bash
srun --jobid=<JOBID> --overlap --pty bash
```

Common uses after attaching:

```bash
hostname
nvidia-smi
tail -f logs/<JOBID>.out
```

For the vLLM serve path:

```bash
curl -s http://127.0.0.1:8000/v1/models
```

## Check live job status

All live jobs for your user:

```bash
squeue -u <UNI>
```

One job:

```bash
squeue -j <JOBID>
```

Estimated start time:

```bash
squeue --start -j <JOBID>
```

Detailed job info:

```bash
scontrol show job <JOBID>
```

Watch it live:

```bash
watch -n 15 'squeue -j <JOBID>'
```

## See whether a job is still live or already finished

If `squeue -j <JOBID>` says `Invalid job id specified`, usually one of these is
true:

- the job already finished or was cancelled
- the job ID is wrong
- the submission failed and no real job exists

Use `sacct` for historical status:

```bash
sacct -j <JOBID> --format=JobID,JobName,State,ExitCode
```

## See how long the job waited in queue

```bash
sacct -j <JOBID> --format=JobID,Submit,Eligible,Start,End,Elapsed,State
```

Useful fields:

- `Submit`: when the job was submitted
- `Eligible`: when it became runnable
- `Start`: when it actually started
- `End`: when it ended
- `Elapsed`: runtime after start

Rough queue wait is `Start - Submit` or `Start - Eligible`.

## Find the right log file

For batch jobs, first check the Slurm stdout/stderr log.

If the script sets `#SBATCH --output=logs/%j.out`, then the file is usually:

```bash
logs/<JOBID>.out
```

Examples:

```bash
ls -l logs/<JOBID>.out
tail -100 logs/<JOBID>.out
```

If you used plain `sbatch --wrap=...` without `--output`, Slurm usually writes:

```bash
slurm-<JOBID>.out
```

in the directory where you ran `sbatch`.

Pair logs with accounting info:

```bash
sacct -j <JOBID> --format=JobID,JobName,State,ExitCode,NodeList
```

## Interactive `srun` vs batch logs

This trips people up a lot:

- If you launched a script with **`sbatch`**, expect a Slurm log file
  (`logs/<JOBID>.out` or `slurm-<JOBID>.out`).
- If you grabbed an interactive shell with **`srun --pty bash`** and then ran
  `bash scripts/run_experiment.sh ...`, there may be **no**
  `logs/exp_<jobid>.out` file for that inner command.

For interactive runs, watch the benchmark artifacts directly instead:

```bash
tail -f benchmarks/cell_Y_plan_execute/raw/<run-id>/harness.log
tail -f benchmarks/cell_Y_plan_execute/raw/<run-id>/vllm.log
```

## Common gotchas

### `fatal: not a git repository` or `config not found` inside `srun`

Your shell is probably inheriting a stale `SLURM_SUBMIT_DIR`.

Fix it in the compute shell:

```bash
cd <repo-root-or-worktree>
export SLURM_SUBMIT_DIR="$PWD"
```

Or:

```bash
unset SLURM_SUBMIT_DIR
```

Then rerun the script.

### `nvidia-smi: command not found`

You are probably on the login node, not the compute node.

Either:

```bash
srun --account=edu --partition=short --qos=short --gres=gpu:1 --time=00:10:00 --pty bash
```

or attach to the running job:

```bash
srun --jobid=<JOBID> --overlap --pty bash
```

### `squeue` is live but the script seems hung

Attach to the job and inspect the real state:

```bash
srun --jobid=<JOBID> --overlap --pty bash
hostname
nvidia-smi
tail -100 logs/<JOBID>.out
```

For benchmark runs, also inspect:

```bash
tail -100 benchmarks/<cell>/raw/<run-id>/harness.log
tail -100 benchmarks/<cell>/raw/<run-id>/vllm.log
```

## Cancel a job

```bash
scancel <JOBID>
```

Cancel all your live jobs:

```bash
scancel -u <UNI>
```

## Useful one-liners

Show just job states:

```bash
squeue -h -u <UNI> -o '%i %T %R'
```

Show estimated starts for all your jobs:

```bash
squeue --start -u <UNI>
```

Check which node a running job landed on:

```bash
squeue -j <JOBID> -o '%i %T %N'
```

Show batch-job history with timing:

```bash
sacct -u <UNI> --format=JobID,JobName,Partition,State,Submit,Start,End,Elapsed
```

## Git-side tip

To inspect recent commits with both short SHA and author:

```bash
git log --oneline --format='%h %an %s'
```

With relative date too:

```bash
git log --format='%h %an %ar %s'
```
