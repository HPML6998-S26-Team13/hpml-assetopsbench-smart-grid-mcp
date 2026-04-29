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
from typing import Callable

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
    return df


def load_real(path: Path | None) -> pd.DataFrame | None:
    """
    Load real DGA dataset. Expected columns:
        h2_ppm, ch4_ppm, c2h2_ppm, c2h4_ppm, c2h6_ppm, fault_label
    Different datasets have different conventions (mg/L vs ppm,
    label encoding, etc.). Adapter functions below normalize a few
    common dataset shapes.
    """
    if path is None or not path.exists():
        return None
    df = pd.read_csv(path)
    return _normalize_real_columns(df)


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
            p = float(ad.significance_level) / 100.0
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

    syn_counts = (
        syn["fault_label"].value_counts().reindex(FAULT_CODES).fillna(0).astype(int)
    )
    n_syn = int(syn_counts.sum())
    if real is not None and "fault_label" in real.columns:
        real_counts = (
            real["fault_label"]
            .value_counts()
            .reindex(FAULT_CODES)
            .fillna(0)
            .astype(int)
        )
        ref = real_counts.values
        ref_label = "real"
    else:
        ref_props = (
            pd.Series(TC10_REFERENCE_PREVALENCE).reindex(FAULT_CODES).fillna(0).values
        )
        ref = (ref_props * n_syn).round().astype(int)
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
    for fault in FAULT_CODES:
        syn_sub = syn[syn["fault_label"] == fault]
        real_sub = real[real["fault_label"] == fault]
        if len(syn_sub) < 3 or len(real_sub) < 3:
            continue
        for gas in FAULT_GASES:
            s = syn_sub[SYN_GAS_COLUMNS[gas]].dropna().values
            r = real_sub[f"{gas}_ppm"].dropna().values
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
            f"| `{t.name}` | {stat} | {pv} | {t.threshold} | "
            f"{'✅' if t.passed else '❌'} | {t.detail} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic", type=Path, required=True)
    parser.add_argument("--real", type=Path, default=None)
    parser.add_argument(
        "--report", type=Path, default=Path("reports/realism_statistical.md")
    )
    parser.add_argument(
        "--json", type=Path, default=None, help="optional JSON dump of full ReportCard"
    )
    args = parser.parse_args(argv)

    syn = load_synthetic(args.synthetic)
    real = load_real(args.real)

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
