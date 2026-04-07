# Evaluation Harness Runbook (Local Windows + Watsonx)

*Last updated: 2026-04-07*

This README is the practical runbook for getting the **AssetOpsBench evaluation harness** running end-to-end on a local Windows machine, then exercising our **Smart Grid scenarios** from `data/scenarios/`.

## What this runbook covers

1. Quick harness smoke test (`plan-execute` + MCP tools + Watsonx)
2. One-command smoke script (`scripts/run_harness_smoke.cmd`)
3. Docker-backed test path for IoT/WO data access (CouchDB)
4. Existing harness end-to-end (`scenario-server` + grading path)
5. Original repo benchmark flow (`benchmark/cods_track1` and `benchmark/cods_track2`)
6. How to test newly-authored Smart Grid scenarios
7. Smart Grid data pipeline notes relevant to benchmark runs
8. Common failure modes and fixes

---

## Repositories and paths used

- Upstream harness repo: `../AssetOpsBench`
- Team repo (this repo): `.`
- Smart Grid scenarios: `data/scenarios/`

> The orchestration harness (`plan-execute`) lives in `AssetOpsBench`. Our Smart Grid scenarios and MCP servers live in this repo.

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
cd /d "c:\Users\aksha\Documents\COLUMBIA\HPML\Final Project\AssetOpsBench"
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
cd /d "c:\Users\aksha\Documents\COLUMBIA\HPML\Final Project\AssetOpsBench"
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
cd /d "c:\Users\aksha\Documents\COLUMBIA\HPML\Final Project\hpml-assetopsbench-smart-grid-mcp"
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
cd /d "c:\Users\aksha\Documents\COLUMBIA\HPML\Final Project\AssetOpsBench"
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
cd /d "c:\Users\aksha\Documents\COLUMBIA\HPML\Final Project\AssetOpsBench\aobench\scenario-server"
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
cd /d "c:\Users\aksha\Documents\COLUMBIA\HPML\Final Project\AssetOpsBench"
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
cd /d "c:\Users\aksha\Documents\COLUMBIA\HPML\Final Project\AssetOpsBench"
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
cd /d "c:\Users\aksha\Documents\COLUMBIA\HPML\Final Project\hpml-assetopsbench-smart-grid-mcp"
python data\scenarios\validate_scenarios.py
```

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
