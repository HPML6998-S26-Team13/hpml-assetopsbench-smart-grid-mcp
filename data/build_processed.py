"""
Data pipeline: raw Kaggle downloads → processed CSVs for MCP servers.

Run from repo root:
    python3 data/build_processed.py

Inputs  (data/raw/):
    power-transformers-fdd-and-rul/     — 3000 per-transformer time-series + labels
    dissolved-gas-analysis-of-transformer/DGA-dataset-1.csv  — 201 raw DGA samples
    sample-power-transformers-health-condition-dataset/Health index2.csv  — 470 health records
    ai-transformer-monitoring/          — real-time readings from one transformer
    power-system-faults-dataset/fault_data.csv  — 506 fault/maintenance events

Outputs (data/processed/):
    asset_metadata.csv    — 20 synthetic transformers (T-001 … T-020)
    sensor_readings.csv   — time-series sensor readings per transformer
    dga_records.csv       — one DGA gas sample per transformer
    failure_modes.csv     — catalogue of fault types derived from DGA labels
    rul_labels.csv        — remaining-useful-life labels per transformer
    fault_records.csv     — maintenance / fault event history per transformer

Synthetic transformer_id key strategy
--------------------------------------
None of the five datasets share a natural join key.  We synthesize one:

  T-001 – T-005  →  FDD category 1, high RUL  (healthy, years of life left)
  T-006 – T-010  →  FDD category 1, low RUL   (healthy but aging)
  T-011 – T-015  →  FDD categories 2–3         (minor / moderate fault)
  T-016 – T-020  →  FDD category 4             (serious fault)

Each transformer ID is anchored to one FDD&RUL file (real time-series data).
DGA records are sampled from the DGA dataset, matched by fault family.
Fault events are distributed from the Fault Records dataset.
The real monitoring time-series (OTI/WTI/voltage/current) is assigned to T-001.
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

RAW = Path(__file__).parent / "raw"
OUT = Path(__file__).parent / "processed"
OUT.mkdir(parents=True, exist_ok=True)

FDD_RAW = RAW / "power-transformers-fdd-and-rul"

# ---------------------------------------------------------------------------
# Step 1: pick 20 representative transformers from FDD&RUL training set
# ---------------------------------------------------------------------------


def select_representatives() -> pd.DataFrame:
    """
    Return a DataFrame with columns [transformer_id, fdd_file, fdd_category, rul_days]
    for 20 selected transformers, 5 per health tier.
    """
    fdd_labels = pd.read_csv(FDD_RAW / "labels_fdd_train.csv")
    rul_labels = pd.read_csv(FDD_RAW / "labels_rul_train.csv")

    # Join on filename
    merged = fdd_labels.merge(rul_labels, on="id")
    merged.rename(columns={"predicted": "rul_days"}, inplace=True)

    tiers = []

    # Tier 1: healthy (cat=1), high RUL — top quartile (≥1093)
    t1 = merged[(merged.category == 1) & (merged.rul_days >= 1093)].sample(
        5, random_state=SEED
    )
    t1 = t1.copy()
    t1["tier"] = "healthy_long"

    # Tier 2: healthy (cat=1), low RUL — bottom quartile (≤560)
    t2 = merged[(merged.category == 1) & (merged.rul_days <= 560)].sample(
        5, random_state=SEED
    )
    t2 = t2.copy()
    t2["tier"] = "healthy_aging"

    # Tier 3: minor/moderate fault (cat 2 or 3)
    t3 = merged[merged.category.isin([2, 3])].sample(5, random_state=SEED)
    t3 = t3.copy()
    t3["tier"] = "minor_fault"

    # Tier 4: serious fault (cat 4)
    t4 = merged[merged.category == 4].sample(5, random_state=SEED)
    t4 = t4.copy()
    t4["tier"] = "serious_fault"

    reps = pd.concat([t1, t2, t3, t4], ignore_index=True)
    reps.insert(0, "transformer_id", [f"T-{i:03d}" for i in range(1, 21)])
    reps.rename(columns={"id": "fdd_file", "category": "fdd_category"}, inplace=True)
    return reps[["transformer_id", "fdd_file", "fdd_category", "rul_days", "tier"]]


# ---------------------------------------------------------------------------
# Step 2: asset_metadata.csv
# ---------------------------------------------------------------------------


def make_asset_metadata(reps: pd.DataFrame) -> pd.DataFrame:
    """
    Static transformer attributes.  Largely synthetic — none of the Kaggle
    datasets include nameplate data.  RUL and fault category inform
    health_status (0=healthy, 1=degraded, 2=critical).
    """
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

    tier_to_status = {
        "healthy_long": 0,
        "healthy_aging": 0,
        "minor_fault": 1,
        "serious_fault": 2,
    }

    rows = []
    for _, row in reps.iterrows():
        install_year = int(rng.integers(2005, 2020))
        rows.append(
            {
                "transformer_id": row.transformer_id,
                "name": f"Power Transformer {row.transformer_id}",
                "manufacturer": random.choice(manufacturers),
                "location": random.choice(locations),
                "voltage_class": random.choice(voltage_classes),
                "rating_kva": random.choice(ratings_kva),
                "install_date": f"{install_year}-{rng.integers(1,13):02d}-{rng.integers(1,28):02d}",
                "age_years": 2024 - install_year,
                "health_status": tier_to_status[row.tier],
                "fdd_category": row.fdd_category,
                "rul_days": row.rul_days,
                "in_service": True,
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "asset_metadata.csv", index=False)
    print(f"  asset_metadata.csv  ({len(df)} rows)")
    return df


# ---------------------------------------------------------------------------
# Step 3: sensor_readings.csv
# ---------------------------------------------------------------------------
# Sources:
#   • FDD&RUL time-series (H2, CO, C2H4, C2H2 — normalized) for all 20 transformers
#   • ai-transformer-monitoring/Overview.csv (OTI, WTI) → assigned to T-001
#   • ai-transformer-monitoring/CurrentVoltage.csv (VL, IL) → assigned to T-001
#
# FDD&RUL values are normalized ratios, not raw ppm.  We scale them by
# representative ppm factors derived from the DGA dataset so they sit in a
# physically plausible range.

# Rough scale factors: median DGA ppm / median FDD&RUL normalized value
# (eyeballed from the data; good enough for synthetic development)
FDD_SCALE = {
    "H2": 50_000,  # FDD H2 ~0.002–0.004  →  ppm  100–200
    "CO": 20_000,  # FDD CO ~0.01–0.03    →  ppm  200–600
    "C2H4": 5_000,  # FDD C2H4 ~0.001–0.005 → ppm  5–25
    "C2H2": 1_000,  # FDD C2H2 ~0.0001–0.001 → ppm 0.1–1
}


def make_sensor_readings(reps: pd.DataFrame) -> pd.DataFrame:
    rows = []

    # --- FDD&RUL gas time-series ---
    for _, rep in reps.iterrows():
        fpath = FDD_RAW / "data_train" / rep.fdd_file
        df_ts = pd.read_csv(fpath)
        n = len(df_ts)
        # Assign synthetic timestamps: one reading per day starting 2024-01-01
        base_ts = datetime(2024, 1, 1)
        timestamps = [base_ts + timedelta(days=i) for i in range(n)]

        for col in ["H2", "CO", "C2H4", "C2H2"]:
            sensor_id = f"dga_{col.lower()}_ppm"
            unit = "ppm"
            values = df_ts[col].values * FDD_SCALE[col]
            for ts, val in zip(timestamps, values):
                rows.append(
                    {
                        "transformer_id": rep.transformer_id,
                        "timestamp": ts.isoformat(),
                        "sensor_id": sensor_id,
                        "value": round(float(val), 4),
                        "unit": unit,
                        "source": "fdd_rul",
                    }
                )

    # --- Real monitoring time-series for T-001 ---
    # Overview.csv: OTI = oil temp index (°C), WTI = winding temp index (°C)
    ov = pd.read_csv(RAW / "ai-transformer-monitoring" / "Overview.csv")
    ov = ov[ov["OTI"] > 0].copy()  # drop zero-padded rows
    for _, r in ov.iterrows():
        for sensor_id, col, unit in [
            ("oil_temp_c", "OTI", "°C"),
            ("winding_temp_c", "WTI", "°C"),
        ]:
            val = r[col]
            if pd.notna(val) and val > 0:
                rows.append(
                    {
                        "transformer_id": "T-001",
                        "timestamp": r["DeviceTimeStamp"],
                        "sensor_id": sensor_id,
                        "value": round(float(val), 2),
                        "unit": unit,
                        "source": "monitoring",
                    }
                )

    # CurrentVoltage.csv: VL1 (voltage L1, V), IL1 (current L1, A)
    cv = pd.read_csv(RAW / "ai-transformer-monitoring" / "CurrentVoltage.csv")
    cv = cv[cv["VL1"] > 0].copy()
    for _, r in cv.iterrows():
        for sensor_id, col, unit in [
            ("voltage_l1_v", "VL1", "V"),
            ("current_l1_a", "IL1", "A"),
        ]:
            val = r[col]
            if pd.notna(val) and val > 0:
                rows.append(
                    {
                        "transformer_id": "T-001",
                        "timestamp": r["DeviceTimeStamp"],
                        "sensor_id": sensor_id,
                        "value": round(float(val), 2),
                        "unit": unit,
                        "source": "monitoring",
                    }
                )

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "sensor_readings.csv", index=False)
    print(f"  sensor_readings.csv  ({len(df):,} rows)")
    return df


# ---------------------------------------------------------------------------
# Step 4: failure_modes.csv
# ---------------------------------------------------------------------------
# Derived from the unique fault types in the DGA dataset, enriched with
# IEC 60599 standard codes and recommended actions.

FAILURE_MODE_CATALOGUE = [
    {
        "failure_mode_id": "FM-001",
        "name": "Partial Discharge",
        "dga_label": "Partial discharge",
        "description": "Low-energy discharge within insulation voids. "
        "Generates mainly H2 and CH4.",
        "severity": "low",
        "iec_code": "PD",
        "key_gases": "H2,CH4",
        "recommended_action": "Monitor closely; schedule inspection within 90 days.",
    },
    {
        "failure_mode_id": "FM-002",
        "name": "Low-Temperature Overheating (< 300°C)",
        "dga_label": "Low-temperature overheating",
        "description": "Thermal fault in core laminations or due to sustained overload. "
        "Elevated CH4 and C2H4.",
        "severity": "medium",
        "iec_code": "T1",
        "key_gases": "CH4,C2H4",
        "recommended_action": "Reduce load; inspect within 30 days.",
    },
    {
        "failure_mode_id": "FM-003",
        "name": "Low/Middle-Temperature Overheating (< 700°C)",
        "dga_label": "Low/Middle-temperature overheating",
        "description": "Thermal fault in conductors or connections. "
        "High C2H4 relative to C2H6.",
        "severity": "medium",
        "iec_code": "T2",
        "key_gases": "C2H4,C2H6",
        "recommended_action": "De-energize and inspect within 7 days.",
    },
    {
        "failure_mode_id": "FM-004",
        "name": "Middle-Temperature Overheating",
        "dga_label": "Middle-temperature overheating",
        "description": "Medium thermal fault with high C2H4 and C2H6.",
        "severity": "high",
        "iec_code": "T2",
        "key_gases": "C2H4,C2H6",
        "recommended_action": "De-energize and inspect within 48 hours.",
    },
    {
        "failure_mode_id": "FM-005",
        "name": "High-Temperature Overheating (> 700°C)",
        "dga_label": "High-temperature overheating",
        "description": "Severe winding conductor overheating. "
        "Very high C2H4 and C2H6.",
        "severity": "critical",
        "iec_code": "T3",
        "key_gases": "C2H4,C2H6,H2",
        "recommended_action": "Immediate de-energization required.",
    },
    {
        "failure_mode_id": "FM-006",
        "name": "Spark Discharge",
        "dga_label": "Spark discharge",
        "description": "Low-energy electrical sparking in oil. "
        "Elevated C2H2 and H2.",
        "severity": "high",
        "iec_code": "D1",
        "key_gases": "C2H2,H2",
        "recommended_action": "De-energize and inspect within 48 hours.",
    },
    {
        "failure_mode_id": "FM-007",
        "name": "Arc Discharge",
        "dga_label": "Arc discharge",
        "description": "High-energy arcing causing severe oil decomposition. "
        "Very high C2H2 and H2.",
        "severity": "critical",
        "iec_code": "D2",
        "key_gases": "C2H2,H2,C2H4",
        "recommended_action": "Immediate de-energization and emergency inspection.",
    },
]


def make_failure_modes() -> pd.DataFrame:
    df = pd.DataFrame(FAILURE_MODE_CATALOGUE)
    df.to_csv(OUT / "failure_modes.csv", index=False)
    print(f"  failure_modes.csv  ({len(df)} rows)")
    return df


# ---------------------------------------------------------------------------
# Step 5: dga_records.csv
# ---------------------------------------------------------------------------
# One real DGA sample per transformer, sourced from the DGA Fault Classification
# dataset and the Health Index dataset.
#
# Fault type → transformer tier mapping:
#   healthy_long / healthy_aging  → no match in DGA (all DGA rows are faulty)
#                                   → use Health Index rows with high health index
#   minor_fault                   → Low/Middle-temperature overheating, Partial discharge
#   serious_fault                 → Arc discharge, Spark discharge, High-temp overheating


def make_dga_records(reps: pd.DataFrame) -> pd.DataFrame:
    dga = pd.read_csv(
        RAW / "dissolved-gas-analysis-of-transformer" / "DGA-dataset-1.csv"
    )
    hi = pd.read_csv(
        RAW / "sample-power-transformers-health-condition-dataset" / "Health index2.csv"
    )

    # Health Index dataset uses different gas column names — rename to match DGA
    hi = hi.rename(
        columns={
            "Hydrogen": "H2",
            "Methane": "CH4",
            "Ethylene": "C2H4",
            "Ethane": "C2H6",
            "Acethylene": "C2H2",
            "CO": "CO",
            "CO2": "CO2",
        }
    )

    # Transformers T-001..T-010 are healthy → sample from Health Index (high score)
    healthy_hi = hi.sort_values("Health index", ascending=False).head(30)

    # Fault families for each tier
    minor_types = [
        "Low-temperature overheating",
        "Low/Middle-temperature overheating",
        "Partial discharge",
    ]
    serious_types = ["Arc discharge", "Spark discharge", "High-temperature overheating"]

    rows = []
    healthy_idx = 0
    minor_dga = dga[dga["Type"].isin(minor_types)].reset_index(drop=True)
    serious_dga = dga[dga["Type"].isin(serious_types)].reset_index(drop=True)
    minor_idx = 0
    serious_idx = 0

    for _, rep in reps.iterrows():
        tid = rep.transformer_id

        if rep.tier in ("healthy_long", "healthy_aging"):
            src_row = healthy_hi.iloc[healthy_idx % len(healthy_hi)]
            healthy_idx += 1
            fault_label = "Normal"
            h2 = float(src_row.get("H2", 0))
            ch4 = float(src_row.get("CH4", 0))
            c2h2 = float(src_row.get("C2H2", 0))
            c2h4 = float(src_row.get("C2H4", 0))
            c2h6 = float(src_row.get("C2H6", 0))
            co = float(src_row.get("CO", 0))
            co2 = float(src_row.get("CO2", 0))

        elif rep.tier == "minor_fault":
            src_row = minor_dga.iloc[minor_idx % len(minor_dga)]
            minor_idx += 1
            fault_label = src_row["Type"]
            h2 = float(src_row["H2"])
            ch4 = float(src_row.get("CH4", 0))
            c2h2 = float(src_row["C2H2"])
            c2h4 = float(src_row["C2H4"])
            c2h6 = float(src_row.get("C2H6", 0))
            co = 0.0
            co2 = 0.0

        else:  # serious_fault
            src_row = serious_dga.iloc[serious_idx % len(serious_dga)]
            serious_idx += 1
            fault_label = src_row["Type"]
            h2 = float(src_row["H2"])
            ch4 = float(src_row.get("CH4", 0))
            c2h2 = float(src_row["C2H2"])
            c2h4 = float(src_row["C2H4"])
            c2h6 = float(src_row.get("C2H6", 0))
            co = 0.0
            co2 = 0.0

        rows.append(
            {
                "transformer_id": tid,
                "sample_date": "2024-01-15",
                "dissolved_h2_ppm": h2,
                "dissolved_ch4_ppm": ch4,
                "dissolved_c2h2_ppm": c2h2,
                "dissolved_c2h4_ppm": c2h4,
                "dissolved_c2h6_ppm": c2h6,
                "dissolved_co_ppm": co,
                "dissolved_co2_ppm": co2,
                "fault_label": fault_label,
                "source_dataset": (
                    "health_index"
                    if rep.tier in ("healthy_long", "healthy_aging")
                    else "dga_fault_classification"
                ),
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "dga_records.csv", index=False)
    print(f"  dga_records.csv  ({len(df)} rows)")
    return df


# ---------------------------------------------------------------------------
# Step 6: rul_labels.csv
# ---------------------------------------------------------------------------
# One row per (transformer, day) using the RUL from labels_rul_train.csv as
# the end-of-window value, counting backwards over 30 days.


def make_rul_labels(reps: pd.DataFrame) -> pd.DataFrame:
    rows = []
    base = datetime(2024, 1, 1)
    days = 30

    for _, rep in reps.iterrows():
        end_rul = rep.rul_days
        for d in range(days + 1):
            ts = base + timedelta(days=d)
            rul = end_rul + (days - d)  # counts up going backward in time
            rows.append(
                {
                    "transformer_id": rep.transformer_id,
                    "timestamp": ts.strftime("%Y-%m-%d"),
                    "rul_days": rul,
                    "health_index": round(min(1.0, rul / 1093.0), 4),
                    "fdd_category": rep.fdd_category,
                }
            )

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "rul_labels.csv", index=False)
    print(f"  rul_labels.csv  ({len(df)} rows)")
    return df


# ---------------------------------------------------------------------------
# Step 7: fault_records.csv
# ---------------------------------------------------------------------------
# Distribute the 506 fault events from the Smart Grid Fault Records dataset
# across transformers.  Serious-fault transformers get more events; healthy
# ones get fewer.

FAULT_WEIGHT = {
    "healthy_long": 0.5,
    "healthy_aging": 1.0,
    "minor_fault": 2.0,
    "serious_fault": 3.5,
}


def make_fault_records(reps: pd.DataFrame) -> pd.DataFrame:
    raw_faults = pd.read_csv(RAW / "power-system-faults-dataset" / "fault_data.csv")

    # Build a weighted pool of transformer IDs to assign to each fault row
    pool: list[str] = []
    for _, rep in reps.iterrows():
        weight = FAULT_WEIGHT[rep.tier]
        pool.extend([rep.transformer_id] * int(weight * 10))

    rng_local = np.random.default_rng(SEED)
    assigned_ids = rng_local.choice(pool, size=len(raw_faults), replace=True)

    df = raw_faults.copy()
    df.insert(0, "transformer_id", assigned_ids)
    df.rename(
        columns={
            "Fault ID": "fault_id",
            "Fault Type": "fault_type",
            "Fault Location (Latitude, Longitude)": "location",
            "Voltage (V)": "voltage_v",
            "Current (A)": "current_a",
            "Power Load (MW)": "power_load_mw",
            "Temperature (°C)": "temperature_c",
            "Wind Speed (km/h)": "wind_speed_kmh",
            "Weather Condition": "weather_condition",
            "Maintenance Status": "maintenance_status",
            "Component Health": "component_health",
            "Duration of Fault (hrs)": "duration_hrs",
            "Down time (hrs)": "downtime_hrs",
        },
        inplace=True,
    )

    df.to_csv(OUT / "fault_records.csv", index=False)
    print(f"  fault_records.csv  ({len(df)} rows)")
    return df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"Building processed datasets → {OUT}\n")

    reps = select_representatives()
    print(f"Selected {len(reps)} representative transformers:")
    print(
        reps[
            ["transformer_id", "fdd_file", "fdd_category", "rul_days", "tier"]
        ].to_string(index=False)
    )
    print()

    make_asset_metadata(reps)
    make_sensor_readings(reps)
    make_failure_modes()
    make_dga_records(reps)
    make_rul_labels(reps)
    make_fault_records(reps)

    print("\nAll processed files written to data/processed/")
