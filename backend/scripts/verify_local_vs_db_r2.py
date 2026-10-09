"""Read-only audit: verify every PDF in both local storage folders has a
matching sha256 in source_documents AND is present on R2.
Reports any that are missing from either. Changes nothing.
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
from app.services.storage import _r2_client, R2Settings, file_path_to_r2_key
from sqlalchemy import select

SCAN_DIRS = [
    Path(r"E:\9. Verity\storage\reports"),
    Path(r"E:\9. Verity\backend\storage\reports"),
]

cfg = R2Settings()
client = _r2_client()

db = SessionLocal()
all_docs = db.execute(select(SourceDocument)).scalars().all()
db.close()

sha_to_doc = {d.sha256: d for d in all_docs}

# ---- Scan all PDFs -------------------------------------------------------
print("Scanning local folders...")
local_files = []
for d in SCAN_DIRS:
    if not d.exists():
        print(f"  (folder does not exist: {d})")
        continue
    pdfs = sorted(d.rglob("*.pdf"))
    print(f"  {d}: {len(pdfs)} PDFs")
    for p in pdfs:
        local_files.append(p)

print(f"\nTotal PDFs found: {len(local_files)}")
print("Computing sha256 and checking DB + R2 (this may take a moment)...\n")

not_in_db   = []
not_on_r2   = []
ok_count    = 0

for fpath in local_files:
    body = fpath.read_bytes()
    sha  = hashlib.sha256(body).hexdigest()

    doc = sha_to_doc.get(sha)
    if doc is None:
        not_in_db.append({'path': str(fpath), 'sha': sha})
        continue

    r2_key = file_path_to_r2_key(doc.file_path)
    try:
        client.head_object(Bucket=cfg.bucket, Key=r2_key)
        ok_count += 1
    except Exception:
        not_on_r2.append({'path': str(fpath), 'sha': sha[:16],
                          'doc_id': doc.id, 'slug': doc.file_path.split('/')[0],
                          'year': doc.fiscal_year, 'r2_key': r2_key})

print(f"=== RESULTS ===")
print(f"Total PDFs checked : {len(local_files)}")
print(f"OK (in DB + on R2) : {ok_count}")
print(f"Not in DB          : {len(not_in_db)}")
print(f"In DB but not on R2: {len(not_on_r2)}")

if not_in_db:
    print(f"\nNOT IN source_documents ({len(not_in_db)}):")
    for f in not_in_db:
        print(f"  sha={f['sha'][:16]}  {f['path']}")

if not_on_r2:
    print(f"\nIN DB BUT NOT ON R2 ({len(not_on_r2)}):")
    for f in not_on_r2:
        print(f"  id={f['doc_id']}  {f['slug']} FY{f['year']}  r2_key={f['r2_key']}")
        print(f"    local: {f['path']}")

if not not_in_db and not not_on_r2:
    print("\nAll local PDFs are accounted for in source_documents and present on R2.")
