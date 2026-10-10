"""Download 9 specific documents from R2 into E:\9. Verity\storage\review\ for hand-checking.

Targets by doc ID (not best_doc logic) so we get exactly the intended file.
Clears the review directory first, then downloads fresh.
Does NOT change any DB classification.
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
from app.services.storage import _r2_client, R2Settings
from sqlalchemy import select

# (doc_id, slug, year) — slug/year used only for the output filename
TARGETS = [
    (70,  'national-bank-of-bahrain',              2023),
    (434, 'bank-albilad',                          2021),
    (449, 'dubai-investment',                      2024),
    (450, 'emirates-nbd-pjsc',                     2022),
    (263, 'air-arabia-pjsc',                       2020),
    (115, 'air-arabia-pjsc',                       2021),
    (246, 'salam-international-investment',         2020),
    (247, 'salam-international-investment',         2021),
]

review_dir = Path(r"E:\9. Verity\storage\review")
review_dir.mkdir(parents=True, exist_ok=True)

# Clear existing files
deleted = 0
for f in review_dir.iterdir():
    if f.is_file():
        f.unlink()
        deleted += 1
print(f"Cleared {deleted} existing file(s) from {review_dir}")

cfg = R2Settings()
client = _r2_client()

db = SessionLocal()
n_ok = n_errors = 0

for doc_id, slug, year in TARGETS:
    d = db.get(SourceDocument, doc_id)
    if d is None:
        print(f"  ERROR: doc id={doc_id} not found in DB")
        n_errors += 1
        continue

    r2_key = d.file_path
    pages = d.page_count or 0
    out_name = f"{slug} FY{year} {pages}p.pdf"
    out_path = review_dir / out_name

    try:
        obj = client.get_object(Bucket=cfg.bucket, Key=r2_key)
        body = obj['Body'].read()
    except Exception as e:
        print(f"  R2_ERROR id={doc_id} {slug} FY{year}: {e}")
        n_errors += 1
        continue

    r2_sha = hashlib.sha256(body).hexdigest()
    if r2_sha != d.sha256:
        print(f"  SHA_MISMATCH id={doc_id}: r2={r2_sha[:16]} db={d.sha256[:16]}")
        n_errors += 1
        continue

    out_path.write_bytes(body)
    print(f"  OK  {out_name}  ({len(body)//1024}KB  id={d.id}  type={d.report_type}  status={d.review_status})")
    n_ok += 1

db.close()

print(f"\n=== DOWNLOAD SUMMARY ===")
print(f"Deleted: {deleted}  Downloaded OK: {n_ok}  Errors: {n_errors}")
print(f"Destination: {review_dir}")
