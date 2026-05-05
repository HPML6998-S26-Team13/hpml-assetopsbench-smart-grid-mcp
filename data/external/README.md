# data/external/

Real-world reference datasets used by `data/scenarios/validate_realism_statistical.py`
(L3 statistical-fidelity validation). CSVs are gitignored per the global `*.csv`
ignore — re-acquire from the sources below to reproduce L3 runs.

## Datasets

| Filename | Source | n | License | Used for |
|---|---|---|---|---|
| `DGA-dataset-1.csv` | Kaggle [`bantipatel20/dissolved-gas-analysis-of-transformer`](https://www.kaggle.com/datasets/bantipatel20/dissolved-gas-analysis-of-transformer) | 201 | Kaggle terms (re-download required) | Full L3 battery — has labeled `Type` column (Partial discharge / Spark discharge / Arc discharge / Low-/Middle-/High-temperature overheating). No `Normal` samples. |
| `transformer_dga_arias.csv` | Mendeley DOI [`10.17632/rz75w3fkxy.1`](https://data.mendeley.com/datasets/rz75w3fkxy/1) (Arias-Mejía Lara 2020). Also mirrored at Kaggle [`shashwatwork/failure-analysis-in-power-transformers-dataset`](https://www.kaggle.com/datasets/shashwatwork/failure-analysis-in-power-transformers-dataset). | 471 | CC-BY-4.0 | Marginal-distribution supplement (KS / EMD / AD on gases) — no fault labels, larger n than `DGA-dataset-1.csv`. |

## Acquisition

```bash
# Browser path (works without Kaggle CLI):
#   1. Sign in at kaggle.com
#   2. Download the dataset
#   3. Drop the CSV into data/external/
#
# CLI path (one-time setup):
pip install kaggle
# kaggle.com → Account → Create New API Token → save kaggle.json to ~/.kaggle/

kaggle datasets download -d bantipatel20/dissolved-gas-analysis-of-transformer \
  -p data/external/ --unzip

# Mendeley/Arias (no auth required):
curl -L -o data/external/transformer_dga_arias.csv \
  "https://data.mendeley.com/public-files/datasets/rz75w3fkxy/files/198f668d-6e0a-481a-9499-2b37d79db683/file_downloaded"
```

## Run L3

```bash
python data/scenarios/validate_realism_statistical.py \
  --synthetic   data/processed/dga_records.csv \
  --real        data/external/DGA-dataset-1.csv \
  --real-source bantipatel20_dga \
  --report      reports/realism_statistical_v1.md \
  --json        reports/realism_statistical_v1.json
```

See `docs/dga_realism_statistical_validation.md` for methodology, thresholds,
and the v0 → v1 → v2 tuning narrative.
