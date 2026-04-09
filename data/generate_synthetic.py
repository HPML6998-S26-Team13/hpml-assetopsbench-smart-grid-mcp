"""
Generate synthetic Smart Grid transformer data for development/testing.

This produces the same CSV schemas that the real Kaggle datasets will be
processed into.  Real data replaces these once the pipeline runs against
the downloaded Kaggle files.

Run:
    python3 data/generate_synthetic.py

Outputs (all in data/processed/):
    asset_metadata.csv    — 20 transformers, static attributes
    sensor_readings.csv   — hourly readings for 30 days per transformer
    failure_modes.csv     — catalogue of DGA-based fault types
    dga_records.csv       — one DGA sample per transformer (some faulty)
    rul_labels.csv        — daily RUL estimates per transformer
    fault_records.csv     — maintenance / work-order history

Synthetic transformer_id key: T-001 … T-020
  T-001 to T-010  →  healthy / approaching end-of-life
  T-011 to T-015  →  minor faults (partial discharge, thermal < 300°C)
  T-016 to T-020  →  serious faults (arcing, thermal > 700°C)
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
rng = np.random.default_rng(SEED)
random.seed(SEED)

OUT = Path(__file__).parent / "processed"
OUT.mkdir(parents=True, exist_ok=True)

N_TRANSFORMERS = 20
IDS = [f"T-{i:03d}" for i in range(1, N_TRANSFORMERS + 1)]

START = datetime(2024, 1, 1)
END = datetime(2024, 1, 31)


# ---------------------------------------------------------------------------
# 1. asset_metadata.csv
# ---------------------------------------------------------------------------
# Why: IoT server needs static attributes to answer "what is transformer T-007?"
# Columns mirror what AssetOpsBench IoT tools return for other domains.


def make_asset_metadata() -> pd.DataFrame:
    manufacturers = ["ABB", "Siemens", "GE", "Eaton", "Schneider Electric"]
    locations = [
        "Substation Alpha",
        "Substation Beta",
        "Substation Gamma",
        "Distribution Center 1",
        "Distribution Center 2",
        "Industrial Park A",
        "Industrial Park B",
    ]
    voltage_classes = ["11kV/0.4kV", "33kV/11kV", "132kV/33kV"]
    ratings_kva = [500, 1000, 1500, 2000, 2500, 5000]

    rows = []
    for i, tid in enumerate(IDS):
        install_year = rng.integers(2005, 2020)
        rows.append(
            {
                "transformer_id": tid,
                "name": f"Power Transformer {tid}",
                "manufacturer": random.choice(manufacturers),
                "location": random.choice(locations),
                "voltage_class": random.choice(voltage_classes),
                "rating_kva": random.choice(ratings_kva),
                "install_date": f"{install_year}-{rng.integers(1,13):02d}-{rng.integers(1,28):02d}",
                "age_years": 2024 - install_year,
                # health_status: healthy (0), degraded (1), critical (2)
                "health_status": 0 if i < 10 else (1 if i < 15 else 2),
                "in_service": True,
            }
        )

    df = pd.DataFrame(rows)
    path = OUT / "asset_metadata.csv"
    df.to_csv(path, index=False)
    print(f"  wrote {path}  ({len(df)} rows)")
    return df


# ---------------------------------------------------------------------------
# 2. sensor_readings.csv
# ---------------------------------------------------------------------------
# Why: IoT server's get_sensor_readings() returns this.
# Sensors: winding_temp, oil_temp, load_current, voltage_hv, voltage_lv.
# Faulty transformers have elevated temperature / voltage anomalies.

SENSORS = {
    "winding_temp_top_c": {
        "healthy": (50, 10),
        "degraded": (80, 15),
        "critical": (105, 20),
        "unit": "°C",
    },
    "oil_temp_c": {
        "healthy": (45, 8),
        "degraded": (70, 12),
        "critical": (90, 18),
        "unit": "°C",
    },
    "load_current_a": {
        "healthy": (200, 40),
        "degraded": (220, 45),
        "critical": (240, 50),
        "unit": "A",
    },
    "voltage_hv_kv": {
        "healthy": (33, 0.5),
        "degraded": (33, 1.0),
        "critical": (32, 2.0),
        "unit": "kV",
    },
    "voltage_lv_kv": {
        "healthy": (11, 0.2),
        "degraded": (11, 0.4),
        "critical": (10.5, 1.0),
        "unit": "kV",
    },
    "power_factor": {
        "healthy": (0.95, 0.02),
        "degraded": (0.90, 0.04),
        "critical": (0.82, 0.06),
        "unit": "",
    },
}


def make_sensor_readings(metadata: pd.DataFrame) -> pd.DataFrame:
    hours = int((END - START).total_seconds() / 3600)
    timestamps = [START + timedelta(hours=h) for h in range(hours)]

    rows = []
    status_map = dict(zip(metadata["transformer_id"], metadata["health_status"]))

    for tid in IDS:
        status_key = ["healthy", "degraded", "critical"][status_map[tid]]
        for sensor_id, params in SENSORS.items():
            mu, sigma = params[status_key]
            values = rng.normal(mu, sigma, len(timestamps))
            # Inject a spike anomaly into critical transformers
            if status_map[tid] == 2 and "temp" in sensor_id:
                spike_idx = rng.integers(100, len(timestamps) - 50)
                values[spike_idx : spike_idx + 12] += rng.uniform(15, 30)
            for ts, val in zip(timestamps, values):
                rows.append(
                    {
                        "transformer_id": tid,
                        "timestamp": ts.isoformat(),
                        "sensor_id": sensor_id,
                        "value": round(float(val), 3),
                        "unit": params["unit"],
                    }
                )

    df = pd.DataFrame(rows)
    path = OUT / "sensor_readings.csv"
    df.to_csv(path, index=False)
    print(f"  wrote {path}  ({len(df):,} rows)")
    return df


# ---------------------------------------------------------------------------
# 3. failure_modes.csv
# ---------------------------------------------------------------------------
# Why: FMSR server's search_failure_modes() and get_sensor_correlation()
#      return entries from this table.
# Based on IEC 60599 DGA interpretation standard and Duval triangle method.


def make_failure_modes() -> pd.DataFrame:
    rows = [
        {
            "failure_mode_id": "FM-001",
            "name": "Partial Discharge",
            "description": "Low-energy electrical discharge within insulation voids. "
            "Indicated by elevated H2 and CH4 with trace C2H2.",
            "severity": "low",
            "iec_code": "PD",
            "affected_sensors": "dissolved_h2_ppm,dissolved_ch4_ppm",
            "recommended_action": "Monitor closely; schedule inspection within 90 days",
        },
        {
            "failure_mode_id": "FM-002",
            "name": "Thermal Fault < 300°C",
            "description": "Low-temperature thermal fault, typically in core laminations "
            "or due to overload. Elevated CH4 and C2H4.",
            "severity": "medium",
            "iec_code": "T1",
            "affected_sensors": "dissolved_ch4_ppm,dissolved_c2h4_ppm,oil_temp_c",
            "recommended_action": "Reduce load; inspect within 30 days",
        },
        {
            "failure_mode_id": "FM-003",
            "name": "Thermal Fault 300–700°C",
            "description": "Medium-temperature thermal fault in conductors or connections. "
            "High C2H4 relative to C2H6.",
            "severity": "high",
            "iec_code": "T2",
            "affected_sensors": "dissolved_c2h4_ppm,dissolved_c2h6_ppm,winding_temp_top_c",
            "recommended_action": "De-energize and inspect within 7 days",
        },
        {
            "failure_mode_id": "FM-004",
            "name": "Thermal Fault > 700°C",
            "description": "High-temperature thermal fault indicating severe overheating, "
            "often in winding conductors. High C2H4 and C2H6.",
            "severity": "critical",
            "iec_code": "T3",
            "affected_sensors": "dissolved_c2h4_ppm,dissolved_c2h6_ppm,winding_temp_top_c,oil_temp_c",
            "recommended_action": "Immediate de-energization required",
        },
        {
            "failure_mode_id": "FM-005",
            "name": "Low-Energy Electrical Discharge",
            "description": "Sparking or tracking in oil. Characterized by elevated C2H2 "
            "alongside H2 and C2H4.",
            "severity": "high",
            "iec_code": "D1",
            "affected_sensors": "dissolved_c2h2_ppm,dissolved_h2_ppm,dissolved_c2h4_ppm",
            "recommended_action": "De-energize and inspect within 48 hours",
        },
        {
            "failure_mode_id": "FM-006",
            "name": "High-Energy Electrical Discharge (Arcing)",
            "description": "High-energy arcing causing significant oil decomposition. "
            "Very high C2H2 and H2.",
            "severity": "critical",
            "iec_code": "D2",
            "affected_sensors": "dissolved_c2h2_ppm,dissolved_h2_ppm,dissolved_c2h4_ppm,dissolved_c2h6_ppm",
            "recommended_action": "Immediate de-energization and emergency inspection",
        },
        {
            "failure_mode_id": "FM-007",
            "name": "Normal Aging",
            "description": "Background gas generation consistent with normal transformer "
            "aging. All gases within IEC limits.",
            "severity": "none",
            "iec_code": "N",
            "affected_sensors": "",
            "recommended_action": "Continue routine monitoring",
        },
    ]

    df = pd.DataFrame(rows)
    path = OUT / "failure_modes.csv"
    df.to_csv(path, index=False)
    print(f"  wrote {path}  ({len(df)} rows)")
    return df


# ---------------------------------------------------------------------------
# 4. dga_records.csv
# ---------------------------------------------------------------------------
# Why: FMSR server's analyze_dga() interprets these gas concentrations.
# Gas values in ppm (parts per million), typical IEC 60599 ranges.
# Each transformer gets one DGA sample; fault profile matches health_status.

DGA_PROFILES = {
    # (h2, ch4, c2h2, c2h4, c2h6, co, co2) mean ± sigma
    "healthy": [(10, 3), (5, 2), (0.1, 0.05), (2, 1), (2, 0.8), (200, 40), (1500, 200)],
    "degraded": [(50, 15), (30, 10), (2, 1), (25, 8), (10, 3), (300, 60), (2000, 300)],
    "critical": [
        (200, 50),
        (80, 20),
        (20, 8),
        (100, 25),
        (40, 10),
        (500, 80),
        (3500, 400),
    ],
}
DGA_COLS = [
    "dissolved_h2_ppm",
    "dissolved_ch4_ppm",
    "dissolved_c2h2_ppm",
    "dissolved_c2h4_ppm",
    "dissolved_c2h6_ppm",
    "dissolved_co_ppm",
    "dissolved_co2_ppm",
]

FAULT_LABEL_MAP = {
    "healthy": "Normal",
    "degraded": "Thermal Fault < 300°C",
    "critical": "High-Energy Electrical Discharge (Arcing)",
}


def make_dga_records(metadata: pd.DataFrame) -> pd.DataFrame:
    status_map = dict(zip(metadata["transformer_id"], metadata["health_status"]))
    rows = []
    for tid in IDS:
        profile_key = ["healthy", "degraded", "critical"][status_map[tid]]
        profile = DGA_PROFILES[profile_key]
        gas_vals = {
            col: round(max(0.0, float(rng.normal(mu, sigma))), 2)
            for col, (mu, sigma) in zip(DGA_COLS, profile)
        }
        rows.append(
            {
                "transformer_id": tid,
                "sample_date": (START + timedelta(days=rng.integers(0, 30))).strftime(
                    "%Y-%m-%d"
                ),
                **gas_vals,
                "fault_label": FAULT_LABEL_MAP[profile_key],
                "sample_source": "synthetic",
            }
        )

    df = pd.DataFrame(rows)
    path = OUT / "dga_records.csv"
    df.to_csv(path, index=False)
    print(f"  wrote {path}  ({len(df)} rows)")
    return df


# ---------------------------------------------------------------------------
# 5. rul_labels.csv
# ---------------------------------------------------------------------------
# Why: TSFM server's forecast_rul() returns predictions against these labels.
# RUL decreases each day; critical transformers have low starting RUL.

RUL_START = {
    "healthy": (3650, 500),  # ~10 years remaining
    "degraded": (730, 200),  # ~2 years
    "critical": (90, 30),  # ~3 months
}


def make_rul_labels(metadata: pd.DataFrame) -> pd.DataFrame:
    status_map = dict(zip(metadata["transformer_id"], metadata["health_status"]))
    rows = []
    for tid in IDS:
        profile_key = ["healthy", "degraded", "critical"][status_map[tid]]
        mu, sigma = RUL_START[profile_key]
        base_rul = max(10, int(rng.normal(mu, sigma)))
        days = (END - START).days
        for d in range(days + 1):
            day = START + timedelta(days=d)
            # Add small noise to daily degradation
            daily_deg = rng.normal(1.0, 0.1)
            rul = max(0, base_rul - int(d * daily_deg))
            health_index = min(1.0, max(0.0, rul / mu))
            rows.append(
                {
                    "transformer_id": tid,
                    "timestamp": day.strftime("%Y-%m-%d"),
                    "rul_days": rul,
                    "health_index": round(float(health_index), 4),
                }
            )

    df = pd.DataFrame(rows)
    path = OUT / "rul_labels.csv"
    df.to_csv(path, index=False)
    print(f"  wrote {path}  ({len(df)} rows)")
    return df


# ---------------------------------------------------------------------------
# 6. fault_records.csv
# ---------------------------------------------------------------------------
# Why: WO server's list_work_orders() and create_work_order() reference these.
# Each critical/degraded transformer has at least one historical fault event.

FAULT_TYPES = [
    "Winding insulation degradation",
    "Oil contamination",
    "Bushing failure",
    "Cooling system failure",
    "Tap changer malfunction",
    "Core ground fault",
    "Overload trip",
]
SEVERITIES = ["low", "medium", "high", "critical"]
STATUSES = ["open", "in_progress", "resolved", "closed"]
TECHNICIANS = ["TEC-01", "TEC-02", "TEC-03", "TEC-04", "TEC-05"]


def make_fault_records(metadata: pd.DataFrame) -> pd.DataFrame:
    status_map = dict(zip(metadata["transformer_id"], metadata["health_status"]))
    rows = []
    fault_counter = 1

    for tid in IDS:
        health = status_map[tid]
        # Healthy: 0-1 records, degraded: 1-3, critical: 2-5
        n_faults = {
            0: rng.integers(0, 2),
            1: rng.integers(1, 4),
            2: rng.integers(2, 6),
        }[health]
        for _ in range(n_faults):
            event_day = START + timedelta(days=int(rng.integers(0, 30)))
            severity = SEVERITIES[min(health + rng.integers(0, 2), 3)]
            downtime = {"low": 4, "medium": 8, "high": 24, "critical": 72}[severity]
            rows.append(
                {
                    "fault_id": f"F-{fault_counter:04d}",
                    "transformer_id": tid,
                    "timestamp": event_day.isoformat(),
                    "fault_type": random.choice(FAULT_TYPES),
                    "severity": severity,
                    "estimated_downtime_hours": downtime + int(rng.integers(-2, 4)),
                    "assigned_technician": random.choice(TECHNICIANS),
                    "status": random.choice(STATUSES),
                    "notes": "",
                }
            )
            fault_counter += 1

    df = pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)
    path = OUT / "fault_records.csv"
    df.to_csv(path, index=False)
    print(f"  wrote {path}  ({len(df)} rows)")
    return df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"Generating synthetic Smart Grid data → {OUT}\n")
    meta = make_asset_metadata()
    make_sensor_readings(meta)
    make_failure_modes()
    make_dga_records(meta)
    make_rul_labels(meta)
    make_fault_records(meta)
    print("\nDone. All files written to data/processed/")
    print(
        "These are SYNTHETIC — replace with real Kaggle data once API access is granted."
    )
