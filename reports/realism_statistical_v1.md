# DGA Statistical Realism Report

- Synthetic: `data\processed\dga_records.csv` (n=20)
- Real: `data\external\DGA-dataset-1.csv` (n=201)
- Result: **5/27** tests passed

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
