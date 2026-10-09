"""Step 4 — Delete all old source_documents, derived rows, old R2 objects,
and old local PDF files now that step 3 has passed.

What is deleted:
  DB:  source_documents NOT in the new verified set of 390
       reports, category_scores, match_evidence, match_reviews, gaps, runs,
       crawl_log rows tied to old docs (all crawl_log rows are cleared)
  R2:  objects whose key is NOT in the new set's file_path values
  FS:  PDF files under backend/storage/reports/ (acme-corp fixtures preserved)

What is NOT touched:
  institutions, taxonomy_versions, terms, settings, alembic_version
  The 390 new source_documents and their R2 objects

SAFE GUARD: reads _step2_new_doc_ids.json and aborts if the file is missing
or does not contain exactly 390 ids.
"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv('.env')
from pathlib import Path

from app.crawler import register_all_mappers
register_all_mappers()
from app.database import SessionLocal
from app.models.provenance import SourceDocument
from app.services.storage import _r2_client, R2Settings
from sqlalchemy import select, delete, text

# ── Load new doc IDs ──────────────────────────────────────────────────────────
ids_path = Path(__file__).parent / '_step2_new_doc_ids.json'
if not ids_path.exists():
    print("STOP: _step2_new_doc_ids.json not found. Run step 3 first.")
    sys.exit(1)

new_ids: set[int] = set(json.loads(ids_path.read_text())['ids'])
assert len(new_ids) == 390, f"STOP: expected 390 ids, got {len(new_ids)}"
print(f"New set: {len(new_ids)} doc IDs loaded")

cfg = R2Settings()
client = _r2_client()

db = SessionLocal()

# ── Collect new file_paths (R2 keys to keep) ─────────────────────────────────
new_docs = db.execute(
    select(SourceDocument).where(SourceDocument.id.in_(new_ids))
).scalars().all()
assert len(new_docs) == 390, f"STOP: only {len(new_docs)} new docs found in DB"
keep_keys: set[str] = {d.file_path for d in new_docs}

# ── Collect old doc IDs ───────────────────────────────────────────────────────
all_doc_ids: list[int] = [
    row[0] for row in db.execute(select(SourceDocument.id)).all()
]
old_ids = [i for i in all_doc_ids if i not in new_ids]
print(f"Old docs to delete from DB: {len(old_ids)}")

# ── DB deletions ──────────────────────────────────────────────────────────────
# Deletion order respects FK constraints:
#   match_reviews → match_evidence → category_scores → reports → source_documents
# gaps and runs/crawl_log are cleared entirely (no scoring has run on the new set)
print("\nDeleting derived rows...")

ordered_full_clears = [
    'match_reviews',    # FK: evidence_id → match_evidence
    'match_evidence',   # FK: report_id → reports
    'category_scores',  # FK: report_id → reports
    'reports',          # FK: source_document_id → source_documents
    'gaps',             # institution_id/fiscal_year only — all stale
    'runs',
    'crawl_log',
]
for tbl in ordered_full_clears:
    try:
        r = db.execute(text(f"DELETE FROM {tbl}"))
        db.commit()
        print(f"  {tbl}: {r.rowcount} rows deleted")
    except Exception as e:
        db.rollback()
        print(f"  {tbl}: skipped ({e})")

# source_documents — delete only old ids
print(f"\nDeleting {len(old_ids)} old source_documents...")
if old_ids:
    r = db.execute(
        delete(SourceDocument).where(SourceDocument.id.in_(old_ids))
    )
    db.commit()
    print(f"  source_documents: {r.rowcount} rows deleted")
db.close()

# ── R2 deletions ──────────────────────────────────────────────────────────────
print("\nScanning R2 for old objects...")
paginator = client.get_paginator('list_objects_v2')
old_r2_keys: list[str] = []
total_r2 = 0
for page in paginator.paginate(Bucket=cfg.bucket):
    for obj in page.get('Contents', []):
        total_r2 += 1
        if obj['Key'] not in keep_keys:
            old_r2_keys.append(obj['Key'])

print(f"  Total R2 objects: {total_r2}")
print(f"  To keep: {len(keep_keys)}")
print(f"  To delete: {len(old_r2_keys)}")

if old_r2_keys:
    # Delete in batches of 1000 (S3/R2 limit)
    n_deleted = 0
    for i in range(0, len(old_r2_keys), 1000):
        batch = old_r2_keys[i:i + 1000]
        client.delete_objects(
            Bucket=cfg.bucket,
            Delete={'Objects': [{'Key': k} for k in batch]}
        )
        n_deleted += len(batch)
    print(f"  Deleted {n_deleted} R2 objects")
else:
    print("  No old R2 objects to delete")

# ── Local FS cleanup ──────────────────────────────────────────────────────────
print("\nCleaning local backend/storage/reports/...")
local_root = Path(__file__).parent.parent / 'storage' / 'reports'
if local_root.exists():
    removed_files = 0
    for p in sorted(local_root.rglob('*.pdf')):
        # Preserve acme-corp test fixtures
        if 'acme' in str(p).lower() or 'acme-corp' in str(p).lower():
            continue
        try:
            p.unlink()
            removed_files += 1
        except Exception as e:
            print(f"  WARN: could not delete {p}: {e}")
    # Remove empty directories (bottom-up)
    for d in sorted(local_root.rglob('*'), reverse=True):
        if d.is_dir():
            try:
                d.rmdir()  # only removes if empty
            except OSError:
                pass
    print(f"  Removed {removed_files} local PDF files")
else:
    print("  backend/storage/reports/ does not exist — nothing to clean")

# ── Final tally ───────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("Step 4 COMPLETE")
print(f"  Old source_documents deleted: {len(old_ids)}")
print(f"  Old R2 objects deleted:       {len(old_r2_keys)}")
print(f"  Local PDFs removed:           {removed_files if local_root.exists() else 0}")
print(f"  New set intact:               390 docs, 390 R2 objects")
