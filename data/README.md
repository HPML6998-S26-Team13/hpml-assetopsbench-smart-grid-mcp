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
├── processed/              # Public-safe TRACKED CSVs generated for development/repro:
│   ├── asset_metadata.csv        # 20 fictional transformers (T-001..T-020)
│   ├── dga_records.csv           # 20 synthetic DGA samples
│   ├── failure_modes.csv         # 6 failure mode entries
│   ├── fault_records.csv         # synthetic historical faults / maintenance events
│   ├── rul_labels.csv            # synthetic RUL labels per transformer per day
│   └── sensor_readings.csv       # hourly synthetic telemetry
└── scenarios/              # Smart Grid scenario files (see scenarios/README.md)
```

## The `transformer_id` key

All 5 source Kaggle datasets cover different slices (gas analysis, health index, RUL, fault records, monitoring) with no common key between them. The pipeline synthesizes a fleet of **20 fictional transformers** (`T-001` through `T-020`) stratified across 4 health tiers (healthy long-life, healthy aging, minor fault, serious fault) and joins each source dataset against this synthetic fleet so that cross-domain queries return **coherent narratives** — a transformer's sensor anomalies align with its fault history which aligns with its failure modes which aligns with its work orders.

See `docs/data_pipeline.tex` for the full methodology writeup (paper-ready LaTeX section).

## Running the pipeline

```bash
# From repo root, with .venv active:

# Full pipeline (requires Kaggle credentials in ~/.kaggle/kaggle.json and may ingest restricted-source data locally):
python data/build_processed.py

# Or, public-safe tracked outputs (no Kaggle access needed):
python data/generate_synthetic.py
```

## Licensing

- **3 of 5 source datasets are CC0** — Power Transformers FDD & RUL, DGA Fault Classification, Smart Grid Fault Records (used for FMSR, TSFM, WO)
- **2 of 5 have redistribution restrictions** — Transformer Health Index (ODbL), Current & Voltage Monitoring (author copyright) — used locally for IoT sensor data only
- **Tracked repo policy:** files committed under `data/processed/` must remain public-safe. The repo's tracked outputs should come from `generate_synthetic.py`, not from restricted-source Kaggle joins.
- **Local benchmarking policy:** if you run `build_processed.py` against Kaggle data, treat those outputs as local-only working data unless the license has been explicitly cleared for redistribution.
- **Upstream PR policy:** any contribution back to AssetOpsBench should use the synthetic/public-safe path by default so all four domains remain runnable without redistribution concerns.

See `docs/project_reference.md` and the midpoint report for the project-level context around this licensing constraint.
