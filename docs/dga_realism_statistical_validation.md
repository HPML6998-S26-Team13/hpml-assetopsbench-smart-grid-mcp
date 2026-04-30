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

L3 was previously implicit. The Apr 28 review of
[PR #147](https://github.com/HPML6998-S26-Team13/hpml-assetopsbench-smart-grid-mcp/pull/147)
(Aaron's `aaron/issue2-scenario-generator` scaffold, +1031/-0) and the
Dhaval pre-call Q&A pass made the gap explicit: we have a strong
narrative-realism story (mentor + domain-expert review of scenario text)
but no quantitative claim that synthetic gas distributions match field
data. Without L3 we cannot defend the synthetic foundation in the May 4
final report.

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

### 2.4 Three-way fault-table divergence (added 2026-04-28; resolved 2026-04-29)

PR #149 encodes Table 1 1:1 in the JSON `fault_table` and the FMSR server's
`_rogers_ratio()` — those are the canonical reconciliation contract; § 13
Appendix A provides citation, encoding conventions, and a paraphrased note
summary.

> **Status: RESOLVED in PR #149 (2b).** Both Table B (JSON `fault_table`)
> and Table C (server `_rogers_ratio`) were rewritten to match IEC 60599:2022
> Table 1 directly in PR #149. `representative_gas_profiles.profiles` were
> regenerated to round-trip via the new server table. The divergence summary
> below is retained as historical context; the current state is **B = C = A**.

**Pre-fix state — three different DGA-classification tables.**

| Table | Where | Pre-fix status | Post-fix status (PR #149) |
|-------|-------|----------------|---------------------------|
| **A — IEC 60599:2022 Table 1** | the standard, Table 1 | ground truth | unchanged — ground truth |
| **B — JSON `fault_table`** | `data/knowledge/transformer_standards.json` § `iec_60599.rogers_ratio_method.fault_table` | claimed IEC; diverged on every electrical-discharge row | rewritten to match A |
| **C — FMSR server `_rogers_ratio()`** | `mcp_servers/fmsr_server/server.py:65-90` | a third version; the one that ran at agent-call time | rewritten to match A; profiles round-trip |

**Worst divergences (B vs A):**

- **D1 R1**: JSON's pre-fix encoding `[0, 0.1]` did not overlap IEC's range — JSON's range ended where IEC's range began.
- **D1 R3**: JSON's pre-fix `[0, 1.0]` and IEC sat on opposite half-lines.
- **D2 R2**: JSON's pre-fix `[3.0, ∞)` did not overlap IEC; the bounds differed by an order of magnitude.
- **T2/T3 R3 boundary**: JSON and IEC placed the dividing value into different fault classes.

(Canonical encoding lives in PR #149's `fault_table` JSON; § 13 Appendix A
gives citation + encoding conventions.)

**Server's own divergence note (`server_rogers_table_note`):** Tanisha
already documents that the server's Rogers table diverges from IEC on PD,
D1, D2, and T1. The note ends: *"Profiles below are calibrated to the
server implementation, not the standard text."*

**Pattern**: JSON ↔ Server agree more often than either ↔ IEC, suggesting
both were derived from a derivative source (textbook, slide deck, or
tutorial) rather than from IEC text directly. The Rogers Ratio name
covers a family of tables — Rogers 1975, IEEE C57.104-1991 four-ratio,
IEC 60599 three-ratio (1999/2007/2015/2022). Without explicit edition
citations, drift is normal.

**Implication for L3:** marginal-KS per gas may pass (gas magnitudes in
the synthesis are physically plausible), but **conditional-KS per fault
class will likely fail on D1, D2, T1**, because synthetic samples were
generated to match the server's table — not IEC's. This explains the
v0 baseline's chi² p = 0.0106 fault-prevalence divergence and predicts
the shape of the v1 failures.

**Recommended remediation** (ranked):
1. Fix B and C in lockstep to match A; re-tune
   `representative_gas_profiles.profiles`; update
   `tests/test_fmsr_server.py` fixtures. Cost: high but one-time.
2. Add a translation layer; tag synthetic samples with both the server's
   code and the IEC-correct code; run L3 against IEC-correct only.
3. Document the divergence as a known limitation; run L3 with the
   server's table as ground truth (i.e., re-classify the real-world
   dataset using the server's table before comparing). Lowest effort,
   intellectually weakest.

**Default plan:** strategy 1 for **PD / D1 R1** (the most-egregious row,
mechanical fix); re-run L3; revisit remaining rows from data.

**Update 2026-04-29:** strategy 1 was applied across **all six fault rows**
(PD, D1, D2, T1, T2, T3) in this PR rather than just PD / D1, because once
we read the standard for those two rows the others were a one-line edit
each. The L3 chi² baseline (now p = 0.0106 from v0) is expected to shift on
re-run; report v1 will use the fixed table as ground truth.

**Other findings from the standard PDF:**

- `meta.sources[0]` mislabels edition: says `"edition": "3rd"` with
  `year: 2022`. 3rd ed. = 2015; 2022 = **4th ed.** Should be `"4th"`.
- IEC Table 1 carries four NOTE rows the JSON does not encode. Most
  relevant: **Note 4** — stray oil gassing produces PD-like patterns
  but is not a real fault. Should be reflected in the synthesis as a
  small "false-PD" fraction.
- IEC § A covers seven equipment classes (power transformers, instrument
  transformers, reactors, bushings, oil-filled cables, switching
  equipment). We use only A.1 (power transformers). Final paper should
  scope explicitly.
- PDF p.37 includes Duval triangle percentage formulas
  (`%C2H2`, `%CH4`, `%C2H4` normalized). Could add as a secondary
  classifier in FMSR.

**Companion analysis** (full row-by-row diff matrix, three-way pair
agreement, per-row contradiction descriptions): see Appendix B (§ 14)
for the historical pre-fix divergence matrix preserved as
paper-methodology evidence. Canonical post-fix bounds live in PR #149's
JSON `fault_table` encoding.

### 2.5 Free-PDF acquisition status (Apr 28 search)

We searched in this session for legitimate-and-free access to the full PDF.

| Source | Result | Notes |
|--------|--------|-------|
| `(third-party host, likely unauthorized)` | unreachable from this network (HTTP 000) | claimed full standard; likely unauthorized re-host; verify legality before use |
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

- `pandas` and `numpy` were already in `requirements.txt`.
- `scipy` is added by this PR; `scipy.stats.ks_2samp`,
  `scipy.stats.anderson_ksamp`, `scipy.stats.wasserstein_distance`, and
  `scipy.stats.chisquare` cover the test battery.
- `openpyxl` is added by this PR for `pd.read_excel(.xlsx)` so the IEEE
  DataPort primary path works without extra setup.
- Legacy `.xls` is intentionally NOT supported — it would require `xlrd`,
  which is not pinned. Convert any `.xls` files to `.xlsx` (Excel /
  LibreOffice "Save as") or `.csv` before running the validator.

---

## 7. Pre-May 4 plan

Ownership shifted on 2026-04-29: Akshat takes over scenario-truth and L3
validation; Alex retains the JSON/server reconciliation work he had personal
research notes for, and shifts focus to AssetOpsBench fork refactor + project
planning. Tanisha picks up paper / NeurIPS framing.

| # | Task | Owner | Day | Acceptance |
|---|------|-------|-----|-----------|
| 1 | Land L3 skeleton + this doc | Alex | Apr 28 | merged in PR #148 |
| 2 | Pin `transformer_standards.json` `meta.sources[0]` to IEC 60599 4th ed. (2022) — old value `"3rd"` was wrong (3rd ed. = 2015). | Alex | Apr 29 | merged in this PR; `meta.sources[0].edition` = `"4th"` |
| 2b | **Fix `fault_table` (JSON) and `_rogers_ratio` (server) to match IEC 60599:2022 Table 1.** All six fault rows (PD, D1, D2, T1, T2, T3) updated; `representative_gas_profiles` regenerated to round-trip; `tests/test_fmsr_server.py` fixtures updated in lockstep. | Alex | Apr 29 | merged in this PR; 23/23 fmsr tests pass; profiles round-trip via server |
| 3 | Acquire IEEE DataPort DGA dataset (Columbia IEEE, or Kaggle backstop) | **Akshat** | by May 1 | `data/external/ieee_dataport_dga.xlsx` (or csv equivalent) on disk |
| 4 | First L3 run: `validate_realism_statistical.py --real <dataset> --real-source ieee_dataport` | **Akshat** | May 1 | `reports/realism_statistical_v1.{md,json}` exist |
| 5 | Tune synthesis: if tests fail, adjust `data/generate_synthetic.py` per-fault gas means/stds, regenerate, re-run | **Akshat** | May 1 – 2 | majority of L3 tests pass at v2 or v3 |
| 6 | Add L3 report-card figure to final report § Methodology | **Akshat** + Tanisha | May 2 | figure rendered, caption written |
| 7 | Wire L3 into PR #147 promotion path: each accepted batch produces a `realism_statistical_<batch_id>.md` | Aaron + Akshat | May 2–3 | scaffold extended, doc updated |
| 8 | Refactor existing code to the AssetOpsBench fork; new GitHub Project planning page | **Alex** | Apr 30 – May 2 | refactor plan filed; migration PR open or merged; project board live |
| 9 | NeurIPS / final paper framing — dual-citation IEC 60599 + IEEE C57.104 + IEC TC 10 (via Duval 2001); methodology / failure-taxonomy / final paper structure | **Tanisha** | May 1 – 3 | references section updated; paper outline circulated |

**Open in-flight PRs to finish first (Akshat + Aaron):** the three open team
PRs at the time of this handoff — see `gh pr list --state open` for current
state. Real-data acquisition and L3 v1 run are unblocked once those merge.

**Hard contingency:** if no real dataset can be acquired by May 1, fall back
to TC 10 reference prevalence chi-squared only and document the gap as a
limitation in the paper. This is degraded but defensible. Alex's personal
fallback dataset acquisition path (Columbia ILL) remains a backstop.

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
- **Edition mismatch.** Resolved in PR #149 — `meta.sources[0].edition`
  pinned to `"4th"` and `publication_id: 66491` added.
- **Stray gassing under-representation (per IEC 60599:2022 Note 4 on
  Table 1).** Real-world DGA datasets contain a small fraction of
  "fake-PD" samples (PD-like ratio signature but no actual fault) caused
  by stray oil gassing; these are tagged `Normal` (or as stray gassing),
  not PD. Our synthesis currently does not emit any. If v1 chi² shows
  synthetic PD over-represented relative to real (or, equivalently, real
  Normal-class ratio mass at PD-like ratios is not matched in synthetic),
  add ~3-5% `Normal_StrayGassing` samples with PD-like ratios but a
  `Normal` ground-truth label. Owner: **Akshat** (decide based on v1
  results; not blocking).
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
- Apr 28 mentor pre-call Q&A pass — § "Knowledge artifacts" and § "What is realism" capture how the L3 vs L2 split was reached. Owner Alex; ask if you need it.
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

---

## 12. Handoff to Akshat

**Owner change:** Alex authored this scaffolding (skeleton + doc + v0
baseline + table-divergence finding). **Akshat takes over L3 execution**
from here (real-data acquisition, v1 run, tuning loop, final-paper figure).
Issue `#53` already lists Akshat as owner of "validate auto-generated
scenarios against hand-crafted reference set"; L3 is the quantitative arm
of that validation lane.

### 12.1 First three commands

```bash
# 1. Get on the branch (or use any worktree of your choice)
cd <repo-root>
git fetch team13
git checkout team13/dat/realism-statistical-validation

# 2. Sanity-check the skeleton runs
.venv/bin/python data/scenarios/validate_realism_statistical.py \
    --synthetic data/processed/dga_records.csv \
    --report /tmp/r.md
# Expect: "0/2 tests passed" (chi² fails vs TC 10 reference, real dataset missing)

# 3. Pull the IEEE DataPort dataset (Columbia IEEE access required; Kaggle
#    backstop if blocked) and re-run with --real + --real-source
mkdir -p data/external
# … download IEEE DataPort dga.xlsx to data/external/ieee_dataport_dga.xlsx …
.venv/bin/python data/scenarios/validate_realism_statistical.py \
    --synthetic   data/processed/dga_records.csv \
    --real        data/external/ieee_dataport_dga.xlsx \
    --real-source ieee_dataport \
    --report      reports/realism_statistical_v1.md \
    --json        reports/realism_statistical_v1.json
```

### 12.2 What you have

- Runnable script (`data/scenarios/validate_realism_statistical.py`),
  black-clean, scipy in `requirements.txt`, smoke-tested.
- This doc — methodology, datasets, thresholds, plan, plug-in for PR #147,
  open questions.
- v0 baseline in `reports/realism_statistical_v0.md` showing the
  prevalence-divergence signal already exists.
- Three-way fault-table divergence finding in § 2.4 — explains why
  conditional-KS is likely to fail until the JSON / server tables are
  reconciled with IEC.

### 12.3 What you need to source

- **IEC 60599:2022 PDF.** Standard is paywalled; sourcing it is on you.
  Use Columbia ILL (engineering library), ask Dhaval for an IBM-licensed
  copy, or check team-share for a licensed copy. Don't commit it to the
  repo regardless of source.
- **IEEE DataPort DGA Dataset** (DOI 10.21227/27vy-h479) — primary target
  per § 4. Columbia IEEE subscription should cover it; ask the engineering
  library if not.
- **Kaggle `failure-analysis-in-power-transformers-dataset`** — backstop
  if IEEE DataPort is gated.
- **Bashir et al. 2024** ("Optimized Synthetic Data Integration with
  Transformer's DGA Data...") — the closest precedent paper for synthetic-
  vs-real DGA validation methodology. Cite in final paper.

### 12.4 Decisions you'll need to make

1. **Table-fix PR (§ 7 task 2b) — landed 2026-04-29.** Both `fault_table`
   (JSON) and `_rogers_ratio` (server) now match IEC 60599:2022 Table 1.
   Run L3 v1 against the fixed table directly. The pre-fix v0 baseline
   (n=20, chi² p=0.0106) is preserved in `reports/realism_statistical_v0.{md,json}`
   as the "broken-baseline" report card and remains useful evidence for the
   paper's methodology section that the reconciliation was necessary.

2. **Treat synthetic CO/CO2 data as out-of-scope for L3, or add a
   second IEEE-C57.104-style cellulose test?** § 9 currently flags this as
   future work; if you have time, an extra two tests on CO + CO2 marginals
   would strengthen the paper's "we covered both standards" claim.

3. **Acceptance thresholds.** § 5.1 defaults: KS p > 0.05, EMD/std ≤ 0.20,
   chi² p > 0.05, corr Δ ≤ 0.20. These are reasonable starting values from
   the literature but can be tuned once you have a real-data baseline. Be
   prepared to defend whatever threshold you set in the paper.

4. **Sample size on the synthetic side.** `dga_records.csv` is currently
   20 rows — too small for KS to be meaningful. Either extend
   `make_dga_records()` to ~600 samples (30 days × 20 transformers) or
   bootstrap from the existing 20. Bootstrapping is a one-line change but
   doesn't add new physical signal.

### 12.5 Where to ask for help

- **Alex** for PR #148/#149 / scaffolding-side questions, AOB fork
  refactor coordination, or anything around how L3 hooks into the
  PS B promotion path.
- **Aaron (afan2g, PR #147)** for the scenario-generator path and how L3
  should hook into its promotion script.
- **Dhaval** for IEC standard interpretation edge cases, IBM-internal
  datasets, or whether IBM AssetOpsBench has an authoritative
  reference dataset.
- **Tanisha** for `transformer_standards.json` historical provenance
  (she authored it pre-PR #149 reconciliation), and for NeurIPS / final
  paper framing.

---

## 13. Appendix A — IEC 60599:2022 Table 1 reference (citation + encoding pointer)

The canonical fault-classification table for this codebase is **IEC 60599:2022
Table 1**. PR #149 encodes the table 1:1 in
`data/knowledge/transformer_standards.json` § `iec_60599.rogers_ratio_method.fault_table`
and `mcp_servers/fmsr_server/server.py:_rogers_ratio()`. Both are the
operational source of truth for the codebase; consult them for the exact
numeric bounds, NS handling, all-zero guards, and match order.

**Internal R-numbering (JSON convention):** `R1 = CH4/H2`,
`R2 = C2H2/C2H4`, `R3 = C2H4/C2H6`. The IEC standard uses a different
column ordering; the JSON encoding's mapping is the conversion of record.

**Encoding choices in our code (not in the standard):**
- `NS` ("non-significant") is encoded as `(0, None)` in range tuples.
- Bounds use the inclusive-low / exclusive-high convention to avoid
  ambiguous tie-breaking on boundary values.
- Match order is most-severe first (D2, D1, T3, T2, T1, PD, then N
  fall-through), so first-match-wins resolves IEC's overlapping ranges
  toward the more severe code.
- All-zero gas readings would otherwise spuriously match PD (R1 and R3
  ranges include 0); the server handles this with an explicit guard
  returning N.

**Notes accompanying Table 1 in the standard** (paraphrased for context;
consult the standard directly for canonical text):

1. **Country/ratio variations.** Some countries use different ratio
   definitions or limits. Our codebase follows the primary IEC table.
2. **Calculation conditions.** Bookkeeping detail in IEC § 6.1; not
   actionable for our classifier.
3. **Equipment-specific PD thresholds.** Instrument transformers and
   bushings carry stricter PD thresholds than power transformers. Our
   synthesis is power-transformer-only (Annex A.1 scope); the paper
   should explicitly state this scope limitation.
4. **Stray gassing.** Stray oil gassing produces PD-like ratio
   signatures even in fault-free transformers, so real datasets contain
   a small fraction of "fake-PD" Normal samples. **Synthesis-side
   enhancement available**: emit ~3-5% of synthetic samples with PD-like
   ratios but a `fault_label = "Normal_StrayGassing"` tag. Trigger
   condition (per § 9): only if v1 chi² shows synthetic PD
   over-represented relative to real, since adding more `Normal`-tagged
   PD-like samples does not raise synthetic PD count. Owner: **Akshat**
   (decide based on v1 results; not blocking).

**Equipment scope:** the standard covers seven equipment classes; we
use Annex A.1 power transformers only. Final paper should explicitly
scope to this class.

**Citation for the final paper:**

- IEC 60599:2022, *Mineral oil-filled electrical equipment in service —
  Guidance on the interpretation of dissolved and free gases analysis*,
  Edition 4.0, International Electrotechnical Commission, Geneva,
  2022-05.
- IEC publication ID 66491. ICS 17.220.99 / 29.040.10 / 29.180. TC 10.

**Acquisition for paper bibliography**: an officially licensed copy will
be obtained before paper submission — purchase via webstore.iec.ch
(~CHF 364), or via Columbia ILL if it lands first. The PDF is not
committed to either repo regardless of source.

---

## 14. Appendix B — Three-way diff matrix (historical, pre-2b)

> **Status: historical.** This matrix describes the divergent state that
> existed *before* the 2026-04-29 reconciliation PR. After that PR, B and C
> were rewritten to match A — every cell below is now ✅ for B↔A and C↔A.
> The matrix is preserved as evidence for the paper's methodology section
> (we found and fixed a three-way disagreement) and as scaffolding for any
> future re-validation.

Tables under comparison (using JSON R-numbering throughout):

- **A** = IEC 60599:2022 Table 1 (the canonical standard).
- **B** = `data/knowledge/transformer_standards.json § iec_60599.rogers_ratio_method.fault_table` *(pre-2b)*.
- **C** = FMSR server `_rogers_ratio()` *(pre-2b)*.

Per-pair-per-cell: ✅ matches; ⚠️ partial overlap or differing bounds;
❌ contradicts (no overlap or opposite half-line).

| Code | Ratio | A↔B (IEC↔JSON) | A↔C (IEC↔Server) | B↔C (JSON↔Server) |
|------|-------|----------------|------------------|-------------------|
| PD | R1 | ✅ | ❌ | ❌ |
| PD | R2 | ❌ | ✅ | ✅ |
| PD | R3 | ❌ | ❌ | ✅ |
| D1 | R1 | ❌ | ❌ | ❌ |
| D1 | R2 | ⚠️ | ⚠️ | ✅ |
| D1 | R3 | ❌ | ❌ | ✅ |
| D2 | R1 | ⚠️ | ⚠️ | ⚠️ |
| D2 | R2 | ❌ | ⚠️ | ❌ |
| D2 | R3 | ⚠️ | ⚠️ | ❌ |
| T1 | R1 | ⚠️ | ❌ | ❌ |
| T1 | R2 | ❌ | ✅ | ✅ |
| T1 | R3 | ✅ | ❌ | ❌ |
| T2 | R1 | ⚠️ | ⚠️ | ✅ |
| T2 | R2 | ✅ | ✅ | ✅ |
| T2 | R3 | ⚠️ | ⚠️ | ✅ |
| T3 | R1 | ⚠️ | ⚠️ | ✅ |
| T3 | R2 | ⚠️ | ✅ | ⚠️ |
| T3 | R3 | ⚠️ | ⚠️ | ✅ |

**Pattern:** B↔C agree more often than either ↔ A — suggests both encodings
trace to a derivative source (textbook, slide deck) rather than to IEC text
directly.

**Worst rows (any pair contradicts on multiple ratios):**
- **D1**: B↔A contradicts on all three ratios. Highest priority for fix.
- **PD**: B↔A contradicts on R2 and R3.
- **T1**: B↔A contradicts on R2; C↔A contradicts on R1 and R3.

**Specific contradictions worth flagging in code comments when fixing**
(canonical bounds in PR #149's JSON `fault_table` encoding):

- **D1 R1**: JSON's range and IEC's range do not overlap; JSON's range ends
  where IEC's range begins. Possible column transposition during the
  original encoding.
- **D1 R3**: JSON and IEC fall on opposite half-lines (one bounded above,
  the other below).
- **D2 R2**: JSON and IEC do not overlap; the bounds differ by roughly an
  order of magnitude.
- **T1 R3**: JSON's bound is closed at the same value where IEC's bound is
  open — open-vs-closed boundary mismatch.
- **T2/T3 R3 boundary**: JSON places the dividing value in T3; IEC places
  it (and the surrounding interval) in T2.
