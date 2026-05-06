# Runbook

*Last updated: 2026-05-05*
*Infra owner: Aaron Fan (af3623) — eval-harness owner: Akshat Bhandari (ab6174) — coordinator: Alex Xin (wax1)*

Canonical reproducibility runbook. A teammate following this from scratch
should be able to stand up the serving environment, submit benchmark cells
through Slurm, and produce matched profiling + benchmark artifacts without
verbal help.

The runbook is split by concern:

- **§1 Preconditions** — accounts, tokens, and approvals you need before starting
- **§2 First-time setup** — clone, venv, model download, credentials
- **§3 Day-to-day workflow** — submit a benchmark cell, check status, collect artifacts
- **§4 Profiling workflow** — GPU + PyTorch Profiler captures linked to WandB
- **§5 Troubleshooting** — decision tree pointing at the detailed docs
- **§6 Related runbooks and pointers**

Cluster-specific gotchas (broken CUDA module, Python version issues, login-
node etiquette) live in [insomnia_runbook.md](insomnia_runbook.md). This
file is the higher-level reproducibility story; read the Insomnia runbook
alongside it.

> **Where new captures land (status as of 2026-05-05):** Insomnia is the
> primary path again — it returned on 2026-05-05 after the 2026-05-03 → 05
> CVE-fix maintenance window. During that downtime the team validated the
> GCP A100 spot path end-to-end (PR #170 hardening + the
> `gcp_a100_final_20260503` closeout, 19 rows × 30 trials, summary at
> `benchmarks/gcp_a100_final_20260503/summary/README.md`),
> so GCP is now a proven fallback rather than just a documented one. Use
> the Insomnia path in §2-§4 by default; switch to the GCP path in §3.7
> when Insomnia is unavailable, queue-saturated, or you need preemption-
> tolerant batching. Resumable runs via `SMARTGRID_RUN_ID` /
> `SMARTGRID_RESUME` work identically across both paths (PR #170), so the
> same `--batch-id` survives a path swap mid-batch if needed.
>
> Apr 26-28 canonical captures (Cells A/B/Y/Z, runs `8979314` /
> `8998340..8998343`) ran on Insomnia A6000. The May 3 closeout ran on
> GCP A100. The `gpu_type` field in `summary.json` (PR #145) records
> which path each run actually used so cross-run comparisons can filter
> accordingly.
>
> See [`infra_profiling_serving_brief.md`](infra_profiling_serving_brief.md) for the one-page fact pack
> (model IDs + version pins + canonical run IDs) that backs the paper's
> infra paragraphs.

---

## 1. Preconditions

You need all of these before §2 setup will succeed. None of them require help
from Aaron.

### Columbia HPC access

- Columbia UNI with Duo 2FA enrolled
- RCS Insomnia access request filed and approved (see Columbia's Insomnia
  onboarding material; team-specific settings live in [insomnia_runbook.md](insomnia_runbook.md))
- `ssh <UNI>@insomnia.rcs.columbia.edu` works end-to-end

Team account details:

| Slurm flag | Value |
|---|---|
| `--account` | `edu` |
| `--partition` | `short` (or `burst`; same nodes, burst is preemptible) |
| `--qos` | must match partition |

Shared team scratch directory (always work from here, not `$HOME`):

```
/insomnia001/depts/edu/users/team13/hpml-assetopsbench-smart-grid-mcp
```

### HuggingFace + Meta Llama access

1. HF account, token with **read** scope (create at
   <https://huggingface.co/settings/tokens>).
2. Accept the Llama 3.1 Community License at
   <https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct>.
3. Export the token before running setup:
   ```bash
   export HF_TOKEN=hf_yourtokenhere
   ```

### WatsonX.ai (required only for the WatsonX serving path)

Credentials live in `.env` at repo root (gitignored). Ask Alex if you don't
have values. Full setup in [reference/watsonx_access.md](reference/watsonx_access.md).

### WandB (required for `ENABLE_WANDB=1`)

- Member of the `assetopsbench-smartgrid` team at <https://wandb.ai>
- `wandb login` run once in the serving venv, or `WANDB_API_KEY` exported

---

## 2. First-time setup

The team shares one checkout + one venv under `team13/`. Alex (wax1) owns the
venv; do not `rm -rf .venv-insomnia` without coordinating with the team.

### 2.1 Reach the team checkout

```bash
ssh <UNI>@insomnia.rcs.columbia.edu
cd /insomnia001/depts/edu/users/team13/hpml-assetopsbench-smart-grid-mcp
git pull
```

For per-branch worktrees on Insomnia, see
[insomnia_runbook.md § Worktrees on Insomnia](insomnia_runbook.md#worktrees-on-insomnia)
— worktrees go in the shared `/insomnia001/depts/edu/users/team13/worktrees/<slug>/`
sibling, with explicit guidance on avoiding detached-HEAD checkouts. Run jobs
from the main checkout; worktrees are for editing.

### 2.2 Verify the venv

The venv (`.venv-insomnia/`) is pre-provisioned with Python 3.11 + the pinned
vLLM stack in `requirements-insomnia.txt`. On the login node, verify with
metadata-only checks:

```bash
source .venv-insomnia/bin/activate
python --version                           # expect 3.11.x
python - <<'PY'
from importlib.metadata import version
print(version("vllm"))
PY
```

If you want to verify `import vllm` itself, do that from a compute node rather
than the login node:

```bash
srun --account=edu --partition=short --qos=short --gres=gpu:A6000:1 \
     --mem=64G --time=01:00:00 --pty bash
cd /insomnia001/depts/edu/users/team13/hpml-assetopsbench-smart-grid-mcp
source .venv-insomnia/bin/activate
python -c "import vllm; print(vllm.__version__)"
```

**If the venv is missing or broken, coordinate with the owner before
recreating.** Recreation steps live in
[insomnia_runbook.md § Recreate the shared env when needed](insomnia_runbook.md#recreate-the-shared-env-when-needed).

### 2.3 Verify the model

```bash
ls models/Llama-3.1-8B-Instruct/ | head
```

Should list `config.json`, `tokenizer.json`, and four `model-*.safetensors`
shards (~16 GB total). If missing, the canonical re-download path is
`bash scripts/setup_insomnia.sh` with `HF_TOKEN` exported. The script now
defaults to the repo-standard `MODEL_REVISION` recorded in
[`governance/model_registry.yaml`](governance/model_registry.yaml):

```bash
export MODEL_REVISION=0e9e39f249a16976918f6564b8830bc894c89659
```

You can leave `MODEL_REVISION` unset for the standard path, but keep the
resolved SHA in run logs and issue comments when reporting benchmark evidence.
Coordinate first because the download is slow and clobbers the shared
`models/` directory.

### 2.4 Verify WatsonX (used by evaluation / judge paths)

From the team checkout:

```bash
.venv/bin/python scripts/verify_watsonx.py --list-only
```

Expect six Llama models listed. Full walkthrough in
[reference/watsonx_access.md](reference/watsonx_access.md).

### 2.5 Set up email-notified Slurm submission

Queue waits on `edu` can run hours. Always attach mail flags so you're not
babysitting `squeue`. Add to `~/.bashrc` on Insomnia:

```bash
export MAIL_USER=<UNI>@columbia.edu
```

Then submit with:

```bash
sbatch --mail-type=BEGIN,END,FAIL --mail-user="$MAIL_USER" scripts/<script>.sh [args...]
```

Shared scripts (`vllm_serve.sh`, `run_experiment.sh`) deliberately don't
hardcode `--mail-user` so teammates aren't spammed with each other's
notifications; pass it per-invocation.

---

## 3. Day-to-day: running a benchmark cell

The canonical benchmark-facing execution path is `scripts/run_experiment.sh
<config.env>`. Configs under `configs/` describe each cell of the
experimental grid; see [configs/README.md](../configs/README.md) for the
5-cell mapping and [execution_plan.md](execution_plan.md) for the cells'
scientific roles.

### 3.1 Pick a config

| File | Cell | Orchestration | MCP mode | Status |
|---|---|---|---|---|
| [configs/example_baseline.env](../configs/example_baseline.env) | Y | Plan-Execute | baseline | Working |
| [configs/aat_direct.env](../configs/aat_direct.env) | A | Agent-as-Tool | direct | Skeleton (needs runner, see [experiment1_capture_plan.md](experiment1_capture_plan.md)) |
| [configs/aat_mcp_baseline.env](../configs/aat_mcp_baseline.env) | B | Agent-as-Tool | baseline | Skeleton |
| [configs/aat_mcp_optimized.env](../configs/aat_mcp_optimized.env) | C | Agent-as-Tool | optimized | Skeleton |

### 3.2 Dry-run the wiring

Always sanity-check a config with `DRY_RUN=1` first. It validates scenarios,
resolves the AssetOpsBench path, and prints the server arguments — without
launching vLLM or Slurm:

```bash
DRY_RUN=1 bash scripts/run_experiment.sh configs/example_baseline.env
```

### 3.3 Submit the real job

```bash
sbatch --mail-type=BEGIN,END,FAIL --mail-user="$MAIL_USER" \
    scripts/run_experiment.sh configs/example_baseline.env
```

Monitor:

```bash
squeue -u $USER
squeue -u $USER --start          # estimated start time when pending
tail -f logs/exp_<jobid>.out     # once the job is running
```

Cancel with `scancel <jobid>`.

### 3.4 Where artifacts land

On job completion, artifacts live under:

```
benchmarks/cell_<X>/
├── config.json            # canonical reproducibility config + wandb_run_url
├── summary.json           # aggregate summary for the latest run
└── raw/<run-id>/
    ├── meta.json          # run metadata, timestamps, pass/fail counts
    ├── latencies.jsonl    # per-step latency records
    ├── harness.log        # harness stderr aggregated across trials
    ├── vllm.log           # vLLM server log (if LAUNCH_VLLM=1)
    └── <scenario>_t<n>.json  # one JSON per scenario × trial
```

WandB run is auto-created when `ENABLE_WANDB=1`, and its URL is stamped into
all three JSON files above. `docs/wandb_schema.md` documents the field names.

### 3.5 Common sbatch overrides

| Goal | Override |
|---|---|
| Default Insomnia evidence GPU | `--gres=gpu:A6000:1` |
| Hardware-flexible exploratory run | `--gres=gpu:1` *(record the allocated GPU; do not mix with typed evidence cohorts)* |
| Specific GPU type | `--gres=gpu:A6000:1`, `--gres=gpu:h100:1`, `--gres=gpu:l40s:1` |
| Longer walltime (up to 12h) | `--time=04:00:00` |
| Different partition | `--partition=burst --qos=burst` |
| Local dev (no Slurm) | `bash scripts/run_experiment.sh <config>` from an `srun --pty` shell |

### 3.6 Resumable runs (preemption-tolerant)

Set `SMARTGRID_RUN_ID` and `SMARTGRID_RESUME=1` to make the runner skip
already-completed trials and pick up where the prior attempt died. Useful
on GCP spot (where preemption can hit mid-run) and harmless on Insomnia
(it just turns into a no-op when no resume state exists). Implementation
in `scripts/gcp_resume_state.py` + `scripts/run_gcp_context_batch.sh`,
landed in PR #170.

```bash
SMARTGRID_RUN_ID=ctx_20260503T063343Z \
SMARTGRID_RESUME=1 \
sbatch --mail-type=BEGIN,END,FAIL --mail-user="$MAIL_USER" \
    scripts/run_experiment.sh configs/<cell>.env
```

`SMARTGRID_RESUME_REQUIRE_LATENCY=1` (default) requires the prior trial
to have written a `latencies.jsonl` row before counting it as resumable.
`SMARTGRID_FORCE_RERUN=1` overrides the skip and retries every trial.

### 3.7 GCP A100 variant (validated fallback)

Insomnia is the primary path again as of 2026-05-05 (see top-of-file
status block); switch to this GCP path when Insomnia is unavailable,
queue-saturated, or you need preemption-tolerant batching.
spin up an A100 spot instance and run the *same* `scripts/run_experiment.sh`
entry point. The serving stack, configs, and artifact layout are
identical — `gpu_type` in `summary.json` records whether each run landed
on Insomnia A6000 vs GCP A100 vs etc. (PR #145 / `#132`).

Full spin-up walkthrough is in [`gcp_fallback.md`](gcp_fallback.md). Day-to-day shape:

```bash
# 1. Spin up an A100-40GB spot instance (~$1.81/hr)
#    Full args + region selection in gcp_fallback.md §4. Tagged with the
#    canonical `smartgrid-*` host prefix so `compute_env=gcp` flips
#    automatically in summary.json.

# 2. SSH in, clone repo, run setup_insomnia.sh (works on GCP too — §6a):
git clone git@github.com:HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp.git
cd hpml-assetopsbench-smart-grid-mcp
bash scripts/setup_insomnia.sh

# 3. Source credentials (see §2.4 / §2.5 — same env vars as Insomnia):
set -a; source ./.env; set +a

# 4. Run the same way as Insomnia, but use `bash` (no Slurm on GCP):
#    SMARTGRID_RUN_ID + SMARTGRID_RESUME so a spot preemption mid-run just
#    resumes from the last completed trial. `run_experiment.sh` is
#    Slurm-aware but not Slurm-dependent (see gcp_fallback.md §6).
SMARTGRID_RUN_ID=ctx_$(date +%Y%m%dT%H%M%SZ) \
SMARTGRID_RESUME=1 \
bash scripts/run_experiment.sh configs/<cell>.env

# 5. Pull artifacts back to a local checkout once the run completes
#    (canonical pattern in scripts/gcp_pull_context_artifacts.sh; PR #170):
bash scripts/gcp_pull_context_artifacts.sh <run_id>
```

The canonical GCP capture (19 rows, 570 trajectories + 570 judge logs)
is summarised at
`benchmarks/gcp_a100_final_20260503/summary/README.md` with per-batch
manifests in `benchmarks/gcp_a100_final_20260503/logs/*_manifest.tsv`
(PR #172). That's the reference for "what a clean GCP capture looks like."

---

## 4. Profiling workflow

Four wrapper scripts under [profiling/scripts/](../profiling/scripts/);
[profiling/README.md](../profiling/README.md) explains when to pick which.

### 4.1 Lightweight GPU telemetry (always-on option)

`nvidia-smi` sampler writes one CSV row per second. Near-zero overhead.
Run it in the background around any benchmark command:

```bash
OUT=profiling/traces/$(date +%Y%m%d-%H%M%S)_mycell
mkdir -p "$OUT"
bash profiling/scripts/sample_nvidia_smi.sh "$OUT/nvidia_smi.csv" &
SMI=$!
# ...your benchmark run here...
kill $SMI
```

### 4.2 Convenience wrapper (recommended)

`capture_around.sh` bundles the nvidia-smi sampler (always) and optionally
`nsys profile` (`CAPTURE_NSYS=1`) around an arbitrary command, and emits a
`capture_meta.json` with host, Slurm job id, timestamps, command, and exit
code.

```bash
srun --jobid=<SLURM_JOB_ID> --overlap --pty bash
# inside the compute shell:
bash profiling/scripts/capture_around.sh profiling/traces/pe_baseline_$(date +%s) \
    -- bash scripts/run_experiment.sh configs/example_baseline.env
```

Do not wrap `sbatch` itself with `capture_around.sh`; that samples the submit
host instead of the compute node. The wrapper should run inside the allocation.

### 4.3 PyTorch Profiler via vLLM

vLLM has built-in `torch.profiler` support. **As of vLLM 0.19.0 the
`VLLM_TORCH_PROFILER_DIR` env var was dropped** and replaced by a
`--profiler-config` CLI flag taking JSON with an absolute path:

```bash
--profiler-config '{"profiler":"torch","torch_profiler_dir":"/abs/path/to/profiling/traces/<run-id>_torch"}'
```

`scripts/run_experiment.sh:783-785` builds this automatically when
`TORCH_PROFILE=1` — the canonical capture route is
`TORCH_PROFILE=1 bash scripts/run_experiment.sh <config>`. For manual
debugging, drive capture with `run_vllm_torch_profile.sh`. Full recipe in
[profiling/README.md#pytorch-profiler-via-vllms-built-in-endpoints](../profiling/README.md#pytorch-profiler-via-vllms-built-in-endpoints);
operational notes in
[insomnia_runbook.md § Debugging: foreground vLLM](insomnia_runbook.md#debugging-foreground-vllm).

### 4.4 Linking profiling outputs to the benchmark's WandB run

Set `BENCHMARK_RUN_DIR` when invoking `capture_around.sh` to point at the
corresponding `benchmarks/cell_<X>/raw/<run-id>/`:

```bash
BENCHMARK_RUN_DIR=benchmarks/cell_Y_plan_execute/raw/$RUN_ID \
    bash profiling/scripts/capture_around.sh profiling/traces/$RUN_ID \
        -- <command>
```

The wrapper calls `log_profiling_to_wandb.py`, which:

1. Parses the WandB run id from the benchmark's `wandb_run_url`
2. Resumes the run via `wandb.init(id=..., resume="allow")`
3. Uploads every file under the profiling dir as a typed Artifact
4. Parses `nvidia_smi.csv` into summary stats (`profiling/gpu_util_{mean,max}`,
   `profiling/gpu_mem_used_mib_{mean,max}`, `profiling/power_draw_w_{mean,max}`, etc.)
5. Stamps `profiling_dir`, `profiling_artifact`, and `profiling_summary`
   back into the benchmark's `meta.json`

Non-fatal on missing `wandb_run_url` or unreachable WandB — artifacts still
land on disk.

---

## 5. Troubleshooting

A symptoms-first decision tree. Each branch points to the doc that
diagnoses it.

| Symptom | Next step |
|---|---|
| `sbatch` returns `ReqNodeNotAvail` or `Priority` forever | [insomnia_runbook.md §"Queue waits"](insomnia_runbook.md) — prefer an off-peak window for evidence runs; use `--gres=gpu:1` only for explicitly hardware-flexible exploratory work |
| Slurm log shows only `Waiting for vLLM server to start...` and vLLM log is 0 bytes | [insomnia_runbook.md §"Debugging: foreground vLLM"](insomnia_runbook.md) — on the current 3.11 / vLLM 0.19 stack this usually means a broken model download, a port conflict, or missing CUDA/cuDNN paths; reproduce in the foreground via `srun --pty` to see the real error |
| `module load cuda/12.3` fails | [insomnia_runbook.md §"CUDA"](insomnia_runbook.md) — module is broken; set `PATH` and `LD_LIBRARY_PATH` directly |
| WandB run doesn't appear under `assetopsbench-smartgrid` | `wandb login` in `.venv-insomnia`, or export `WANDB_API_KEY`; `ENABLE_WANDB=0` suppresses WandB entirely |
| `plan-execute` can't find the AssetOpsBench checkout | Set `AOB_PATH` in the config, or clone AssetOpsBench as a sibling directory of the team checkout |
| HF download fails with 401 / gated-repo error | License not accepted yet at <https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct>, or `HF_TOKEN` not exported |
| Permission denied writing into `logs/` / `benchmarks/` | Shared-dir group-write perms — ask Alex to run `chmod -R g+w` on the write-heavy directories; see the Apr 16 Slack thread |
| `import vllm` warning email from RCS | You're on the login node. Use `srun --pty bash` to grab a compute node first; see [insomnia_runbook.md §"Login node etiquette"](insomnia_runbook.md) |

---

## 6. Related runbooks and pointers

### Infra / profiling / serving (Aaron's lane — `#49`)

**Paper-bound 1-page fact pack** (model IDs + version pins + canonical run
IDs + known limitations, sized for §3 System Design and the §infra
paragraphs): [infra_profiling_serving_brief.md](infra_profiling_serving_brief.md).

**GCP A100 path** — validated fallback (proven during the 2026-05-03 → 05
Insomnia CVE-fix downtime; now used when Insomnia is unavailable,
queue-saturated, or for preemption-tolerant batching):
[gcp_fallback.md](gcp_fallback.md). Day-to-day shape lives in §3.7
above; this doc has spin-up + instance selection + preemption + artifact
persistence + budget tracking.

**Insomnia cluster ops** (Slurm details, Python/CUDA gotchas, foreground-debug
recipe): [insomnia_runbook.md](insomnia_runbook.md). Still relevant for
the Apr 26-28 captures and for Insomnia returns post-CVE-fix.

**Compute strategy** (which GPU for which phase, Insomnia vs GCP, budget
math): [compute_plan.md](compute_plan.md).

**WandB schema** (canonical field names used in `benchmarks/cell_<X>/config.json`
and `summary.json`, including the new `vllm_extra_args` from PR #129 and
`gpu_type` from PR #145): [wandb_schema.md](wandb_schema.md).

**Lane 2 INT8 + KV-cache decision evidence** (smoke jobs `8979532` /
`8979660`, why `--enable-prefix-caching` ships and `--kv-cache-dtype fp8`
+ INT8 are deferred): [lane2_int8_kv_status.md](lane2_int8_kv_status.md).

**Validation log** (per-canonical-capture run IDs, WandB URLs, artifact
paths, what each run actually proves): [validation_log.md](validation_log.md).

### Eval / scenarios / judge (Akshat / Tanisha lanes)

**Eval harness side** (Akshat's half of the runbook, covers scenario
execution + judge + grading): [eval_harness_readme.md](eval_harness_readme.md).

**Orchestration wiring** (what Plan-Execute / AaT / Hybrid look like today,
and what's still upstream): [orchestration_wiring.md](orchestration_wiring.md).

**Experiment 1 capture plan** (the Direct / MCP-baseline / MCP-optimized
story, dependencies, run sequence): [experiment1_capture_plan.md](experiment1_capture_plan.md).

**Experiment 2 capture plan** (orchestration comparison Y/Z + Self-Ask
ablations): [experiment2_capture_plan.md](experiment2_capture_plan.md).

**PS B (auto-scenario generation) runbook**:
[auto_scenario_generation_runbook.md](auto_scenario_generation_runbook.md).
First inspection-only batch lands at
`data/scenarios/generated/first_review_20260503/`; `#53` validation
rubric application owns the official quality call.

### Historical

The earlier combined `Insomnia or GCP Environment.md` draft lived in an
earlier branch but was superseded by `insomnia_runbook.md` + this runbook.
