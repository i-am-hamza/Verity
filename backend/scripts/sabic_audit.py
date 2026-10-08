"""Audit SABIC held files and existing DB entries.

For each of the 9 HOLD files and 3 existing SABIC DB entries (FY2020, FY2022, FY2025):
  - filename, sha256 (recomputed from source), page count (recomputed), cover text
  - cross-match sha256 between hold files and DB entries to detect duplicates
"""
import sys, io, hashlib, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv('.env')

import pymupdf
from pathlib import Path

from app.crawler import register_all_mappers
register_all_mappers()
from app.database import SessionLocal
from app.models.provenance import SourceDocument
from app.models.institution import Institution
from app.services.storage import _r2_client, R2Settings, file_path_to_r2_key
from sqlalchemy import select

SABIC_HOLD_NAMES = [
    'SABIC Annual Report 2020.pdf',
    'SABIC Annual Report 2021.pdf',
    'SABIC Annual Report 2022.pdf',
    'SABIC Annual Report 2023.pdf',
    'SABIC Annual Report 2024.pdf',
    'SABIC Annual Report 2025.pdf',
    'SABIC-Integrated-Annual-Report-2023.pdf',
    'SABIC-Integrated-Annual-Report-2024.pdf',
    'SABIC_Annual_Report_2021.pdf',
]

source_dir = Path(r"E:\9. Verity\storage\reports")
cfg = R2Settings()
client = _r2_client()

db = SessionLocal()
sabic_inst = db.execute(select(Institution).where(Institution.slug == 'sabic')).scalar_one()
existing_docs = db.execute(
    select(SourceDocument).where(SourceDocument.institution_id == sabic_inst.id)
).scalars().all()
db.close()


def cover_text(pdf_bytes, n_pages=2):
    doc = pymupdf.open("pdf", pdf_bytes)
    pages = doc.page_count
    text = ""
    for pg in range(min(n_pages, pages)):
        text += doc[pg].get_text()
    doc.close()
    cleaned = re.sub(r"\s+", " ", text[:1200]).strip()
    return pages, cleaned.encode('utf-8', errors='replace').decode('utf-8')


print("=" * 90)
print("PART A: 9 SABIC HOLD FILES (from source folder)")
print("=" * 90)

hold_sha_map = {}  # sha256 -> filename
for fname in SABIC_HOLD_NAMES:
    fpath = source_dir / fname
    if not fpath.exists():
        print(f"\n  MISSING: {fname}")
        continue
    body = fpath.read_bytes()
    sha = hashlib.sha256(body).hexdigest()
    pages, text = cover_text(body)
    hold_sha_map[sha] = fname
    print(f"\n--- {fname} ---")
    print(f"  sha256:     {sha}")
    print(f"  pages:      {pages}")
    print(f"  cover text: {text[:500]}")

print()
print("=" * 90)
print("PART B: 3 EXISTING SABIC DB ENTRIES (FY2020, FY2022, FY2025) — fetched from R2")
print("=" * 90)

db_sha_map = {}  # sha256 -> (id, year)
for d in sorted(existing_docs, key=lambda x: x.fiscal_year):
    r2_key = file_path_to_r2_key(d.file_path)
    print(f"\n--- DB FY{d.fiscal_year}  id={d.id}  db_pages={d.page_count}  db_sha={d.sha256} ---")
    print(f"  R2 key: {r2_key}")
    try:
        obj = client.get_object(Bucket=cfg.bucket, Key=r2_key)
        body = obj['Body'].read()
        sha = hashlib.sha256(body).hexdigest()
        pages, text = cover_text(body)
        db_sha_map[sha] = (d.id, d.fiscal_year)
        sha_match = "MATCH" if sha == d.sha256 else f"MISMATCH (R2 sha={sha[:16]})"
        print(f"  sha256 (R2):  {sha}  [{sha_match}]")
        print(f"  pages (R2):   {pages}")
        print(f"  cover text:   {text[:500]}")
    except Exception as e:
        print(f"  R2 error: {e}")

print()
print("=" * 90)
print("PART C: SHA256 CROSS-MATCH")
print("=" * 90)
overlap = set(hold_sha_map) & set(db_sha_map)
if overlap:
    for sha in sorted(overlap):
        hold_f = hold_sha_map[sha]
        db_id, db_year = db_sha_map[sha]
        print(f"  DUPLICATE: hold file '{hold_f}'  ==  DB id={db_id} FY{db_year}  sha={sha[:16]}")
else:
    print("  No sha256 overlaps between held files and existing DB entries.")
