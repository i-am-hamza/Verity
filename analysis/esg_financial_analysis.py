"""
ESG disclosure and financial performance: analysis pipeline.

Reproduces every table, chart and figure in the final analysis from two inputs:

  1. The Verity ESG export (Excel, sheet "Scores by year"): one row per
     company-year with E, S, G, General and composite scores on a 0-100 scale.
  2. The researcher's financial data (Excel, sheet "Ali Data"): one row per
     company-year with market cap, EPS, leverage, net margin, RoE and RoA.

Usage
-----
    python esg_financial_analysis.py \
        --esg verity_esg_scores.xlsx \
        --financials Data_20_10_2026.xlsx \
        --out results/

Outputs (in --out)
------------------
    ESG_vs_Financials_Results.xlsx   all tables, ready for the thesis
    esg_financials_results.json      the same results, for the Verity web page
    chart_*.png                      figures

Model summary
-------------
Variables (company i, year t):
    Dependent      Y_it  : RoA, RoE, net margin, EPS, leverage, ln(market cap)
    Independent    ESG_it: Verity composite score (0-100); E, S, G and
                           General scores in the pillar models
    Controls       ln(market cap)_it and leverage_it (each dropped when it is
                   the dependent variable); year, industry and country effects

Models (ESG entered per 10 points, standard errors clustered by company):
    A1  Y_it = a + b*ESG_it + c'X_it + year_t + industry_j + e_it
    A2  A1 + country_k                                    (main, across firms)
    B0  Y_it = a_i + b*ESG_it + c'X_it + e_it             (no year effects)
    B   Y_it = a_i + b*ESG_it + c'X_it + year_t + e_it    (main, within firm)
    C   Y_it = a_i + b*ESG_i,t-1 + c'X_it + year_t + e_it (ESG leads)
    D   ESG_it = a_i + d*Y_i,t-1 + year_t + e_it          (reverse direction)
"""

from __future__ import annotations

import argparse
import difflib
import json
import logging
import re
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from linearmodels.panel import PanelOLS
from openpyxl import load_workbook
from scipy.stats import spearmanr

warnings.filterwarnings("ignore")
log = logging.getLogger("esg_fin")

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
FIN_COLUMNS = {"EPS": 10, "Leverage": 11, "NetMargin": 12, "ROE": 13, "ROA": 14}
OUTCOMES = ["ROA", "ROE", "NetMargin", "EPS", "Leverage", "lnMcap"]
LABELS = {
    "ROA": "RoA (%)", "ROE": "RoE (%)", "NetMargin": "Net margin (%)",
    "EPS": "EPS", "Leverage": "Leverage (D/E)", "lnMcap": "Market cap (log)",
}
ESG_COLUMNS = {
    "Environmental (0-100)": "E", "Social (0-100)": "S", "Governance (0-100)": "G",
    "General (0-100)": "Gen", "Composite (0-100)": "ESG",
    "Composite 3-pillar (0-100)": "ESG3", "Composite no-new3 (0-100)": "ESGno3",
}
# Board + firm-age columns in the Verity export. Ages here may be stale when the
# researcher has updated incoming/company_ages_board_2020_2025.xlsx but the DB
# has not been re-loaded; --ages overrides them row-by-row.
BOARD_COLUMNS = {
    "Board size": "BoardSize",
    "Age since established": "AgeEst",
    "Age since listed": "AgeList",
}
ESG_LABELS = {"ESG": "ESG composite", "E": "Environmental", "S": "Social",
              "G": "Governance", "Gen": "General"}
MODELS = {
    "A1": "Across companies (industry, year)",
    "A2": "Across companies (+ country) [main]",
    "B0": "Within company, no year effects",
    "B": "Within company (company, year) [main]",
    "C": "ESG this year -> ratio next year",
    "D": "Reverse: ratio last year -> ESG this year",
}
# Company names in the financial file that differ from the Verity export.
NAME_OVERRIDES = {
    "Saudi Arabian Fertilizer Company": "SABIC Agri-Nutrients Company",
    "Dubai Investment PJSC": "Dubai Investments PJSC",
    "Oman Telecommunications Company": "Oman Telecommunications Company OTEL",
    "Yanbu National Petrochemical": "Yanbu National Petrochemical Co",
}


@dataclass(frozen=True)
class Correction:
    company: str
    year: int
    measure: str
    old: float
    new: float
    basis: str


# Documented corrections to the researcher's data (see the Corrections sheet).
CORRECTIONS = [
    Correction("Saudi Aramco", 2024, "ROE", 16.07, 26.32, "RoA and RoE were swapped"),
    Correction("Saudi Aramco", 2024, "ROA", 26.32, 16.07, "RoA and RoE were swapped"),
    Correction("Saudi Aramco", 2025, "ROE", 13.99, 23.59, "RoA and RoE were swapped"),
    Correction("Saudi Aramco", 2025, "ROA", 23.59, 13.99, "RoA and RoE were swapped"),
    Correction("Sahara International Petrochemical Co.", 2025, "NetMargin", 2.45, -12.6,
               "Net loss attributable to shareholders / revenue"),
    Correction("Bank Aljazira", 2020, "EPS", 0.70, 0.03,
               "Adjusted-share basis, consistent with the company's other years"),
]


# --------------------------------------------------------------------------
# Loading and preparation
# --------------------------------------------------------------------------
def _to_number(x) -> float:
    """Parse numbers that may be stored as text with hidden characters."""
    if x is None:
        return np.nan
    if isinstance(x, (int, float)):
        return float(x)
    s = re.sub(r"[\u200e\u200f\u202a-\u202e\s,%]", "", str(x))
    try:
        return float(s)
    except ValueError:
        return np.nan


def _market_cap_usd(x) -> float:
    """Convert text such as '$2.053 T' or '$950 M' to US dollars."""
    s = re.sub(r"[\u200e\u200f\u202a-\u202e\s,$]", "", str(x))
    m = re.match(r"([\d.]+)([TBM])", s)
    return float(m.group(1)) * {"T": 1e12, "B": 1e9, "M": 1e6}[m.group(2)] if m else np.nan


def load_financials(path: Path) -> pd.DataFrame:
    ws = load_workbook(path, data_only=True)["Ali Data"]
    rows = []
    for r in range(2, ws.max_row + 1):
        if ws.cell(r, 2).value is None:
            continue
        row = {
            "Company": str(ws.cell(r, 2).value).strip(),
            "Year": int(ws.cell(r, 4).value),
            "MarketCapUSD": _market_cap_usd(ws.cell(r, 9).value),
        }
        row.update({k: _to_number(ws.cell(r, c).value) for k, c in FIN_COLUMNS.items()})
        rows.append(row)
    return pd.DataFrame(rows)


def apply_corrections(fin: pd.DataFrame) -> pd.DataFrame:
    fin = fin.copy()
    for c in CORRECTIONS:
        mask = (fin.Company == c.company) & (fin.Year == c.year)
        if mask.sum() != 1:
            raise ValueError(f"Correction target not found: {c}")
        current = fin.loc[mask, c.measure].iloc[0]
        if not np.isclose(current, c.old):
            raise ValueError(f"Unexpected value for {c}: found {current}")
        fin.loc[mask, c.measure] = c.new
    return fin


def match_names(fin_names, esg_names) -> dict[str, str]:
    norm = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())
    by_norm = {norm(n): n for n in esg_names}
    mapping = {}
    for name in fin_names:
        target = NAME_OVERRIDES.get(name, name)
        key = norm(target)
        if key in by_norm:
            mapping[name] = by_norm[key]
            continue
        close = difflib.get_close_matches(key, list(by_norm), n=1, cutoff=0.6)
        if not close:
            raise ValueError(f"No ESG match for company: {name}")
        mapping[name] = by_norm[close[0]]
        log.warning("Matched %r to %r by similarity", name, mapping[name])
    if len(set(mapping.values())) != len(mapping):
        raise ValueError("Two companies matched to the same ESG company")
    return mapping


def _load_ages(path: Path, name_map: dict[str, str]) -> pd.DataFrame:
    """Load the researcher's firm-ages workbook keyed by Verity company name."""
    ws = load_workbook(path, data_only=True).active
    headers = [c.value for c in ws[1]]
    i_name = headers.index("Company")
    i_year = headers.index("Year")
    i_est = headers.index("Age since established")
    i_list = headers.index("Age since listed")
    rows = []
    for r in range(2, ws.max_row + 1):
        name_raw = ws.cell(r, i_name + 1).value
        if name_raw is None:
            continue
        name = str(name_raw).strip()
        rows.append({
            "Company": name_map.get(name, name),
            "Year": int(ws.cell(r, i_year + 1).value),
            "AgeEst_r": ws.cell(r, i_est + 1).value,
            "AgeList_r": ws.cell(r, i_list + 1).value,
        })
    return pd.DataFrame(rows)


def build_panel(esg_path: Path, fin_path: Path,
                ages_path: Path | None = None) -> pd.DataFrame:
    fin = apply_corrections(load_financials(fin_path))
    esg = pd.read_excel(esg_path, sheet_name="Scores by year").rename(columns=ESG_COLUMNS)
    esg = esg.rename(columns=BOARD_COLUMNS)
    fin["Company"] = fin.Company.map(match_names(fin.Company.unique(), esg.Company.unique()))
    esg = esg.rename(columns={"Fiscal year": "Year"})[
        ["Company", "Year", "Country", "SASB industry", "Financial", "Data-quality flag",
         *ESG_COLUMNS.values(), *BOARD_COLUMNS.values()]]
    df = fin.merge(esg, on=["Company", "Year"], how="left", validate="one_to_one")
    if df.ESG.isna().any():
        raise ValueError("Some company-years have no ESG score")

    if ages_path is not None:
        # Build a name map identical to the ESG match (ESG workbook names ARE
        # the researcher's canonical names here) so a Company that already
        # matches is left alone.
        age_name_map = match_names(
            pd.unique(_load_ages(ages_path, {}).Company), esg.Company.unique()
        )
        ages = _load_ages(ages_path, age_name_map)
        df = df.merge(ages, on=["Company", "Year"], how="left", validate="one_to_one")
        # Only override where the researcher workbook has a value (keep ESG-xlsx
        # value otherwise — e.g., when the workbook is missing a row).
        df["AgeEst"] = df.AgeEst_r.where(df.AgeEst_r.notna(), df.AgeEst)
        df["AgeList"] = df.AgeList_r.where(df.AgeList_r.notna(), df.AgeList)
        # BUT: NaN in the workbook is a *deliberate* "blank" (SNB FY2020), so
        # when a workbook row exists with a NaN we honour the blank. Use the
        # presence of a workbook row as the signal.
        in_workbook = ages.set_index(["Company", "Year"]).index
        key = pd.MultiIndex.from_frame(df[["Company", "Year"]])
        mask = key.isin(in_workbook)
        df.loc[mask, "AgeEst"] = df.loc[mask, "AgeEst_r"]
        df.loc[mask, "AgeList"] = df.loc[mask, "AgeList_r"]
        df = df.drop(columns=["AgeEst_r", "AgeList_r"])

    # Coerce board + age columns to numeric (openpyxl can return str for ints).
    for c in ("BoardSize", "AgeEst", "AgeList"):
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df["Fin"] = df.Financial.eq("Yes")
    df["lnMcap"] = np.log(df.MarketCapUSD / 1e9)
    df["ln1pAgeEst"] = np.log1p(df.AgeEst)
    # Cap extreme values at the 1st and 99th percentiles (pooled).
    for k in ["ROA", "ROE", "NetMargin", "EPS", "Leverage"]:
        lo, hi = df[k].quantile([0.01, 0.99])
        df[k + "_w"] = df[k].clip(lo, hi)
    df["lnMcap_w"] = df.lnMcap
    df = df.sort_values(["Company", "Year"]).reset_index(drop=True)
    g = df.groupby("Company")
    for c in ["ESG", "E", "S", "G", "Gen", "ESG3", "ESGno3", "BoardSize"]:
        df[c + "_lag"] = g[c].shift(1)
    for k in OUTCOMES:
        df[k + "_lagY"] = g[k + "_w"].shift(1)
    log.info("Panel: %d company-years, %d companies, %d financial",
             len(df), df.Company.nunique(), df[df.Fin].Company.nunique())
    return df


# --------------------------------------------------------------------------
# Models
# --------------------------------------------------------------------------
def _controls(outcome: str) -> list[str]:
    return [c for c in ["lnMcap_w", "Leverage_w"] if not c.startswith(outcome)]


def across(d, y, x, controls, country: bool):
    d = d[[y, x, *controls, "Year", "SASB industry", "Country", "Company"]].dropna().copy()
    d["x10"] = d[x] / 10
    f = f"{y} ~ x10 + {' + '.join(controls)} + C(Year)"
    if d["SASB industry"].nunique() > 1:
        f += " + C(Q('SASB industry'))"
    if country:
        f += " + C(Country)"
    m = smf.ols(f, d).fit(cov_type="cluster", cov_kwds={"groups": d.Company})
    return m.params["x10"], m.bse["x10"], m.pvalues["x10"], int(m.nobs)


def within(d, y, x, controls, year_effects: bool = True):
    d = d[[y, x, *controls, "Company", "Year"]].dropna().copy()
    d["x10"] = d[x] / 10
    d = d.set_index(["Company", "Year"])
    m = PanelOLS(d[y], d[["x10", *controls]], entity_effects=True,
                 time_effects=year_effects).fit(cov_type="clustered", cluster_entity=True)
    return m.params["x10"], m.std_errors["x10"], m.pvalues["x10"], int(m.nobs)


def reverse(d, outcome):
    x = outcome + "_lagY"
    d = d[["ESG", x, "Company", "Year"]].dropna().set_index(["Company", "Year"])
    m = PanelOLS(d["ESG"], d[[x]], entity_effects=True, time_effects=True).fit(
        cov_type="clustered", cluster_entity=True)
    return m.params[x], m.std_errors[x], m.pvalues[x], int(m.nobs)


def groups(df):
    return {"All companies": df, "Non-financial": df[~df.Fin], "Financial": df[df.Fin]}


def correlations(df) -> pd.DataFrame:
    rows = []
    for g, s in groups(df).items():
        for v, vl in ESG_LABELS.items():
            for k in OUTCOMES:
                d = s[[v, k + "_w"]].dropna()
                rho, p = spearmanr(d[v], d[k + "_w"])
                rows.append(dict(Group=g, ESG=vl, Measure=LABELS[k], rho=rho, p=p, N=len(d)))
    avg = df.groupby("Company")[[*ESG_LABELS, *(k + "_w" for k in OUTCOMES)]].mean()
    for v, vl in ESG_LABELS.items():
        for k in OUTCOMES:
            d = avg[[v, k + "_w"]].dropna()
            rho, p = spearmanr(d[v], d[k + "_w"])
            rows.append(dict(Group="Company 6-year averages", ESG=vl, Measure=LABELS[k],
                             rho=rho, p=p, N=len(d)))
    return pd.DataFrame(rows)


def regressions(df) -> pd.DataFrame:
    rows = []
    for g, s in groups(df).items():
        for k in OUTCOMES:
            y, cs = k + "_w", _controls(k)
            runs = {
                "A1": lambda: across(s, y, "ESG", cs, False),
                "A2": lambda: across(s, y, "ESG", cs, True),
                "B0": lambda: within(s, y, "ESG", cs, False),
                "B": lambda: within(s, y, "ESG", cs, True),
                "C": lambda: within(s, y, "ESG_lag", cs, True),
                "D": lambda: reverse(s, k),
            }
            for code, fn in runs.items():
                b, se, p, n = fn()
                rows.append(dict(Group=g, Measure=LABELS[k], Model=f"{code}. {MODELS[code]}",
                                 beta=b, se=se, p=p, N=n))
    return pd.DataFrame(rows)


def robustness(df) -> pd.DataFrame:
    variants = [("Main composite", "ESG", None),
                ("3-pillar composite (no General)", "ESG3", None),
                ("Composite without innovation, feedback, digital services", "ESGno3", None),
                ("Excluding flagged report", "ESG", "flag")]
    rows = []
    for g, s in groups(df).items():
        for k in ["ROA", "ROE", "NetMargin", "lnMcap"]:
            y, cs = k + "_w", _controls(k)
            for label, x, flt in variants:
                sub = s[s["Data-quality flag"].isna()] if flt else s
                b1, _, p1, n = across(sub, y, x, cs, True)
                b2, _, p2, _ = within(sub, y, x, cs, True)
                rows.append(dict(Group=g, Measure=LABELS[k], ESG_measure=label,
                                 beta_A2=b1, p_A2=p1, beta_B=b2, p_B=p2, N=n))
    return pd.DataFrame(rows)


def pillars(df) -> pd.DataFrame:
    rows = []
    for g, s in groups(df).items():
        for k in OUTCOMES:
            y, cs = k + "_w", _controls(k)
            for v in ["E", "S", "G", "Gen"]:
                b1, _, p1, n = across(s, y, v, cs, True)
                b2, _, p2, _ = within(s, y, v, cs, True)
                rows.append(dict(Group=g, Measure=LABELS[k], Pillar=ESG_LABELS[v],
                                 beta_A2=b1, p_A2=p1, beta_B=b2, p_B=p2, N=n))
    return pd.DataFrame(rows)


def quartiles(df) -> pd.DataFrame:
    rows = []
    for g, s in [("Non-financial", df[~df.Fin]), ("Financial", df[df.Fin])]:
        q = pd.qcut(s.ESG, 4, labels=["Q1 (lowest ESG)", "Q2", "Q3", "Q4 (highest ESG)"])
        for lab, d in s.groupby(q, observed=True):
            rows.append(dict(Group=g, Quartile=lab, N=len(d), ESG_median=d.ESG.median(),
                             **{LABELS[k]: d[k + "_w"].median() for k in ["ROA", "ROE", "NetMargin", "Leverage"]},
                             **{"Market cap ($bn)": (d.MarketCapUSD / 1e9).median()}))
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Board-size module
#
# "Does board size go with ESG disclosure, does an increase in board size
# lead to more disclosure, and does disclosure lead to board changes?"
# Groups: all, financial, non-financial. The four not_found company-years
# are excluded (dropna on BoardSize).
# --------------------------------------------------------------------------
BOARD_ESG_METRICS = {"ESG": "ESG composite", "E": "Environmental", "S": "Social",
                     "G": "Governance", "Gen": "General"}


def _board_df(df):
    """Panel restricted to rows with a board size (drops the 4 not_found)."""
    return df[df.BoardSize.notna()].copy()


def _board_groups(df):
    b = _board_df(df)
    return {"All companies": b, "Financial": b[b.Fin], "Non-financial": b[~b.Fin]}


def board_descriptives(df) -> pd.DataFrame:
    """Board-size descriptives per group, plus a per-year summary for 'All'."""
    rows: list[dict] = []
    for g, s in _board_groups(df).items():
        n = len(s)
        companies = s.Company.nunique()
        # Count companies with >= 1 year-on-year change (needs >= 2 obs).
        changed = (s.sort_values(["Company", "Year"]).groupby("Company")["BoardSize"]
                   .apply(lambda v: v.dropna().nunique() > 1).sum())
        # Count distinct year-to-year changes (consecutive-year transitions).
        s_sorted = s.sort_values(["Company", "Year"]).copy()
        s_sorted["prev_board"] = s_sorted.groupby("Company").BoardSize.shift(1)
        s_sorted["prev_year"] = s_sorted.groupby("Company").Year.shift(1)
        consec = (s_sorted.prev_year.notna()) & (s_sorted.prev_year == s_sorted.Year - 1)
        yoy_changes = int(((s_sorted.BoardSize != s_sorted.prev_board) & consec).sum())
        rows.append({
            "Group": g, "N_obs": n, "N_companies": companies,
            "mean_boardsize": round(s.BoardSize.mean(), 3),
            "median_boardsize": float(s.BoardSize.median()),
            "min_boardsize": int(s.BoardSize.min()),
            "max_boardsize": int(s.BoardSize.max()),
            "companies_changed_at_least_once": int(changed),
            "year_to_year_changes": yoy_changes,
        })
    return pd.DataFrame(rows)


def board_year_summary(df) -> pd.DataFrame:
    """Mean and median board size per year, across groups."""
    rows: list[dict] = []
    for g, s in _board_groups(df).items():
        yr = s.groupby("Year")["BoardSize"].agg(["count", "mean", "median"]).reset_index()
        for _, r in yr.iterrows():
            rows.append({"Group": g, "Year": int(r["Year"]), "N": int(r["count"]),
                         "mean_boardsize": round(float(r["mean"]), 3),
                         "median_boardsize": float(r["median"])})
    return pd.DataFrame(rows)


def board_correlations(df) -> pd.DataFrame:
    rows: list[dict] = []
    for g, s in _board_groups(df).items():
        for v, vl in BOARD_ESG_METRICS.items():
            d = s[["BoardSize", v]].dropna()
            rho, p = spearmanr(d.BoardSize, d[v])
            rows.append({"Group": g, "ESG": vl, "rho": float(rho),
                         "p": float(p), "N": int(len(d))})
    return pd.DataFrame(rows)


def _board_across(d, y, controls, country: bool):
    """Across-companies OLS with industry/country/year effects, SE clustered
    by Company. Returns b per +1 seat."""
    d = d[[y, "BoardSize", *controls, "Year", "SASB industry", "Country", "Company"]].dropna().copy()
    f = f"{y} ~ BoardSize + {' + '.join(controls)} + C(Year)"
    if d["SASB industry"].nunique() > 1:
        f += " + C(Q('SASB industry'))"
    if country and d.Country.nunique() > 1:
        f += " + C(Country)"
    m = smf.ols(f, d).fit(cov_type="cluster", cov_kwds={"groups": d.Company})
    return m.params["BoardSize"], m.bse["BoardSize"], m.pvalues["BoardSize"], int(m.nobs)


def _board_within(d, y, x, controls):
    """Within-company (entity + time effects) panel OLS, SE clustered by Company.
    `x` is the regressor whose coefficient we report (BoardSize or BoardSize_lag)."""
    d = d[[y, x, *controls, "Company", "Year"]].dropna().copy()
    d = d.set_index(["Company", "Year"])
    m = PanelOLS(d[y], d[[x, *controls]], entity_effects=True, time_effects=True).fit(
        cov_type="clustered", cluster_entity=True)
    return m.params[x], m.std_errors[x], m.pvalues[x], int(m.nobs)


def _board_reverse(d, controls):
    """Reverse direction: Board_t = d * (ESG_lag/10) + controls + FE. The
    coefficient is reported per 10 ESG points."""
    d = d[["BoardSize", "ESG_lag", *controls, "Company", "Year"]].dropna().copy()
    d["ESG_lag_10"] = d.ESG_lag / 10
    d = d.set_index(["Company", "Year"])
    m = PanelOLS(d["BoardSize"], d[["ESG_lag_10", *controls]],
                 entity_effects=True, time_effects=True).fit(
        cov_type="clustered", cluster_entity=True)
    return m.params["ESG_lag_10"], m.std_errors["ESG_lag_10"], m.pvalues["ESG_lag_10"], int(m.nobs)


def board_regressions(df) -> pd.DataFrame:
    """A and B for each of ESG/E/S/G/Gen; C and D for the composite only.

    Controls:
      A: ln(market cap), ln(1 + age since established)
      B: ln(market cap)
      C: ln(market cap)
      D: ln(market cap)
    """
    across_controls = ["lnMcap_w", "ln1pAgeEst"]
    within_controls = ["lnMcap_w"]
    rows: list[dict] = []
    for g, s in _board_groups(df).items():
        for v, vl in BOARD_ESG_METRICS.items():
            b1, se1, p1, n1 = _board_across(s, v, across_controls, country=True)
            rows.append({"Group": g, "ESG": vl, "Model": "A. Across companies (industry, country, year)",
                         "beta_per_seat": float(b1), "se": float(se1), "p": float(p1), "N": int(n1)})
            b2, se2, p2, n2 = _board_within(s, v, "BoardSize", within_controls)
            rows.append({"Group": g, "ESG": vl, "Model": "B. Within company (company, year)",
                         "beta_per_seat": float(b2), "se": float(se2), "p": float(p2), "N": int(n2)})
        # C and D for composite only.
        b3, se3, p3, n3 = _board_within(s, "ESG", "BoardSize_lag", within_controls)
        rows.append({"Group": g, "ESG": "ESG composite",
                     "Model": "C. Board last year -> ESG this year",
                     "beta_per_seat": float(b3), "se": float(se3), "p": float(p3), "N": int(n3)})
        b4, se4, p4, n4 = _board_reverse(s, within_controls)
        rows.append({"Group": g, "ESG": "ESG composite",
                     "Model": "D. Reverse: ESG last year -> Board this year (per +10 ESG points)",
                     "beta_per_seat": float(b4), "se": float(se4), "p": float(p4), "N": int(n4)})
    return pd.DataFrame(rows)


def trends(df) -> pd.DataFrame:
    t = df.groupby("Year").agg(ESG=("ESG", "mean"), E=("E", "mean"), S=("S", "mean"),
                               G=("G", "mean"), General=("Gen", "mean")).reset_index()
    for fin, name in [(True, "Financial"), (False, "Non-financial")]:
        m = df[df.Fin == fin].groupby("Year").agg(RoA=("ROA_w", "median"), RoE=("ROE_w", "median"))
        t[f"RoA median ({name})"] = t.Year.map(m.RoA)
        t[f"RoE median ({name})"] = t.Year.map(m.RoE)
    return t


# --------------------------------------------------------------------------
# Outputs
# --------------------------------------------------------------------------
BOARD_SUMMARY = (
    "Larger boards go with more ESG disclosure, but this reflects company "
    "size: once size, age, industry, country and year are taken into "
    "account, board size has no significant link with ESG disclosure, "
    "and changes in board size are not followed by changes in disclosure, "
    "or the other way round."
)


def write_excel(path: Path, df, tables: dict[str, pd.DataFrame],
                board_tables: dict[str, pd.DataFrame]) -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        for name, t in tables.items():
            t.to_excel(xw, sheet_name=name[:31], index=False)
        for name, t in board_tables.items():
            t.to_excel(xw, sheet_name=name[:31], index=False)
        pd.DataFrame([c.__dict__ for c in CORRECTIONS]).to_excel(xw, sheet_name="Corrections", index=False)
        cols = ["Company", "Year", "Country", "Financial", "SASB industry", "ESG", "E", "S", "G", "Gen",
                "ROA", "ROE", "NetMargin", "EPS", "Leverage", "MarketCapUSD",
                "BoardSize", "AgeEst", "AgeList"]
        df[cols].to_excel(xw, sheet_name="Data used", index=False)


def write_json(path: Path, df, tables: dict[str, pd.DataFrame],
               board_tables: dict[str, pd.DataFrame]) -> None:
    def records(t):
        return json.loads(t.round(4).to_json(orient="records"))
    payload = {
        "meta": {
            "companies": int(df.Company.nunique()),
            "company_years": int(len(df)),
            "financial_companies": int(df[df.Fin].Company.nunique()),
            "years": [int(df.Year.min()), int(df.Year.max())],
            "esg_scale": "0-100, rank-based across all company-years",
            "effect_unit": "change in the measure per +10 ESG points",
        },
        "variables": {
            "dependent": [LABELS[k] for k in OUTCOMES],
            "independent": "ESG composite (0-100); E, S, G and General in pillar models",
            "controls": ["ln(market cap)", "leverage", "year effects",
                         "industry effects", "country effects (main across-company model)"],
        },
        **{name: records(t) for name, t in tables.items()},
        "board": {
            "summary": BOARD_SUMMARY,
            "variables": {
                "dependent": "ESG composite and E, S, G, General pillars (0-100)",
                "independent": "Board size (seats at fiscal year-end, researcher-read)",
                "effect_unit": "change in ESG per +1 board seat (per +10 ESG points for the reverse model D)",
                "exclusions": "4 company-years with board_size not available",
                "controls": [
                    "ln(market cap)",
                    "ln(1 + age since established)  [in model A only]",
                    "year effects", "SASB industry effects", "country effects (A)",
                    "company fixed effects (B, C, D)",
                ],
            },
            "descriptives": records(board_tables["board_descriptives"]),
            "year_summary": records(board_tables["board_year_summary"]),
            "correlations": records(board_tables["board_correlations"]),
            "regressions": records(board_tables["board_regressions"]),
        },
        "points": records(df[["Company", "Year", "Financial", "ESG", "ROA_w", "ROE_w",
                              "NetMargin_w", "EPS_w", "Leverage_w", "lnMcap"]]
                          .rename(columns=lambda c: c.replace("_w", ""))),
    }
    path.write_text(json.dumps(payload, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--esg", type=Path, required=True)
    ap.add_argument("--financials", type=Path, required=True)
    ap.add_argument("--ages", type=Path, default=None,
                    help="Optional researcher ages workbook; if given, overrides "
                         "Age since established / Age since listed from the ESG export.")
    ap.add_argument("--out", type=Path, default=Path("results"))
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args.out.mkdir(parents=True, exist_ok=True)

    df = build_panel(args.esg, args.financials, ages_path=args.ages)
    tables = {
        "correlations": correlations(df),
        "regressions": regressions(df),
        "robustness": robustness(df),
        "pillars": pillars(df),
        "quartiles": quartiles(df),
        "trends": trends(df),
    }
    board_tables = {
        "board_descriptives": board_descriptives(df),
        "board_year_summary": board_year_summary(df),
        "board_correlations": board_correlations(df),
        "board_regressions": board_regressions(df),
    }
    write_excel(args.out / "ESG_vs_Financials_Results.xlsx", df, tables, board_tables)
    write_json(args.out / "esg_financials_results.json", df, tables, board_tables)
    log.info("Done: results written to %s", args.out)


if __name__ == "__main__":
    main()
