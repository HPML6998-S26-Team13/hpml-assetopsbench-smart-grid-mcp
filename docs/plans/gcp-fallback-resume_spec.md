# Spec: GCP fallback resume and artifact recovery

Companion to [gcp-fallback-resume.md](gcp-fallback-resume.md).

## Operating Model

There are two cooperating roles:

- **Runner agent:** owns live cloud resources, monitors active captures, decides
  whether to restart/stop/move a VM, and pulls artifacts after completion.
- **Build agent:** implements repo changes and tests. It must not mutate live VM
  state unless the runner hands over that specific action.

This split matters because a working A100 batch can be more valuable than a tidy
deployment. Code should land locally first, then the runner decides whether it is
worth copying to the active VM.

## Resume Contract

### Inputs

`scripts/run_experiment.sh` should accept:

| Env var | Default | Meaning |
|---|---|---|
| `SMARTGRID_RUN_ID` | unset | Full run ID to use instead of `${SLURM_JOB_ID:-local-...}_${EXPERIMENT_NAME}`. |
| `SMARTGRID_RESUME` | `0` | When `1`, inventory existing trial artifacts and skip terminal completed trials. |
| `SMARTGRID_FORCE_RERUN` | `0` | When `1`, ignore existing artifacts and rerun all trials. |
| `SMARTGRID_RESUME_REQUIRE_LATENCY` | `1` | Require matching latency row before a trial is considered complete. |
| `SMARTGRID_BATCH_ID` | unset | Optional outer GCP batch id for manifest grouping. |

Default behavior must remain clean-start compatible with Insomnia Slurm jobs.

### Trial Identity

Canonical identity is:

```text
(scenario_file, scenario_basename, trial_index)
```

The current filename contains a date prefix via `RUN_BASENAME`. Resume must not
depend on that date prefix. If an old completed file matches:

```text
*_<scenario_basename>_runNN.json
```

then resume should reuse that path instead of creating a new date-prefixed file.
Only create a new path when no terminal file for that scenario/trial exists.

### Terminal Trial Definition

A terminal trial JSON is valid when:

1. The file exists and is non-empty.
2. It parses as a JSON object.
3. It either already has `scenario`, or can be postprocessed with the scenario
   payload.
4. `success` is a bool or can be derived from history/trajectory/answer using
   the same precedence as the existing runner.
5. If `SMARTGRID_RESUME_REQUIRE_LATENCY=1`, `latencies.jsonl` contains exactly
   one matching row for that scenario/trial/output path, or a row can be safely
   repaired from a stored manifest event.

Both `success=true` and `success=false` are terminal. A failed terminal
trajectory is not an incomplete trial.

### Incomplete Artifacts

Treat these as incomplete:

- missing trial JSON;
- zero-byte trial JSON;
- invalid JSON;
- dangling `.stdout` without a sibling valid terminal JSON;
- `.tmp` files;
- valid JSON with no latency row when latency is required;
- duplicate conflicting latency rows;
- output JSON whose scenario/trial identity conflicts with the expected loop
  identity.

Incomplete artifacts should be preserved for diagnosis and recorded in
`resume_manifest.jsonl` with `state: "incomplete"`. File renames such as
`.incomplete.<timestamp>` are optional operator visibility aids; the manifest
event is the source of truth.

A legacy `.stdout` file beside a valid terminal JSON is not incomplete by
itself. Older runner captures wrote `.stdout` non-atomically, so the resume
helper should classify the JSON/latency pair first and only treat stdout as
dangling when no valid terminal JSON exists for that trial.

## Atomicity

The trial write path should avoid counting half-written files after preemption.
Recommended sequence:

1. Runner writes raw stdout to `${TRIAL_OUT}.stdout.tmp`.
2. JSON extractor writes `${TRIAL_OUT}.tmp`.
3. Postprocess scenario/success into `${TRIAL_OUT}.tmp`.
4. `mv "${TRIAL_OUT}.tmp" "$TRIAL_OUT"` atomically.
5. Append/replace one latency row for the trial.
6. Append manifest event `complete_success` or `complete_failure`.

If preemption lands before step 4, the trial is incomplete. If it lands after
step 4 but before step 5, the default latency-required policy reruns the trial
so latency evidence stays usable for the paper. When the pre-latency output is
recoverable, the manifest should record its content hash and the replacement
output hash, plus `divergent: true|false|unknown`, so cross-VM or post-upgrade
reruns remain auditable instead of implying deterministic replay.

## Summary Semantics

`summary.json` should report:

- `scenarios_attempted`: expected scenario x trial count, including skipped
  completed trials.
- `scenarios_completed`: terminal trials whose success is true.
- `failure_count`: terminal trials whose success is false plus missing trials
  that remain after the run.
- `resume_skipped_count`: number of terminal trials skipped because resume mode
  found prior artifacts.
- `resume_rerun_count`: number of incomplete trials rerun.
- `run_status`: `success` if no failures, `partial` if at least one pass and at
  least one failure, `failed` if no passes.

Latency aggregates should be computed from available numeric latency rows only.
Do not synthesize fake latency for skipped trials.

## Manifest Schema

Per-run manifest: `benchmarks/cell_*/raw/<run-id>/resume_manifest.jsonl`.

Recommended fields:

```json
{
  "schema_version": 1,
  "batch_id": "a100_context_20260503T063343Z",
  "run_name": "local-...",
  "event": "trial_complete",
  "state": "complete_success",
  "scenario_file": "data/scenarios/multi_01_end_to_end_fault_response.json",
  "scenario_basename": "multi_01_end_to_end_fault_response",
  "trial_index": 1,
  "output_path": "benchmarks/...run01.json",
  "latency_seconds": 82.4,
  "return_code": 0,
  "started_at": "2026-05-03T06:33:55Z",
  "finished_at": "2026-05-03T06:35:25Z",
  "compute_provider": "gcp",
  "compute_zone": "us-central1-a",
  "compute_instance": "smartgrid-a100-spot-20260503-0217",
  "gpu_type": "NVIDIA A100-SXM4-40GB"
}
```

Outer batch manifest: `logs/gcp_<batch-id>_manifest.tsv` and optional
`logs/gcp_<batch-id>_manifest.jsonl`.

The TSV is for quick shell reading. JSONL is for reliable tooling.

## Judge Idempotency

Score-row identity:

```text
(run_name, scenario_id, trial_index, judge_model, judge_prompt_version)
```

Default rejudge behavior should skip existing identities. Score rows should
carry `judge_prompt_version` so a stricter rubric or prompt update can coexist
with the same `judge_model` name. Forced behavior should append replacement rows
only if the output path or judge config changed, or it should write to a temp
file and replace rows atomically.

Never merge a remote VM `scenario_scores.jsonl` wholesale into local results
without filtering by the batch run names and deduping identities.

## Artifact Return

Minimum pull set for each terminal GCP batch:

- batch logs: `logs/gcp_<batch-id>*`;
- batch launcher used: `logs/run_a100_batch.sh` or the canonical repo launcher;
- raw run dirs from the batch manifest;
- `results/judge_logs/<run_name>/`;
- filtered score rows for run names in the batch manifest;
- any VM-local setup manifest that records model revision, AOB snapshot, Python,
  torch, vLLM, CUDA driver, compiler, zone, and GPU.

The canonical source of truth stays the local/team repo. The VM is a worker and
cache, not the final archive.

## Disk and Region Recovery

Persistent disks are zonal. Recovery options in preference order:

1. **Same VM restart:** cheapest and fastest when Spot capacity returns.
2. **Same-zone helper VM:** if GPU capacity is full but CPU capacity exists,
   attach the retained disk read-only or read-write to a CPU helper and copy
   artifacts out.
3. **Snapshot to new zone/region:** create a snapshot from the boot disk, create
   a new disk from that snapshot in the target zone, then create a new VM.
4. **Local/GCS artifact-first recovery:** if the run has already been pulled
   back, recreate from the canonical repo plus model cache instead of moving
   the disk.

Do not assume `autoDelete=false` makes cross-region recovery automatic. It only
prevents the disk from disappearing when the VM is stopped/deleted.

## Preemption and Health

The immediate deadline path can rely on retained disk plus manual restart, but
the implementation should leave room for:

- metadata polling of `instance/preempted`;
- a heartbeat JSON that records current row/scenario/trial;
- status markers such as `RUNNING`, `PREEMPTED`, `FINISHED`, `FAILED`;
- restart config with the same batch id and same run IDs;
- stale heartbeat detection.

These are proven patterns in our local cloud helper code. The public contract in
this repo is the artifact/status shape, not the private implementation lineage.

## Compiler and Runtime Preflight

Every GCP GPU capture launcher should check:

- `nvidia-smi` sees exactly one expected GPU;
- Python is 3.11 through `.venv-insomnia`;
- `torch.cuda.is_available()` is true;
- `vllm` imports;
- `g++` and `cc1plus` exist for FlashInfer JIT;
- `HF_TOKEN`, `WANDB_API_KEY` when enabled, and WatsonX judge credentials when
  judging are present through `.env` or environment;
- model paths exist for FP16 and INT8 configs;
- AOB sibling snapshot exists and is the intended commit/branch.

Fail before launching vLLM when any of these are missing.

## Open Decisions

1. Whether to make `SMARTGRID_RESUME_REQUIRE_LATENCY=1` permanently strict or
   allow a deadline override that skips completed JSON even without latency.
2. Whether to introduce optional GCS artifact staging now or keep IAP SCP only
   until after May 6.
3. Whether A100 evidence should become a separate validation-log section or a
   hardware-comparison subsection under the L4 GCP fallback closeout.
4. Whether the seven-row context cohort should remain a hard-coded TSV or be
   generated from the experiment matrix once the matrix is fully canonical.
