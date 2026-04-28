# DGA Statistical Realism Validation

*Created: 2026-04-28*
*Owner: Alex Xin (`wax1`)*
*Issue/PR anchors: `#2`, `#51`, `#52`, `#53`, **PR #147** (PS B scenario generator scaffold)*

This note is the working specification for **statistical-fidelity** validation
of the synthetic transformer DGA data that backs Problem-Statement B (PS B)
scenarios. It complements, but does not replace, the existing
narrative-realism rubric in `docs/scenario_realism_validation.md` and the
schema validator in `data/scenarios/validate_scenarios.py`.

It captures everything we know as of 2026-04-28: the IEC 60599 (publication
**66491**) status, what we have already ingested into the repo, what's still
missing, the public datasets we plan to compare against, the test battery,
the acceptance thresholds, and the pre-final-submission plan.

---

## 1. Origin

The PS B lane (issue `#2`) generates transformer-maintenance scenarios on top
of synthetic DGA data produced by `data/generate_synthetic.py`. Three
artifacts already validate scenarios at increasing depth:

| Layer | What it checks | Owner / Artifact |
|-------|----------------|------------------|
| **L1** Schema / structural | required fields, canonical tool names, asset-id integrity | `data/scenarios/validate_scenarios.py` |
| **L2** Narrative realism | "would a transformer engineer recognize this as plausible work?" | `docs/scenario_realism_validation.md`, `docs/ps_b_evaluation_methodology.md`, mentor review (Dhaval), Akshat in `#53` |
| **L3** Statistical fidelity | do the gas-concentration distributions and fault-class proportions in our synthetic dataset resemble published real-world DGA data? | **this doc + `data/scenarios/validate_realism_statistical.py`** |

L3 was previously implicit. The Apr 28 conversation around
[PR #147](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/pull/147)
(Aaron's `aaron/issue2-scenario-generator` scaffold, +1031/-0) and the
Dhaval pre-call Q&A bank
(`Final_Project/planning/2026-04-28_smartgridbench_qa_bank.md` § "Knowledge
artifacts" + § "What is realism") made the gap explicit: we have a strong
narrative-realism story but no quantitative claim that synthetic gas
distributions match field data. Without L3 we cannot defend the synthetic
foundation in the May 4 final report.

**Why now:** PR #147 lands the generator path that will produce the first
reviewable batch. Akshat's `#53` validation pass needs to point at *both*
narrative ratings *and* a statistical report card. May 4 deadline → L3 must
ship before submission.

**Driving question:** *how do we validate that our scenarios represent
real-world scenarios?*

**Reference docs:**
- `docs/ps_b_evaluation_methodology.md` (6-criteria rubric; L3 plugs into the
  "Realism" criterion as a quantitative substrate)
- `docs/scenario_realism_validation.md` (Apr 10/11 narrative-realism note)
- `data/knowledge/transformer_standards.json` (encoded standards facts)
- `mcp_servers/fmsr_server/server.py` (Rogers Ratio classifier)

---

## 2. IEC 60599 (publication 66491) — what is it, what we have, what we don't

### 2.1 The standard

- **Webstore ID:** [66491](https://webstore.iec.ch/en/publication/66491)
- **Title:** *Mineral oil-filled electrical equipment in service — Guidance
  on the interpretation of dissolved and free gases analysis*
- **Edition:** 4th edition, published 2022-05-25 (replaces 3rd ed. 2015)
- **Length:** 80 pp, 1.59 MB
- **Stability date:** 2026
- **Issuing TC:** IEC TC 10 (Fluids for electrotechnical applications)
- **Scope:** dissolved + free gas interpretation for transformers, reactors,
  bushings, switchgear, oil-filled cables — application annexes per
  equipment class
- **List price:** ~CHF 270 / ~USD 300, paywalled at IEC, ANSI, VDE, Accuris
- **Companion standard:** IEEE C57.104-2019 (DGA condition framework) — we
  treat them as a pair

### 2.2 What we have ingested

| Artifact | Location | Source for |
|----------|----------|-----------|
| Rogers Ratio fault table (R1/R2/R3 ranges → IEC fault codes PD/T1/T2/T3/D1/D2) | `data/knowledge/transformer_standards.json` § `iec_60599.rogers_ratio_method.fault_table` | `_rogers_ratio()` classifier, generation hints |
| Key-gas guide | same JSON | per-fault gas-signature heuristics |
| Representative gas profiles | same JSON | synthesis defaults |
| IEEE C57.104-2019 four-condition framework + Table 1 thresholds | same JSON § `ieee_c57_104` | health-tier stratification of T-001..T-020 |
| Operational context (maintenance horizons, work-order minimums) | same JSON § `operational_context` | WO scenarios |
| Per-scenario-type generation hints | same JSON § `scenario_generator_hints` | LLM prompt support |
| Rogers Ratio classifier impl | `mcp_servers/fmsr_server/server.py:53-296` (`_rogers_ratio()` + `analyze_dga`) | FMSR MCP tool, agent-callable |
| Test coverage | `tests/test_fmsr_server.py` | confirms IEC code "N" / "Normal / Inconclusive" is a valid output |
| Doc references | `README.md`, `CHANGELOG.md`, `docs/scenario_realism_validation.md`, `docs/project_synopsis.md`, `planning/archive/task_tracker.md`, `planning/archive/task_specs.md`, `planning/archive/mid_report_slides.md`, `planning/archive/2026-04-07_call_agenda.md` | establishes that PS B is grounded in IEC 60599 + IEEE C57.104, not arbitrary heuristics |

### 2.3 What we do NOT have

- **Raw 80-page PDF** (paywalled, never licensed).
- **Application annexes** beyond transformers — reactors, bushings,
  switchgear, oil-filled cables. Currently our synthesis is transformer-only
  so this is acceptable, but the gap should be flagged in the paper.
- **"Free gases" interpretation guidance** added in the 4th edition (vs the
  3rd ed.'s dissolved-only scope).
- **Edition citation in `transformer_standards.json` `meta.source`** — the
  JSON does not currently pin which edition the encoded thresholds came from.
  Confirm 4th ed. 2022 vs 3rd ed. 2015 and update.
- **IEC TC 10 raw case database** (~117 cases) — referenced inside IEC 60599
  Annex A. We have it transitively via Duval & dePablo 2001 reproduction
  (see § 4) but not as a primary file in the repo.

### 2.4 Free-PDF acquisition status (Apr 28 search)

We searched in this session for legitimate-and-free access to the full PDF.

| Source | Result | Notes |
|--------|--------|-------|
| `pstco.net/wp-content/uploads/2023/04/IEC-60599-2022.pdf` | unreachable from this network (HTTP 000) | claimed full standard; likely unauthorized re-host; verify legality before use |
| `cdn.standards.iteh.ai/.../IEC-60599-2022.pdf` (sample) | downloaded, **15 pages of 80** | preview only — ToC, foreword, intro |
| iteh.ai CMV variant | downloaded, **14 pages** | "commented version" preview |
| Anna's Archive (`annas-archive.gd`) | **no 2022 4th ed.** | older eds present (2007/2008/2015/2016); 3rd ed. 2015 is the closest practical fallback (same Rogers Ratio fault table) |
| Columbia Engineering Library | not directly subscribed to IEC | ILL is the recommended legitimate path; user emailed library 2026-04-28 |
| IBM / Dhaval | likely has enterprise IEC license | user emailed Dhaval 2026-04-28 |
| ResearchGate (Clerot et al., DGA.pdf) | full text of *companion* paper, not the standard | useful as secondary methodology citation |
| Authorized purchase | webstore.iec.ch / ANSI / VDE / Accuris | ~$300; defer unless ILL fails |

**Recommendation:** wait on the library + Dhaval emails. If neither produces
a copy by 2026-05-01, fall back to the **3rd edition (2015)** via Anna's
Archive — Rogers Ratio fault table is unchanged across editions; only the
"free gases" annex is new in the 4th. For our scope (dissolved-gas-only
synthesis), the 3rd ed. is functionally sufficient.

---

## 3. Existing implementation snapshot

### 3.1 Synthesis pipeline

```
data/generate_synthetic.py
     │
     ├─ make_asset_metadata()    → 20 transformers T-001..T-020,
     │                             stratified across 4 IEEE C57.104
     │                             health tiers (Conditions 1-4)
     │
     ├─ make_dga_records()       → 1 DGA sample per transformer
     │                             columns: H2, CH4, C2H2, C2H4, C2H6,
     │                                       CO, CO2 + fault_label
     │                             output: data/processed/dga_records.csv (21 lines)
     │
     ├─ make_sensor_readings()   → hourly traces × 30 days × 20 transformers
     │                             output: data/processed/sensor_readings.csv (5.0 MB)
     │
     ├─ make_failure_modes()     → fault-mode catalogue
     ├─ make_fault_records()     → discrete fault events
     └─ make_rul_labels()        → RUL labels for TSFM
```

`data/build_processed.py` is the orchestrator. The 20-transformer stratified
sample is intentionally small — it's enough for end-to-end scenario
authoring, not enough for distributional analysis. **L3 validation needs
either (a) more synthetic samples, or (b) bootstrapping, or (c) a multi-day
synthesis to expand n.**

### 3.2 FMSR Rogers Ratio classifier

`mcp_servers/fmsr_server/server.py:53-296` implements `_rogers_ratio()`:

- Input: H2, CH4, C2H2, C2H4, C2H6 (ppm)
- Computes R1 = C2H2/C2H4, R2 = CH4/H2, R3 = C2H4/C2H6
- Looks up IEC 60599 Table 1 ranges → returns `{iec_code, label,
  severity, condition_4_trigger}`
- Codes: `N` (Normal/Inconclusive), `PD`, `T1`, `T2`, `T3`, `D1`, `D2`
- Test coverage in `tests/test_fmsr_server.py`

### 3.3 PR #147 — PS B scenario generator scaffold

[PR #147](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/pull/147)
(branch `aaron/issue2-scenario-generator`, author **afan2g** = Aaron Fan,
state **OPEN** as of 2026-04-28T21:58Z, 4 files, +1031/-0).

**What it lands:**

```
docs/knowledge/scenario_generation_support.json   ← family matrix + templates (#83/#90)
docs/knowledge/generated_scenario_authoring_and_ground_truth.md  ← no-hint contract + GT schema
docs/knowledge/generated_scenario_template.json   ← annotated template
                              │
                              ▼
                scripts/generate_scenarios.py
                              │
       ┌──────────────────────┼──────────────────────┐
       ▼                      ▼                      ▼
  load support           build_prompt           call_llm via LiteLLM
  load handcrafted      (no-hint rules         (default WatsonX
  load asset_ids         inlined verbatim)      Llama-3.3-70B —
                                                no GPU contention with W5)
                                                       │
                                                       ▼
                                             parse_response
                                             attach_provenance
                                             nearest_handcrafted
                                             validate_scenario
                                              ↑
                                              └── reuses
                                                  data/scenarios/validate_scenarios.py (L1 only)
                                                       │
       ┌─────────────────────────────────────────────┴─────────────────────┐
       ▼                                                                   ▼
data/scenarios/generated/<batch_id>/SGT-GEN-NNN.json          .../invalid/SGT-GEN-NNN.json
+ batch_manifest.json                                         (with validator error list)
+ prompts/                                                    for debugging / iteration
+ raw_responses/
```

**L3 plug-in point:** PR #147 currently calls `validate_scenarios.py` (L1
schema only). After PR #147 merges, scenario batches should also feed their
underlying gas-concentration data through `validate_realism_statistical.py`
in CI / pre-promotion. The L3 report card belongs in
`reports/realism_statistical_<batch_id>.md` next to the batch manifest.

### 3.4 Realism review surfaces

- `docs/scenario_realism_validation.md` — narrative-realism note, owner Alex,
  Apr 10/11. Pre-Dhaval review.
- `docs/ps_b_evaluation_methodology.md` — 6-criteria rubric (schema, no-hint,
  novelty, **realism**, tool-path, usefulness) + 5-disposition decision
  (`reject_structural`, `accept`, `accept_with_edits`, `reject_duplicate`,
  `reject_unusable`). Issue `#51`. The "realism" column today is a 3-bucket
  human rating (`accept | borderline | reject`); L3 supplies the
  quantitative substrate.
- Issue `#53` (Akshat) — applies the methodology to the first generated
  batch.
- Issue `#52` (Alex) — comparative analysis hand-crafted vs generated.

---

## 4. Real-world DGA datasets — ranked

Acquisition target list, ranked by usefulness × accessibility.

| Rank | Dataset | Access | Fields | Labels | Notes |
|------|---------|--------|--------|--------|-------|
| 1 | **IEEE DataPort DGA Dataset** (Dissanayake 2026) — DOI [10.21227/27vy-h479](https://ieee-dataport.org/documents/dga-dataset) | Columbia IEEE subscription | H2, CH4, C2H6, C2H4, C2H2 + integer fault label | yes | **Three Excel files**: balanced training, **unseen real-world test set**, **canonical IEC TC 10 benchmark**. Best primary target. |
| 2 | **IEC TC 10 raw set** (~117 cases) | Reproduced in [Duval & dePablo 2001](https://ieeexplore.ieee.org/iel5/57/19819/00917529.pdf) (IEEE Xplore, Columbia access) | 5 fault gases + fault-class labels | yes | Historical reference; cited by IEC 60599 itself. Smaller n but authoritative. |
| 3 | **Kaggle: [Failure Analysis in Power Transformers](https://www.kaggle.com/datasets/shashwatwork/failure-analysis-in-power-transformers-dataset)** (shashwatwork) | direct download, no auth | DGA + failure metadata | yes | Frictionless backstop if IEEE DataPort is gated. |
| 4 | **IEEE DataPort: [DGA + Membership Degree](https://ieee-dataport.org/documents/dissolved-gas-data-transformer-oil-fault-diagnosis-power-transformers-membership-degree)** | IEEE subscription | gas concentrations + fault labels | yes | Different fault-encoding scheme; useful as secondary check on label-mapping robustness. |
| 5 | **GitHub: [ahmedtariq71/Dataset1](https://github.com/ahmedtariq71/Dataset1)** | public | DGA samples | yes | Companion to a published paper. |
| 6 | **GitHub: NanaudKmer/Springer_EETE_…_Ranking_Sequence** | public | DGA + MATLAB methods | yes | Useful for cross-checking Rogers/Doernenburg implementations more than for distribution comparison. |
| 7 | **Kaggle: [Distributed Transformer Monitoring](https://www.kaggle.com/datasets/sreshta140/ai-transformer-monitoring)** | direct | sensor traces | partial | More relevant for IoT scenario realism (sensor-side) than for DGA-side L3. |

**Acquisition path:**

1. Pull dataset #1 via Columbia IEEE access. If IEEE DataPort requires a
   separate subscription on top of the IEEE digital library, Columbia ILL
   should still work.
2. Backstop with #3 (Kaggle) — no auth, immediate.
3. For #2, extract IEC TC 10 case data from the Duval & dePablo 2001
   tables/figures, type into a CSV under `data/external/iec_tc10_duval2001.csv`.
4. Place all real datasets under `data/external/` (gitignored if licensed,
   committed if open).

---

## 5. Validation methodology

### 5.1 Test battery

| Test | Compares | Catches | Threshold |
|------|----------|---------|-----------|
| Two-sample **Kolmogorov-Smirnov** per gas | marginal `gas_i` distributions: synthetic vs real | shape mismatch in any single gas | `p > 0.05` |
| **Anderson-Darling** k-sample per gas | same, weighted toward tails | extreme-value miscalibration (matters for D2 / arcing) | `p > 0.05` |
| **Wasserstein / EMD** per gas | distributions, smooth metric | integrated "how far apart" measure | `EMD / std_real ≤ 0.20` |
| **Chi-squared** on fault-class proportions | fault prevalence: synthetic vs real (or vs TC10 ref) | mis-stratified fault frequency | `p > 0.05` |
| **Conditional KS**: `gas_i \| fault_class` | per-fault gas signatures | "marginals match but PD scenarios have wrong CH4 mean" | `p > 0.05` |
| **Pearson correlation Δ** matrix | inter-gas correlation structure | uncorrelated noise pretending to be physical signal | `max abs Δ ≤ 0.20` |

### 5.2 Why these tests, in plain English

1. **KS** — basic sanity: do our H2 readings come from the same shape as real
   H2 readings? Cheap, well-understood, scale-free.
2. **Anderson-Darling** — KS is weak in the tails. AD weights tails heavier.
   Critical for arcing (D2) where we care about extreme C2H2 values.
3. **EMD** — KS gives a binary p-value answer. EMD gives a continuous
   "how close" answer that doesn't blow up at large n. Good for
   visualization and trend reporting.
4. **Chi-squared on fault prevalence** — even if every gas distribution is
   perfect, if our synthesis emits 80% Normal / 20% PD when real data is
   27% Normal / 7% PD / 13% T1 / …, the benchmark is biased.
5. **Conditional KS per fault** — passes the marginal but fails the
   conditional means our PD scenarios have realistic-looking H2 *across the
   whole population* but specifically the PD subset has wrong H2. This is
   how you detect "synthesis is averaging out the physics."
6. **Correlation Δ** — real DGA gases co-vary in physically meaningful ways
   (CH4 ↔ C2H6 in low-temp thermal; C2H2 ↔ C2H4 in arcing). Synthesis that
   draws each gas independently from a marginal distribution will pass the
   first five tests and fail this one.

### 5.3 Reference fault prevalence (TC 10)

From IEC 60599 Annex A / Duval & dePablo 2001:

| Fault | Approx. share |
|-------|---------------|
| Normal | ~27% |
| PD | ~7% |
| T1 | ~13% |
| T2 | ~10% |
| T3 | ~13% |
| D1 | ~13% |
| D2 | ~17% |

Encoded in `validate_realism_statistical.py:TC10_REFERENCE_PREVALENCE`. Used
as the chi-squared `f_exp` when no real dataset is loaded; superseded by the
real dataset's empirical proportions when one is available.

### 5.4 Precedent paper

**Bashir et al. (2024)**, *Optimized Synthetic Data Integration with
Transformer's DGA Data for Improved ML-Based Fault Identification*. Mirror
their methodology: per-gas distribution comparison, fault-prevalence chi-2,
synthetic-augmented training set vs real-only test set. Citation goes in
the paper's methodology section.

---

## 6. Implementation — `validate_realism_statistical.py`

Skeleton landed in this PR at `data/scenarios/validate_realism_statistical.py`.

### 6.1 Interface

```bash
python3 data/scenarios/validate_realism_statistical.py \
    --synthetic data/processed/dga_records.csv \
    --real      data/external/ieee_dataport_dga.csv \
    --report    reports/realism_statistical_v1.md \
    --json      reports/realism_statistical_v1.json
```

Exit code = 0 if all tests pass, 1 otherwise. Suitable for CI gating.

### 6.2 Output: report card

Markdown table with columns: test name, statistic, p-value, threshold, pass,
detail. Summary line: `N passed of M tests`. JSON dump for programmatic
consumption.

### 6.3 Real-data adapter

`_normalize_real_columns()` recognizes column conventions for the four
likely sources: IEEE DataPort, Kaggle `failure-analysis`,
`ahmedtariq71/Dataset1`, and the Duval & dePablo TC 10 reproduction. New
sources → add a branch.

### 6.4 Behavior when real data is missing

If `--real` is omitted or the file doesn't exist, the script:

1. Emits a single chi-squared on synthetic fault prevalence vs
   `TC10_REFERENCE_PREVALENCE`.
2. Adds a `real_dataset_present: false` failing test with a pointer to this
   doc's § 4 acquisition list.
3. Returns exit 1 (so CI can't pass without real data).

This means the script is useful immediately — even before any real dataset
is loaded — and degrades cleanly.

### 6.5 Dependencies

- `pandas`, `numpy`, `scipy` (all already in repo deps)
- No new pin required; `scipy.stats.ks_2samp`,
  `scipy.stats.anderson_ksamp`, `scipy.stats.wasserstein_distance`, and
  `scipy.stats.chisquare` cover the test battery.

---

## 7. Pre-May 4 plan

| # | Task | Owner | Day | Acceptance |
|---|------|-------|-----|-----------|
| 1 | Land L3 skeleton + this doc | Alex | Apr 28 | this PR merges |
| 2 | Pin `transformer_standards.json` `meta.source` to IEC 60599 ed. 4 (2022) — or ed. 3 (2015) if that's what was actually used | Alex | Apr 29 | JSON `meta.source` field updated, CHANGELOG entry |
| 3 | Acquire IEEE DataPort DGA dataset (Columbia IEEE, or Kaggle backstop) | Alex | Apr 29 | `data/external/ieee_dataport_dga.csv` (or Kaggle equivalent) on disk |
| 4 | First L3 run: `validate_realism_statistical.py` with real data | Alex | Apr 29 | `reports/realism_statistical_v1.md` exists |
| 5 | Tune synthesis: if any test fails, adjust `data/generate_synthetic.py` per-fault gas means/stds, regenerate, re-run | Alex | Apr 30 – May 1 | majority of tests pass at v2 or v3 |
| 6 | Add L3 report-card figure to `reports/2026-05-04_final.pdf` § Methodology | Alex | May 2 | figure rendered, caption written |
| 7 | Wire L3 into PR #147 promotion path: each accepted batch produces a `realism_statistical_<batch_id>.md` | Alex / Aaron | May 2–3 | scaffold extended, doc updated |
| 8 | Mention dual-citation in paper: IEC 60599 + IEEE C57.104 + IEC TC 10 (via Duval 2001) | Alex | May 3 | references section updated |

**Hard contingency:** if no real dataset can be acquired by Apr 30, fall
back to TC 10 reference prevalence chi-squared only and document the gap as
a limitation in the paper. This is degraded but defensible.

---

## 8. Mentor / library questions (Apr 28 emails)

The user emailed Dhaval and the Columbia Engineering Library on 2026-04-28.
Questions to follow up on, ordered by leverage:

1. **Dhaval** — does IBM AssetOpsBench have an internal real-DGA dataset we
   can compare against, or should we stick with public benchmarks (IEEE
   DataPort + IEC TC 10 via Duval 2001)?
2. **Dhaval** — does IBM Research have an enterprise IEC license; can we
   reference the 4th-edition annex content for transformer applications in
   our methodology section?
3. **Library** — ILL request for IEC 60599:2022 (4th ed.); turnaround
   expectation; alternatives if IEC isn't ILL-able (peer-institution
   subscription, ASTM/Accuris backdoor).
4. **Library** — does Columbia have IEEE DataPort access bundled with the
   IEEE digital library subscription?

---

## 9. Open questions / risks

- **Small synthetic n.** `data/processed/dga_records.csv` has 20 rows. KS is
  unreliable below n ≈ 30 per group. Mitigations: (a) regenerate with more
  samples per transformer (multi-day synthesis); (b) bootstrap; (c) accept
  L3 as "directional, not significance-tested" until n grows. Decision:
  prefer (a) — extend `make_dga_records()` to emit 30 days × 20
  transformers = 600 samples.
- **Edition mismatch.** If `transformer_standards.json` was sourced from
  IEC 60599 3rd ed. (2015), but we cite 4th ed. (2022) in the paper, that's
  a defendable but noteworthy gap. Pin the edition explicitly.
- **Label-encoding mismatch across datasets.** IEEE DataPort uses integer
  fault codes; IEC 60599 uses alpha codes (PD/T1/T2/T3/D1/D2). Adapter
  function `_normalize_real_columns()` handles column names but not yet
  label values. Add a `LABEL_MAP` translation table per source.
- **Free-gas vs dissolved-gas scope.** The 4th-ed addition on free gases is
  not modeled in our synthesis. Acceptable for PS B but worth flagging.
- **CO/CO2 (cellulose-side) gases.** Excluded from L3 because IEC 60599
  Rogers Ratio operates on the 5 fault gases only. CO/CO2 belongs to IEEE
  C57.104 cellulose-degradation tracking — separate validation, possibly
  L4 / future work.

---

## 10. References

- IEC 60599:2022 (4th ed.), pub [66491](https://webstore.iec.ch/en/publication/66491). Mineral oil-filled electrical equipment — DGA interpretation. ICS 17.220.99, 29.040.10, 29.180. TC 10.
- IEEE C57.104-2019 — IEEE Guide for the Interpretation of Gases Generated in Mineral Oil-Immersed Transformers.
- Duval, M. & dePablo, A. (2001). *Interpretation of gas-in-oil analysis using new IEC publication 60599 and IEC TC 10 databases.* IEEE Electrical Insulation Magazine 17(2), 31–41. [IEEE Xplore link](https://ieeexplore.ieee.org/iel5/57/19819/00917529.pdf).
- Dissanayake, T. (2026). *DGA dataset.* IEEE DataPort. DOI [10.21227/27vy-h479](https://ieee-dataport.org/documents/dga-dataset).
- Bashir et al. (2024). *Optimized Synthetic Data Integration with Transformer's DGA Data for Improved ML-Based Fault Identification.* ResearchGate publication 381933991.
- IBM AssetOpsBench upstream: [github.com/IBM/AssetOpsBench](https://github.com/IBM/AssetOpsBench).
- Personal-repo Q&A bank: `Final_Project/planning/2026-04-28_smartgridbench_qa_bank.md` (especially § "Knowledge artifacts" and § "What is realism").
- Team-repo PS B methodology: `docs/ps_b_evaluation_methodology.md` (Issue `#51`).
- Team-repo narrative realism: `docs/scenario_realism_validation.md`.
- PR #147: [PS B scenario generator scaffold (#2 prototype)](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/pull/147), branch `aaron/issue2-scenario-generator`, author afan2g, opened 2026-04-28.

---

## 11. Implementation-Ready Checklist

- [ ] `data/scenarios/validate_realism_statistical.py` — skeleton landed. **Acceptance:** `python3 data/scenarios/validate_realism_statistical.py --synthetic data/processed/dga_records.csv --report /tmp/test.md` runs without error, emits a stub report indicating real dataset is missing.
- [ ] `docs/dga_realism_statistical_validation.md` — this file. **Acceptance:** PR review LGTM.
- [ ] `data/knowledge/transformer_standards.json` — pin `meta.source` edition. **Acceptance:** `meta.source` field includes "IEC 60599:2022" or "IEC 60599:2015" with deliberate decision recorded in CHANGELOG.
- [ ] `data/external/` — create dir; gitignore licensed datasets. **Acceptance:** `.gitignore` updated; placeholder README listing expected dataset filenames.
- [ ] `data/external/README.md` — dataset acquisition log. **Acceptance:** documents which of § 4's datasets have been acquired, when, by whom.
- [ ] `data/generate_synthetic.py` — extend `make_dga_records()` to emit ≥ 30 samples per transformer. **Acceptance:** `data/processed/dga_records.csv` has ≥ 600 rows; existing scenarios still validate against the expanded data.
- [ ] First L3 run (depends on real-data acquisition). **Acceptance:** `reports/realism_statistical_v1.md` exists, ≥ 70% of tests pass at v1, failing tests have follow-up tickets.
- [ ] Wire into PR #147 promotion path. **Acceptance:** when PR #147 merges, the scenario-batch promotion script also runs L3 and stores the report under `reports/`.
- [ ] Final report figure. **Acceptance:** `reports/2026-05-04_final.pdf` § Methodology contains an L3 report-card summary table.

### Acceptance Gates

- **Gate A (this PR):** skeleton + doc land; existing tests still pass; CHANGELOG entry added.
- **Gate B (Apr 30):** real dataset acquired; first L3 run produces a non-stub report.
- **Gate C (May 2):** at minimum the chi-squared on fault prevalence and KS on H2 + C2H2 pass; remaining failing tests documented as limitations.
- **Gate D (May 4):** L3 report-card cited in final paper as evidence of statistical realism.
