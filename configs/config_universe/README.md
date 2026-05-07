# Config Universe

Generated SmartGridBench experiment configs for opportunistic compute waves.
The evidence registry, not this directory, decides which completed runs are paper-grade.

Materialize the per-row `.env` files locally on a VM with:

```bash
python3 scripts/generate_config_universe.py
```

This writes ignored files under `configs/config_universe/generated/`. The
tracked source of truth is the generator plus this directory's `catalog.tsv` and
`cohorts/*.tsv` manifests. Each cohort TSV has the existing two-column runner
shape: `label` and `config`, and the `config` paths resolve after local
materialization.

Check that the tracked manifests are fresh with:

```bash
python3 scripts/generate_config_universe.py --check
```

`--check` regenerates in place before comparing tracked manifests. If it
fails, run the generator normally and inspect the resulting diff.

## Cohorts

| Cohort | Rows | Expected trajectories | Notes |
|---|---:|---:|---|
| `context_all31x3_full` | 60 | 6480 | 8K/16K/32K context ablations for every local method row |
| `decoding_all31x3` | 14 | 1512 | temperature ablation on core local rows |
| `local_all31x5_full` | 20 | 3600 | full local 8B method cross-product over all 31 canonical scenarios |
| `local_fmsr7_5x_full` | 20 | 800 | local 8B method cross-product on one canonical domain slice |
| `local_generated5x5_full` | 20 | 500 | local 8B method cross-product over the latest reviewed generated-scenario batch |
| `local_iot6_5x_full` | 20 | 900 | local 8B method cross-product on one canonical domain slice |
| `local_multi7_5x_full` | 20 | 700 | local 8B method cross-product on one canonical domain slice |
| `local_smoke1x1_full` | 20 | 20 | one-scenario local 8B smoke for every local method row |
| `local_tsfm5_5x_full` | 20 | 500 | local 8B method cross-product on one canonical domain slice |
| `local_wo6_5x_full` | 20 | 700 | local 8B method cross-product on one canonical domain slice |
| `mitigation_all31x5_full` | 64 | 11520 | 4-tier mitigation ladder crossed with every PE-family local method |
| `mitigation_generated5x5_full` | 64 | 1600 | 4-tier mitigation ladder over the latest reviewed generated-scenario batch |
| `repair_depth_all31x3` | 24 | 2592 | repair/adjudication depth ablation on the main Self-Ask PE-family rows |
| `watsonx70b_all31x5_full` | 11 | 1980 | hosted-70B all-31 core/transport PE-family expansion |
| `watsonx70b_generated5x5_full` | 11 | 275 | hosted-70B method cross-product over the latest reviewed generated-scenario batch |
| `watsonx70b_mitigation_all31x5_full` | 32 | 5760 | hosted-70B mitigation ladder for hosted-compatible PE-family rows |
| `watsonx70b_mitigation_generated5x5_full` | 32 | 800 | hosted-70B mitigation ladder over the latest reviewed generated-scenario batch |
| `watsonx70b_smoke1x1_full` | 11 | 11 | one-scenario hosted-70B smoke for every hosted-compatible method row |

## Guardrails

- Run `local_smoke1x1_full` or `watsonx70b_smoke1x1_full` before a new family if access or runner state changed.
- Preserve raw run directories. Promote only after pullback, count validation, judge rows, and registry review.
- Hosted WatsonX rows require fresh credentials plus all aliases: `WATSONX_APIKEY`, `WATSONX_API_KEY`, `WX_API_KEY`, `WATSONX_PROJECT_ID`, `WX_PROJECT_ID`, `WATSONX_URL`, `WX_URL`.
- D/TD local rows require the INT8 model path and FlashInfer build dependencies on the VM.
