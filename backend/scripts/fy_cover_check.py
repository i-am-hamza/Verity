"""Check cover page text for uncertain docs and verify a few systematic cases."""
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

cfg = R2Settings()
client = _r2_client()
db = SessionLocal()

# Al Othaim FY2024/2025 (uncertain) + Ooredoo FY2021 as sanity check
CHECKS = [
    (254, 'al-othaim', 2024, 'cover only'),
    (255, 'al-othaim', 2025, 'cover only'),
    (183, 'ooredoo',   2021, 'first match only'),  # sanity check
    (188, 'qatar-fuel', 2021, 'auditor text'),      # auditor_phrase case
]

_YE_RX = re.compile(
    r"(?:for\s+the\s+)?(?:financial\s+|fiscal\s+)?year\s+ended"
    r"\s+"
    r"(\d{1,2}\s+(?:january|february|march|april|may|june|july|august|"
    r"september|october|november|december)\s+20\d{2}"
    r"|(?:january|february|march|april|may|june|july|august|"
    r"september|october|november|december)\s+\d{1,2},?\s+20\d{2}"
    r"|31/12/20\d{2})",
    re.IGNORECASE,
)
_YEAR_RX = re.compile(r"(20\d{2})")
_AUDITOR_RX = re.compile(
    r"independent\s+auditor(?:s)?(?:'|')?s?\s+report"
    r"|report\s+of\s+the\s+independent\s+auditor",
    re.IGNORECASE,
)

for doc_id, label, assigned, note in CHECKS:
    d = db.get(SourceDocument, doc_id)
    obj = client.get_object(Bucket=cfg.bucket, Key=d.file_path)
    body = obj['Body'].read()
    pdf = pymupdf.open(stream=body, filetype="pdf")

    print(f"\n{'='*80}")
    print(f"id={doc_id}  {label}  assigned=FY{assigned}  pages={pdf.page_count}  ({note})")

    # Cover: first 3 pages full text
    for i in range(min(3, pdf.page_count)):
        t = pdf[i].get_text("text") or ""
        years = re.findall(r"20\d{2}", t)
        yr_counts: dict[str, int] = {}
        for y in years:
            yr_counts[y] = yr_counts.get(y, 0) + 1
        # Show top years and any "year ended" hits on cover
        ye_hits = list(_YE_RX.finditer(t))
        print(f"  p{i+1}: year_counts={sorted(yr_counts.items())}  ye_hits={[m.group(0)[:60] for m in ye_hits]}")
        if i == 0:
            # Show first 400 chars of cover page
            print(f"  cover_text_snippet: {t[:400].replace(chr(10), ' ')!r}")

    pdf.close()

db.close()
