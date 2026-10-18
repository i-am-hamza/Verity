"""Fiscal-year audit: find the actual fiscal year each report covers.

For every active company-year cell (390 total):
  - Uses the eligible doc if one exists, otherwise the best doc in cell.
  - Downloads from R2 and scans the full text for "for the year ended [date]".
  - Falls back to cover-page title year if no auditor phrase found.
  - Reports mismatches (assigned year != actual year) and non-December year-ends.
  - For Sohar International Bank, prints detailed evidence per doc.

Read-only. Changes nothing.
"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv('.env')

from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from dataclasses import dataclass, field

import pymupdf

from app.crawler import register_all_mappers
register_all_mappers()
from app.database import SessionLocal
from app.models.provenance import SourceDocument
from app.models.institution import Institution
from app.services.storage import _r2_client, R2Settings
from sqlalchemy import select

# ── year-end phrase patterns ────────────────────────────────────────────────
# Matches: "for the year ended 31 December 2023", "year ended December 31, 2023",
#          "year ended 31/12/2023", "financial year ended ...", etc.
_YE_RX = re.compile(
    r"(?:for\s+the\s+)?(?:financial\s+|fiscal\s+)?year\s+ended"
    r"\s+"
    r"(\d{1,2}\s+(?:january|february|march|april|may|june|july|august|"
    r"september|october|november|december)\s+20\d{2}"
    r"|(?:january|february|march|april|may|june|july|august|"
    r"september|october|november|december)\s+\d{1,2},?\s+20\d{2}"
    r"|31/12/20\d{2}"
    r"|20\d{2}-12-31)",
    re.IGNORECASE,
)

# Extract the 4-digit year from a date string
_YEAR_RX = re.compile(r"(20\d{2})")

# Extract month from a date string
_MONTH_RX = re.compile(
    r"(january|february|march|april|may|june|july|august|"
    r"september|october|november|december)",
    re.IGNORECASE,
)

DEC_MONTHS = {"december"}

# Auditor's report marker — helps locate evidence on which page
_AUDITOR_RX = re.compile(
    r"independent\s+auditor(?:s)?(?:'|')?s?\s+report"
    r"|report\s+of\s+the\s+independent\s+auditor",
    re.IGNORECASE,
)


@dataclass
class CellResult:
    slug: str
    assigned_year: int
    doc_id: int | None
    pages: int
    eligible: bool         # True = auto_ok + annual/integrated + not superseded
    actual_year: int | None
    year_end_date: str | None    # e.g. "31 December 2023"
    year_end_page: int | None    # 1-based
    year_end_source: str | None  # "auditor_phrase" | "title_phrase" | "dominant_year"
    non_december: bool
    mismatch: bool
    evidence: str | None         # best matching phrase
    error: str | None = None


def extract_fy(body: bytes, doc_id: int) -> tuple[int | None, str | None, int | None, str | None]:
    """Return (actual_year, date_string, page_1based, source_label) by scanning full text."""
    try:
        pdf = pymupdf.open(stream=body, filetype="pdf")
    except Exception as e:
        return None, None, None, f"open_error: {e}"

    try:
        page_count = pdf.page_count
        all_matches: list[tuple[int, str, str, str]] = []  # (page, phrase, date_str, source)

        for i in range(page_count):
            try:
                text = pdf[i].get_text("text") or ""
            except Exception:
                continue

            # Is this the auditor's report page?
            is_auditor_page = bool(_AUDITOR_RX.search(text))
            source_label = "auditor_phrase" if is_auditor_page else "title_phrase"

            for m in _YE_RX.finditer(text):
                date_str = m.group(1).strip()
                yr_m = _YEAR_RX.search(date_str)
                if yr_m:
                    yr = int(yr_m.group(1))
                    if 2018 <= yr <= 2026:
                        all_matches.append((i + 1, m.group(0).strip(), date_str, source_label))

        if not all_matches:
            # Fallback: dominant year in first 3 pages (cover)
            cover_text = ""
            for i in range(min(3, page_count)):
                try:
                    cover_text += pdf[i].get_text("text") or ""
                except Exception:
                    pass
            years_found = [int(y) for y in _YEAR_RX.findall(cover_text) if 2018 <= int(y) <= 2026]
            if years_found:
                dominant = max(set(years_found), key=years_found.count)
                return dominant, None, None, "dominant_year"
            return None, None, None, "not_found"

        # Prefer auditor page match; else first match
        auditor_matches = [(p, ph, d, s) for p, ph, d, s in all_matches if s == "auditor_phrase"]
        best = auditor_matches[0] if auditor_matches else all_matches[0]
        page, phrase, date_str, src = best
        yr_m = _YEAR_RX.search(date_str)
        actual_year = int(yr_m.group(1)) if yr_m else None
        return actual_year, date_str, page, src

    finally:
        pdf.close()


def non_december(date_str: str | None) -> bool:
    if not date_str:
        return False
    m = _MONTH_RX.search(date_str or "")
    if m:
        return m.group(1).lower() not in DEC_MONTHS
    return False


# ── DB setup ─────────────────────────────────────────────────────────────────
TARGET_YEARS = [2020, 2021, 2022, 2023, 2024, 2025]
ANNUAL_TYPES = {"annual", "integrated"}

db = SessionLocal()
institutions = sorted(
    db.execute(select(Institution).where(Institution.active == True)).scalars().all(),
    key=lambda i: i.slug,
)
all_docs = db.execute(select(SourceDocument)).scalars().all()
db.close()

doc_map: dict[tuple[int, int], list[SourceDocument]] = {}
for d in all_docs:
    doc_map.setdefault((d.institution_id, d.fiscal_year), []).append(d)

inst_by_id = {i.id: i for i in institutions}


def pick_doc(doc_list: list) -> tuple[SourceDocument | None, bool]:
    """Return (doc, is_eligible). Eligible = auto_ok + annual/integrated + not superseded."""
    eligible = [
        x for x in doc_list
        if str(x.review_status) == "auto_ok"
        and str(x.report_type) in ANNUAL_TYPES
        and x.superseded_by_id is None
    ]
    if eligible:
        return max(eligible, key=lambda d: d.page_count or 0), True
    # Fallback: best annual/integrated; else highest pages
    annual = [x for x in doc_list if str(x.report_type) in ANNUAL_TYPES]
    pool = annual if annual else doc_list
    return (max(pool, key=lambda d: d.page_count or 0) if pool else None), False


# Build work list
work_items: list[tuple[str, int, SourceDocument, bool]] = []  # (slug, year, doc, eligible)
for inst in institutions:
    for year in TARGET_YEARS:
        doc_list = doc_map.get((inst.id, year), [])
        doc, elig = pick_doc(doc_list)
        if doc:
            work_items.append((inst.slug, year, doc, elig))
        # cells with no doc at all are noted separately later

print(f"Work items: {len(work_items)}  (of 390 total cells)")
print("Downloading and scanning... (this may take several minutes)\n")

# ── parallel download + scan ──────────────────────────────────────────────────
cfg = R2Settings()
print_lock = Lock()
results: list[CellResult] = []
results_lock = Lock()

SOHAR_SLUG = "sohar-international-bank"


def process_item(slug: str, year: int, doc: SourceDocument, eligible: bool) -> CellResult:
    try:
        client = _r2_client()
        obj = client.get_object(Bucket=cfg.bucket, Key=doc.file_path)
        body = obj["Body"].read()
    except Exception as e:
        return CellResult(slug=slug, assigned_year=year, doc_id=doc.id,
                          pages=doc.page_count or 0, eligible=eligible,
                          actual_year=None, year_end_date=None, year_end_page=None,
                          year_end_source=None, non_december=False,
                          mismatch=False, evidence=None, error=f"R2_ERROR: {e}")

    actual_year, date_str, page, src = extract_fy(body, doc.id)
    nd = non_december(date_str)
    mismatch = (actual_year is not None and actual_year != year)

    return CellResult(
        slug=slug, assigned_year=year, doc_id=doc.id,
        pages=doc.page_count or 0, eligible=eligible,
        actual_year=actual_year, year_end_date=date_str, year_end_page=page,
        year_end_source=src, non_december=nd,
        mismatch=mismatch, evidence=date_str, error=None,
    )


with ThreadPoolExecutor(max_workers=15) as pool:
    futures = {pool.submit(process_item, s, y, d, e): (s, y) for s, y, d, e in work_items}
    done = 0
    for fut in as_completed(futures):
        r = fut.result()
        with results_lock:
            results.append(r)
        done += 1
        if done % 50 == 0:
            print(f"  ... {done}/{len(work_items)} done")

# ── sort results ──────────────────────────────────────────────────────────────
results.sort(key=lambda r: (r.slug, r.assigned_year))

# ── REPORT ────────────────────────────────────────────────────────────────────
DIVIDER = "=" * 110

# 1. Full table (abbreviated: only show non-trivial rows in detail)
print(f"\n{DIVIDER}")
print("SECTION 1 — FULL COVERAGE TABLE (mismatches / non-Dec / errors highlighted)")
print(DIVIDER)
print(f"{'Company':<52} {'FY':>4}  {'Elig':^5}  {'ActualFY':>8}  {'YearEnd':^22}  {'Pg':>4}  {'Src':^15}  Note")
print("-" * 130)

mismatches: list[CellResult] = []
non_dec_rows: list[CellResult] = []
errors: list[CellResult] = []

for r in results:
    flag = ""
    if r.error:
        flag = "ERROR"
        errors.append(r)
    elif r.mismatch:
        flag = "MISMATCH"
        mismatches.append(r)
    elif r.non_december:
        flag = "NON-DEC"
        non_dec_rows.append(r)
    elif r.actual_year is None:
        flag = "NOT_FOUND"

    # Always print flagged rows; for clean rows just show a dot
    if flag:
        elig_str = "OK" if r.eligible else "INELIG"
        date_disp = (r.year_end_date or "-")[:22]
        print(f"{r.slug:<52} {r.assigned_year:>4}  {elig_str:^6}  {str(r.actual_year or '?'):>8}  "
              f"{date_disp:<22}  {str(r.year_end_page or '-'):>4}  {(r.year_end_source or '-'):<15}  {flag}")
    else:
        # Quiet row — just a dot; uncomment the line below to see all rows
        pass
        # print(f"{r.slug:<52} {r.assigned_year:>4}  OK  {r.actual_year}  {r.year_end_date}")

# Count quiet rows
quiet = [r for r in results if not r.error and not r.mismatch and not r.non_december and r.actual_year is not None]
print(f"\n({len(quiet)} cells confirmed matching December year-end — suppressed for brevity)")

# ── Find cells with zero docs ─────────────────────────────────────────────────
cells_with_doc = {(r.slug, r.assigned_year) for r in results}
zero_doc_cells = []
for inst in institutions:
    for year in TARGET_YEARS:
        if (inst.slug, year) not in cells_with_doc:
            zero_doc_cells.append((inst.slug, year))

# ── SECTION 2: Mismatches ─────────────────────────────────────────────────────
print(f"\n{DIVIDER}")
print("SECTION 2 — YEAR MISMATCHES (assigned FY ≠ actual FY found in text)")
print(DIVIDER)
if mismatches:
    for r in mismatches:
        elig = "eligible" if r.eligible else "INELIGIBLE"
        print(f"  {r.slug:<52} assigned={r.assigned_year}  actual={r.actual_year}  "
              f"date='{r.year_end_date}'  page={r.year_end_page}  src={r.year_end_source}  [{elig}  id={r.doc_id}]")
else:
    print("  None found.")

# ── SECTION 3: Gaps and duplicates ───────────────────────────────────────────
print(f"\n{DIVIDER}")
print("SECTION 3 — GAPS AND DUPLICATES")
print(DIVIDER)

# Gaps: cells with no document at all
print(f"\nCells with no document at all ({len(zero_doc_cells)}):")
for slug, year in zero_doc_cells:
    print(f"  {slug}  FY{year}")

# Same fiscal year covered by two non-superseded documents
print(f"\nCells where two or more non-superseded annual/integrated docs cover the same year:")
dupe_cells = []
for inst in institutions:
    for year in TARGET_YEARS:
        cell = doc_map.get((inst.id, year), [])
        non_sup = [d for d in cell
                   if str(d.report_type) in ANNUAL_TYPES
                   and d.superseded_by_id is None]
        if len(non_sup) > 1:
            dupe_cells.append((inst.slug, year, non_sup))
if dupe_cells:
    for slug, year, docs in dupe_cells:
        ids = [(d.id, d.page_count, str(d.review_status)) for d in docs]
        print(f"  {slug}  FY{year}: {ids}")
else:
    print("  None.")

# Actual fiscal year mismatches creating implicit gaps/duplicates
if mismatches:
    print(f"\nActual fiscal year coverage implied by mismatches:")
    for r in mismatches:
        print(f"  {r.slug}: cell={r.assigned_year} but doc covers {r.actual_year} "
              f"→ actual FY{r.assigned_year} may be uncovered; FY{r.actual_year} double-covered")

# ── SECTION 4: Non-December year ends ────────────────────────────────────────
print(f"\n{DIVIDER}")
print("SECTION 4 — NON-DECEMBER YEAR-ENDS")
print(DIVIDER)
if non_dec_rows:
    for r in non_dec_rows:
        print(f"  {r.slug:<52} FY{r.assigned_year}  year_end='{r.year_end_date}'  "
              f"page={r.year_end_page}  src={r.year_end_source}  id={r.doc_id}")
else:
    print("  None found.")

# ── SECTION 5: Sohar detail ───────────────────────────────────────────────────
print(f"\n{DIVIDER}")
print("SECTION 5 — SOHAR INTERNATIONAL BANK: evidence for all six documents")
print(DIVIDER)
sohar_rows = [r for r in results if r.slug == SOHAR_SLUG]
if not sohar_rows:
    print("  No Sohar rows found in results.")
else:
    for r in sohar_rows:
        elig = "eligible" if r.eligible else "INELIGIBLE (needs_review)"
        print(f"\n  FY{r.assigned_year}  id={r.doc_id}  pages={r.pages}  [{elig}]")
        print(f"    actual_year={r.actual_year}  mismatch={r.mismatch}")
        print(f"    year_end_date : '{r.year_end_date}'")
        print(f"    year_end_page : {r.year_end_page}")
        print(f"    source        : {r.year_end_source}")
        if r.error:
            print(f"    ERROR: {r.error}")

# ── SECTION 6: Errors ────────────────────────────────────────────────────────
if errors:
    print(f"\n{DIVIDER}")
    print(f"SECTION 6 — ERRORS ({len(errors)})")
    print(DIVIDER)
    for r in errors:
        print(f"  {r.slug}  FY{r.assigned_year}  id={r.doc_id}  error={r.error}")

print(f"\n{DIVIDER}")
print(f"SUMMARY")
print(DIVIDER)
print(f"  Work items processed : {len(results)}")
print(f"  Cells with no doc    : {len(zero_doc_cells)}")
print(f"  Year mismatches      : {len(mismatches)}")
print(f"  Non-December year-end: {len(non_dec_rows)}")
print(f"  Confirmed (Dec, OK)  : {len(quiet)}")
print(f"  Errors               : {len(errors)}")
print(f"  Not-found            : {sum(1 for r in results if r.actual_year is None and not r.error)}")
