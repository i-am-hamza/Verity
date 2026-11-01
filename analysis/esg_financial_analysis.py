"""
ESG disclosure and financial performance: full analysis pipeline (v2).

Inputs
------
  --esg         Verity full export (sheet "Scores by year"): E, S, G, General and
                composite scores (0-100), board size, firm age, listing age,
                SASB sector and industry, financial flag.
  --financials  Researcher's financial data (sheet "Ali Data").
  --assets      Total assets and total liabilities (USD million), one row per
                company-year.

Outputs (in --out)
------------------
  ESG_vs_Financials_Results.xlsx   every table
  esg_financials_results.json      the same results, for the Verity web page

Variables (company i, year t)
-----------------------------
  Dependent    RoA, RoE, net margin, EPS (profitability); Tobin's Q and
               price-to-book (firm value)
  Independent  ESG composite (0-100); E, S, G and General in pillar models
  Controls     firm size ln(total assets), leverage (debt/equity), board size,
               ln(1 + firm age); year, industry, country or company effects

  Tobin's Q     = (market capitalisation + total liabilities) / total assets
  Price-to-book = market capitalisation / (total assets - total liabilities)

Models (ESG per 10 points; standard errors clustered by company)
----------------------------------------------------------------
  A1  across companies: controls + year + industry effects
  A2  A1 + country effects                                  (main, across)
  RE  random effects with year effects
  B0  company effects, no year effects
  B   company + year effects                                (main, within)
  C   ESG of the previous year, company + year effects
  D   reverse: ESG on the previous year's ratio
  IV  2SLS: ESG instrumented by the average ESG of same-sector firms in other countries
  Hausman test (B vs RE), VIF of the controls, descriptive statistics,
  Pearson correlation matrix, Spearman correlations, board-size models.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from linearmodels.iv import IV2SLS
from linearmodels.panel import PanelOLS, RandomEffects
from openpyxl import load_workbook
from scipy.stats import chi2, spearmanr
from statsmodels.stats.outliers_influence import variance_inflation_factor

warnings.filterwarnings("ignore")
log = logging.getLogger("esg_fin")

FIN_COLUMNS = {"EPS": 10, "Leverage": 11, "NetMargin": 12, "ROE": 13, "ROA": 14, "Growth": 15}
DV = ["ROA", "ROE", "NetMargin", "EPS", "TobinQ", "PB"]
LABELS = {"ROA": "RoA (%)", "ROE": "RoE (%)", "NetMargin": "Net margin (%)", "EPS": "EPS",
          "TobinQ": "Tobin's Q", "PB": "Price-to-book"}
ESG_COLS = {"Environmental (0-100)": "E", "Social (0-100)": "S", "Governance (0-100)": "G",
            "General (0-100)": "Gen", "Composite (0-100)": "ESG",
            "Composite 3-pillar (0-100)": "ESG3", "Composite no-new3 (0-100)": "ESGno3",
            "Board size": "Board", "Age since established": "AgeEst", "Age since listed": "AgeList"}
ESG_LABELS = {"ESG": "ESG composite", "E": "Environmental", "S": "Social", "G": "Governance", "Gen": "General"}
CONTROLS = ["lnTA", "Lev_w", "Board", "lnAge"]
NAME_OVERRIDES = {"Saudi Arabian Fertilizer Company": "SABIC Agri-Nutrients Company",
                  "Dubai Investment PJSC": "Dubai Investments PJSC",
                  "Oman Telecommunications Company": "Oman Telecommunications Company OTEL",
                  "Yanbu National Petrochemical": "Yanbu National Petrochemical Co"}


@dataclass(frozen=True)
class Correction:
    company: str
    year: int
    measure: str
    old: float
    new: float
    basis: str


CORRECTIONS = [
    Correction("Saudi Aramco", 2024, "ROE", 16.07, 26.32, "RoA and RoE were swapped"),
    Correction("Saudi Aramco", 2024, "ROA", 26.32, 16.07, "RoA and RoE were swapped"),
    Correction("Saudi Aramco", 2025, "ROE", 13.99, 23.59, "RoA and RoE were swapped"),
    Correction("Saudi Aramco", 2025, "ROA", 23.59, 13.99, "RoA and RoE were swapped"),
    Correction("Sahara International Petrochemical Co.", 2025, "NetMargin", 2.45, -12.6,
               "Net loss attributable to shareholders / revenue"),
    Correction("Bank Aljazira", 2020, "EPS", 0.70, 0.03, "Adjusted-share basis"),
]


# ---------------------------------------------------------------- loading
def _num(x) -> float:
    if x is None:
        return np.nan
    if isinstance(x, (int, float)):
        return float(x)
    s = re.sub(r"[\u200e\u200f\u202a-\u202e\s,%]", "", str(x))
    try:
        return float(s)
    except ValueError:
        return np.nan


def _mcap(x) -> float:
    s = re.sub(r"[\u200e\u200f\u202a-\u202e\s,$]", "", str(x))
    m = re.match(r"([\d.]+)([TBM])", s)
    return float(m.group(1)) * {"T": 1e12, "B": 1e9, "M": 1e6}[m.group(2)] if m else np.nan


def _norm(s) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def load_financials(path: Path, esg_names) -> pd.DataFrame:
    ws = load_workbook(path, data_only=True)["Ali Data"]
    rows = []
    for r in range(2, ws.max_row + 1):
        if ws.cell(r, 2).value is None:
            continue
        row = {"Company": str(ws.cell(r, 2).value).strip(), "Year": int(ws.cell(r, 4).value),
               "MarketCapUSD": _mcap(ws.cell(r, 9).value)}
        row.update({k: _num(ws.cell(r, c).value) for k, c in FIN_COLUMNS.items()})
        rows.append(row)
    fin = pd.DataFrame(rows)
    for c in CORRECTIONS:
        m = (fin.Company == c.company) & (fin.Year == c.year)
        if m.sum() != 1 or not np.isclose(fin.loc[m, c.measure].iloc[0], c.old):
            raise ValueError(f"Correction does not apply cleanly: {c}")
        fin.loc[m, c.measure] = c.new
    by = {_norm(n): n for n in esg_names}
    fin["Company"] = fin.Company.map(lambda n: by.get(_norm(NAME_OVERRIDES.get(n, n))))
    if fin.Company.isna().any():
        raise ValueError("Unmatched company names in the financial file")
    return fin


def build_panel(esg_path: Path, fin_path: Path, assets_path: Path) -> pd.DataFrame:
    esg = pd.read_excel(esg_path, sheet_name="Scores by year").rename(columns=ESG_COLS)
    esg = esg.rename(columns={"Fiscal year": "Year"})
    fin = load_financials(fin_path, esg.Company.unique())
    ast = pd.read_excel(assets_path)
    by = {_norm(n): n for n in esg.Company.unique()}
    ast["Company"] = ast.Company.map(lambda n: by.get(_norm(n)))
    ast = ast.rename(columns={"Total Assets (USD million)": "TA", "Total Liabilities (USD million)": "TL"})
    keep = ["Company", "Year", "Ticker", "Country", "SASB sector", "SASB industry", "Financial",
            "Data-quality flag", *ESG_COLS.values()]
    df = (esg[keep].merge(fin, on=["Company", "Year"], how="left", validate="one_to_one")
          .merge(ast[["Company", "Year", "TA", "TL"]], on=["Company", "Year"], how="left", validate="one_to_one"))
    if len(df) != 390 or df.ESG.isna().any():
        raise ValueError("Panel is not complete")
    df["Fin"] = df.Financial.eq("Yes")
    df["McapM"] = df.MarketCapUSD / 1e6
    df["TobinQ"] = (df.McapM + df.TL) / df.TA
    eq = df.TA - df.TL
    df["PB"] = np.where(eq > 0, df.McapM / eq, np.nan)
    df["lnTA"] = np.log(df.TA)
    df["lnAge"] = np.log1p(df.AgeEst)
    for k in ["ROA", "ROE", "NetMargin", "EPS", "Leverage", "TobinQ", "PB"]:
        lo, hi = df[k].quantile([0.01, 0.99])
        df[k + "_w"] = df[k].clip(lo, hi)
    df["Lev_w"] = df.Leverage_w
    df = df.sort_values(["Company", "Year"]).reset_index(drop=True)
    g = df.groupby("Company")
    df["ESG_lag"] = g.ESG.shift(1)
    df["Board_lag"] = g.Board.shift(1)
    for k in DV:
        df[k + "_lagY"] = g[k + "_w"].shift(1)
    # instrument: average ESG of same-sector companies in OTHER countries, same year
    # (no mechanical link with the firm's own score or its own country's conditions)
    gs = df.groupby(["SASB sector", "Year"]).ESG
    gc = df.groupby(["SASB sector", "Year", "Country"]).ESG
    num = gs.transform("sum") - gc.transform("sum")
    den = gs.transform("count") - gc.transform("count")
    df["ESG_peer"] = np.where(den > 0, num / den.where(den > 0), np.nan)
    log.info("Panel: %d company-years, %d companies", len(df), df.Company.nunique())
    return df


# ---------------------------------------------------------------- models
def groups(df):
    return {"All companies": df, "Non-financial": df[~df.Fin], "Financial": df[df.Fin]}


def _ctrl(k):
    return [c for c in CONTROLS if not (k == "Leverage" and c == "Lev_w")]


def m_across(d, y, x, cs, country):
    d = d[[y, x, *cs, "Year", "SASB industry", "Country", "Company"]].dropna().copy()
    d["x10"] = d[x] / 10
    f = f"{y} ~ x10 + {' + '.join(cs)} + C(Year)"
    if d["SASB industry"].nunique() > 1:
        f += " + C(Q('SASB industry'))"
    if country:
        f += " + C(Country)"
    m = smf.ols(f, d).fit(cov_type="cluster", cov_kwds={"groups": d.Company})
    return dict(beta=m.params["x10"], se=m.bse["x10"], p=m.pvalues["x10"], N=int(m.nobs), R2=m.rsquared)


def _panel(d, y, xs):
    return d[[y, *xs, "Company", "Year"]].dropna().set_index(["Company", "Year"])


def m_within(d, y, x, cs, year_fx=True):
    p = _panel(d, y, [x, *cs]).copy()
    p["x10"] = p[x] / 10
    m = PanelOLS(p[y], p[["x10", *cs]], entity_effects=True, time_effects=year_fx).fit(
        cov_type="clustered", cluster_entity=True)
    return dict(beta=m.params["x10"], se=m.std_errors["x10"], p=m.pvalues["x10"], N=int(m.nobs),
                R2=m.rsquared_within)


def m_random(d, y, x, cs):
    p = _panel(d, y, [x, *cs]).copy()
    p["x10"] = p[x] / 10
    yd = pd.get_dummies(p.index.get_level_values("Year"), prefix="y", drop_first=True, dtype=float)
    yd.index = p.index
    X = sm.add_constant(pd.concat([p[["x10", *cs]], yd], axis=1))
    m = RandomEffects(p[y], X).fit(cov_type="clustered", cluster_entity=True)
    return dict(beta=m.params["x10"], se=m.std_errors["x10"], p=m.pvalues["x10"], N=int(m.nobs),
                R2=m.rsquared_overall)


def hausman(d, y, x, cs):
    """Classic Hausman test: company + year effects (FE) vs random effects with year dummies."""
    p = _panel(d, y, [x, *cs]).copy()
    p["x10"] = p[x] / 10
    xs = ["x10", *cs]
    fe = PanelOLS(p[y], p[xs], entity_effects=True, time_effects=True).fit()
    yd = pd.get_dummies(p.index.get_level_values("Year"), prefix="y", drop_first=True, dtype=float)
    yd.index = p.index
    re_ = RandomEffects(p[y], sm.add_constant(pd.concat([p[xs], yd], axis=1))).fit()
    b = fe.params[xs] - re_.params[xs]
    v = fe.cov.loc[xs, xs] - re_.cov.loc[xs, xs]
    try:
        stat = float(b.T @ np.linalg.pinv(v.values) @ b)
    except np.linalg.LinAlgError:
        return dict(chi2=np.nan, df=len(xs), p=np.nan)
    stat = abs(stat)
    return dict(chi2=stat, df=len(xs), p=float(1 - chi2.cdf(stat, len(xs))))


def m_iv(d, y, cs):
    d = d[[y, "ESG", "ESG_peer", *cs, "Year", "Country", "Company"]].dropna().copy()
    d["x10"], d["z10"] = d.ESG / 10, d.ESG_peer / 10
    ex = pd.get_dummies(d[["Year", "Country"]].astype(str), drop_first=True, dtype=float)
    exog = sm.add_constant(pd.concat([d[cs], ex], axis=1))
    m = IV2SLS(d[y], exog, d["x10"], d["z10"]).fit(cov_type="clustered", clusters=d.Company)
    fs = m.first_stage.diagnostics
    return dict(beta=m.params["x10"], se=m.std_errors["x10"], p=m.pvalues["x10"], N=int(m.nobs),
                first_stage_F=float(fs["f.stat"].iloc[0]))


def m_reverse(d, k):
    x = k + "_lagY"
    p = _panel(d, "ESG", [x])
    m = PanelOLS(p["ESG"], p[[x]], entity_effects=True, time_effects=True).fit(
        cov_type="clustered", cluster_entity=True)
    return dict(beta=m.params[x], se=m.std_errors[x], p=m.pvalues[x], N=int(m.nobs), R2=m.rsquared_within)


MODEL_NAMES = {"A1": "Across companies (industry, year)", "A2": "Across companies + country [main]",
               "RE": "Random effects", "B0": "Within company, no year effects",
               "B": "Within company + year effects [main]", "C": "ESG this year -> ratio next year",
               "D": "Reverse: ratio last year -> ESG", "IV": "2SLS (other-country sector ESG instrument)"}


def regressions(df):
    rows, haus = [], []
    for g, s in groups(df).items():
        for k in DV:
            y, cs = k + "_w", _ctrl(k)
            runs = {"A1": lambda: m_across(s, y, "ESG", cs, False),
                    "A2": lambda: m_across(s, y, "ESG", cs, True),
                    "RE": lambda: m_random(s, y, "ESG", cs),
                    "B0": lambda: m_within(s, y, "ESG", cs, False),
                    "B": lambda: m_within(s, y, "ESG", cs, True),
                    "C": lambda: m_within(s, y, "ESG_lag", cs, True),
                    "D": lambda: m_reverse(s, k),
                    "IV": lambda: m_iv(s, y, cs)}
            for code, fn in runs.items():
                try:
                    r = fn()
                except Exception as e:  # report, never hide
                    r = dict(beta=np.nan, se=np.nan, p=np.nan, N=0, note=str(e)[:80])
                rows.append(dict(Group=g, Measure=LABELS[k], Model=f"{code}. {MODEL_NAMES[code]}", **r))
            h = hausman(s, y, "ESG", cs)
            haus.append(dict(Group=g, Measure=LABELS[k], **h,
                             Preferred="Fixed effects" if h["p"] < 0.05 else "Random effects"))
    return pd.DataFrame(rows), pd.DataFrame(haus)


def pillars(df):
    rows = []
    for g, s in groups(df).items():
        for k in DV:
            y, cs = k + "_w", _ctrl(k)
            for v in ["E", "S", "G", "Gen"]:
                a, b = m_across(s, y, v, cs, True), m_within(s, y, v, cs, True)
                rows.append(dict(Group=g, Measure=LABELS[k], Pillar=ESG_LABELS[v], beta_A2=a["beta"],
                                 p_A2=a["p"], beta_B=b["beta"], p_B=b["p"], N=a["N"]))
    return pd.DataFrame(rows)


def robustness(df):
    rows = []
    for g, s in groups(df).items():
        for k in ["ROA", "ROE", "TobinQ"]:
            y, cs = k + "_w", _ctrl(k)
            for label, x, sub in [("Main composite", "ESG", s), ("3-pillar composite", "ESG3", s),
                                  ("Without innovation, feedback, digital services", "ESGno3", s),
                                  ("Excluding flagged report", "ESG", s[s["Data-quality flag"].isna()]),
                                  ("Size = ln(market cap) instead of ln(total assets)", "ESG", s)]:
                cc = ["lnMcap" if c == "lnTA" else c for c in cs] if "market cap" in label else cs
                if "market cap" in label:
                    sub = sub.assign(lnMcap=np.log(sub.MarketCapUSD))
                a, b = m_across(sub, y, x, cc, True), m_within(sub, y, x, cc, True)
                rows.append(dict(Group=g, Measure=LABELS[k], Variant=label, beta_A2=a["beta"], p_A2=a["p"],
                                 beta_B=b["beta"], p_B=b["p"], N=a["N"]))
    return pd.DataFrame(rows)


def board_models(df):
    rows = []
    for g, s in groups(df).items():
        a = m_across(s.assign(ESGy=s.ESG), "ESGy", "Board", ["lnTA", "lnAge"], True)
        a["beta"], a["se"] = a["beta"] / 10, a["se"] / 10  # m_across reports per 10 units; convert to per seat
        b = m_within(s.assign(ESGy=s.ESG), "ESGy", "Board", ["lnTA"], True)
        b["beta"], b["se"] = b["beta"] / 10, b["se"] / 10
        p = _panel(s, "Board", ["ESG_lag", "lnTA"]).copy()
        p["x10"] = p.ESG_lag / 10
        d = PanelOLS(p.Board, p[["x10", "lnTA"]], entity_effects=True, time_effects=True).fit(
            cov_type="clustered", cluster_entity=True)
        x = s[["Board", "ESG"]].dropna()
        rho, pr = spearmanr(x.Board, x.ESG)
        rows += [dict(Group=g, Test="Spearman, board size vs ESG", beta=rho, p=pr, N=len(x)),
                 dict(Group=g, Test="A2: ESG points per extra seat, across companies", beta=a["beta"], p=a["p"], N=a["N"]),
                 dict(Group=g, Test="B: ESG points per extra seat, within company", beta=b["beta"], p=b["p"], N=b["N"]),
                 dict(Group=g, Test="D: seats per 10 ESG points (next year)", beta=d.params["x10"], p=d.pvalues["x10"], N=int(d.nobs))]
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- descriptives
DESC = {"ESG": "ESG composite (0-100)", "E": "Environmental", "S": "Social", "G": "Governance", "Gen": "General",
        "ROA": "RoA (%)", "ROE": "RoE (%)", "NetMargin": "Net margin (%)", "EPS": "EPS", "Leverage": "Leverage (D/E)",
        "TobinQ": "Tobin's Q", "PB": "Price-to-book", "McapB": "Market cap (US$ bn)", "TAB": "Total assets (US$ bn)",
        "TLB": "Total liabilities (US$ bn)", "Board": "Board size", "AgeEst": "Firm age (years)", "AgeList": "Listing age (years)"}


def descriptives(df):
    d = df.assign(McapB=df.MarketCapUSD / 1e9, TAB=df.TA / 1e3, TLB=df.TL / 1e3)
    rows = []
    for g, s in groups(d).items():
        for c, lab in DESC.items():
            x = s[c].dropna()
            rows.append(dict(Group=g, Variable=lab, N=len(x), Mean=x.mean(), SD=x.std(), Min=x.min(),
                             P25=x.quantile(.25), Median=x.median(), P75=x.quantile(.75), Max=x.max()))
    return pd.DataFrame(rows)


CORR_VARS = {"ESG": "ESG", "ROA_w": "RoA", "ROE_w": "RoE", "NetMargin_w": "Net margin", "EPS_w": "EPS",
             "TobinQ_w": "Tobin's Q", "PB_w": "P/B", "lnTA": "ln(assets)", "Lev_w": "Leverage", "Board": "Board size",
             "lnAge": "ln(1+age)"}


def correlation_matrix(df):
    c = df[list(CORR_VARS)].rename(columns=CORR_VARS).corr(method="pearson")
    return c.reset_index().rename(columns={"index": "Variable"})


def vif(df):
    rows = []
    for g, s in groups(df).items():
        X = sm.add_constant(s[["ESG", *CONTROLS]].dropna())
        for i, c in enumerate(X.columns):
            if c != "const":
                rows.append(dict(Group=g, Variable={"ESG": "ESG composite", "lnTA": "ln(total assets)",
                                                    "Lev_w": "Leverage", "Board": "Board size",
                                                    "lnAge": "ln(1 + firm age)"}[c],
                                 VIF=variance_inflation_factor(X.values, i)))
    return pd.DataFrame(rows)


def spearman(df):
    rows = []
    for g, s in groups(df).items():
        for v, vl in ESG_LABELS.items():
            for k in DV:
                x = s[[v, k + "_w"]].dropna()
                rho, p = spearmanr(x[v], x[k + "_w"])
                rows.append(dict(Group=g, ESG=vl, Measure=LABELS[k], rho=rho, p=p, N=len(x)))
    return pd.DataFrame(rows)


def trends(df):
    t = df.groupby("Year").agg(ESG=("ESG", "mean"), E=("E", "mean"), S=("S", "mean"), G=("G", "mean"),
                               General=("Gen", "mean")).reset_index()
    for fin, name in [(True, "Financial"), (False, "Non-financial")]:
        m = df[df.Fin == fin].groupby("Year").agg(RoA=("ROA_w", "median"), RoE=("ROE_w", "median"),
                                                  Q=("TobinQ_w", "median"))
        for c in m.columns:
            t[f"{c} median ({name})"] = t.Year.map(m[c])
    return t


# ---------------------------------------------------------------- outputs
def run(esg, fin, assets, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    df = build_panel(esg, fin, assets)
    reg, haus = regressions(df)
    tables = {"descriptives": descriptives(df), "correlation_matrix": correlation_matrix(df), "vif": vif(df),
              "spearman": spearman(df), "regressions": reg, "hausman": haus, "pillars": pillars(df),
              "robustness": robustness(df), "board_size": board_models(df), "trends": trends(df)}
    with pd.ExcelWriter(out / "ESG_vs_Financials_Results.xlsx", engine="openpyxl") as xw:
        for name, t in tables.items():
            t.to_excel(xw, sheet_name=name[:31], index=False)
        pd.DataFrame([c.__dict__ for c in CORRECTIONS]).to_excel(xw, sheet_name="corrections", index=False)
    pts = df[["Company", "Year", "Financial", "ESG", "ROA_w", "ROE_w", "NetMargin_w", "EPS_w", "TobinQ_w", "PB_w",
              "Board"]].rename(columns=lambda c: c.replace("_w", ""))
    payload = {"meta": {"companies": int(df.Company.nunique()), "company_years": int(len(df)),
                        "financial_companies": int(df[df.Fin].Company.nunique()),
                        "effect_unit": "change in the measure per +10 ESG points"},
               **{k: json.loads(v.round(4).to_json(orient="records")) for k, v in tables.items()},
               "points": json.loads(pts.round(4).to_json(orient="records"))}
    (out / "esg_financials_results.json").write_text(json.dumps(payload, indent=1))
    df.to_pickle(out / "panel.pkl")
    return df, tables


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--esg", type=Path, required=True)
    ap.add_argument("--financials", type=Path, required=True)
    ap.add_argument("--assets", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("results"))
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run(a.esg, a.financials, a.assets, a.out)


if __name__ == "__main__":
    main()
