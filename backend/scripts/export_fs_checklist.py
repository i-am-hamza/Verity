"""
export_fs_checklist.py  --  Export docs/exports/fs_sourcing_checklist.xlsx

Lists the 25 company-years whose FS_BOUNDARY_NOT_FOUND flag is the ONLY flag
(i.e., no financial statements were found in the PDF we have).

Columns: company, ticker, exchange, fiscal_year,
         Downloaded (Yes/No) [blank], File name [blank]

Separate financial statements should be saved under:
  E:\\9. Verity\\storage\\financial_statements\\
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv
load_dotenv(BACKEND / ".env")

import app.models.institution  # noqa: F401
import app.models.provenance   # noqa: F401
import app.models.report       # noqa: F401
import app.models.review       # noqa: F401
import app.models.run          # noqa: F401
import app.models.score        # noqa: F401
import app.models.taxonomy     # noqa: F401

from app.database import SessionLocal
from app.models.institution import Institution
from sqlalchemy import select

CSV_IN   = REPO_ROOT / "docs" / "exports" / "financials_extracted.csv"
XLSX_OUT = REPO_ROOT / "docs" / "exports" / "fs_sourcing_checklist.xlsx"

# Country → exchange name mapping for GCC markets.
# UAE companies may be on ADX or DFM; without a separate field we use the country.
_EXCHANGE = {
    "Saudi Arabia": "Saudi Exchange (Tadawul)",
    "UAE":          "ADX / DFM",
    "Kuwait":       "Boursa Kuwait",
    "Qatar":        "Qatar Stock Exchange",
    "Oman":         "Muscat Stock Exchange (MSX)",
    "Bahrain":      "Bahrain Bourse",
}


_OTHER_FLAG_PREFIXES = {
    "BS_MISMATCH", "NP_ATTR_GT_TOTAL", "EPS_MISMATCH",
    "ROE_NPA_FALLBACK", "LEVERAGE_NEGATIVE_EQUITY", "OCR_HEAVY",
}


def _is_true_no_fs(flags_str: str) -> bool:
    """True when FS_BOUNDARY_NOT_FOUND is the only flag type present.

    Cannot split on ";" because the flag message itself contains a semicolon.
    """
    if not flags_str:
        return False
    if "FS_BOUNDARY_NOT_FOUND" not in flags_str:
        return False
    return not any(p in flags_str for p in _OTHER_FLAG_PREFIXES)


def main() -> int:
    # -- load CSV ---------------------------------------------------------------
    with open(CSV_IN, newline="", encoding="utf-8") as fh:
        all_rows = list(csv.DictReader(fh))

    no_fs = [
        (r["slug"], int(r["fiscal_year"]))
        for r in all_rows
        if "FS_BOUNDARY_NOT_FOUND" in (r.get("flags") or "")
    ]
    print(f"Rows with FS_BOUNDARY_NOT_FOUND: {len(no_fs)}")

    # -- query institution data -------------------------------------------------
    db = SessionLocal()
    inst_rows = db.execute(
        select(Institution.slug, Institution.name, Institution.ticker, Institution.country)
        .where(Institution.active.is_(True))
    ).all()
    db.close()

    by_slug: dict[str, tuple[str, str | None, str]] = {
        slug: (name, ticker, country)
        for slug, name, ticker, country in inst_rows
    }

    # -- build checklist rows ---------------------------------------------------
    checklist: list[dict[str, object]] = []
    for slug, fy in sorted(no_fs, key=lambda x: (x[0], x[1])):
        name, ticker, country = by_slug.get(slug, (slug, None, ""))
        exchange = _EXCHANGE.get(country, country)
        checklist.append({
            "company":           name,
            "ticker":            ticker or "",
            "exchange":          exchange,
            "fiscal_year":       fy,
            "Downloaded (Yes/No)": "",
            "File name":         "",
        })

    # -- write XLSX -------------------------------------------------------------
    import openpyxl
    from openpyxl.styles import Alignment, Font, PatternFill

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "FS Sourcing Checklist"

    columns = ["company", "ticker", "exchange", "fiscal_year",
               "Downloaded (Yes/No)", "File name"]

    header_fill = PatternFill("solid", fgColor="1F4E79")
    header_font = Font(bold=True, color="FFFFFF")

    for col_i, col_name in enumerate(columns, start=1):
        cell = ws.cell(row=1, column=col_i, value=col_name)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    for row_i, row in enumerate(checklist, start=2):
        for col_i, col_name in enumerate(columns, start=1):
            ws.cell(row=row_i, column=col_i, value=row[col_name])

    # Column widths
    ws.column_dimensions["A"].width = 50   # company
    ws.column_dimensions["B"].width = 15   # ticker
    ws.column_dimensions["C"].width = 35   # exchange
    ws.column_dimensions["D"].width = 14   # fiscal_year
    ws.column_dimensions["E"].width = 22   # Downloaded
    ws.column_dimensions["F"].width = 40   # File name

    ws.freeze_panes = "A2"
    wb.save(XLSX_OUT)
    print(f"XLSX -> {XLSX_OUT}")
    print(f"Rows written: {len(checklist)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
