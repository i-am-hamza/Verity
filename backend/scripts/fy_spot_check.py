"""Spot-check suspicious mismatches: extract the specific page text
where the year-end phrase was found, plus the nearest auditor's report page.
"""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv('.env')

import pymupdf
from app.crawler import register_all_mappers
register_all_mappers()
from app.database import SessionLocal
from app.models.provenance import SourceDocument
from app.services.storage import _r2_client, R2Settings

_AUDITOR_RX = re.compile(
    r"independent\s+auditor(?:s)?(?:'|')?s?\s+report"
    r"|report\s+of\s+the\s+independent\s+auditor",
    re.IGNORECASE,
)
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

# (doc_id, slug, assigned_year, found_year, found_page)
SUSPECTS = [
    (459, 'riyad-bank', 2025, 2023, 56),
    (461, 'the-saudi-national-bank', 2023, 2021, 43),
    (254, 'abdullah-al-othaim-markets', 2024, 2025, 65),
    (255, 'abdullah-al-othaim-markets', 2025, 2026, 74),
]

cfg = R2Settings()
client = _r2_client()
db = SessionLocal()

for doc_id, slug, assigned_yr, found_yr, found_page in SUSPECTS:
    d = db.get(SourceDocument, doc_id)
    if not d:
        print(f"id={doc_id}: NOT FOUND")
        continue

    print(f"\n{'='*90}")
    print(f"id={doc_id}  {slug}  assigned=FY{assigned_yr}  suspicious_find=FY{found_yr}  "
          f"on_page={found_page}  total_pages={d.page_count}")
    print(f"  file: {d.file_path}")

    obj = client.get_object(Bucket=cfg.bucket, Key=d.file_path)
    body = obj['Body'].read()
    pdf = pymupdf.open(stream=body, filetype="pdf")

    # Print the suspicious page text
    page_idx = found_page - 1
    if 0 <= page_idx < pdf.page_count:
        text = pdf[page_idx].get_text("text") or ""
        # Highlight year-end occurrences
        matches = list(_YE_RX.finditer(text))
        print(f"\n--- Page {found_page} (all year-ended phrases): ---")
        for m in matches:
            start = max(0, m.start() - 60)
            end = min(len(text), m.end() + 60)
            snippet = text[start:end].replace('\n', ' ')
            print(f"  ...{snippet}...")

    # Find auditor's report pages
    auditor_pages = []
    all_ye_hits: list[tuple[int, str]] = []
    for i in range(pdf.page_count):
        try:
            t = pdf[i].get_text("text") or ""
        except Exception:
            t = ""
        if _AUDITOR_RX.search(t):
            auditor_pages.append(i + 1)
        for m in _YE_RX.finditer(t):
            all_ye_hits.append((i + 1, m.group(0).strip()))

    print(f"\n  Auditor report pages: {auditor_pages}")
    print(f"\n  ALL 'year ended' occurrences (page, phrase):")
    for pg, phrase in all_ye_hits[:30]:  # cap at 30
        print(f"    p{pg:4d}  {phrase[:90]}")
    if len(all_ye_hits) > 30:
        print(f"    ... and {len(all_ye_hits)-30} more")

    pdf.close()

db.close()
