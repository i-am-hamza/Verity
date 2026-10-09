"""Step 3 — Verify the 390 new documents before any deletion.

Checks:
  1. All 390 new doc IDs exist in DB with review_status=auto_ok and
     report_type in {annual, integrated} and superseded_by_id IS NULL.
  2. Every one of the 65×6 cells has exactly one such document.
  3. Every new doc's R2 object exists and sha256 round-trips correctly.

Exits 0 only if all three pass. Prints STOP and exits 1 otherwise.
"""
import sys, io, hashlib, json
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

ids_path = Path(__file__).parent / '_step2_new_doc_ids.json'
new_ids: list[int] = json.loads(ids_path.read_text())['ids']
assert len(new_ids) == 390, f"Expected 390 ids, got {len(new_ids)}"

cfg = R2Settings()
client = _r2_client()

db = SessionLocal()
institutions = {i.id: i for i in db.execute(select(Institution).where(Institution.active == True)).scalars().all()}
all_new_docs = {
    d.id: d for d in db.execute(
        select(SourceDocument).where(SourceDocument.id.in_(new_ids))
    ).scalars().all()
}
db.close()

TARGET_YEARS = [2020, 2021, 2022, 2023, 2024, 2025]
ANNUAL_TYPES = {'annual', 'integrated'}

failures: list[str] = []

# ── Check 1: DB state of each new doc ────────────────────────────────────────
print(f"Check 1: DB state of {len(new_ids)} new documents...")
for doc_id in new_ids:
    d = all_new_docs.get(doc_id)
    if d is None:
        failures.append(f"  MISSING from DB: id={doc_id}")
        continue
    if str(d.review_status) != 'auto_ok':
        failures.append(f"  NOT auto_ok: id={doc_id} status={d.review_status}")
    if str(d.report_type) not in ANNUAL_TYPES:
        failures.append(f"  BAD type: id={doc_id} type={d.report_type}")
    if d.superseded_by_id is not None:
        failures.append(f"  SUPERSEDED: id={doc_id} superseded_by={d.superseded_by_id}")
if not [f for f in failures if 'Check 1' in f or failures]:
    print(f"  OK — all {len(new_ids)} docs have auto_ok + annual/integrated + not superseded")

# ── Check 2: exactly one eligible doc per cell ────────────────────────────────
print(f"\nCheck 2: exactly one eligible doc per 65×6 cell...")
from collections import defaultdict
cell_docs: dict[tuple[int, int], list[int]] = defaultdict(list)
for doc_id, d in all_new_docs.items():
    cell_docs[(d.institution_id, d.fiscal_year)].append(doc_id)

missing_cells = []
multi_cells = []
for inst_id in institutions:
    for yr in TARGET_YEARS:
        docs = cell_docs.get((inst_id, yr), [])
        if len(docs) == 0:
            slug = institutions[inst_id].slug
            missing_cells.append(f"  NO_DOC: {slug} FY{yr}")
        elif len(docs) > 1:
            slug = institutions[inst_id].slug
            multi_cells.append(f"  MULTI({len(docs)}): {slug} FY{yr} ids={docs}")

if missing_cells:
    failures.extend(missing_cells)
if multi_cells:
    failures.extend(multi_cells)

if not missing_cells and not multi_cells:
    print(f"  OK — all 390 cells have exactly one eligible document")

# ── Check 3: R2 sha256 round-trip for every new doc ───────────────────────────
print(f"\nCheck 3: R2 sha256 round-trip for all 390 objects...")
r2_failures = 0
for i, (doc_id, d) in enumerate(sorted(all_new_docs.items()), 1):
    try:
        obj = client.get_object(Bucket=cfg.bucket, Key=d.file_path)
        body = obj['Body'].read()
        r2_sha = hashlib.sha256(body).hexdigest()
        if r2_sha != d.sha256:
            failures.append(f"  SHA_MISMATCH: id={doc_id} key={d.file_path}")
            r2_failures += 1
    except Exception as e:
        failures.append(f"  R2_ERROR: id={doc_id} key={d.file_path}: {e}")
        r2_failures += 1
    if i % 60 == 0:
        print(f"  ... {i}/390 checked")

if r2_failures == 0:
    print(f"  OK — all 390 R2 sha256 round-trips passed")

# ── Result ────────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
if failures:
    print(f"STOP — {len(failures)} failures. Do NOT delete anything.\n")
    for f in failures:
        print(f)
    sys.exit(1)
else:
    print("Step 3 PASS — all 390 documents verified. Safe to proceed to step 4.")
    sys.exit(0)
