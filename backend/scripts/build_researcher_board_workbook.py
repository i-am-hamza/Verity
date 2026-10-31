"""Produce docs/exports/company_ages_board_2020_2025_completed.xlsx.

Starts from incoming/company_ages_board_2020_2025.xlsx (the researcher's
original workbook with Company, Ticker, Year, Age since established, Age
since listed, Board members columns) and:

  * replaces the "Board members" placeholder text with the extracted
    board size number (int) from company_year_data.
  * adds "Board size basis" and "Board size page" columns alongside it.
  * leaves Company, Ticker, Year, Age since established, Age since
    listed untouched.

Rows whose company name does not match an institution slug (via the
same name_to_slug map used by extract_board_size.py) are left with
empty board columns and a short note.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(BACKEND / ".env")

from app.crawler import register_all_mappers  # noqa: E402
register_all_mappers()

import openpyxl  # noqa: E402
from openpyxl.styles import Font  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models.company_year import CompanyYearData  # noqa: E402
from app.models.institution import Institution  # noqa: E402

SRC = REPO_ROOT / "incoming" / "company_ages_board_2020_2025.xlsx"
DST = REPO_ROOT / "docs" / "exports" / "company_ages_board_2020_2025_completed.xlsx"

NAME_TO_SLUG: dict[str, str] = {
    "National Bank of Bahrain": "national-bank-of-bahrain",
    "The National Bank of Ras Al Khaimah": "the-national-bank-of-ras-al-khaimah",
    "Dubai Investments PJSC": "dubai-investment",
}


def main() -> int:
    DST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SRC, DST)

    wb = openpyxl.load_workbook(DST)
    ws = wb.active
    assert ws is not None
    header = [c.value for c in ws[1]]
    i_name = header.index("Company")
    i_year = header.index("Year")
    i_board = header.index("Board members")

    # Rename "Board members" column to "Board size" and append two more.
    ws.cell(row=1, column=i_board + 1).value = "Board size"
    ws.cell(row=1, column=i_board + 1).font = Font(bold=True)
    ws.cell(row=1, column=ws.max_column + 1).value = "Board size basis"
    ws.cell(row=1, column=ws.max_column).font = Font(bold=True)
    i_basis = ws.max_column - 1
    ws.cell(row=1, column=ws.max_column + 1).value = "Board size page"
    ws.cell(row=1, column=ws.max_column).font = Font(bold=True)
    i_page = ws.max_column - 1
    # After both appends, i_basis and i_page are 0-indexed on the current
    # header; recompute from the row we just wrote.
    header_now = [c.value for c in ws[1]]
    i_basis = header_now.index("Board size basis")
    i_page = header_now.index("Board size page")

    db = SessionLocal()
    try:
        insts = db.execute(select(Institution)).scalars().all()
        name_to_slug = {inst.name: inst.slug for inst in insts}
        name_to_slug.update(NAME_TO_SLUG)
        slug_to_id = {inst.slug: inst.id for inst in insts}
        cyd_by_key: dict[tuple[int, int], CompanyYearData] = {
            (c.institution_id, c.fiscal_year): c
            for c in db.execute(select(CompanyYearData)).scalars()
        }
    finally:
        db.close()

    filled = 0
    missing = 0
    for row in range(2, ws.max_row + 1):
        name = ws.cell(row=row, column=i_name + 1).value
        year = ws.cell(row=row, column=i_year + 1).value
        slug = name_to_slug.get(str(name)) if name else None
        iid = slug_to_id.get(slug) if slug else None
        cyd = cyd_by_key.get((iid, int(year))) if (iid and year) else None
        if cyd and cyd.board_size is not None:
            ws.cell(row=row, column=i_board + 1).value = cyd.board_size
            ws.cell(row=row, column=i_basis + 1).value = cyd.board_size_basis.value
            ws.cell(row=row, column=i_page + 1).value = cyd.board_size_pages or ""
            filled += 1
        else:
            # No value yet — leave board cell blank (replacing the placeholder
            # researcher text) and note the status.
            ws.cell(row=row, column=i_board + 1).value = None
            ws.cell(row=row, column=i_basis + 1).value = (
                "not_found" if cyd else "no_matching_institution"
            )
            ws.cell(row=row, column=i_page + 1).value = ""
            missing += 1

    wb.save(str(DST))
    print(f"Saved: {DST.relative_to(REPO_ROOT)}")
    print(f"  filled: {filled}, missing (needs annotation): {missing}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
