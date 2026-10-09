"""Download specific documents from R2 into E:\9. Verity\storage\review\ for hand-checking.

Files:
- 16 wrong_type cells from coverage matrix
- emirates-nbd-pjsc FY2020 (30p)
- abdullah-al-othaim-markets FY2021 (33p)

Named: "<slug> FY<year> <pages>p.pdf". Does NOT change DB classification.
"""
import sys, io, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv('.env')

from pathlib import Path

from app.crawler import register_all_mappers
register_all_mappers()

from app.database import SessionLocal
from app.models.provenance import SourceDocument
from app.models.institution import Institution
from app.services.storage import _r2_client, R2Settings, file_path_to_r2_key
from sqlalchemy import select

TARGETS = [
    # (slug, year)  — 16 wrong_type + 2 short/under-30
    ('al-rajhi-bank', 2024),
    ('bank-dhofar', 2022),
    ('bank-muscat-bkmb', 2022),
    ('boubyan-bank', 2023),
    ('boubyan-bank', 2024),
    ('dubai-investment', 2024),
    ('dubai-islamic-bank', 2024),
    ('kuwait-finance-house', 2023),
    ('national-bank-of-bahrain', 2020),
    ('national-bank-of-bahrain', 2022),
    ('national-bank-of-kuwait', 2021),
    ('qnb-qatar-national-bank', 2021),
    ('riyad-bank', 2023),
    ('the-national-bank-of-ras-al-khaimah', 2023),
    ('the-saudi-national-bank', 2023),
    ('the-saudi-national-bank', 2024),
    # additional short-page entries
    ('emirates-nbd-pjsc', 2020),
    ('abdullah-al-othaim-markets', 2021),
]

review_dir = Path(r"E:\9. Verity\storage\review")
review_dir.mkdir(parents=True, exist_ok=True)

cfg = R2Settings()
client = _r2_client()

db = SessionLocal()
inst_by_slug = {i.slug: i for i in db.execute(select(Institution)).scalars().all()}
all_docs = db.execute(select(SourceDocument)).scalars().all()
db.close()

# Index: (inst_id, year) -> best doc (prefer annual/integrated, then highest pages)
ANNUAL_TYPES = {'annual', 'integrated'}

def best_doc(docs):
    annual = [d for d in docs if str(d.report_type) in ANNUAL_TYPES]
    pool = annual if annual else docs
    return max(pool, key=lambda d: (d.page_count or 0))

doc_map = {}
for d in all_docs:
    doc_map.setdefault((d.institution_id, d.fiscal_year), []).append(d)

n_ok = 0
n_errors = 0

for slug, year in TARGETS:
    inst = inst_by_slug.get(slug)
    if inst is None:
        print(f"  ERROR: slug {slug!r} not in DB")
        n_errors += 1
        continue

    cell = doc_map.get((inst.id, year), [])
    if not cell:
        print(f"  ERROR: no source_document for {slug} FY{year}")
        n_errors += 1
        continue

    d = best_doc(cell)
    r2_key = file_path_to_r2_key(d.file_path)
    pages = d.page_count or 0
    out_name = f"{slug} FY{year} {pages}p.pdf"
    out_path = review_dir / out_name

    if out_path.exists():
        print(f"  SKIP (exists): {out_name}")
        n_ok += 1
        continue

    try:
        obj = client.get_object(Bucket=cfg.bucket, Key=r2_key)
        body = obj['Body'].read()
    except Exception as e:
        print(f"  R2_ERROR {slug} FY{year}: {e}")
        n_errors += 1
        continue

    # sha256 integrity check
    r2_sha = hashlib.sha256(body).hexdigest()
    if r2_sha != d.sha256:
        print(f"  SHA_MISMATCH {slug} FY{year}: r2={r2_sha[:16]} db={d.sha256[:16]}")
        n_errors += 1
        continue

    out_path.write_bytes(body)
    print(f"  OK  {out_name}  ({len(body)//1024}KB  id={d.id}  type={d.report_type})")
    n_ok += 1

print(f"\n=== DOWNLOAD SUMMARY ===")
print(f"OK: {n_ok}  Errors: {n_errors}")
print(f"Destination: {review_dir}")
