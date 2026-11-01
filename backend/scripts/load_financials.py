"""Load researcher-supplied financial measures into company_year_data.

Reads two workbooks and writes 390 (institution, fiscal_year) rows:

  analysis/data/Data_20_10_2026.xlsx          (sheet "Ali Data")
      Country, Company, Symbol, Year, Market Cap, EPS, Leverage Ratio,
      Net Margin, ROE, ROA, Growth Rate (growth is empty in source)

  analysis/data/company_assets_liabilities_2020_2025_USD.xlsx (sheet 1)
      Company, Ticker, Year, Total Assets (USD million),
      Total Liabilities (USD million)

Applies four researcher corrections (six cells) BEFORE writing:
  Saudi Aramco                       2024  RoE  26.32  RoA  16.07   (swap)
  Saudi Aramco                       2025  RoE  23.59  RoA  13.99   (swap)
  Sahara International Petrochemical 2025  Net margin  -12.60
  Bank Aljazira                      2020  EPS          0.03

Computes two derived ratios and writes them too:
  Tobin's Q      = (market cap + total liabilities) / total assets
  Price-to-book  = market cap / (total assets - total liabilities); NULL
                   if equity is zero or negative.

Idempotent: existing company_year_data rows are updated in place; missing
rows are created. Running the script twice yields the same database state.

Usage:
    python scripts/load_financials.py [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND / ".env")

import openpyxl  # noqa: E402
from sqlalchemy import select  # noqa: E402

import app.models.company_year  # noqa: E402, F401
import app.models.provenance  # noqa: E402, F401
import app.models.report  # noqa: E402, F401
import app.models.review  # noqa: E402, F401
import app.models.run  # noqa: E402, F401
import app.models.score  # noqa: E402, F401
import app.models.taxonomy  # noqa: E402, F401
from app.database import SessionLocal  # noqa: E402
from app.models.company_year import CompanyYearData  # noqa: E402
from app.models.institution import Institution  # noqa: E402


FIN_XLSX = REPO_ROOT / "analysis" / "data" / "Data_20_10_2026.xlsx"
ASSETS_XLSX = (
    REPO_ROOT / "analysis" / "data" / "company_assets_liabilities_2020_2025_USD.xlsx"
)


# Four researcher corrections (six cells). "old" is the value in the source
# workbook; applying the correction before the write produces "new". A
# strict match on "old" fails the loader if the source changes under us.
@dataclass(frozen=True, slots=True)
class Correction:
    company: str
    year: int
    field: str   # 'roe' | 'roa' | 'net_margin' | 'eps'
    old: float
    new: float


CORRECTIONS: list[Correction] = [
    Correction("Saudi Aramco", 2024, "roe", 16.07, 26.32),
    Correction("Saudi Aramco", 2024, "roa", 26.32, 16.07),
    Correction("Saudi Aramco", 2025, "roe", 13.99, 23.59),
    Correction("Saudi Aramco", 2025, "roa", 23.59, 13.99),
    Correction("Sahara International Petrochemical Co.", 2025, "net_margin", 2.45, -12.6),
    Correction("Bank Aljazira", 2020, "eps", 0.70, 0.03),
]


# Workbook-name → Institution.name mapping, for rows where the researcher
# wrote a name that is slightly different from the registered institution.
NAME_OVERRIDES: dict[str, str] = {
    "Saudi Arabian Fertilizer Company": "SABIC Agri-Nutrients Company",
    "Dubai Investment PJSC": "Dubai Investments PJSC",
    "Oman Telecommunications Company": "Oman Telecommunications Company OTEL",
    "Yanbu National Petrochemical": "Yanbu National Petrochemical Co",
}


@dataclass(slots=True)
class FinRow:
    company: str          # resolved to Institution.name
    year: int
    market_cap_usd_m: float | None
    eps: float | None
    leverage: float | None
    net_margin: float | None
    roe: float | None
    roa: float | None
    total_assets_usd_m: float | None = None
    total_liabilities_usd_m: float | None = None
    tobins_q: float | None = None
    price_to_book: float | None = None


# ------------------------------------------------------------------ parsing
def _norm(s: Any) -> str:
    """Lowercase + strip anything that isn't a-z0-9. For name matching."""
    return re.sub(r"[^a-z0-9]", "", str(s or "").lower())


def _num(x: Any) -> float | None:
    """Parse a cell to float. Treat empty/None/non-numeric strings as None.
    Strips invisible marks, thousands separators, percent signs."""
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = re.sub(r"[‎‏‪-‮\s,%]", "", str(x))
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


_MCAP_RE = re.compile(r"([\d.]+)\s*([TBM])", re.IGNORECASE)
_MCAP_UNITS = {"t": 1e12, "b": 1e9, "m": 1e6}


def parse_market_cap_to_usd_millions(x: Any) -> float | None:
    """`$2.053 T` → 2_053_000; `$5.6 B` → 5_600; `$920 M` → 920.
    Returns None for blanks or unparseable text."""
    if x is None:
        return None
    if isinstance(x, (int, float)):
        # Numeric cells are already in USD; convert to USD millions.
        return float(x) / 1e6
    s = re.sub(r"[‎‏‪-‮\s,$]", "", str(x))
    if not s:
        return None
    m = _MCAP_RE.match(s)
    if m is None:
        return None
    return float(m.group(1)) * _MCAP_UNITS[m.group(2).lower()] / 1e6


def apply_corrections(rows: list[FinRow]) -> None:
    """Verify each correction's old value matches, then overwrite with new.
    Raises if any correction cannot be applied cleanly — the researcher
    may have revised the source and the loader must be reviewed."""
    by_key: dict[tuple[str, int], FinRow] = {(r.company, r.year): r for r in rows}
    for c in CORRECTIONS:
        row = by_key.get((c.company, c.year))
        if row is None:
            raise ValueError(f"Correction target missing: {c.company} FY{c.year}")
        current = getattr(row, c.field)
        if current is None or abs(current - c.old) > 1e-6:
            raise ValueError(
                f"Correction mismatch: {c.company} FY{c.year} {c.field} "
                f"expected {c.old}, source has {current}"
            )
        setattr(row, c.field, c.new)


def compute_tobins_q_and_pb(rows: list[FinRow]) -> None:
    """Fill tobins_q and price_to_book from market cap + assets + liabs.
    Leaves either as None when inputs are missing. P/B is None if equity
    (TA - TL) is zero or negative."""
    for r in rows:
        if (
            r.market_cap_usd_m is not None
            and r.total_assets_usd_m is not None
            and r.total_liabilities_usd_m is not None
            and r.total_assets_usd_m > 0
        ):
            r.tobins_q = (r.market_cap_usd_m + r.total_liabilities_usd_m) / r.total_assets_usd_m
            equity = r.total_assets_usd_m - r.total_liabilities_usd_m
            if equity > 0:
                r.price_to_book = r.market_cap_usd_m / equity
            else:
                r.price_to_book = None


# ------------------------------------------------------------------ loading
def _col_index(header: list[Any], name: str) -> int:
    for i, h in enumerate(header):
        if str(h or "").strip() == name:
            return i
    raise ValueError(f"Column {name!r} not found in {header!r}")


def load_financials_xlsx(path: Path) -> list[FinRow]:
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    ws = wb["Ali Data"]
    rows = list(ws.iter_rows(values_only=True))
    header = [str(c).strip() if c else "" for c in rows[0]]
    i_country = _col_index(header, "Country")
    i_company = _col_index(header, "Company")
    i_year = _col_index(header, "Year")
    i_mcap = _col_index(header, "Market Cap")
    i_eps = _col_index(header, "EPS")
    i_lev = _col_index(header, "Leverage Ratio")
    i_nm = _col_index(header, "Net Margin")
    i_roe = _col_index(header, "ROE")
    i_roa = _col_index(header, "ROA")
    _ = i_country  # not stored; kept for header validation

    out: list[FinRow] = []
    for row in rows[1:]:
        if row[i_company] is None:
            continue
        out.append(FinRow(
            company=str(row[i_company]).strip(),
            year=int(row[i_year]),
            market_cap_usd_m=parse_market_cap_to_usd_millions(row[i_mcap]),
            eps=_num(row[i_eps]),
            leverage=_num(row[i_lev]),
            net_margin=_num(row[i_nm]),
            roe=_num(row[i_roe]),
            roa=_num(row[i_roa]),
        ))
    wb.close()
    return out


def load_assets_xlsx(path: Path) -> dict[tuple[str, int], tuple[float | None, float | None]]:
    """Return (company, year) → (total_assets_usd_m, total_liabilities_usd_m)."""
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    ws = wb.worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    header = [str(c).strip() if c else "" for c in rows[0]]
    i_company = _col_index(header, "Company")
    i_year = _col_index(header, "Year")
    i_ta = _col_index(header, "Total Assets (USD million)")
    i_tl = _col_index(header, "Total Liabilities (USD million)")

    out: dict[tuple[str, int], tuple[float | None, float | None]] = {}
    for row in rows[1:]:
        if row[i_company] is None:
            continue
        name = str(row[i_company]).strip()
        year = int(row[i_year])
        ta = _num(row[i_ta])
        tl = _num(row[i_tl])
        out[(name, year)] = (ta, tl)
    wb.close()
    return out


def resolve_institution_names(
    rows: list[FinRow],
    institutions: list[Institution],
) -> dict[str, str]:
    """Build workbook-name → Institution.name map (after NAME_OVERRIDES).
    Returns the final mapping; raises if any source row cannot be matched."""
    by_norm = {_norm(inst.name): inst.name for inst in institutions}
    resolved: dict[str, str] = {}
    unmatched: list[str] = []
    for r in rows:
        raw = r.company
        candidate = NAME_OVERRIDES.get(raw, raw)
        inst_name = by_norm.get(_norm(candidate))
        if inst_name is None:
            unmatched.append(raw)
        else:
            resolved[raw] = inst_name
    if unmatched:
        unique = sorted(set(unmatched))
        raise ValueError(
            "Unmatched companies in financial workbook: " + ", ".join(unique[:5])
            + (f" (+{len(unique) - 5} more)" if len(unique) > 5 else "")
        )
    return resolved


# ------------------------------------------------------------------ writing
def _f(x: float | None) -> float | None:
    """Round to 6 dp to keep DB values stable across re-runs."""
    return None if x is None else round(float(x), 6)


def write_db(rows: list[FinRow], *, dry_run: bool) -> int:
    db = SessionLocal()
    try:
        name_to_id = {
            inst.name: inst.id
            for inst in db.execute(select(Institution)).scalars()
        }
        wrote = 0
        for r in rows:
            iid = name_to_id.get(r.company)
            if iid is None:
                raise ValueError(f"Institution not found for {r.company!r}")
            cyd = db.execute(
                select(CompanyYearData).where(
                    CompanyYearData.institution_id == iid,
                    CompanyYearData.fiscal_year == r.year,
                )
            ).scalar_one_or_none()
            if cyd is None:
                cyd = CompanyYearData(institution_id=iid, fiscal_year=r.year)
                db.add(cyd)
            cyd.market_cap_usd_m = _f(r.market_cap_usd_m)
            cyd.eps = _f(r.eps)
            cyd.leverage = _f(r.leverage)
            cyd.net_margin = _f(r.net_margin)
            cyd.roe = _f(r.roe)
            cyd.roa = _f(r.roa)
            cyd.total_assets_usd_m = _f(r.total_assets_usd_m)
            cyd.total_liabilities_usd_m = _f(r.total_liabilities_usd_m)
            cyd.tobins_q = _f(r.tobins_q)
            cyd.price_to_book = _f(r.price_to_book)
            wrote += 1
        if dry_run:
            db.rollback()
        else:
            db.commit()
        return wrote
    finally:
        db.close()


def load_rows() -> list[FinRow]:
    """Full load pipeline, DB-free (used by tests)."""
    fin = load_financials_xlsx(FIN_XLSX)
    assets = load_assets_xlsx(ASSETS_XLSX)
    apply_corrections(fin)
    # Attach total assets / total liabilities by (company, year).
    for r in fin:
        ta_tl = assets.get((r.company, r.year))
        if ta_tl is None:
            # Match on name-overridden version too.
            candidate = NAME_OVERRIDES.get(r.company, r.company)
            ta_tl = assets.get((candidate, r.year))
        if ta_tl is not None:
            r.total_assets_usd_m, r.total_liabilities_usd_m = ta_tl
    compute_tobins_q_and_pb(fin)
    return fin


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--dry-run", action="store_true",
        help="Load and transform but roll back instead of committing.",
    )
    args = ap.parse_args()

    rows = load_rows()
    if len(rows) != 390:
        print(f"WARN: expected 390 financial rows, got {len(rows)}")

    db = SessionLocal()
    try:
        insts = list(db.execute(select(Institution)).scalars())
    finally:
        db.close()
    resolved = resolve_institution_names(rows, insts)
    for r in rows:
        r.company = resolved[r.company]

    n = write_db(rows, dry_run=args.dry_run)
    verb = "would update" if args.dry_run else "updated"
    print(f"{verb} {n} company_year_data rows "
          f"({sum(1 for r in rows if r.tobins_q is not None)} with Tobin's Q, "
          f"{sum(1 for r in rows if r.price_to_book is not None)} with P/B)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
