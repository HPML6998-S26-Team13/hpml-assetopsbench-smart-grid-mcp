---
status: canonical
scope: team-repo
owner: Team 13
canonical: true
---

# Evaluation Harness Runbook (Local Windows + WatsonX)

*Last updated: 2026-05-10. Owns the eval-harness half of issue #67 (runbook); see `docs/runbook.md` for the Insomnia/Slurm + GCP A100 production paths and `docs/content_brief_scenarios_eval.md` for current scenario/eval/judge facts.*

This README is the practical runbook for getting the **AssetOpsBench evaluation harness** running end-to-end on a local Windows machine, then exercising our **Smart Grid scenarios** from `data/scenarios/`.

## What this runbook covers

1. Quick harness smoke test (`plan-execute` + MCP tools + Watsonx)
2. One-command smoke script ([../scripts/run_harness_smoke.cmd](../scripts/run_harness_smoke.cmd))
3. Docker-backed test path for IoT/WO data access (CouchDB)
4. Existing harness end-to-end (`scenario-server` + grading path)
5. Original repo benchmark flow (`benchmark/cods_track1` and `benchmark/cods_track2`)
6. How to test newly-authored Smart Grid scenarios
7. Smart Grid data pipeline notes relevant to benchmark runs
8. Common failure modes and fixes
9. Recommended minimum test matrix
10. Troubleshooting
11. Security reminder
12. Issue #3 — canonical harness smoke run (non-Smart-Grid scenario)
13. Judge scoring (LLM-as-Judge, 6-dimension rubric)
14. L3 statistical-fidelity validation (DGA realism)
15. Result interpretation — JSONL, taxonomy CSV, evidence registry
16. Current-main reproduction proof note (#67)

---

## Repositories and paths used

- Upstream harness repo: `%AOB_PATH%`
- Team repo (this repo): `%SMARTGRID_REPO%`
- Smart Grid scenarios: `%SMARTGRID_REPO%\data\scenarios\`

> The orchestration harness (`plan-execute`) lives in `AssetOpsBench`. Our Smart Grid scenarios and MCP servers live in this repo.

Suggested environment variables for the examples below:

```cmd
set "AOB_PATH=C:\path\to\AssetOpsBench"
set "SMARTGRID_REPO=C:\path\to\hpml-assetopsbench-smart-grid-mcp"
```

---

## Prerequisites

### Required

- Windows terminal (`cmd.exe` commands below)
- Python available on PATH
- `uv` installed
- Watsonx credentials:
  - `WATSONX_APIKEY`
  - `WATSONX_PROJECT_ID`
  - optional `WATSONX_URL` (defaults to `https://us-south.ml.cloud.ibm.com`)

### Optional (for IoT/WO tool paths)

- Docker Desktop (or equivalent Docker engine)

---

## 1) One-time setup (AssetOpsBench)

Run from the upstream harness repo.

```cmd
cd /d "%AOB_PATH%"
uv sync
```

Set Watsonx env vars **for current terminal**:

```cmd
set WATSONX_APIKEY=YOUR_API_KEY
set WATSONX_PROJECT_ID=YOUR_PROJECT_ID
set WATSONX_URL=https://us-south.ml.cloud.ibm.com
set LOG_LEVEL=INFO
```

Optional persistent values (new terminals only):

```cmd
setx WATSONX_APIKEY "YOUR_API_KEY"
setx WATSONX_PROJECT_ID "YOUR_PROJECT_ID"
setx WATSONX_URL "https://us-south.ml.cloud.ibm.com"
```

---

## 2) Quick smoke test (no Docker required)

This verifies the full loop: discover tools → plan → execute tool call → summarize.

```cmd
cd /d "%AOB_PATH%"
uv run plan-execute --verbose --show-plan --show-trajectory --model-id watsonx/meta-llama/llama-3-3-70b-instruct "Using the utilities server, call the current_date_time tool and return the UTC timestamp."
```

Expected success signals:

- `Plan has 1 step(s)` (or more)
- trajectory includes `[OK ] Step ...`
- final answer returns a timestamp

---

## 3) One-command smoke script (recommended)

From this repo root, run:

```cmd
cd /d "%SMARTGRID_REPO%"
scripts\run_harness_smoke.cmd
```

If your `AssetOpsBench` path is different:

```cmd
scripts\run_harness_smoke.cmd "C:\full\path\to\AssetOpsBench"
```

What it does:

- validates `uv` and Watsonx env vars
- runs `uv sync` in `AssetOpsBench`
- executes a no-Docker utilities smoke test
- executes optional Docker-backed IoT smoke test if Docker is available

---

## 4) Docker-backed smoke test (IoT/WO paths)

Use this when you want harness calls that require CouchDB-backed data (especially IoT/WO).

Start CouchDB:

```cmd
cd /d "%AOB_PATH%"
docker compose -f src/couchdb/docker-compose.yaml up -d
```

Run a data question:

```cmd
uv run plan-execute --verbose --show-plan --show-trajectory --model-id watsonx/meta-llama/llama-3-3-70b-instruct "What assets are available at site MAIN?"
```

Stop CouchDB:

```cmd
docker compose -f src/couchdb/docker-compose.yaml down
```

---

## 5) Existing harness end-to-end (`scenario-server` + grade)

This path uses the original `aobench/scenario-server` API and confirms scenario fetch + grading loop works.

### Terminal 1 — Start scenario server

```cmd
cd /d "%AOB_PATH%\aobench\scenario-server"
uv sync
uv run python serve.py
```

Keep this terminal running.

### Terminal 2 — Discover a scenario-set ID

```cmd
curl http://127.0.0.1:8099/scenario-types
```

Copy one `id` from response (example placeholder below as `SCENARIO_SET_ID`).

### Terminal 2 — Fetch scenarios

```cmd
curl http://127.0.0.1:8099/scenario-set/SCENARIO_SET_ID
```

### Terminal 2 — Submit a minimal grading payload

> For AOB handlers, `answer` should be a JSON-string payload with `trace` and `result` fields.

```cmd
curl -X POST http://127.0.0.1:8099/scenario-set/SCENARIO_SET_ID/grade -H "Content-Type: application/json" -d "{\"submission\":[{\"scenario_id\":\"501\",\"answer\":\"{\\\"trace\\\":\\\"smoke\\\",\\\"result\\\":[] }\"}]}"
```

If that endpoint returns grades (even incorrect grades), the existing harness grading pipeline is running end-to-end.

---

## 6) Original repo benchmark flow (both CODS tracks)

This is the official containerized benchmark path from `AssetOpsBench/benchmark/README.md`.

### Track 1 (Planning track)

Linux/macOS command in upstream docs:

```bash
cd /path/to/AssetOpsBench
chmod +x benchmark/cods_track1/entrypoint.sh
docker-compose -f benchmark/cods_track1/docker-compose.yml up
```

Windows (`cmd.exe`) equivalent:

```cmd
cd /d "%AOB_PATH%"
docker compose -f benchmark/cods_track1/docker-compose.yml up
```

### Track 2 (Execution track)

Linux/macOS command pattern:

```bash
cd /path/to/AssetOpsBench
chmod +x benchmark/cods_track2/entrypoint.sh
docker-compose -f benchmark/cods_track2/docker-compose.yml up
```

Windows (`cmd.exe`) equivalent:

```cmd
cd /d "%AOB_PATH%"
docker compose -f benchmark/cods_track2/docker-compose.yml up
```

Stop either track:

```cmd
docker compose -f benchmark/cods_track1/docker-compose.yml down
docker compose -f benchmark/cods_track2/docker-compose.yml down
```

Notes:

- On Windows, `chmod` is not needed.
- The track containers run the benchmark scripts (`run_track_1.py` / `run_track_2.py`) via each track's `entrypoint.sh`.
- Use this path when you want behavior closest to official benchmark packaging.

---

## 7) Test new Smart Grid scenarios (this repo)

### Step A — Validate scenario structure

```cmd
cd /d "%SMARTGRID_REPO%"
python data/scenarios/validate_scenarios.py
```

Expected on current main (post PR #199):

```
Validation passed for 61 scenario files and 5 negative fixtures.
```

The exact integer is whatever the validator prints — match the validator's output rather than hard-coding a count in your issue comment. Negative fixtures live under `data/scenarios/negative_checks/` and exercise the validator's reject path; they are not part of the runnable corpus.

## What counts as proof of a successful canonical run?

For issue closure or board status, do not treat “I ran it locally” as enough by itself. A successful harness or scenario run should leave at least one of:

- a committed artifact or log under `benchmarks/` or another agreed repo path
- a terminal snippet in the issue comment showing the exact command and success signal
- a short note pointing to the exact scenario file, exact command, and exact output/log location

For the first canonical run, the minimum useful proof is:

- the exact command used
- the exact scenario or benchmark target
- a success indicator from the run
- a pointer to the saved output, trajectory, or grading artifact

Expected:

- `Validation passed for <N> scenario files.`

### Step B — Run scenario prompts through harness manually

Current quickest path is to copy a scenario `text` field into `plan-execute`.

Example (from `data/scenarios/multi_01_end_to_end_fault_response.json`):

```cmd
cd /d "c:\Users\aksha\Documents\COLUMBIA\HPML\Final Project\AssetOpsBench"
uv run plan-execute --verbose --show-plan --show-trajectory --model-id watsonx/meta-llama/llama-3-3-70b-instruct "Transformer T-015 shows rising load and intermittent over-temperature alerts. Investigate recent sensor behavior, infer probable fault mode, estimate short-term risk over 30 days, and issue a maintenance work order recommendation."
```

### Step C — Save JSON output for evaluation logs

```cmd
cd /d "c:\Users\aksha\Documents\COLUMBIA\HPML\Final Project\AssetOpsBench"
uv run plan-execute --json --model-id watsonx/meta-llama/llama-3-3-70b-instruct "Using the utilities server, call the current_date_time tool and return the UTC timestamp." > smoke_result.json
```

---

## 8) Smart Grid data pipeline notes relevant to benchmark runs

Our Smart Grid scenarios rely on the processed dataset under `data/processed/`:

- `asset_metadata.csv`
- `dga_records.csv`
- `failure_modes.csv`
- `fault_records.csv`
- `rul_labels.csv`
- `sensor_readings.csv`

Pipeline entry points:

```cmd
cd /d "c:\Users\aksha\Documents\COLUMBIA\HPML\Final Project\hpml-assetopsbench-smart-grid-mcp"
python data\build_processed.py
python data\generate_synthetic.py
```

Use guidance:

- Use `build_processed.py` for full local benchmarking when Kaggle credentials are available.
- Use `generate_synthetic.py` for offline/CI/public-safe runs.
- For upstream/public contribution paths, prefer synthetic data to avoid redistribution restrictions.

Licensing reminder for benchmark publication:

- CC0-backed sources are safe to share in open benchmark artifacts.
- Restricted-source-derived artifacts should remain internal unless replaced with synthetic equivalents.

---

## 9) Recommended minimum test matrix (this week)

Run at least these 4 checks before reporting harness status:

1. **Utilities-only smoke** (no Docker)
2. **FMSR/domain reasoning prompt**
3. **IoT prompt with Docker on**
4. **One Smart Grid multi-domain scenario prompt** from `data/scenarios/`

Mark harness as "working end-to-end" only if all 4 pass with non-empty plan and at least one `[OK ]` trajectory step.

---

## 10) Troubleshooting

### Symptom: `Plan has 0 step(s)`

Likely planner-output formatting mismatch from LLM.

Workarounds:

- Use a more constrained instruction (explicitly mention server/tool)
- Retry with a simpler query first (`current_date_time`)
- Keep `--verbose --show-plan --show-trajectory` on for debugging

### Symptom: Watsonx auth/model errors

Check env vars in the same terminal session:

```cmd
echo %WATSONX_APIKEY%
echo %WATSONX_PROJECT_ID%
echo %WATSONX_URL%
```

If `setx` was used recently, open a new terminal.

### Symptom: IoT/WO calls fail

- Confirm Docker is installed/running
- Confirm CouchDB stack is up via compose command above
- Retry query after container health stabilizes

### Symptom: benchmark track compose run fails

- Ensure Docker engine is running before `docker compose ... up`
- Check track-specific compose file path (`cods_track1` vs `cods_track2`)
- If container image pull fails, retry with network access and credentials as needed

### Symptom: `uv` not found

Install `uv`, then reopen terminal and rerun `uv sync`.

---

## 11) Security reminder

Never commit live credentials to git-tracked files. Keep Watsonx keys in ignored `.env` files or shell environment variables only.

---

## 12) Issue #3 — Canonical harness smoke run (non-Smart-Grid scenario)

**Purpose:** Prove the evaluation harness runs on canonical org repo main branch using an existing non-Smart-Grid FMSR scenario. Deliverable for GitHub issue #3.

**Scenario:** `data/scenarios/aob_fmsr_01_list_failure_modes.json` (`AOB-FMSR-001`)  
Query: *"List all known failure modes in the transformer dataset. For each, provide the severity level and recommended maintenance action."*  
Server required: `fmsr` only (reads `data/processed/failure_modes.csv` — no CouchDB, no Docker).

### Step 1 — Validate scenario passes schema check

```cmd
cd /d "%SMARTGRID_REPO%"
python data/scenarios/validate_scenarios.py
```

Expected on current main (post PR #199): `Validation passed for 61 scenario files and 5 negative fixtures.` See `data/scenarios/README.md` for the corpus breakdown (handcrafted SGT-001..SGT-035, gap-fill SGT-036..SGT-050, capability-targeted SGT-051..SGT-060, AOB carry-over fixtures). Always match the validator's output rather than hardcoding it in your issue comment.

### Step 2 — Run through the evaluation harness (Windows)

```cmd
cd /d "%AOB_PATH%"
uv run plan-execute --json --show-plan --show-trajectory ^
  --model-id watsonx/meta-llama/llama-3-3-70b-instruct ^
  --server "fmsr=%SMARTGRID_REPO%\mcp_servers\fmsr_server\server.py" ^
  "List all known failure modes in the transformer dataset. For each, provide the severity level and recommended maintenance action." ^
  > "%SMARTGRID_REPO%\benchmarks\cell_Y_plan_execute\raw\issue3-aob-harness-smoke\issue3_aob_fmsr_run01.json" 2> "%SMARTGRID_REPO%\benchmarks\cell_Y_plan_execute\raw\issue3-aob-harness-smoke\harness.log"
```

### Step 3 — Save evidence

Commit the generated files under `benchmarks/cell_Y_plan_execute/raw/issue3-aob-harness-smoke/`.

Success indicators in the JSON output:
- `"plan"` array contains at least one step with `"server": "fmsr"`
- `"trajectory"` contains at least one entry with `"success": true`
- `"answer"` is a non-empty string describing failure modes

### Notes

- `run_experiment.sh` is a Linux/Slurm script — use the `plan-execute` invocation above on Windows.
- The committed config for this run is `configs/issue3_aob_harness_smoke.env` (Linux/Insomnia path).
- Passing only `--server fmsr=...` is intentional: the scenario requires only the FMSR server, and this isolates the smoke test from CouchDB dependencies.

---

## 13) Judge scoring (LLM-as-Judge, 6-dimension rubric)

After a benchmark cell finishes, the trajectory JSON files under
`benchmarks/<cell>/raw/<run-id>/` are scored by `scripts/judge_trajectory.py`.
Schema is documented in [judge_schema.md](judge_schema.md); judge model defaults
to `watsonx/meta-llama/llama-4-maverick-17b-128e-instruct-fp8`.

### 13.1 Score every trajectory in a run directory

```bash
# From the repo root, with the AssetOpsBench venv active so litellm is
# importable (the judge is just a litellm client; this works on Insomnia,
# GCP, or a local Linux/macOS box). On Windows, run from WSL or use the
# AssetOpsBench `uv run` wrapper.
python scripts/judge_trajectory.py \
  --run-dir       benchmarks/cell_Y_plan_execute/raw/<run-id> \
  --scenario-dir  data/scenarios \
  --out           results/metrics/scenario_scores.jsonl \
  --log-dir       results/judge_logs/<run-id>
```

What it does:

1. Walks `<run-dir>` for `*_t<n>.json` trajectory files.
2. Joins each trajectory to its scenario by `scenario_id`.
3. Calls the judge with the [6-dimension rubric prompt](../scripts/judge_trajectory.py).
4. Appends one JSON object per `(scenario_id, trial_index)` to `--out`
   (newline-delimited JSON, schema v1).
5. Writes per-call audit logs (prompt + raw response) to `--log-dir`.

The runner deduplicates by `(run_name, scenario_id, trial_index, judge_model, judge_prompt_version)` —
re-running is cheap and idempotent; pass `--force` to override. `judge_model`
is part of the key on purpose: re-scoring a run with a different judge model
appends new rows rather than overwriting the prior judge's verdict.

### 13.2 Score a single trajectory

```bash
python scripts/judge_trajectory.py \
  --trajectory benchmarks/cell_Y_plan_execute/raw/<run-id>/SGT-001_t1.json \
  --scenario   data/scenarios/iot_01_list_transformer_sensors.json \
  --run-meta   benchmarks/cell_Y_plan_execute/raw/<run-id>/meta.json \
  --out        results/metrics/scenario_scores.jsonl
```

(`iot_01_list_transformer_sensors.json` is the file backing scenario
`SGT-001`; pick whatever scenario JSON matches the trajectory you're
scoring. The judge looks the trajectory's `scenario_id` up against the
file you pass.)

### 13.3 Required env vars

```bash
export WATSONX_APIKEY=...
export WATSONX_PROJECT_ID=...
# Optional:
export WATSONX_URL=https://us-south.ml.cloud.ibm.com
```

To use a non-default judge model, pass `--judge-model litellm_proxy/<model>` and
set `LITELLM_API_KEY` + `LITELLM_BASE_URL` instead.

### 13.4 What good output looks like

One line of `results/metrics/scenario_scores.jsonl` (truncated):

```json
{
  "schema_version": "v1",
  "scored_at": "2026-05-06T14:55:03Z",
  "run_name": "exp2_cell_Y_pe_mcp_baseline_8998340",
  "scenario_id": "SGT-001",
  "trial_index": 1,
  "experiment_cell": "Y",
  "orchestration_mode": "plan_execute",
  "model_id": "watsonx/meta-llama/llama-3-3-70b-instruct",
  "judge_model": "watsonx/meta-llama/llama-4-maverick-17b-128e-instruct-fp8",
  "dim_task_completion": true,
  "dim_data_retrieval_accuracy": true,
  "dim_generalized_result_verification": true,
  "dim_agent_sequence_correct": true,
  "dim_clarity_and_justification": true,
  "dim_hallucinations": false,
  "score_6d": 1.0,
  "pass": true,
  "pass_threshold": 0.6,
  "suggestions": "",
  "trajectory_file": "benchmarks/cell_Y_plan_execute/raw/.../SGT-001_t1.json"
}
```

`dim_hallucinations` is inverted: `false` = good (no hallucinations detected).
The score formula sums the five "good when true" dims plus `(NOT hallucinations)`
divided by 6; pass threshold is 0.6 (4 of 6).

### 13.5 Where the audit logs land

`--log-dir` writes one file per scored trial:

```
results/judge_logs/<run-id>/<scenario_id>_run<NN>_judge_log.json
```

Each contains the rendered system + user prompt sent to the judge and the
verbatim model response, so anyone can re-derive the score without re-running
the LLM. These are reproducibility evidence — keep them when archiving a
canonical capture.

---

## 14) L3 statistical-fidelity validation (DGA realism)

The synthetic DGA data under `data/processed/dga_records.csv` backs every
PS B and SGT-* scenario that touches `fmsr.get_dga_record` /
`fmsr.analyze_dga`. The L3 validator quantifies how closely synthetic gas
distributions match published real-world DGA datasets — KS / EMD / chi-squared
per gas + per fault class — and writes a versioned report card.

Layer model:

| Layer | What it checks | Driver |
|---|---|---|
| L1 schema/structural | required keys, asset-id integrity, single-domain rule | `data/scenarios/validate_scenarios.py` |
| L2 narrative realism | "would a transformer engineer recognize this as plausible work?" | `docs/archive/scenario_realism_validation.md` + mentor review |
| **L3 statistical fidelity** | KS / EMD / chi-squared per gas + fault | `data/scenarios/validate_realism_statistical.py` + `docs/dga_realism_statistical_validation.md` |

### 14.1 Run the L3 validator (canonical command)

```bash
python data/scenarios/validate_realism_statistical.py \
  --synthetic      data/processed/dga_records.csv \
  --real           data/external/DGA-dataset-1.csv \
  --real-source    bantipatel20_dga \
  --retrieved-date 2026-05-04 \
  --report         reports/realism_statistical_v1.md \
  --json           reports/realism_statistical_v1.json
```

`--retrieved-date YYYY-MM-DD` is required when `--real` is set — it stamps the
acquisition date into the report's provenance block. Without `--real`, the
script emits a stub naming the dataset(s) that still need to be acquired.

The validator depends on `numpy` and `pandas`; install via
`uv pip install -r requirements.txt` (or use the team venv that already has
them). Plain `pip install -r requirements.txt` works for non-`uv` Windows
setups outside the repo's normal flow.

### 14.2 Version progression

The repo carries the v0 → v1 progression:

| Version | What it shows | Artifact |
|---|---|---|
| v0 | pre-tuning baseline (n_synthetic=20, naive label mapping) | `reports/realism_statistical_v0.{md,json}` |
| v1 | post-fix: descriptive→IEC label map, 5/27 tests pass, directional/pre-tuning | `reports/realism_statistical_v1.{md,json}` |
| v2/v3 | post-tuning of `data/generate_synthetic.py` (planned in #53) | `reports/realism_statistical_v2.{md,json}` (TBD) |

Treat v1 as the published baseline; the v2 plan is in
[`docs/dga_realism_statistical_validation.md`](dga_realism_statistical_validation.md) §9 / §12.4.

### 14.3 PS B per-batch convention

Accepted PS B (auto-generated) batches under `data/scenarios/generated/<batch>/`
should produce a per-batch realism report named:

```
data/scenarios/generated/<batch>/realism_statistical_<batch_id>.md
```

This is the L3 hook into the auto-scenario-generation runbook (see
[`auto_scenario_generation_runbook.md`](auto_scenario_generation_runbook.md))
and is the L3 row in the §42 / §53 promotion table. When a batch is accepted
into canon (e.g. PR #195 promoted 5/15 from `first_review_20260502`), the
realism report is the corresponding L3 evidence artifact.

### 14.4 What the v1 report shows

`reports/realism_statistical_v1.md` carries:

- Provenance block (real-CSV SHA256 + MD5, row count, exact command, script HEAD)
- Per-gas KS test results (H2, CH4, C2H2, C2H4, C2H6)
- Per-fault chi-squared comparison (Normal / PD / T1-T3 / D1-D2)
- Aggregate verdict line (e.g. `Result: 5/27 tests passed`) and the
  pre-tuning caveat (synthetic n=20 is below the ≈30/group rule of thumb)

This is the figure cited by the paper's §realism paragraph and Row 6 of the
content brief in [`content_brief_scenarios_eval.md`](content_brief_scenarios_eval.md).

---

## 15) Result interpretation — JSONL, taxonomy CSV, evidence registry

After a canonical capture lands and the judge has run, the three files under
`results/metrics/` are the team-owned aggregates. A teammate following this
runbook should read them in this order:

### 15.1 `results/metrics/scenario_scores.jsonl` — the per-trial truth table

One row per `(run_name, scenario_id, trial_index)`. Schema v1 lives in
[`judge_schema.md`](judge_schema.md). Use this when you need:

- Pass/fail at the trial granularity (`pass`, `score_6d`)
- Which dimensions failed (`dim_*` booleans)
- What the judge said it would change (`suggestions`)
- The trajectory file the judge actually scored (`trajectory_file`)

Quick aggregations:

```bash
# Total scored trials on current main:
wc -l results/metrics/scenario_scores.jsonl

# Pass-rate by experiment cell:
python -c "
import json, collections
agg = collections.defaultdict(lambda: [0, 0])
with open('results/metrics/scenario_scores.jsonl') as f:
    for line in f:
        if line.strip():
            r = json.loads(line)
            cell = r.get('experiment_cell', '?')
            agg[cell][0] += int(bool(r.get('pass')))
            agg[cell][1] += 1
for cell in sorted(agg):
    p, t = agg[cell]
    print(f'{cell}: {p}/{t} = {p/t:.2%}')
"
```

### 15.2 `results/metrics/failure_taxonomy_current.csv` — paper-grade failures

Built by `scripts/build_failure_taxonomy.py` from the JSONL above; rows are
the *failures* (any `dim_*` was false). Columns of interest:

| Column | Meaning |
|---|---|
| `paper_eligible` | Row passes the paper inclusion gate (current canon, baseline cells, etc.) |
| `failed_dims` | Comma-joined list of failed dimensions |
| `auto_taxonomy_label` | Berkeley-style label assigned automatically |
| `audit_decision` / `audit_decision_source` | Hand-audit override (see PR #197) |
| `berkeley_label` | Final Berkeley taxonomy label after audit |
| `failure_stage` | planning / tool selection / tool execution / verification / final answer |

The current canon (post PR #197) contains roughly **1.97k failure rows** of
which ~**1.28k** are `paper_eligible=True` — i.e. the "paper-grade failures"
that back §failure-modes in the writeup. Stage / Berkeley counts live in the
sibling `failure_*_counts.csv` files.

### 15.3 `results/metrics/evidence_registry.csv` — what each capture proves

One row per archived run + cohort (91 data rows on current main, 92 lines
including the header), each labeled with what claim it backs in the paper.
This is the authoritative list of paper-eligible experiment cells. New
captures should append a row here before being cited.

### 15.4 Result-interpretation rule of thumb

- `score_6d == 1.0` and `pass=True` → the agent passed cleanly; no follow-up.
- `0.6 ≤ score_6d < 1.0` and `pass=True` → soft pass; check `failed_dims` and
  `suggestions` to see which dimension was on the edge.
- `pass=False` → row should appear in `failure_taxonomy_current.csv` with a
  `failed_dims` list. Cross-reference `audit_decision` if a hand audit has
  flipped or confirmed the auto-label.
- A failure row missing from `failure_taxonomy_current.csv` means the
  taxonomy CSV is stale — re-run `python scripts/build_failure_taxonomy.py`.

---

## 16) Current-main reproduction proof note (#67)

This section is a teammate-cold reproduction proof for the eval / scenario / L3
side of the runbook. Re-run any time the corpus or judge schema changes; keep
the most recent run-of-record at the top.

### 16.1 Run-of-record: 2026-05-10 on `akshat/issue67-runbook-eval-section`

| Field | Value |
|---|---|
| Repo SHA (branch tip) | `07cf0cf62d44e356e0265963e85c7663818c37ee` (`akshat/issue67-runbook-eval-section` v1; the post-merge squash SHA on `main` will differ — refresh this row after #200 lands) |
| Branch base | `origin/main` at `c726220` (W&B final evidence dashboard, #45) |
| OS / shell | Windows 11, MSYS2 bash + system `python` |
| Python | 3.x (system) — used only for the schema validator |
| Working dir | `hpml-assetopsbench-smart-grid-mcp` repo root |

#### Command 1 — L1 schema validation

```cmd
python data/scenarios/validate_scenarios.py
```

Observed stdout (verbatim):

```
Validation passed for 61 scenario files and 5 negative fixtures.
```

Artifact paths covered: every `data/scenarios/*.json` plus the negative
fixtures under `data/scenarios/negative_checks/`.

#### Command 2 — Judge JSONL aggregate sanity check

```bash
wc -l results/metrics/scenario_scores.jsonl
```

Observed stdout (verbatim):

```
3716 results/metrics/scenario_scores.jsonl
```

That's **3,716 scored trials** in the canonical aggregate. Schema documented
in `docs/judge_schema.md`; per-call audit logs under
`results/judge_logs/<run_name>/`.

#### Command 3 — Failure-taxonomy CSV size + paper-eligibility split

```bash
wc -l results/metrics/failure_taxonomy_current.csv
python -c "
import csv
rows = list(csv.DictReader(open('results/metrics/failure_taxonomy_current.csv')))
print('total_failure_rows =', len(rows))
print('paper_eligible     =', sum(1 for r in rows if r.get('paper_eligible','').lower()=='true'))
"
```

Observed stdout (verbatim):

```
1967 results/metrics/failure_taxonomy_current.csv
total_failure_rows = 1966
paper_eligible     = 1276
```

(The `wc -l` count includes the header row; `1966` is the data-row count.)

#### Command 4 — L3 statistical-fidelity (already-archived v1 report)

The L3 validator was *not* re-run in this proof pass because it depends on
`numpy` / `pandas` and the paper-cited result is already the v1 report. The
canonical command and provenance block are reproduced verbatim in:

- `reports/realism_statistical_v1.md` (provenance block + 5/27 verdict)
- `reports/realism_statistical_v1.json`

To re-run from a clean checkout (requires `pip install -r requirements.txt`):

```bash
python data/scenarios/validate_realism_statistical.py \
  --synthetic      data/processed/dga_records.csv \
  --real           data/external/DGA-dataset-1.csv \
  --real-source    bantipatel20_dga \
  --retrieved-date 2026-05-04 \
  --report         reports/realism_statistical_v1.md \
  --json           reports/realism_statistical_v1.json
```

The v1 report's archived `Script HEAD: eea6cb432b32328cce5a967c5641a2be9849aed4`
fixes the validator version that produced the report on file.

### 16.2 Artifact-path index (one-stop)

| Artifact | Path |
|---|---|
| Canonical scenarios | `data/scenarios/*.json` (61 files) |
| Negative validator fixtures | `data/scenarios/negative_checks/` (5 files) |
| Per-trial judge JSONL | `results/metrics/scenario_scores.jsonl` |
| Per-call judge audit logs | `results/judge_logs/<run_name>/*_judge_log.json` |
| Failure taxonomy (paper-grade) | `results/metrics/failure_taxonomy_current.csv` |
| Failure stage / Berkeley counts | `results/metrics/failure_taxonomy_current_*_counts.csv` |
| Evidence registry | `results/metrics/evidence_registry.csv` |
| L3 v0 baseline report | `reports/realism_statistical_v0.{md,json}` |
| L3 v1 report (paper-cited) | `reports/realism_statistical_v1.{md,json}` |
| Trajectory dumps (per cell × run) | `benchmarks/<cell>/raw/<run-id>/<scenario_id>_t<n>.json` |
| Run summaries | `benchmarks/<cell>/raw/<run-id>/{meta,summary,latencies}.{json,jsonl}` |

### 16.3 What this proof note does NOT cover

- A live judge call (LLM round-trip) — that requires WatsonX credentials and
  is exercised by §13.1 / §13.2 commands above. The archived JSONL plus
  `results/judge_logs/` together demonstrate that path.
- A live `plan-execute` harness call — covered by §2 and §12 commands above
  and by the `run_harness_smoke.cmd` script.
- An L3 re-run — depends on `numpy`/`pandas`; v1 report is the published
  baseline.

A teammate following this section cold should be able to:

1. Confirm the corpus is intact (Command 1).
2. Confirm the judge aggregate is intact (Commands 2 + 3).
3. Locate every artifact the paper cites (§16.2 table).
4. Re-run any of §13 / §14 / §15 commands without verbal context.
