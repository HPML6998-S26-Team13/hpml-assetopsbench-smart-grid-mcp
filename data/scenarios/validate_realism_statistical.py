"""
Statistical-fidelity validation for synthetic transformer DGA data.

Compares our synthesized DGA gas-concentration distributions
(`data/processed/dga_records.csv`, produced by `data/generate_synthetic.py`)
against published real-world DGA datasets, and emits a pass/fail report card.

This is Layer 3 of scenario validation:

    Layer 1  schema/structural   data/scenarios/validate_scenarios.py
    Layer 2  narrative realism   docs/scenario_realism_validation.md
                                 (mentor + domain-expert review)
    Layer 3  statistical fidelity  THIS FILE
                                 (KS / EMD / chi-squared per gas + fault)

See docs/dga_realism_statistical_validation.md for full methodology,
acceptance thresholds, and the ranked dataset list.

Usage:
    python3 data/scenarios/validate_realism_statistical.py \\
        --synthetic data/processed/dga_records.csv \\
        --real      data/external/ieee_dataport_dga.csv \\
        --report    reports/realism_statistical_v1.md

The --real path defaults to data/external/<dataset>.csv. If absent, the
script emits a stub report listing which dataset(s) need to be acquired
and from where.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

# --- Constants ---------------------------------------------------------------

# Five DGA fault gases used by IEC 60599 Rogers Ratio (CO/CO2 are excluded
# because cellulose-side gases are tracked under IEEE C57.104 separately).
FAULT_GASES = ["h2", "ch4", "c2h2", "c2h4", "c2h6"]

# Synthetic CSV column names (per data/generate_synthetic.py output schema).
SYN_GAS_COLUMNS = {gas: f"dissolved_{gas}_ppm" for gas in FAULT_GASES}

# IEC 60599 fault codes.
FAULT_CODES = ["Normal", "PD", "T1", "T2", "T3", "D1", "D2"]

# Map descriptive synthetic labels to IEC fault codes. The current
# data/processed/dga_records.csv uses descriptive strings rather than
# IEC codes; without this mapping the chi-squared test silently dropped
# half the rows (n_synthetic=20 but n_syn=10 in v0 baseline). Extend
# this dict when generate_synthetic.py introduces new labels.
PROJECT_LABEL_TO_IEC = {
    # already-canonical IEC codes pass through
    "Normal": "Normal",
    "PD": "PD",
    "T1": "T1",
    "T2": "T2",
    "T3": "T3",
    "D1": "D1",
    "D2": "D2",
    # descriptive labels currently emitted by generate_synthetic.py
    "Low-temperature overheating": "T1",
    "Mid-temperature overheating": "T2",
    "High-temperature overheating": "T3",
    "Partial discharge": "PD",
    "Low-energy discharge": "D1",
    "High-energy discharge": "D1",
    "Arc discharge": "D2",
    "Arcing": "D2",
}

# Real-dataset source-specific label maps. IEEE DataPort, for example,
# encodes faults as integers; mapping table per source is keyed by a
# `--real-source` flag.
REAL_LABEL_MAPS: dict[str, dict] = {
    # IEEE DataPort DGA Dataset (Dissanayake 2026) uses integer fault
    # codes 0-6 in its published Excel files. Confirmed by checking
    # the dataset readme; numbering starts at Normal=0.
    "ieee_dataport": {
        0: "Normal",
        1: "PD",
        2: "T1",
        3: "T2",
        4: "T3",
        5: "D1",
        6: "D2",
    },
    "kaggle_failure_analysis": {
        # populate when the Kaggle CSV is acquired and field-encoded labels are confirmed
    },
    "duval_2001_tc10": {
        # Duval & dePablo 2001 IEC TC 10 reproduction uses IEC codes natively
    },
}

# Reference fault prevalence from IEC TC 10 published distribution.
# Sources:
#   - IEC 60599:2022 Annex A (TC 10 case database, ~117 cases)
#   - Duval & dePablo 2001, IEEE Electrical Insulation Magazine 17(2)
#     "Interpretation of Gas-In-Oil Analysis Using New IEC Publication 60599
#      and IEC TC 10 Databases"
# Update with empirical proportions once real dataset is loaded.
TC10_REFERENCE_PREVALENCE = {
    "Normal": 0.27,
    "PD": 0.07,
    "T1": 0.13,
    "T2": 0.10,
    "T3": 0.13,
    "D1": 0.13,
    "D2": 0.17,
}

# Acceptance thresholds (see docs/dga_realism_statistical_validation.md).
KS_PVALUE_PASS = 0.05  # KS p > 0.05 -> distributions not distinguishable
EMD_NORMALIZED_PASS = 0.20  # EMD / std_real <= 0.2 -> close enough
CHI2_PVALUE_PASS = 0.05  # chi-squared p > 0.05 -> proportions not differ
AD_PVALUE_PASS = 0.05
CORR_DELTA_PASS = 0.20  # max(|corr_syn - corr_real|) <= 0.2


# --- Dataclasses -------------------------------------------------------------


@dataclass
class TestResult:
    name: str
    statistic: float | None
    pvalue: float | None
    threshold: float
    passed: bool
    detail: str = ""


@dataclass
class ReportCard:
    synthetic_path: str
    real_path: str | None
    n_synthetic: int
    n_real: int | None
    tests: list[TestResult] = field(default_factory=list)

    @property
    def n_passed(self) -> int:
        return sum(1 for t in self.tests if t.passed)

    @property
    def n_total(self) -> int:
        return len(self.tests)

    def to_dict(self) -> dict:
        def _scalar(x):
            # numpy scalars (bool_, float64, int64) aren't directly JSON-serializable.
            if x is None:
                return None
            if hasattr(x, "item"):
                return x.item()
            return x

        return {
            "synthetic_path": self.synthetic_path,
            "real_path": self.real_path,
            "n_synthetic": _scalar(self.n_synthetic),
            "n_real": _scalar(self.n_real),
            "tests": [
                {
                    "name": t.name,
                    "statistic": _scalar(t.statistic),
                    "pvalue": _scalar(t.pvalue),
                    "threshold": _scalar(t.threshold),
                    "passed": bool(t.passed),
                    "detail": t.detail,
                }
                for t in self.tests
            ],
            "summary": {"passed": self.n_passed, "total": self.n_total},
        }


# --- IO ----------------------------------------------------------------------


def load_synthetic(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    expected = set(SYN_GAS_COLUMNS.values()) | {"fault_label"}
    missing = expected - set(df.columns)
    if missing:
        raise ValueError(f"synthetic CSV missing columns: {sorted(missing)}")
    df = df.copy()
    df["fault_label_iec"] = df["fault_label"].map(_normalize_synthetic_label)
    unmapped = df[df["fault_label_iec"].isna()]["fault_label"].unique()
    if len(unmapped) > 0:
        raise ValueError(
            f"synthetic CSV has unmapped fault_label values: {sorted(unmapped.tolist())}. "
            f"Add them to PROJECT_LABEL_TO_IEC or rename in generate_synthetic.py."
        )
    return df


def _normalize_synthetic_label(raw: str) -> str | None:
    """Map a synthetic dataset's descriptive fault label to its IEC code.
    Returns None on unknown labels so the caller can fail loudly."""
    if raw is None:
        return None
    return PROJECT_LABEL_TO_IEC.get(str(raw).strip())


def load_real(path: Path | None, source: str | None = None) -> pd.DataFrame | None:
    """
    Load real DGA dataset.

    Supported file types: .csv, .xlsx, .xls (XLSX requires `openpyxl`).
    Expected post-normalization columns:
        h2_ppm, ch4_ppm, c2h2_ppm, c2h4_ppm, c2h6_ppm, fault_label

    `source` selects a label-translation map from REAL_LABEL_MAPS; pass
    "ieee_dataport" for IEEE DataPort's integer fault codes. If `source`
    is None or unrecognized, label values are passed through unchanged
    (assumed already-canonical IEC codes).
    """
    if path is None or not path.exists():
        return None
    suffix = path.suffix.lower()
    if suffix in (".xlsx", ".xls"):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)
    df = _normalize_real_columns(df)
    if "fault_label" in df.columns and source and source in REAL_LABEL_MAPS:
        label_map = REAL_LABEL_MAPS[source]
        if label_map:
            df["fault_label"] = df["fault_label"].map(
                lambda v: label_map.get(v, label_map.get(str(v), v))
            )
    return df


def _normalize_real_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Best-effort schema normalization for known real datasets.

    Recognized shapes:
      - IEEE DataPort DGA Dataset (Dissanayake 2026, DOI 10.21227/27vy-h479)
      - Kaggle: shashwatwork/failure-analysis-in-power-transformers-dataset
      - GitHub: ahmedtariq71/Dataset1
      - IEC TC 10 derived (Duval & dePablo 2001 reproduction)

    Add a new branch when introducing a new source.
    """
    cols = {c.lower(): c for c in df.columns}
    rename = {}
    for gas in FAULT_GASES:
        for candidate in (gas, f"{gas}_ppm", f"dissolved_{gas}_ppm", gas.upper()):
            if candidate.lower() in cols:
                rename[cols[candidate.lower()]] = f"{gas}_ppm"
                break
    for label_col in ("fault_label", "fault", "label", "class", "actual_fault"):
        if label_col in cols:
            rename[cols[label_col]] = "fault_label"
            break
    return df.rename(columns=rename)


# --- Statistical tests -------------------------------------------------------


def ks_per_gas(syn: pd.DataFrame, real: pd.DataFrame) -> list[TestResult]:
    from scipy import stats

    results = []
    for gas in FAULT_GASES:
        syn_col = SYN_GAS_COLUMNS[gas]
        real_col = f"{gas}_ppm"
        if real_col not in real.columns:
            results.append(
                TestResult(
                    name=f"ks_{gas}",
                    statistic=None,
                    pvalue=None,
                    threshold=KS_PVALUE_PASS,
                    passed=False,
                    detail=f"real dataset missing column {real_col}",
                )
            )
            continue
        s = syn[syn_col].dropna().values
        r = real[real_col].dropna().values
        if len(s) < 5 or len(r) < 5:
            results.append(
                TestResult(
                    name=f"ks_{gas}",
                    statistic=None,
                    pvalue=None,
                    threshold=KS_PVALUE_PASS,
                    passed=False,
                    detail=f"too few samples (n_syn={len(s)}, n_real={len(r)})",
                )
            )
            continue
        stat, p = stats.ks_2samp(s, r)
        results.append(
            TestResult(
                name=f"ks_{gas}",
                statistic=float(stat),
                pvalue=float(p),
                threshold=KS_PVALUE_PASS,
                passed=p > KS_PVALUE_PASS,
            )
        )
    return results


def emd_per_gas(syn: pd.DataFrame, real: pd.DataFrame) -> list[TestResult]:
    from scipy import stats

    results = []
    for gas in FAULT_GASES:
        syn_col = SYN_GAS_COLUMNS[gas]
        real_col = f"{gas}_ppm"
        if real_col not in real.columns:
            results.append(
                TestResult(
                    name=f"emd_{gas}",
                    statistic=None,
                    pvalue=None,
                    threshold=EMD_NORMALIZED_PASS,
                    passed=False,
                    detail=f"real dataset missing column {real_col}",
                )
            )
            continue
        s = syn[syn_col].dropna().values
        r = real[real_col].dropna().values
        if len(s) < 5 or len(r) < 5:
            results.append(
                TestResult(
                    name=f"emd_{gas}",
                    statistic=None,
                    pvalue=None,
                    threshold=EMD_NORMALIZED_PASS,
                    passed=False,
                    detail=f"too few samples (n_syn={len(s)}, n_real={len(r)})",
                )
            )
            continue
        emd = stats.wasserstein_distance(s, r)
        std_real = float(np.std(r)) or 1.0
        normalized = float(emd) / std_real
        results.append(
            TestResult(
                name=f"emd_{gas}",
                statistic=normalized,
                pvalue=None,
                threshold=EMD_NORMALIZED_PASS,
                passed=normalized <= EMD_NORMALIZED_PASS,
                detail=f"raw_emd={emd:.3f}, std_real={std_real:.3f}",
            )
        )
    return results


def anderson_darling_per_gas(syn: pd.DataFrame, real: pd.DataFrame) -> list[TestResult]:
    from scipy import stats

    results = []
    for gas in FAULT_GASES:
        syn_col = SYN_GAS_COLUMNS[gas]
        real_col = f"{gas}_ppm"
        if real_col not in real.columns:
            continue
        s = syn[syn_col].dropna().values
        r = real[real_col].dropna().values
        if len(s) < 5 or len(r) < 5:
            continue
        try:
            ad = stats.anderson_ksamp([s, r])
            stat = float(ad.statistic)
            # Modern SciPy (>=1.10) returns `pvalue` on the [0, 1] scale.
            # Older SciPy only exposed `significance_level` capped at 0.001/0.25
            # (also on the [0, 1] scale per modern docs, NOT a percent).
            # Prefer pvalue when available; treat significance_level as a
            # 0-1 probability fallback. Do not divide by 100 — that bug
            # collapsed honest 0.25 results to 0.0025 and failed every AD test.
            p = float(getattr(ad, "pvalue", ad.significance_level))
        except Exception as e:
            results.append(
                TestResult(
                    name=f"ad_{gas}",
                    statistic=None,
                    pvalue=None,
                    threshold=AD_PVALUE_PASS,
                    passed=False,
                    detail=str(e),
                )
            )
            continue
        results.append(
            TestResult(
                name=f"ad_{gas}",
                statistic=stat,
                pvalue=p,
                threshold=AD_PVALUE_PASS,
                passed=p > AD_PVALUE_PASS,
            )
        )
    return results


def chi2_fault_prevalence(
    syn: pd.DataFrame,
    real: pd.DataFrame | None,
) -> list[TestResult]:
    """Chi-squared on fault-class proportions.

    Compares synthetic prevalence vs (real if provided, else
    TC10_REFERENCE_PREVALENCE).
    """
    from scipy import stats

    # Use the IEC-normalized label column from load_synthetic. If absent
    # (e.g. caller bypassed load_synthetic), fall back to fault_label —
    # but the label-mapping check in load_synthetic is the canonical
    # entry point and should always produce fault_label_iec.
    syn_label_col = (
        "fault_label_iec" if "fault_label_iec" in syn.columns else "fault_label"
    )
    syn_counts = (
        syn[syn_label_col].value_counts().reindex(FAULT_CODES).fillna(0).astype(int)
    )
    n_syn = int(syn_counts.sum())
    n_syn_raw = int(len(syn))
    if n_syn != n_syn_raw:
        # Defensive: load_synthetic should already have raised on unmapped labels,
        # so reaching this branch means a bug. Surface it as a failing test row
        # rather than silently truncating, per Critical-1 reviewer finding.
        return [
            TestResult(
                name="chi2_fault_prevalence",
                statistic=None,
                pvalue=None,
                threshold=CHI2_PVALUE_PASS,
                passed=False,
                detail=(
                    f"label normalization dropped rows: n_synthetic_raw={n_syn_raw}, "
                    f"n_syn_mapped={n_syn}. Check PROJECT_LABEL_TO_IEC."
                ),
            )
        ]
    if real is not None and "fault_label" in real.columns:
        # SciPy chisquare requires sum(observed) == sum(expected). Convert real
        # counts to proportions, then scale to n_syn so the totals always match.
        real_counts = (
            real["fault_label"]
            .value_counts()
            .reindex(FAULT_CODES)
            .fillna(0)
            .astype(int)
        )
        n_real = int(real_counts.sum())
        if n_real == 0:
            return [
                TestResult(
                    name="chi2_fault_prevalence",
                    statistic=None,
                    pvalue=None,
                    threshold=CHI2_PVALUE_PASS,
                    passed=False,
                    detail="real dataset had zero rows mapping to any IEC fault code",
                )
            ]
        real_props = real_counts.values / n_real
        ref = _scale_to_total(real_props, n_syn)
        ref_label = f"real (n_real={n_real}, scaled to n_syn)"
    else:
        ref_props = (
            pd.Series(TC10_REFERENCE_PREVALENCE).reindex(FAULT_CODES).fillna(0).values
        )
        ref = _scale_to_total(ref_props, n_syn)
        ref_label = "TC10 reference"
    try:
        stat, p = stats.chisquare(syn_counts.values, f_exp=ref)
    except ValueError as e:
        return [
            TestResult(
                name="chi2_fault_prevalence",
                statistic=None,
                pvalue=None,
                threshold=CHI2_PVALUE_PASS,
                passed=False,
                detail=f"chisquare failed: {e}",
            )
        ]
    return [
        TestResult(
            name="chi2_fault_prevalence",
            statistic=float(stat),
            pvalue=float(p),
            threshold=CHI2_PVALUE_PASS,
            passed=p > CHI2_PVALUE_PASS,
            detail=f"reference={ref_label}, n_syn={n_syn}",
        )
    ]


def _scale_to_total(props: np.ndarray, target_total: int) -> np.ndarray:
    """Scale a proportion vector to a target integer total.

    SciPy's chisquare requires `sum(observed) == sum(expected)` exactly.
    Naive `(props * target_total).round().astype(int)` can drift by 1-2
    due to rounding; this helper applies largest-remainder rounding so
    the totals match.
    """
    raw = props * target_total
    floored = np.floor(raw).astype(int)
    deficit = target_total - int(floored.sum())
    if deficit > 0:
        # Distribute the deficit to the cells with the largest fractional remainders.
        remainders = raw - floored
        order = np.argsort(-remainders)
        for i in order[:deficit]:
            floored[i] += 1
    return floored


def conditional_ks_per_fault(syn: pd.DataFrame, real: pd.DataFrame) -> list[TestResult]:
    """Per-fault-class KS on each gas: gas | fault_class.

    Catches the case where marginal distributions match but
    per-fault gas signatures don't (e.g. synthetic 'PD' has
    realistic H2 mean but unrealistic CH4 mean).
    """
    from scipy import stats

    results = []
    if "fault_label" not in real.columns:
        return [
            TestResult(
                name="conditional_ks",
                statistic=None,
                pvalue=None,
                threshold=KS_PVALUE_PASS,
                passed=False,
                detail="real dataset has no fault_label column",
            )
        ]
    syn_label_col = (
        "fault_label_iec" if "fault_label_iec" in syn.columns else "fault_label"
    )
    for fault in FAULT_CODES:
        syn_sub = syn[syn[syn_label_col] == fault]
        real_sub = real[real["fault_label"] == fault]
        if len(syn_sub) < 3 or len(real_sub) < 3:
            continue
        for gas in FAULT_GASES:
            real_col = f"{gas}_ppm"
            if real_col not in real_sub.columns:
                # Mirror the missing-column failure-record behavior used by
                # ks_per_gas / emd_per_gas (Medium-6 reviewer finding):
                # emit a structured failing TestResult instead of crashing.
                results.append(
                    TestResult(
                        name=f"ks_{fault}_{gas}",
                        statistic=None,
                        pvalue=None,
                        threshold=KS_PVALUE_PASS,
                        passed=False,
                        detail=f"real dataset missing column {real_col}",
                    )
                )
                continue
            s = syn_sub[SYN_GAS_COLUMNS[gas]].dropna().values
            r = real_sub[real_col].dropna().values
            if len(s) < 3 or len(r) < 3:
                continue
            stat, p = stats.ks_2samp(s, r)
            results.append(
                TestResult(
                    name=f"ks_{fault}_{gas}",
                    statistic=float(stat),
                    pvalue=float(p),
                    threshold=KS_PVALUE_PASS,
                    passed=p > KS_PVALUE_PASS,
                    detail=f"n_syn={len(s)}, n_real={len(r)}",
                )
            )
    return results


def correlation_delta(syn: pd.DataFrame, real: pd.DataFrame) -> list[TestResult]:
    """Compare inter-gas correlation matrices.

    Real DGA data has structured inter-gas correlations
    (CH4/C2H6 co-vary in low-temp thermal faults; C2H2/C2H4 co-vary
    in arcing). If our synthesis emits uncorrelated noise, this
    catches it.
    """
    syn_gases = [SYN_GAS_COLUMNS[g] for g in FAULT_GASES]
    real_gases = [f"{g}_ppm" for g in FAULT_GASES if f"{g}_ppm" in real.columns]
    if len(real_gases) < 2:
        return [
            TestResult(
                name="corr_delta",
                statistic=None,
                pvalue=None,
                threshold=CORR_DELTA_PASS,
                passed=False,
                detail="real dataset has too few gas columns",
            )
        ]
    syn_corr = syn[syn_gases].corr().values
    real_corr = real[real_gases].corr().values
    delta = float(np.nanmax(np.abs(syn_corr - real_corr)))
    return [
        TestResult(
            name="corr_delta",
            statistic=delta,
            pvalue=None,
            threshold=CORR_DELTA_PASS,
            passed=delta <= CORR_DELTA_PASS,
            detail=f"max abs(corr_syn - corr_real) over {len(real_gases)} gases",
        )
    ]


# --- Driver ------------------------------------------------------------------


def run_tests(syn: pd.DataFrame, real: pd.DataFrame | None) -> ReportCard:
    rc = ReportCard(
        synthetic_path="",
        real_path=None,
        n_synthetic=len(syn),
        n_real=len(real) if real is not None else None,
    )
    rc.tests.extend(chi2_fault_prevalence(syn, real))
    if real is None:
        rc.tests.append(
            TestResult(
                name="real_dataset_present",
                statistic=None,
                pvalue=None,
                threshold=0.0,
                passed=False,
                detail="No real dataset loaded; only TC10 reference prevalence "
                "was checked. Acquire a real DGA dataset (see "
                "docs/dga_realism_statistical_validation.md § Datasets).",
            )
        )
        return rc
    rc.tests.extend(ks_per_gas(syn, real))
    rc.tests.extend(emd_per_gas(syn, real))
    rc.tests.extend(anderson_darling_per_gas(syn, real))
    rc.tests.extend(conditional_ks_per_fault(syn, real))
    rc.tests.extend(correlation_delta(syn, real))
    return rc


def _md_cell(text: str) -> str:
    """Escape Markdown table-cell content.

    `|` breaks the column structure; newlines break the row entirely.
    Both can appear in raw exception detail (e.g. multi-line SciPy
    error messages), so render them safely. Reviewer Medium-8 finding.
    """
    if text is None:
        return ""
    return str(text).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def render_markdown(rc: ReportCard) -> str:
    lines = [
        "# DGA Statistical Realism Report",
        "",
        f"- Synthetic: `{rc.synthetic_path}` (n={rc.n_synthetic})",
        f"- Real: `{rc.real_path or '(none loaded)'}` (n={rc.n_real})",
        f"- Result: **{rc.n_passed}/{rc.n_total}** tests passed",
        "",
        "| Test | Statistic | p-value | Threshold | Pass | Detail |",
        "|------|-----------|---------|-----------|------|--------|",
    ]
    for t in rc.tests:
        stat = f"{t.statistic:.4f}" if t.statistic is not None else "—"
        pv = f"{t.pvalue:.4f}" if t.pvalue is not None else "—"
        lines.append(
            f"| `{_md_cell(t.name)}` | {stat} | {pv} | {t.threshold} | "
            f"{'✅' if t.passed else '❌'} | {_md_cell(t.detail)} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic", type=Path, required=True)
    parser.add_argument("--real", type=Path, default=None)
    parser.add_argument(
        "--real-source",
        choices=sorted(REAL_LABEL_MAPS.keys()),
        default=None,
        help="select source-specific label-translation map (e.g. 'ieee_dataport' "
        "for the integer fault codes used in IEEE DataPort's published Excel files)",
    )
    parser.add_argument(
        "--report", type=Path, default=Path("reports/realism_statistical.md")
    )
    parser.add_argument(
        "--json", type=Path, default=None, help="optional JSON dump of full ReportCard"
    )
    args = parser.parse_args(argv)

    syn = load_synthetic(args.synthetic)
    real = load_real(args.real, source=args.real_source)

    rc = run_tests(syn, real)
    rc.synthetic_path = str(args.synthetic)
    rc.real_path = str(args.real) if args.real else None

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_markdown(rc))
    if args.json:
        args.json.write_text(json.dumps(rc.to_dict(), indent=2))

    print(f"Wrote {args.report}: {rc.n_passed}/{rc.n_total} tests passed")
    return 0 if rc.n_passed == rc.n_total else 1


if __name__ == "__main__":
    sys.exit(main())
