"""
IoT MCP Server — sensor telemetry and asset metadata for Smart Grid transformers.

Tools exposed to the LLM agent:
  list_assets        — list all transformer assets (optionally filter by status)
  get_asset_metadata — static nameplate info for one transformer
  list_sensors       — which sensor IDs exist for a transformer
  get_sensor_readings — time-series readings for one sensor

Data source: data/processed/asset_metadata.csv, sensor_readings.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make the repo root importable so `mcp_servers.base` resolves regardless of
# where the server is launched from.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
from mcp.server.fastmcp import FastMCP

from mcp_servers.base import load_asset_metadata, load_sensor_readings

mcp = FastMCP("smart-grid-iot")

# ---------------------------------------------------------------------------
# Module-level data cache
# ---------------------------------------------------------------------------
# We load the CSVs once at startup rather than on every tool call.
# In production this would be replaced by a database connection.

_metadata: pd.DataFrame | None = None
_readings: pd.DataFrame | None = None


def _get_metadata() -> pd.DataFrame:
    global _metadata
    if _metadata is None:
        _metadata = load_asset_metadata()
    return _metadata


def _get_readings() -> pd.DataFrame:
    global _readings
    if _readings is None:
        _readings = load_sensor_readings()
    return _readings


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def list_assets(health_status: int | None = None) -> list[dict]:
    """
    List all Smart Grid transformer assets.

    Args:
        health_status: Optional filter. 0 = healthy, 1 = degraded, 2 = critical.
                       Omit to return all assets.

    Returns:
        List of dicts, each with keys:
          transformer_id, name, location, health_status, rul_days, in_service
    """
    df = _get_metadata()
    if health_status is not None:
        df = df[df["health_status"] == health_status]

    return df[["transformer_id", "name", "location", "health_status",
               "rul_days", "in_service"]].to_dict(orient="records")


@mcp.tool()
def get_asset_metadata(transformer_id: str) -> dict:
    """
    Return full nameplate and status metadata for a single transformer.

    Args:
        transformer_id: Asset identifier, e.g. "T-001".

    Returns:
        Dict with keys: transformer_id, name, manufacturer, location,
        voltage_class, rating_kva, install_date, age_years, health_status,
        fdd_category, rul_days, in_service.
        Returns an error dict if the ID is not found.
    """
    df = _get_metadata()
    row = df[df["transformer_id"] == transformer_id]
    if row.empty:
        return {"error": f"Transformer '{transformer_id}' not found."}
    return row.iloc[0].to_dict()


@mcp.tool()
def list_sensors(transformer_id: str) -> list[dict]:
    """
    List all sensor IDs available for a given transformer.

    Args:
        transformer_id: Asset identifier, e.g. "T-001".

    Returns:
        List of dicts with keys: sensor_id, unit, num_readings.
        Returns an error list if the transformer ID is not found.
    """
    df = _get_readings()
    subset = df[df["transformer_id"] == transformer_id]
    if subset.empty:
        return [{"error": f"No sensor data found for '{transformer_id}'."}]

    summary = (
        subset.groupby(["sensor_id", "unit"])
        .size()
        .reset_index(name="num_readings")
    )
    return summary.to_dict(orient="records")


@mcp.tool()
def get_sensor_readings(
    transformer_id: str,
    sensor_id: str,
    start_time: str | None = None,
    end_time: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """
    Return time-series readings for one sensor on one transformer.

    Args:
        transformer_id: Asset identifier, e.g. "T-001".
        sensor_id:      Sensor name, e.g. "dga_h2_ppm" or "winding_temp_c".
                        Use list_sensors() to discover valid sensor IDs.
        start_time:     ISO-8601 datetime string (inclusive). Optional.
        end_time:       ISO-8601 datetime string (inclusive). Optional.
        limit:          Maximum number of rows to return (default 100, max 1000).

    Returns:
        List of dicts with keys: timestamp, value, unit.
        Sorted ascending by timestamp.
        Returns an error list if the transformer or sensor is not found.
    """
    df = _get_readings()
    subset = df[
        (df["transformer_id"] == transformer_id) &
        (df["sensor_id"] == sensor_id)
    ].copy()

    if subset.empty:
        return [{"error": f"No readings found for transformer='{transformer_id}' "
                          f"sensor='{sensor_id}'."}]

    # Ensure timestamp column is datetime
    subset["timestamp"] = pd.to_datetime(subset["timestamp"])

    if start_time:
        subset = subset[subset["timestamp"] >= pd.to_datetime(start_time)]
    if end_time:
        subset = subset[subset["timestamp"] <= pd.to_datetime(end_time)]

    subset = subset.sort_values("timestamp").head(min(limit, 1000))

    return subset[["timestamp", "value", "unit"]].assign(
        timestamp=subset["timestamp"].dt.isoformat()
    ).to_dict(orient="records")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
# When run as a subprocess by the agent harness, `mcp.run()` starts the
# stdio JSON-RPC loop.  The process reads tool-call requests from stdin and
# writes results to stdout until the parent closes the pipe.

if __name__ == "__main__":
    mcp.run()
