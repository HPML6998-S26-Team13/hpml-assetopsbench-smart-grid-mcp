# GCP Fallback Setup

*Last updated: 2026-04-18*
*Owner: Aaron Fan (af3623)*

Emergency fallback path for the compute plan's "GCP as backup" lane. Use this
when Insomnia is unavailable, the `edu` queue is saturated near a deadline,
or a job genuinely needs longer than the 12-hour cluster walltime.

**This is a mechanically complete runbook but has not yet been end-to-end
validated with a real benchmark run.** Treat the first GCP execution as a
shakedown and update this doc with anything that surprises you.

See [compute_plan.md](compute_plan.md) §2 for the strategic rationale
(Insomnia-first, GCP as insurance); this doc is the tactical how-to.

## 1. When to actually use GCP

Default to Insomnia. Spend credits only when one of these is true:

| Trigger | Example |
|---|---|
| **Insomnia unavailable** | Cluster maintenance window, RCS outage, or login node failures lasting >2 hours near a deadline |
| **Deadline + saturated queue** | `squeue --start` shows your job ~24+ hours out and a deliverable is due sooner |
| **Walltime > 12 hours** | A scenario sweep that can't fit in a single `short` allocation and can't be chunked |
| **Judge model > 34 GB** | Maverick-17B via WatsonX usually handles this, but if WatsonX quotas bite, A100-80GB is the cheapest local path |

**If none of the above apply, stay on Insomnia.** The team budget is $2,000
total ($500 per member). At spot pricing on A100-40GB (~$1.81/hr), that's
~1,100 GPU-hours — enough for the whole project, but only if we don't burn
it on work Insomnia handles fine.

## 2. Credit / account prerequisites

Each team member had $500 GCP credits issued at project start. Before your
first use:

1. Confirm your credit balance at
   <https://console.cloud.google.com/billing> — look for the "Education"
   credits line item. If it's expired or missing, email
   [cloud-billing@columbia.edu](mailto:cloud-billing@columbia.edu).
2. Enable the required APIs on your GCP project:
   ```bash
   gcloud services enable compute.googleapis.com
   gcloud services enable storage.googleapis.com
   ```
3. Request an **A100 GPU quota** for the region you'll use. A100s are a
   quota-restricted resource and the default is zero. For us-central1 / us-west1:
   - Console → IAM & Admin → Quotas
   - Filter on `NVIDIA A100 80GB GPUs` (or `NVIDIA A100 GPUs` for 40GB) and
     `Preemptible NVIDIA A100 GPUs` for spot access
   - Request 1 GPU in your primary region (takes 1-48 hours to approve)
4. Set up `gcloud` CLI locally:
   ```bash
   gcloud auth login
   gcloud config set project <your-project-id>
   gcloud config set compute/zone us-central1-a
   ```
   If quota is only approved in a different zone, use that zone instead.

## 3. Instance selection

Default picks from [compute_plan.md](compute_plan.md):

| Instance | GPU | VRAM | Spot $/hr | On-demand $/hr | Good for |
|---|---|---|---|---|---|
| `a2-highgpu-1g` | 1× A100 | 40 GB | ~$1.81 | ~$3.67 | Llama-3.1-8B serving + profiling (matches Insomnia A6000 envelope) |
| `a2-ultragpu-1g` | 1× A100 | 80 GB | ~$2.50 | ~$5.07 | Judge model (Maverick-17B) or room for larger batch / KV cache experiments |

**Spot vs on-demand:** spot is ~50% cheaper but can be preempted with 30s
notice. Acceptable for short profiling runs, risky for a full cell capture
(3 trials × 30 scenarios × 2 min ≈ 3 hrs exposed to preemption). For
critical captures use on-demand or checkpoint between trials.

## 4. Spin up an instance

```bash
export PROJECT=<your-gcp-project-id>
export ZONE=us-central1-a
export INSTANCE=smartgrid-bench-$(date +%Y%m%d-%H%M)

gcloud compute instances create "$INSTANCE" \
    --project="$PROJECT" \
    --zone="$ZONE" \
    --machine-type=a2-highgpu-1g \
    --accelerator=type=nvidia-tesla-a100,count=1 \
    --image-family=common-cu124-debian-11 \
    --image-project=deeplearning-platform-release \
    --boot-disk-size=200GB \
    --boot-disk-type=pd-ssd \
    --maintenance-policy=TERMINATE \
    --metadata="install-nvidia-driver=True" \
    --provisioning-model=SPOT \
    --instance-termination-action=DELETE
```

Flag breakdown:

- `a2-highgpu-1g` + `nvidia-tesla-a100` — the 40GB A100 SKU
- `common-cu124-debian-11` — Deep Learning VM image, CUDA 12.4 preinstalled
  (close enough to Insomnia's 12.9 for our vLLM pin)
- `--boot-disk-size=200GB` — the DL image is ~50GB, leaves ~150GB for model
  weights (16GB) + benchmark outputs + profiling traces
- `--provisioning-model=SPOT` — drop to `STANDARD` for on-demand if you need
  preemption immunity
- `--instance-termination-action=DELETE` — auto-clean spot instances to
  avoid accidentally leaving one running overnight on credits

For the **80GB judge-model variant**, swap `a2-ultragpu-1g` + `count=1` on
the same accelerator type (the accelerator type name is the same — GCP
distinguishes by machine type).

## 5. Connect and verify

```bash
gcloud compute ssh "$INSTANCE" --project="$PROJECT" --zone="$ZONE"

# Inside the instance:
nvidia-smi                                # confirm A100 + driver
python3 --version                         # 3.10+; DL image default is 3.10
pip --version
```

If `nvidia-smi` returns "command not found", the driver install is still
running; wait ~3 minutes and try again. The DL VM metadata script handles it.

## 6. Environment setup

The Insomnia venv isn't transferable (NFS paths baked into vLLM's cache).
Recreate on GCP. Two options — pick based on urgency.

### 6a. Fast path: reuse `scripts/setup_insomnia.sh`

```bash
# On the GCP instance
git clone https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp.git
cd hpml-assetopsbench-smart-grid-mcp
export HF_TOKEN=hf_yourtokenhere
export MODEL_REVISION=$(cat .model_revision 2>/dev/null || echo 0e9e39f249a16976918f6564b8830bc894c89659)
bash scripts/setup_insomnia.sh
```

The script uses `uv venv --python 3.11` and pins the same versions in
`requirements-insomnia.txt`. The `.venv-insomnia` name is fine on GCP —
it's just a directory name — and keeps script paths identical to Insomnia.
Takes ~15-30 min for the first setup (torch + vLLM wheels + model
download).

### 6b. Faster (but fragile) path: gsutil-based weight transfer

If you've previously uploaded the model to a GCS bucket:

```bash
mkdir -p models
gsutil -m cp -r gs://<team-bucket>/models/Llama-3.1-8B-Instruct \
    models/
```

Still need the venv, but you skip the ~16GB HF download (~5-10 min saved).
The team bucket doesn't exist yet; skip this path until somebody stands it
up and documents the bucket URL here.

### 6c. Smoke test

Same as the Insomnia smoke test from [runbook.md](runbook.md) §2:

```bash
source .venv-insomnia/bin/activate
python -c "import vllm; print(vllm.__version__)"
```

## 7. Running a benchmark on GCP

`scripts/run_experiment.sh` is Slurm-aware but not Slurm-dependent. When no
`$SLURM_*` env vars are set, it falls back to a local run ID (see
`REPO_ROOT` resolution in the script). Run directly:

```bash
bash scripts/run_experiment.sh configs/example_baseline.env
```

No Slurm header is read because we're not running under `sbatch`. The script
launches vLLM in the background, waits for `/health`, runs the scenarios,
and writes the same `benchmarks/cell_<X>/raw/<run-id>/` layout.

Because there's no queue on GCP, you can run cells back-to-back. The time
budget becomes a cost question, not a scheduler one.

Run provenance should be explicit when GCP artifacts enter the matrix. Current
summaries stamp `host_name`, `gpu_type`, `slurm_job_id`, `git_sha`,
`git_branch`, and `git_dirty`. Interpret GCP captures as `slurm_job_id=null`
with a `smartgrid-*` host and `gpu_type` such as `NVIDIA A100-SXM4-40GB`
or `NVIDIA L4`; Insomnia captures
have numeric Slurm IDs and `ins###` hosts. Matrix rows should record the
hardware/provider as separate row metadata or in an adjacent provenance column,
not silently overwrite an Insomnia row with a GCP run.

### Resumable GCP runs

Use a stable run ID for any preemption-prone GCP capture:

```bash
SMARTGRID_RUN_ID=<stable-run-id> SMARTGRID_RESUME=1 \
  bash scripts/run_experiment.sh configs/context_ablation/pe_m_8192.env
```

Resume mode inventories the existing run directory, skips terminal success and
terminal failure JSONs that already have matching latency rows, reruns missing
or incomplete trials, and appends trial decisions to
`resume_manifest.jsonl`. Keep `SMARTGRID_RESUME_REQUIRE_LATENCY=1` for
benchmark captures. Set `SMARTGRID_FORCE_RERUN=1` only when intentionally
discarding prior evidence.

For the May 2026 context closeout cohort, use the canonical batch wrapper:

```bash
SMARTGRID_COMPUTE_PROVIDER=gcp \
SMARTGRID_COMPUTE_ZONE="$ZONE" \
SMARTGRID_COMPUTE_INSTANCE="$INSTANCE" \
  bash scripts/run_gcp_context_batch.sh --resume-batch <batch-id>
```

The wrapper reads `configs/gcp_context_closeout.tsv`, writes
`logs/gcp_<batch-id>_state.tsv` plus TSV/JSONL manifests, reuses stable row run
IDs, skips rows already marked complete, and judges rows idempotently.

### Profiling works unchanged

```bash
BENCHMARK_RUN_DIR=benchmarks/cell_<X>/raw/<run-id> \
    bash profiling/scripts/capture_around.sh profiling/traces/<run-id> \
        -- <command>
```

nvidia-smi + nsys + vLLM's torch profiler all behave identically to
Insomnia.

## 8. Persisting artifacts off the instance

Before shutting down, copy benchmark outputs back to the local Mac or a shared
bucket. The default should be: **pull from GCP over IAP, inspect locally, commit
locally, then push to `team13` from the trusted local checkout.** Avoid putting
GitHub credentials on a transient VM unless the deadline leaves no better
option.

```bash
# From the local Mac, after the run finishes:
export PROJECT=fleet-garage-490218-c8
export ZONE=us-central1-a
export INSTANCE=smartgrid-a100-YYYYMMDD-HHMM
export LOCAL_REPO=/Users/wax/coding/hpml-assetopsbench-smart-grid-mcp

gcloud compute scp --project="$PROJECT" --zone="$ZONE" --tunnel-through-iap \
    --recurse \
    "$INSTANCE:~/hpml-assetopsbench-smart-grid-mcp/benchmarks/cell_<X>/raw/<run-id>" \
    "$LOCAL_REPO/benchmarks/cell_<X>/raw/"

# Then commit from the local repo/worktree after inspection.
cd "$LOCAL_REPO"
git status --porcelain --branch
git add benchmarks/cell_<X>/raw/<run-id>/
git commit -m "Add Cell <X> raw artifacts from GCP run <run-id>"
git push team13 HEAD:<branch>
```

For a context-batch pullback, prefer the helper because it copies small manifests
first, stages remote judge rows separately, dedupes local score rows, and bounds
larger raw-directory copies:

```bash
bash scripts/gcp_pull_context_artifacts.sh \
  --instance "$INSTANCE" \
  --zone "$ZONE" \
  --batch-id <batch-id> \
  --parallel 2
```

Direct `git push` from the VM is possible, but it requires installing a GitHub
token or SSH key on the VM. If you choose that path, push a feature branch only,
remove the credential afterward, and check shell history before deleting or
reusing the disk.

```bash
# On the VM only when direct push is intentionally chosen:
cd hpml-assetopsbench-smart-grid-mcp
git add benchmarks/cell_<X>/raw/<run-id>/
git commit -m "Add Cell <X> raw artifacts from GCP run <run-id>"
git push origin <branch>
```

Profiling traces are larger and gitignored; use GCS or `gcloud compute scp`
instead of git:

```bash
gsutil -m cp -r profiling/traces/<run-id>/ \
    gs://<team-bucket>/profiling/traces/<run-id>/
```

Set this up with a shutdown trap so you never lose data:

```bash
# In ~/.bashrc on the GCP instance
trap 'cd ~/hpml-assetopsbench-smart-grid-mcp && git push || echo "MANUAL PUSH NEEDED"' EXIT
```

## 9. Shut down and reclaim credits

**Always delete the instance when done.** A spot A100-40GB left running for
24 hours accidentally costs ~$43, or ~9% of one person's budget.

```bash
gcloud compute instances delete "$INSTANCE" \
    --project="$PROJECT" --zone="$ZONE" --quiet
```

Or from the console: Compute Engine → VM instances → select → Delete.

Verify nothing lingers:

```bash
gcloud compute instances list --project="$PROJECT"
gcloud compute disks list --project="$PROJECT"   # persistent disks can outlive instances
```

Boot disks are normally deleted with the instance when
`--instance-termination-action=DELETE` is set, but double-check. An idle
200GB pd-ssd costs ~$34/month if you forget it.

## 10. Spot preemption handling

When a spot instance is about to be reclaimed, GCP signals via the metadata
server and gives you ~30 seconds before `SIGTERM`. A production-grade run
would add a metadata preemption watcher and shutdown hook. For our current
deadline path, the practical mitigation is:

1. **Prefer on-demand for canonical captures.** Spot is fine for setup and
   shakedowns; on-demand avoids restarting vLLM and repeating a partially run
   cell.
2. **Let persistent disk bound the loss, then resume with a stable run ID.** The
   runner writes one JSON per scenario × trial incrementally. Completed trial
   files survive on disk, and `SMARTGRID_RESUME=1` skips terminal successes and
   terminal failures when their latency rows are present.
3. **Treat the in-flight trial as suspect.** Delete or rerun the trial whose
   JSON/latency record was being written at preemption time; completed earlier
   trial JSONs should be recoverable.
4. **If capacity is unavailable on restart, keep the disk.** You can attach the
   zonal persistent disk to another VM in the same zone, or snapshot it if you
   need to move zones:
   ```bash
   gcloud compute disks snapshot "$DISK" \
       --project="$PROJECT" --zone="$OLD_ZONE" \
       --snapshot-names="$DISK-$(date +%Y%m%d-%H%M)"

   gcloud compute disks create "$NEW_DISK" \
       --project="$PROJECT" --zone="$NEW_ZONE" \
       --source-snapshot="$SNAPSHOT" \
       --type=pd-ssd
   ```
   Cross-region resume is artifact-first: copy completed run directories back to
   the local Mac or GCS, recreate a VM in the stocked region, restore artifacts,
   then resume with the same `SMARTGRID_RUN_ID`.

Tracked hardening items live in GitHub Issue #91. The implemented safe path now
covers resume/skip, same-zone restart, snapshot-to-new-zone recovery, and
artifact return over IAP. Remaining production-hardening items:

- A launcher/helper that tries zones first, then regions, and writes the chosen
  project/zone/instance/run directory into a handoff file.
- A cleanup/audit helper that lists instances, disks, snapshots, routers/NATs,
  static IPs, and active quota preferences before the fallback lane is closed.

## 11. Budget tracking

Rough hourly burn at current spot pricing:

| Workload | Instance | $/hour | Typical session |
|---|---|---|---|
| Llama-3.1-8B serving + single cell capture | `a2-highgpu-1g` spot | $1.81 | 1-3 hours = $2-$6 |
| Same, on-demand (no preemption risk) | `a2-highgpu-1g` | $3.67 | $4-$11 |
| Judge model (Maverick-17B) serving | `a2-ultragpu-1g` spot | $2.50 | 30 min batch = $1.25 |
| Full 5-cell grid replay (~15 hr GPU-time) | `a2-highgpu-1g` spot | $1.81 | ~$27 |

At the full-grid cost of ~$27, one person's $500 covers ~18 independent
replays. That's generous margin; the dominant risk is idle instances, not
workload cost.

Monitor spend at
<https://console.cloud.google.com/billing/reports> and set a budget alert at
$100/month as a canary.

## 12. Known differences from Insomnia

Worth noting up front so profiling comparisons don't mislead:

| Factor | Insomnia | GCP A100-40GB |
|---|---|---|
| GPU | A6000 (48 GB, Ampere) | A100 (40 GB, Ampere) |
| Peak FP16 throughput | ~150 TFLOPS | ~312 TFLOPS |
| NVLink | No | Single-GPU so N/A, but available on multi-GPU SKUs |
| CUDA version | 12.9 | 12.4 (DL image default) |
| Filesystem | NFS (`/insomnia001/...`) | Local SSD |
| Shared env | yes (team venv) | per-instance |

**A100 is roughly 2× faster than A6000** on FP16 inference. If you're using
GCP as a fallback during a deadline rush, flag any latency numbers from
there as "GPU-heterogeneous" when comparing to the baseline Insomnia
dataset — don't mix them into the canonical Cell A/B/C captures without a
controls note in the paper.

## 13. TODO / follow-ups

- Shared GCS bucket for model weights + profiling trace storage (§6b, §8)
- Tested end-to-end run on GCP — update this doc with the actual spin-up time,
  first-hit gotchas, and observed vs projected cost
- Reusable startup script that installs the venv + runs a specified config
  automatically, so the whole GCP path becomes one `gcloud` command
- Preemption-resistant artifact-pushing trap (§10) if GCP graduates from
  emergency-only to routine use

## References

- [compute_plan.md](compute_plan.md) §2 — why Insomnia is the default and GCP is insurance
- [runbook.md](runbook.md) — the Insomnia-side runbook, which the GCP path mirrors
- [insomnia_runbook.md](insomnia_runbook.md) — the underlying Insomnia-specific quirks that mostly don't apply on GCP
- [GCP Deep Learning VM images](https://cloud.google.com/deep-learning-vm/docs/images)
- [GCP A100 pricing](https://cloud.google.com/compute/gpus-pricing)
