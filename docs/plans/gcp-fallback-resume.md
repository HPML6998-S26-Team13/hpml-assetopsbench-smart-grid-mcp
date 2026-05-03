# Plan: harden GCP fallback resume and artifact recovery

*Plan for Alex Xin (eggrollofchaos). Companion spec at
[gcp-fallback-resume_spec.md](gcp-fallback-resume_spec.md).*

## Origin

This plan was triggered by the May 2-3, 2026 GCP fallback shakedown for Issue
#91, after Insomnia's seven-job PE/context-window closeout queue stayed pending
for roughly a day and the GCP L4 lane produced six clean 6/6 captures plus one
terminal model/tool partial. The first A100 Spot attempt then proved both sides
of the fallback story: a Spot preemption stopped the VM during vLLM warmup, but
the retained boot disk preserved the runtime, model cache, and partial run
state. The seed artifacts are Issue #91, `docs/gcp_fallback.md`, the local A100
batch manifest `logs/gcp_a100_context_20260503T063343Z_manifest.tsv`, and the
GCP provenance patch in `scripts/run_experiment.sh`. Backlog lineage is Issue
#91's planned work: auto-resume / skip completed trial files, recovery when a
disk is zonal but capacity moves elsewhere, zone/region fallback, artifact
return, and cleanup audit. Reference context is `docs/gcp_fallback.md`,
`docs/insomnia_runbook.md`, `docs/validation_log.md`, and the current
benchmark artifact contract in `benchmarks/README.md`.

## Goals

1. Make `scripts/run_experiment.sh` safely resumable for preempted GCP captures
   without changing the default clean-start behavior.
2. Add a canonical GCP context-batch launcher that can restart the seven-row
   cohort and skip rows/trials that already completed.
3. Make judge scoring idempotent so restart or artifact-pull workflows do not
   duplicate `(run_name, scenario_id, trial_index)` rows.
4. Define the cross-zone/cross-region recovery path for retained disks,
   snapshots, and artifact return to the local/team canonical repo.
5. Preserve current evidence semantics: a completed failed model trajectory is
   evidence and must not be silently rerun into a success.

## Non-Goals

- Do not replace Insomnia as the canonical preferred runtime. GCP remains a
  fallback lane.
- Do not rebuild a full generic cloud orchestrator for this repo. Reuse the
  small, battle-tested patterns we need: manifest/status files, heartbeat,
  preemption detection, restart arguments, and artifact pull/merge behavior.
- Do not make GCS mandatory for the current no-external-IP/IAP VM workflow.
  Persistent boot disk plus IAP SCP is enough for the immediate paper deadline;
  GCS remains an optional durability layer.
- Do not rerun completed terminal failures by default. Rerun only missing,
  invalid, or incomplete trials unless an operator explicitly forces a clean
  rerun.

## Design Summary

Resume is keyed by stable run identity and deterministic trial identity, not by
process lifetime. A GCP restart reuses a `SMARTGRID_RUN_ID`, enters the same
`benchmarks/cell_*/raw/<run-id>` directory, inventories existing
`*_runNN.json` files, verifies that each terminal trial has a matching latency
record, and only executes missing or incomplete trials.

The implementation should keep the shell runner thin. Any JSON validation,
latency-row dedupe, and manifest manipulation should move into a testable Python
helper so the next agent can add unit tests without launching vLLM or touching
GCP.

## Phases

### Phase 0 - Protect the Live A100 Run

The current A100 batch is operator-owned by the runner agent. The build agent
must not kill the `a100_batch` tmux session, stop the A100 VM, overwrite
`logs/run_a100_batch.sh`, or change files on the VM without explicit handoff
from the runner.

Acceptance gate: runner confirms whether the current A100 batch is still active,
preempted, or complete before any deployment to that VM.

### Phase 1 - Resumable Trial Semantics

Add explicit resume knobs to `scripts/run_experiment.sh`:

- `SMARTGRID_RUN_ID`: optional full run ID override. Required for restart-safe
  GCP relaunches.
- `SMARTGRID_RESUME=1`: inventory existing run-dir contents and skip completed
  terminal trials.
- `SMARTGRID_FORCE_RERUN=1`: ignore existing trial artifacts and rerun.
- `SMARTGRID_RESUME_REQUIRE_LATENCY=1` by default: a trial is complete only when
  the JSON is valid and the matching latency row exists.

Completion definition:

- `complete_success`: valid terminal JSON, postprocessed scenario payload,
  explicit or derivable `success=true`, latency row present.
- `complete_failure`: valid terminal JSON, postprocessed scenario payload,
  explicit or derivable `success=false`, latency row present.
- `incomplete`: missing JSON, zero-byte JSON, invalid JSON, dangling `.stdout`,
  or valid JSON without latency when latency is required.

Acceptance gate: local tests prove completed failures are skipped in resume mode
by the trial-status decision helper without launching a runner. The
`summary.json` accounting proof is a Phase 2 gate because it depends on the
manifest and summary inventory stream.

### Phase 2 - Atomic Trial Writes and Resume Manifest

Make trial output writes preemption-safe:

- Write runner stdout and trial JSON through temporary files in the run dir.
- Atomically rename final JSON into place only after parse/postprocess succeeds.
- Record one JSONL manifest event per trial with state, scenario file, trial
  index, output path, started/finished timestamps, run/skip reason, and return
  code.

Acceptance gate: a synthetic interrupted run with a partial temp/stdout file is
resumed by rerunning only that trial, not by counting it as evidence. The same
fixture proves `summary.json` reports attempted, completed, failed, skipped,
and rerun counts from the merged executed-plus-skipped inventory.

### Phase 3 - Canonical GCP Context Batch Launcher

Replace the ad hoc VM-local batch script with a repo script, for example
`scripts/run_gcp_context_batch.sh`, that:

- Runs the current seven-row cohort in order: Y8, Y32, Y16, YS16, ZS16, D16,
  ZSD16.
- Sets GCP provenance env vars and `SMARTGRID_RESUME=1`.
- Reuses `SMARTGRID_RUN_ID`s from a batch state file on restart.
- Writes a batch manifest with label, config, run dir, run rc, judge rc,
  started/finished timestamps, and provider/hardware fields.
- Judges each successful or partial terminal run once.

Acceptance gate: the launcher can be killed after Y8, restarted, and it skips
Y8 while continuing at Y32.

### Phase 4 - Idempotent Judge and Score Merge

Make scoring restart-safe:

- Add a `--skip-existing` or equivalent resume mode to
  `scripts/judge_trajectory.py`, or add a small score-merge helper that filters
  duplicate rows by `(run_name, scenario_id, trial_index, judge_model)`.
- Ensure GCP artifact pullback appends only new score rows to the local
  `results/metrics/scenario_scores.jsonl`.
- Preserve judge logs under `results/judge_logs/<run_name>/` and treat existing
  logs as reusable unless `--force` is supplied.

Acceptance gate: running judge twice on the same run dir leaves score-row counts
unchanged unless forced.

### Phase 5 - Artifact Pullback and Disk Recovery

Add the operator path for getting data back:

- Pull raw run dirs, batch logs, judge logs, and score rows from a no-external-IP
  VM over IAP.
- Merge score rows locally with dedupe.
- Pull small manifests/logs before raw run dirs, and expose a bounded
  parallelism knob for larger artifact trees so IAP tunnel throughput or
  terminal timeouts do not hide partial pull failures.
- Stop the VM after artifact pullback; retain disk only while it is still useful.
- Document the zonal-disk boundary: same-zone restart is cheapest; if the zone
  is full, either attach the disk to a same-zone helper VM to copy artifacts, or
  snapshot the boot disk and create a new disk/VM in the target zone or region.

Acceptance gate: docs and helper commands cover same-zone restart, same-zone
helper attach, snapshot-to-new-zone, and local artifact pullback.

### Phase 6 - Zone/Region and Quota Ladder

Codify the operational ladder already discovered live:

- Try other zones in the same region before crossing regions.
- Try each in-region zone with bounded retries and backoff before crossing
  regions, and record why each zone was skipped.
- Check regional GPU quota and `GPUS_ALL_REGIONS` before create attempts.
- For A100, distinguish standard quota from Spot/preemptible quota.
- Keep `autoDelete=false` for capture VM boot disks by default.
- Have the launcher or preflight fail loudly when the active capture VM boot
  disk is still set to auto-delete.
- Record capacity/stockout/preemption outcomes in Issue #91 and the GCP runbook.

Acceptance gate: one command or documented checklist produces the next VM-create
attempt order and the reason a region/zone was skipped.

## Verification

Run these without GPUs:

```bash
bash -n scripts/run_experiment.sh scripts/run_gcp_context_batch.sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q \
  tests/test_run_experiment_summary.py \
  tests/test_gcp_resume_state.py
DRY_RUN=1 SMARTGRID_RESUME=1 SMARTGRID_RUN_ID=resume-smoke \
  bash scripts/run_experiment.sh configs/context_ablation/pe_m_8192.env
```

Run these only on the GCP VM or another approved GPU node:

```bash
SMARTGRID_RUN_ID=<existing-y8-run-id> SMARTGRID_RESUME=1 \
  bash scripts/run_experiment.sh configs/context_ablation/pe_m_8192.env

bash scripts/run_gcp_context_batch.sh --resume-batch <batch-id>
```

Expected proof:

- Existing completed trials are skipped and logged as skipped.
- Missing/incomplete trials rerun.
- `summary.json` counts skipped terminal failures as failures, not as passes.
- `latencies.jsonl` has no duplicate scenario/trial rows.
- judge score rows are deduped.

## Implementation-Ready Checklist

### Phase 1-2: Runner Resume Core

- [ ] `scripts/run_experiment.sh`
  - **Task:** Add `SMARTGRID_RUN_ID`, `SMARTGRID_RESUME`,
    `SMARTGRID_FORCE_RERUN`, and `SMARTGRID_RESUME_REQUIRE_LATENCY`; use the
    Python helper for trial status and latency-row writes; skip completed
    trials in resume mode; write atomic temp outputs before final rename.
  - **Acceptance:** a local synthetic run dir with one complete success, one
    complete failure, and one partial stdout causes exactly two skips and one
    rerun; summary counts match terminal JSON state.

- [ ] `scripts/gcp_resume_state.py`
  - **Task:** New testable helper for trial identity resolution, valid JSON
    detection, latency-row lookup/dedupe, manifest event writes, and summary
    inventory support.
  - **Acceptance:** unit tests cover complete success, complete failure,
    missing latency, invalid JSON, dangling stdout, duplicate latency rows, and
    date-prefix changes across restarts.

- [ ] `tests/test_gcp_resume_state.py`
  - **Task:** Cover the Python helper with temporary run dirs and JSONL sidecars.
  - **Acceptance:** tests pass without importing torch, vLLM, or external SDKs.

- [ ] `tests/test_run_experiment_summary.py`
  - **Task:** Extend the existing summary-generation tests for resume-mode
    fields (`resume_skipped_count`, `resume_rerun_count`) and partial/failure
    status semantics.
  - **Acceptance:** summary tests prove skipped terminal failures remain counted
    as failures and skipped successful trials remain counted as completed.

### Phase 3: GCP Batch Launcher

- [ ] `scripts/run_gcp_context_batch.sh`
  - **Task:** Add canonical seven-row GCP batch launcher with restart-safe batch
    state, GCP provenance env, compiler/runtime preflight, resume mode, per-row
    judge, retained-disk auto-delete preflight, and TSV/JSON manifest.
  - **Acceptance:** shellcheck/bash syntax passes; dry-run mode writes stable
    batch state; restart after a completed mock row skips that row.

- [ ] `configs/gcp_context_closeout.tsv`
  - **Task:** Store the row label/config mapping consumed by the batch launcher
    instead of hard-coding arrays in multiple places.
  - **Acceptance:** launcher rejects unknown labels and fails fast if any config
    path is missing.

### Phase 4: Judge and Score Dedupe

- [ ] `scripts/judge_trajectory.py`
  - **Task:** Add idempotent `--skip-existing` behavior keyed by
    `(run_name, scenario_id, trial_index, judge_model)` or delegate that
    filtering to a shared helper.
  - **Acceptance:** rerunning judge on the same run dir does not append
    duplicates by default.

- [ ] `tests/test_judge_trajectory.py`
  - **Task:** Add focused tests for duplicate score-row detection and forced
    rejudge behavior.
  - **Acceptance:** test uses local temp JSONL files and does not call WatsonX.

### Phase 5-6: Artifact Recovery and Docs

- [ ] `scripts/gcp_pull_context_artifacts.sh`
  - **Task:** Pull run dirs/logs/judge logs from a no-external-IP VM over IAP,
    stage remote score rows to a temp file, merge only new rows locally, and
    expose a bounded parallelism flag for larger artifact trees.
  - **Acceptance:** dry-run prints the exact gcloud scp commands; merge mode
    dedupes a fixture score file.

- [ ] `docs/gcp_fallback.md`
  - **Task:** Document resume flags, batch launcher, A100 Spot behavior,
    `autoDelete=false`, same-zone restart, snapshot/cross-region recovery, and
    artifact pullback.
  - **Acceptance:** runbook has one clear operator path for preemption,
    stockout, cross-region move, and final cleanup.

- [ ] `docs/validation_log.md`
  - **Task:** After the A100 batch finishes, record the A100 run IDs, provider,
    zone, hardware, run statuses, and judge outcomes.
  - **Acceptance:** validation evidence distinguishes Insomnia, L4, and A100
    captures by provider/hardware metadata.

- [ ] `CHANGELOG.md`
  - **Task:** Add one bullet for resumable GCP fallback execution and one bullet
    for idempotent GCP artifact/judge recovery.
  - **Acceptance:** changelog names behavior, not private tooling.
