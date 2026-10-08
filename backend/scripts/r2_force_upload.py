"""Force-upload the 30 Phase-1 new-company files to R2 under their existing keys.
These are in source_documents (ids 222-251) and in backend/storage/reports/
but were never uploaded to R2 (Phase 1 ran without R2 configured).
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

# The 30 source_document IDs (5 companies x 6 years each)
TARGET_IDS = list(range(222, 252))  # 222 to 251 inclusive

cfg = R2Settings()
client = _r2_client()
assert client is not None, "R2 not configured — aborting"
print(f"R2 bucket: {cfg.bucket}")

backend_reports = Path(r"E:\9. Verity\backend\storage\reports")

db = SessionLocal()
docs = db.execute(select(SourceDocument).where(SourceDocument.id.in_(TARGET_IDS))).scalars().all()
db.close()

print(f"\nUploading {len(docs)} files to R2...\n")

results = []
for doc in sorted(docs, key=lambda d: (d.institution_id, d.fiscal_year)):
    r2_key = file_path_to_r2_key(doc.file_path)
    local_path = backend_reports / r2_key.replace('/', '\\')

    if not local_path.exists():
        results.append({'id': doc.id, 'key': r2_key, 'status': 'ERROR: local file missing', 'verified': False})
        print(f"  ERROR id={doc.id} key={r2_key}: local file not found at {local_path}")
        continue

    # Read local file
    body = local_path.read_bytes()
    local_sha = hashlib.sha256(body).hexdigest()

    # Verify local sha256 matches DB record
    if local_sha != doc.sha256:
        results.append({'id': doc.id, 'key': r2_key, 'status': f'MISMATCH local sha={local_sha[:16]} db sha={doc.sha256[:16]}', 'verified': False})
        print(f"  MISMATCH id={doc.id}: local sha {local_sha[:16]} != DB {doc.sha256[:16]}")
        continue

    # Check if already on R2
    try:
        client.head_object(Bucket=cfg.bucket, Key=r2_key)
        results.append({'id': doc.id, 'key': r2_key, 'status': 'already_on_r2', 'verified': True})
        print(f"  SKIP id={doc.id} key={r2_key}: already on R2")
        continue
    except Exception:
        pass  # Not on R2, proceed to upload

    # Upload to R2
    try:
        client.put_object(
            Bucket=cfg.bucket, Key=r2_key, Body=body,
            ContentType='application/pdf'
        )
    except Exception as e:
        results.append({'id': doc.id, 'key': r2_key, 'status': f'UPLOAD_ERROR: {e}', 'verified': False})
        print(f"  UPLOAD_ERROR id={doc.id} key={r2_key}: {e}")
        continue

    # sha256 round-trip verification: download from R2 and check
    try:
        obj = client.get_object(Bucket=cfg.bucket, Key=r2_key)
        r2_body = obj['Body'].read()
        r2_sha = hashlib.sha256(r2_body).hexdigest()
    except Exception as e:
        results.append({'id': doc.id, 'key': r2_key, 'status': f'ROUNDTRIP_DOWNLOAD_ERROR: {e}', 'verified': False})
        print(f"  ROUNDTRIP_ERROR id={doc.id}: {e}")
        continue

    if r2_sha != doc.sha256:
        results.append({'id': doc.id, 'key': r2_key, 'status': f'ROUNDTRIP_SHA_MISMATCH r2={r2_sha[:16]} db={doc.sha256[:16]}', 'verified': False})
        print(f"  ROUNDTRIP_MISMATCH id={doc.id}: R2 sha {r2_sha[:16]} != DB {doc.sha256[:16]}")
        continue

    results.append({'id': doc.id, 'key': r2_key, 'status': 'uploaded_verified', 'verified': True, 'bytes': len(body)})
    print(f"  OK id={doc.id} key={r2_key}: uploaded + verified ({len(body)//1024}KB sha={r2_sha[:16]})")

# Summary
ok = [r for r in results if r['verified']]
errors = [r for r in results if not r['verified']]
print(f"\n=== R2 UPLOAD SUMMARY ===")
print(f"Total: {len(results)}  OK/verified: {len(ok)}  Errors: {len(errors)}")
if errors:
    print("\nErrors:")
    for e in errors:
        print(f"  id={e['id']} {e['key']}: {e['status']}")

# Check no local fallback happened: verify R2 client is active
if not cfg.enabled:
    print("\nSTOP: R2 is not enabled — writes would go to local disk!")
    raise SystemExit(1)
print("\nR2 is enabled. No local disk fallback.")
