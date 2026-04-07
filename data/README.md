# data/

Data pipeline for Smart Grid transformer datasets. Combines 5 Kaggle datasets into a unified, cross-domain format tied together by a synthesized `transformer_id` key.

## Structure

```
data/
├── build_processed.py      # Main pipeline: downloads raw Kaggle data, joins via synthesized
│                           #   transformer_id, writes the CSVs in processed/
├── generate_synthetic.py   # Offline synthetic generator (no Kaggle access required)
│                           #   Produces a fully-synthetic equivalent dataset for CI and dev
├── raw/                    # GITIGNORED — raw Kaggle downloads
├── processed/              # Joined, cleaned, TRACKED CSVs:
│   ├── asset_metadata.csv        # 20 fictional transformers (T-001..T-020)
│   ├── dga_records.csv           # 21 rows: DGA gas samples per transformer
│   ├── failure_modes.csv         # 8 rows: failure mode taxonomy
│   ├── fault_records.csv         # 507 rows: historical faults
│   ├── rul_labels.csv            # 621 rows: remaining useful life per transformer per snapshot
│   └── sensor_readings.csv       # 96,486 rows: timeseries telemetry
└── scenarios/              # Smart Grid scenario files (see scenarios/README.md)
```

## The `transformer_id` key

All 5 source Kaggle datasets cover different slices (gas analysis, health index, RUL, fault records, monitoring) with no common key between them. The pipeline synthesizes a fleet of **20 fictional transformers** (`T-001` through `T-020`) stratified across 4 health tiers (healthy long-life, healthy aging, minor fault, serious fault) and joins each source dataset against this synthetic fleet so that cross-domain queries return **coherent narratives** — a transformer's sensor anomalies align with its fault history which aligns with its failure modes which aligns with its work orders.

See `docs/data_pipeline.tex` for the full methodology writeup (paper-ready LaTeX section).

## Running the pipeline

```bash
# From repo root, with .venv active:

# Full pipeline (requires Kaggle credentials in ~/.kaggle/kaggle.json):
python data/build_processed.py

# Or, offline-only equivalent (no Kaggle access needed):
python data/generate_synthetic.py
```

## Licensing

- **3 of 5 source datasets are CC0** — Power Transformers FDD & RUL, DGA Fault Classification, Smart Grid Fault Records (used for FMSR, TSFM, WO)
- **2 of 5 have redistribution restrictions** — Transformer Health Index (ODbL), Current & Voltage Monitoring (author copyright) — used locally for IoT sensor data only
- **Public PR plans:** `generate_synthetic.py` will be the default IoT data source for any upstream PR to AssetOpsBench, so all 4 domains are covered end-to-end without any redistribution concerns. Real Kaggle data remains on team machines for internal benchmarking.

See Slide 5 of `reports/2026-04-06_midpoint_submission.pdf` for more detail on the licensing gap and mitigation.
