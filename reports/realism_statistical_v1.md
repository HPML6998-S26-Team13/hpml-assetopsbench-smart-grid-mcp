# DGA Statistical Realism Report

- Synthetic: `data/processed/dga_records.csv` (n=20)
- Real: `data/external/DGA-dataset-1.csv` (n=201)
- Result: **5/27** tests passed

> **Caveat — directional/pre-tuning evidence.** Synthetic n=20 is below the ≈30/group rule of thumb for reliable KS / AD tests, and conditional-KS subsets shrink further. Treat this report as a v1 baseline that quantifies the synthesis-vs-real gap, not a final statistical-realism pass. See `docs/dga_realism_statistical_validation.md` § 9 / § 12.4 for the v2 tuning plan.

## Provenance

- Real source: `bantipatel20_dga` (retrieved 2026-05-05)
- Real CSV SHA256: `42a845b029f86877d3e633aee2bc1eead993c545640e85cb45eed41a0a567665`
- Real CSV MD5: `6443538fff0eeefc5dc0740e97f49ee1`
- Rows / columns: 201 / ['NM', 'H2', 'CH4', 'C2H6', 'C2H4', 'C2H2', 'Type']
- Script HEAD: `b2bb2837df6198708fef478242aa303d5a2d3746` (working tree dirty)
- Exact command: `python data/scenarios/validate_realism_statistical.py --synthetic data/processed/dga_records.csv --real data/external/DGA-dataset-1.csv --real-source bantipatel20_dga --report reports/realism_statistical_v1.md --json reports/realism_statistical_v1.json`
- Real label counts (raw `Type` column):
  - `Arc discharge`: 54
  - `Spark discharge`: 49
  - `High-temperature overheating`: 38
  - `Low-temperature overheating`: 19
  - `Partial discharge`: 16
  - `Low/Middle-temperature overheating`: 16
  - `Middle-temperature overheating`: 9
- Real label counts (after IEC mapping):
  - `D2`: 54
  - `D1`: 49
  - `T3`: 38
  - `T1`: 19
  - `PD`: 16
  - `T2`: 25

| Test | Statistic | p-value | Threshold | Pass | Detail |
|------|-----------|---------|-----------|------|--------|
| `chi2_fault_prevalence` | — | — | 0.05 | ❌ | reference=real (n_real=201, scaled to n_syn) has zero expected count for classes ['Normal'] but synthetic has rows there; chi-squared undefined. Acquire a real dataset covering those classes or apply a documented pseudocount. |
| `ks_h2` | 0.5622 | 0.0000 | 0.05 | ❌ |  |
| `ks_ch4` | 0.6269 | 0.0000 | 0.05 | ❌ |  |
| `ks_c2h2` | 0.5025 | 0.0001 | 0.05 | ❌ |  |
| `ks_c2h4` | 0.5174 | 0.0000 | 0.05 | ❌ |  |
| `ks_c2h6` | 0.3930 | 0.0046 | 0.05 | ❌ |  |
| `emd_h2` | 0.3593 | — | 0.2 | ❌ | raw_emd=3355.269, std_real=9337.918 |
| `emd_ch4` | 0.2924 | — | 0.2 | ❌ | raw_emd=2042.686, std_real=6985.987 |
| `emd_c2h2` | 0.2403 | — | 0.2 | ❌ | raw_emd=1221.439, std_real=5083.328 |
| `emd_c2h4` | 0.2493 | — | 0.2 | ❌ | raw_emd=2084.142, std_real=8358.881 |
| `emd_c2h6` | 0.1477 | — | 0.2 | ✅ | raw_emd=855.106, std_real=5791.306 |
| `ad_h2` | 15.7352 | 0.0010 | 0.05 | ❌ |  |
| `ad_ch4` | 14.2088 | 0.0010 | 0.05 | ❌ |  |
| `ad_c2h2` | 8.4747 | 0.0010 | 0.05 | ❌ |  |
| `ad_c2h4` | 9.4836 | 0.0010 | 0.05 | ❌ |  |
| `ad_c2h6` | 5.1320 | 0.0031 | 0.05 | ❌ |  |
| `ks_T1_h2` | 0.5263 | 0.1714 | 0.05 | ✅ | n_syn=5, n_real=19 |
| `ks_T1_ch4` | 0.3789 | 0.5114 | 0.05 | ✅ | n_syn=5, n_real=19 |
| `ks_T1_c2h2` | 0.9474 | 0.0003 | 0.05 | ❌ | n_syn=5, n_real=19 |
| `ks_T1_c2h4` | 0.6842 | 0.0309 | 0.05 | ❌ | n_syn=5, n_real=19 |
| `ks_T1_c2h6` | 0.5263 | 0.1714 | 0.05 | ✅ | n_syn=5, n_real=19 |
| `ks_D2_h2` | 0.7593 | 0.0037 | 0.05 | ❌ | n_syn=5, n_real=54 |
| `ks_D2_ch4` | 0.7778 | 0.0026 | 0.05 | ❌ | n_syn=5, n_real=54 |
| `ks_D2_c2h2` | 0.9074 | 0.0001 | 0.05 | ❌ | n_syn=5, n_real=54 |
| `ks_D2_c2h4` | 0.7778 | 0.0026 | 0.05 | ❌ | n_syn=5, n_real=54 |
| `ks_D2_c2h6` | 0.5185 | 0.1212 | 0.05 | ✅ | n_syn=5, n_real=54 |
| `corr_delta` | 0.9189 | — | 0.2 | ❌ | max abs(corr_syn - corr_real) over 5 gases |
