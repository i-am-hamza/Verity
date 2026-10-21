"""Add Bank Aljazira to the study universe and mark SIIG inactive.

Researcher decision 2026-10-21: SIIG replaced by Bank Aljazira because
SIIG has no revenue line, so net margin cannot be calculated for it.

This script:
  1. Marks SIIG inactive in the DB (keeps all its documents/reports).
  2. Inserts Bank Aljazira (ticker 1020, Commercial Banks, is_financial=True).
  3. Updates docs/methodology/Verity_SASB_Mapping_Signed.xlsx:
       - Adds Bank Aljazira as row 66.
       - Adds a note to SIIG's row: "Replaced by Bank Aljazira 2026-10-21".
  4. Updates data/List of Companies.xlsx:
       - Replaces SIIG's row with Bank Aljazira (same rank slot).

Idempotent: re-running converges on the same state.
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND / ".env")

from app.crawler import register_all_mappers  # noqa: E402

register_all_mappers()

import openpyxl  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models.institution import Institution, InstitutionType, Wave  # noqa: E402

SASB_XLSX = REPO_ROOT / "docs" / "methodology" / "Verity_SASB_Mapping_Signed.xlsx"
LIST_XLSX = REPO_ROOT / "data" / "List of Companies.xlsx"

SIIG_SLUG = "saudi-industrial-investment-group"
ALJAZIRA = {
    "name": "Bank Aljazira",
    "slug": "bank-aljazira",
    "ticker": "1020",
    "country": "Saudi Arabia",
    "industry": "Financial Services",
    "sasb_sector": "Financials",
    "sasb_industry": "Commercial Banks",
    "is_financial": True,
    "wave": Wave.financial,
    "institution_type": InstitutionType.bank,
}


def _update_sasb_xlsx() -> None:
    wb = openpyxl.load_workbook(str(SASB_XLSX))
    ws = wb["Company industries"]

    # Find SIIG row and add replacement note
    siig_row_idx: int | None = None
    siig_num: int | None = None
    for row_idx in range(2, ws.max_row + 1):
        name_cell = ws.cell(row_idx, 2)
        if name_cell.value and "saudi industrial" in str(name_cell.value).lower():
            siig_row_idx = row_idx
            siig_num = ws.cell(row_idx, 1).value
            break

    if siig_row_idx is None:
        print("  WARNING: SIIG not found in SASB mapping xlsx")
    else:
        note_cell = ws.cell(siig_row_idx, 11)  # col 11 = Note
        existing_note = note_cell.value or ""
        marker = "Replaced by Bank Aljazira (1020) 2026-10-21"
        if marker not in str(existing_note):
            note_cell.value = (existing_note + "; " + marker).lstrip("; ")
            print(f"  SASB xlsx: updated SIIG note at row {siig_row_idx}")
        else:
            print("  SASB xlsx: SIIG note already updated")

    # Check if Bank Aljazira already in sheet
    aljazira_exists = any(
        ws.cell(r, 2).value and "bank aljazira" in str(ws.cell(r, 2).value).lower()
        for r in range(2, ws.max_row + 1)
    )
    if not aljazira_exists:
        # Append Bank Aljazira row
        new_row_num = (siig_num or 65) + 1  # number in the # column
        new_row_data = [
            new_row_num,           # # (sequence number)
            "Bank Aljazira",       # Company
            "1020",                # Symbol
            "Saudi Arabia",        # Country
            "Financial Services",  # Industry (your list)
            "Yes",                 # Labelled financial today?
            "Financials",          # SASB sector
            "Commercial Banks",    # SASB industry
            "Commercial bank",     # Main business
            "High",                # Confidence
            "Replaces SIIG (2250) 2026-10-21; SIIG had no revenue line",  # Note
            "Yes",                 # Gets financial add-on?
            16,                    # Core terms weight (same as other commercial banks)
            "Yes",                 # Agree?
            None,                  # Change to
            None,                  # Comment
        ]
        ws.append(new_row_data)
        print(f"  SASB xlsx: appended Bank Aljazira as row #{new_row_num}")
    else:
        print("  SASB xlsx: Bank Aljazira already present")

    wb.save(str(SASB_XLSX))
    print(f"  Saved: {SASB_XLSX}")


def _update_list_xlsx(siig_rank: int | None) -> None:
    wb = openpyxl.load_workbook(str(LIST_XLSX))
    ws = wb.active

    # Find and replace SIIG row
    siig_row_idx: int | None = None
    for row_idx in range(3, ws.max_row + 1):
        name_val = ws.cell(row_idx, 2).value
        if name_val and "saudi industrial" in str(name_val).lower():
            siig_row_idx = row_idx
            break

    if siig_row_idx is None:
        print("  WARNING: SIIG not found in List of Companies xlsx — appending Aljazira")
        # Append at end
        ws.append([siig_rank or 31, "Bank Aljazira", 1020, "Saudi Arabia", None, "Financial Services"])
    else:
        # Check if already replaced
        existing_name = ws.cell(siig_row_idx, 2).value
        if existing_name and "bank aljazira" in str(existing_name).lower():
            print("  List xlsx: Bank Aljazira already in place")
            wb.save(str(LIST_XLSX))
            return
        rank_in_list = ws.cell(siig_row_idx, 1).value
        ws.cell(siig_row_idx, 1).value = rank_in_list  # keep same rank slot
        ws.cell(siig_row_idx, 2).value = "Bank Aljazira"
        ws.cell(siig_row_idx, 3).value = 1020
        ws.cell(siig_row_idx, 4).value = "Saudi Arabia"
        ws.cell(siig_row_idx, 5).value = None  # market cap unknown for replacement
        ws.cell(siig_row_idx, 6).value = "Financial Services"
        print(f"  List xlsx: replaced SIIG at row {siig_row_idx} with Bank Aljazira")

    wb.save(str(LIST_XLSX))
    print(f"  Saved: {LIST_XLSX}")


def main() -> int:
    db = SessionLocal()
    try:
        # ---- Step 1: mark SIIG inactive ----
        siig = (
            db.query(Institution)
            .filter(Institution.slug == SIIG_SLUG)
            .first()
        )
        if siig is None:
            print(f"ERROR: {SIIG_SLUG} not found in DB")
            return 1

        siig_rank = siig.rank
        if siig.active:
            siig.active = False
            siig.rank = None  # clear unique rank so Aljazira can take it
            db.flush()
            print(f"Marked SIIG (id={siig.id}) inactive, cleared rank={siig_rank}")
        else:
            print(f"SIIG already inactive (id={siig.id})")

        # ---- Step 2: insert Bank Aljazira ----
        existing = (
            db.query(Institution)
            .filter(Institution.slug == ALJAZIRA["slug"])
            .first()
        )
        if existing is None:
            aljazira = Institution(
                name=ALJAZIRA["name"],
                slug=ALJAZIRA["slug"],
                ticker=ALJAZIRA["ticker"],
                country=ALJAZIRA["country"],
                industry=ALJAZIRA["industry"],
                sasb_industry=ALJAZIRA["sasb_industry"],
                is_financial=ALJAZIRA["is_financial"],
                wave=ALJAZIRA["wave"],
                institution_type=ALJAZIRA["institution_type"],
                sector="banking",
                rank=siig_rank,
                active=True,
            )
            db.add(aljazira)
            db.commit()
            print(
                f"Inserted Bank Aljazira: id={aljazira.id} slug={aljazira.slug!r} "
                f"rank={aljazira.rank} sasb_industry={aljazira.sasb_industry!r}"
            )
        else:
            # Ensure fields are correct on re-run
            existing.active = True
            existing.is_financial = True
            existing.wave = Wave.financial
            existing.sasb_industry = ALJAZIRA["sasb_industry"]
            existing.institution_type = InstitutionType.bank
            if existing.rank is None:
                existing.rank = siig_rank
            db.commit()
            print(
                f"Bank Aljazira already exists (id={existing.id}), fields verified"
            )

        # ---- Verification ----
        n_active = db.query(Institution).filter(Institution.active).count()
        print(f"\nActive institutions: {n_active}  (expected 65)")
        if n_active != 65:
            print("WARNING: active count is not 65!")

    finally:
        db.close()

    # ---- Step 3: update XLSX files ----
    print("\nUpdating SASB mapping xlsx...")
    _update_sasb_xlsx()

    print("\nUpdating List of Companies xlsx...")
    _update_list_xlsx(siig_rank)

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
