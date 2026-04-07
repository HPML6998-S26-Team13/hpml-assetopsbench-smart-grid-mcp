# mcp_servers/

MCP (Model Context Protocol) servers wrapping the four AssetOpsBench tool domains. Each subdirectory is a standalone MCP server that can be launched independently or composed into a multi-server agent pipeline.

## Architecture

All four servers inherit from `base.py`, which provides shared data-loading helpers pointing at `data/processed/`. Each server exposes a set of tools via the MCP JSON-RPC interface.

```
mcp_servers/
├── base.py                 # shared data loader + utilities
├── iot_server/             # asset metadata + sensor readings
│   └── server.py           # tools: list_assets, get_asset_metadata, list_sensors, get_sensor_readings
├── fmsr_server/            # failure mode to sensor relation
│   └── server.py           # tools: list_failure_modes, search_failure_modes, get_sensor_correlation,
│                           #        get_dga_record, analyze_dga (IEC 60599 Rogers Ratio)
├── tsfm_server/            # time-series forecasting + RUL
│   └── server.py           # tools: get_rul, forecast_rul, detect_anomalies (z-score),
│                           #        trend_analysis (OLS)
└── wo_server/              # work order management
    └── server.py           # tools: list/get fault records, create/list/update work orders,
                            #        estimate_downtime
```

## Running a server

```bash
# From repo root, with the team .venv active:
python -m mcp_servers.iot_server.server
```

Each server runs as an independent process listening on its own socket. The agent (not the server) is responsible for orchestrating multi-turn tool calls across servers.

## Design notes

- **Shared base class** keeps data loading DRY — schema changes in `data/processed/` only need updating in `base.py`.
- **Stateless tool calls** — servers don't maintain session state; the agent holds multi-turn context.
- **No network side effects** — all tools read from local CSVs. This is a benchmark, not a live industrial system.
- **Real domain logic, not stubs** — e.g. `fmsr_server.analyze_dga` implements the IEC 60599 Rogers Ratio method for dissolved gas analysis, not a dummy return.

## Status (Apr 7, 2026)

- **Skeletons landed** for all four domains (commit `717e9b4`, Tanisha)
- **Substantive domain logic** implemented (Rogers Ratio, RUL forecast, anomaly detection, work-order CRUD)
- **In progress (W2):** hardening, unit tests, integration with the AssetOpsBench evaluation harness
