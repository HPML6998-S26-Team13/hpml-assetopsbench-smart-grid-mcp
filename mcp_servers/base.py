"""
Shared data-loading stubs for all four Smart Grid MCP servers.

Each server imports from here to get a consistent view of the processed
datasets.  Fill in each function once the corresponding Kaggle CSV(s) have
been downloaded to data/processed/.

Dataset → server mapping:
  Power Transformers FDD & RUL  →  IoT, TSFM
  DGA Fault Classification       →  FMSR
  Smart Grid Fault Records       →  WO
  Transformer Health Index       →  FMSR (supplemental)
  Current & Voltage Monitoring   →  IoT, TSFM (supplemental)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd

# Root of the repository — resolved relative to this file so imports work
# from any working directory.
REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data" / "processed"


# ---------------------------------------------------------------------------
# IoT domain
# ---------------------------------------------------------------------------


def load_asset_metadata() -> pd.DataFrame:
    """
    Load static asset metadata (transformer ID, location, manufacturer,
    installation date, rated capacity, etc.).

    Source CSV: data/processed/asset_metadata.csv
    Synthesized from: Power Transformers FDD & RUL dataset.
    """
    path = DATA_DIR / "asset_metadata.csv"
    _require(path)
    return pd.read_csv(path)


def load_sensor_readings() -> pd.DataFrame:
    """
    Load time-series sensor readings indexed by (transformer_id, timestamp).

    Source CSV: data/processed/sensor_readings.csv
    Synthesized from: Power Transformers FDD & RUL + Current & Voltage
    Monitoring datasets.

    Expected columns:
        transformer_id, timestamp, sensor_id, value, unit
    """
    path = DATA_DIR / "sensor_readings.csv"
    _require(path)
    df = pd.read_csv(path, parse_dates=["timestamp"])
    return df


# ---------------------------------------------------------------------------
# FMSR domain
# ---------------------------------------------------------------------------


def load_failure_modes() -> pd.DataFrame:
    """
    Load failure mode descriptions and their associated sensor signatures.

    Source CSV: data/processed/failure_modes.csv
    Synthesized from: DGA Fault Classification + Transformer Health Index.

    Expected columns:
        failure_mode_id, name, description, severity, affected_sensors
    """
    path = DATA_DIR / "failure_modes.csv"
    _require(path)
    return pd.read_csv(path)


def load_dga_records() -> pd.DataFrame:
    """
    Load dissolved gas analysis (DGA) records used for fault classification.

    Source CSV: data/processed/dga_records.csv
    Synthesized from: DGA Fault Classification dataset.

    Expected columns:
        transformer_id, h2, ch4, c2h2, c2h4, c2h6, co, co2, fault_label
    """
    path = DATA_DIR / "dga_records.csv"
    _require(path)
    return pd.read_csv(path)


# ---------------------------------------------------------------------------
# TSFM domain
# ---------------------------------------------------------------------------


def load_rul_labels() -> pd.DataFrame:
    """
    Load remaining-useful-life (RUL) ground-truth labels per transformer.

    Source CSV: data/processed/rul_labels.csv
    Synthesized from: Power Transformers FDD & RUL dataset.

    Expected columns:
        transformer_id, timestamp, rul_days, health_index
    """
    path = DATA_DIR / "rul_labels.csv"
    _require(path)
    return pd.read_csv(path, parse_dates=["timestamp"])


# ---------------------------------------------------------------------------
# WO domain
# ---------------------------------------------------------------------------


def load_fault_records() -> pd.DataFrame:
    """
    Load historical fault / maintenance event records.

    Source CSV: data/processed/fault_records.csv
    Synthesized from: Smart Grid Fault Records dataset.

    Expected columns:
        fault_id, transformer_id, timestamp, fault_type, severity,
        estimated_downtime_hours, status
    """
    path = DATA_DIR / "fault_records.csv"
    _require(path)
    return pd.read_csv(path, parse_dates=["timestamp"])


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _require(path: Path) -> None:
    """Raise a clear error if a processed data file hasn't been created yet."""
    if not path.exists():
        raise FileNotFoundError(
            f"Processed data file not found: {path}\n"
            "Run the data pipeline (data/processed/) to generate it first."
        )
