# DGA Statistical Realism Report

- Synthetic: `data/processed/dga_records.csv` (n=20)
- Real: `(none loaded)` (n=None)
- Result: **0/2** tests passed

| Test | Statistic | p-value | Threshold | Pass | Detail |
|------|-----------|---------|-----------|------|--------|
| `chi2_fault_prevalence` | 16.6667 | 0.0106 | 0.05 | ❌ | reference=TC10 reference, n_syn=20 |
| `real_dataset_present` | — | — | 0.0 | ❌ | No real dataset loaded; only TC10 reference prevalence was checked. Acquire a real DGA dataset (see docs/dga_realism_statistical_validation.md § Datasets). |
