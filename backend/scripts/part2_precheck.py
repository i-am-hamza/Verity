"""Pre-check for Part 2: verify every 'Full report added to folder' row in
Verity_Report_Sourcing.xlsx has its file present in storage\\reports\\.
Also resolves DB ids for the 8 'Existing file is the annual report' rows.
Prints a STOP message and exits non-zero if any file is missing.
Changes nothing.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv('.env')

import openpyxl
from pathlib import Path

from app.crawler import register_all_mappers
register_all_mappers()
from app.database import SessionLocal
from app.models.provenance import SourceDocument
from app.models.institution import Institution
from sqlalchemy import select

SOURCE_DIR = Path(r"E:\9. Verity\storage\reports")
WB_PATH = Path(r"E:\9. Verity\docs\methodology\Verity_Report_Sourcing.xlsx")

# Company name → slug mapping (exactly as shown in the spreadsheet)
COMPANY_TO_SLUG = {
    "The Saudi National Bank":                               "the-saudi-national-bank",
    "Riyad Bank":                                            "riyad-bank",
    "Bank Albilad":                                          "bank-albilad",
    "Saudi Industrial Investment Group":                     "saudi-industrial-investment-group",
    "Abu Dhabi Commercial Bank":                             "abu-dhabi-commercial-bank",
    "The National Bank of Ras Al Khaimah":                   "the-national-bank-of-ras-al-khaimah",
    "Dubai Investments PJSC":                                "dubai-investment",
    "Emirates NBD PJSC":                                     "emirates-nbd-pjsc",
    "Kuwait Finance House":                                  "kuwait-finance-house",
    "Boubyan Bank":                                          "boubyan-bank",
    "Bank Muscat BKMB":                                      "bank-muscat-bkmb",
    "Oman International Development and Investment Company": "oman-international-development-and-investment-company",
    "Bank Dhofar":                                           "bank-dhofar",
    "Air Arabia PJSC":                                       "air-arabia-pjsc",
    "Salam International Investment":                        "salam-international-investment",
    "QNB (Qatar National Bank)":                             "qnb-qatar-national-bank",
    "Dubai Islamic Bank":                                    "dubai-islamic-bank",
    "Al Rajhi Bank":                                         "al-rajhi-bank",
    "The Saudi National Bank":                               "the-saudi-national-bank",
    "National Bank of Bahrain":                              "national-bank-of-bahrain",
    "National Bank of Kuwait":                               "national-bank-of-kuwait",
    "Abdullah Al Othaim Markets":                            "abdullah-al-othaim-markets",
}

wb = openpyxl.load_workbook(WB_PATH, read_only=True, data_only=True)
ws = wb["To source"]
rows = list(ws.iter_rows(values_only=True))[1:]  # skip header
wb.close()

db = SessionLocal()
inst_by_slug = {i.slug: i for i in db.execute(select(Institution)).scalars().all()}

# Build: (inst_id, year) -> sorted list of docs by page_count desc
all_docs = db.execute(select(SourceDocument)).scalars().all()
doc_map = {}
for d in all_docs:
    doc_map.setdefault((d.institution_id, d.fiscal_year), []).append(d)
db.close()

full_report_rows = []
existing_file_rows = []

for row in rows:
    _, company, _, fy, _, _, _, _, expected_fname, result, _ = row
    if result == "Full report added to folder":
        full_report_rows.append((company, int(fy), expected_fname))
    elif result == "Existing file is the annual report":
        existing_file_rows.append((company, int(fy), expected_fname))

print(f"'Full report added to folder' rows: {len(full_report_rows)}")
print(f"'Existing file is the annual report' rows: {len(existing_file_rows)}")

# ---- Check each 'Full report added to folder' file exists -----------------
print("\n--- Checking 36 expected files in storage\\reports ---")
missing = []
found = []
for company, fy, expected_fname in full_report_rows:
    fpath = SOURCE_DIR / expected_fname
    slug = COMPANY_TO_SLUG.get(company)
    if not fpath.exists():
        missing.append((company, fy, expected_fname))
        print(f"  MISSING: {expected_fname}")
    else:
        found.append((company, fy, expected_fname, fpath, slug))
        print(f"  OK    : {expected_fname}")

if missing:
    print(f"\nSTOP: {len(missing)} files missing from storage\\reports\\:")
    for company, fy, fname in missing:
        print(f"  {company} FY{fy}: {fname}")
    sys.exit(1)

print(f"\nAll {len(found)} files present.")

# ---- Also check for unexpected files in source dir matching expected names -
# (no extra check needed — we keyed on exact expected_fname)

# ---- Resolve DB ids for 'Existing file is the annual report' rows ---------
print("\n--- Resolving DB ids for 8 reclassification rows ---")
ANNUAL_TYPES = {'annual', 'integrated'}
for company, fy, expected_fname in existing_file_rows:
    slug = COMPANY_TO_SLUG.get(company)
    inst = inst_by_slug.get(slug) if slug else None
    if not inst:
        print(f"  ERROR: no slug mapping for {company!r}")
        continue
    cell = sorted(doc_map.get((inst.id, fy), []),
                  key=lambda d: (d.page_count or 0), reverse=True)
    if not cell:
        print(f"  ERROR: no docs for {slug} FY{fy}")
        continue
    # Pick the best doc — prefer higher page count among annual/integrated, else highest overall
    annual = [d for d in cell if str(d.report_type) in ANNUAL_TYPES]
    best = annual[0] if annual else cell[0]
    all_ids = [(d.id, d.page_count, str(d.report_type), str(d.review_status)) for d in cell]
    print(f"  {slug} FY{fy}: best_id={best.id} pages={best.page_count} "
          f"type={best.report_type} status={best.review_status}  all={all_ids}")

print("\nPre-check complete. No missing files.")
