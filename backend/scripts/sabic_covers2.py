"""Read cover pages of all 9 SABIC source files + 3 existing DB entries."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv(".env")

import re
from pathlib import Path
import pymupdf

from app.crawler import register_all_mappers
register_all_mappers()
from app.database import SessionLocal
from app.models.provenance import SourceDocument
from app.models.institution import Institution
from app.services.storage import _r2_client, R2Settings, file_path_to_r2_key
from sqlalchemy import select

source_dir = Path(r"E:\9. Verity\storage\reports")
sabic_files = sorted(source_dir.glob("SABIC*.pdf")) + sorted(source_dir.glob("sabic*.pdf"))
# dedupe
seen = set()
unique_sabic = []
for f in sabic_files:
    if f.name not in seen:
        seen.add(f.name)
        unique_sabic.append(f)

print("=" * 80)
print("SABIC files in source folder (9 files)")
print("=" * 80)
for f in unique_sabic:
    print(f"\n--- {f.name} ---")
    doc = pymupdf.open(str(f))
    pages = doc.page_count
    text = ""
    for pg in range(min(2, pages)):
        text += doc[pg].get_text()
    doc.close()
    cleaned = re.sub(r"\s+", " ", text[:900]).strip()
    cleaned = cleaned.encode('utf-8', errors='replace').decode('utf-8')
    print(f"  Pages: {pages}")
    print(f"  Text: {cleaned[:700]}")

print()
print("=" * 80)
print("Existing SABIC entries in DB (FY2020, FY2022, FY2025)")
print("=" * 80)

db = SessionLocal()
sabic_inst = db.execute(select(Institution).where(Institution.slug == "sabic")).scalar_one()
existing = db.execute(
    select(SourceDocument).where(SourceDocument.institution_id == sabic_inst.id)
).scalars().all()
db.close()

cfg = R2Settings()
client = _r2_client()

for d in sorted(existing, key=lambda x: x.fiscal_year):
    r2_key = file_path_to_r2_key(d.file_path)
    print(f"\nFY{d.fiscal_year}  id={d.id}  type={d.report_type}  sha={d.sha256[:16]}  pages={d.page_count}")
    print(f"  key: {r2_key}")
    try:
        obj = client.get_object(Bucket=cfg.bucket, Key=r2_key)
        data = obj["Body"].read()
        doc = pymupdf.open("pdf", data)
        pages = doc.page_count
        text = ""
        for pg in range(min(2, pages)):
            text += doc[pg].get_text()
        doc.close()
        cleaned = re.sub(r"\s+", " ", text[:800]).strip()
        cleaned = cleaned.encode('utf-8', errors='replace').decode('utf-8')
        print(f"  Pages from R2: {pages}")
        print(f"  Cover text: {cleaned[:600]}")
    except Exception as e:
        print(f"  R2 read error: {e}")
