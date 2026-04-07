@echo off
setlocal enabledelayedexpansion

REM Usage:
REM   run_harness_smoke.cmd
REM   run_harness_smoke.cmd "C:\path\to\AssetOpsBench"

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "HPML_ROOT=%%~fI"

if "%~1"=="" (
  set "AOB_PATH=%HPML_ROOT%\..\AssetOpsBench"
) else (
  set "AOB_PATH=%~1"
)

echo [INFO] HPML root: %HPML_ROOT%
echo [INFO] AssetOpsBench path: %AOB_PATH%

if not exist "%AOB_PATH%\pyproject.toml" (
  echo [ERROR] Could not find AssetOpsBench repo at: %AOB_PATH%
  echo [HINT] Pass explicit path: run_harness_smoke.cmd "C:\full\path\to\AssetOpsBench"
  exit /b 1
)

where uv >nul 2>nul
if errorlevel 1 (
  echo [ERROR] uv not found on PATH.
  exit /b 1
)

if "%WATSONX_APIKEY%"=="" (
  echo [ERROR] WATSONX_APIKEY is not set in this terminal.
  exit /b 1
)

if "%WATSONX_PROJECT_ID%"=="" (
  echo [ERROR] WATSONX_PROJECT_ID is not set in this terminal.
  exit /b 1
)

if "%WATSONX_URL%"=="" (
  set "WATSONX_URL=https://us-south.ml.cloud.ibm.com"
)

set "MODEL_ID=watsonx/meta-llama/llama-3-3-70b-instruct"

pushd "%AOB_PATH%"

echo [STEP] Ensuring dependencies are synced...
call uv sync
if errorlevel 1 (
  echo [ERROR] uv sync failed.
  popd
  exit /b 1
)

echo [STEP] Running utilities-only smoke test (no Docker required)...
call uv run plan-execute --verbose --show-plan --show-trajectory --model-id %MODEL_ID% "Using the utilities server, call the current_date_time tool and return the UTC timestamp."
if errorlevel 1 (
  echo [ERROR] Utilities smoke test failed.
  popd
  exit /b 1
)

echo [STEP] Checking optional Docker-backed IoT smoke test...
where docker >nul 2>nul
if errorlevel 1 (
  echo [WARN] Docker not found. Skipping IoT/CouchDB smoke test.
  goto :done
)

call docker compose -f src/couchdb/docker-compose.yaml up -d
if errorlevel 1 (
  echo [WARN] Could not start Docker compose stack. Skipping IoT smoke test.
  goto :done
)

call uv run plan-execute --verbose --show-plan --show-trajectory --model-id %MODEL_ID% "What assets are available at site MAIN?"
if errorlevel 1 (
  echo [WARN] IoT smoke test failed. Check Docker/CouchDB status.
)

call docker compose -f src/couchdb/docker-compose.yaml down

:done
echo [OK] Harness smoke run completed.
popd
exit /b 0
