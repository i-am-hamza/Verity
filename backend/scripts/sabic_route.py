"""Route the 9 SABIC HOLD files to the correct institutions.

6 SABIC Agri-Nutrients files → saudi-arabian-fertilizer-company FY2020-2025 (annual)
3 SABIC proper files → sabic FY2021 (annual), FY2023 (integrated), FY2024 (integrated)

Researcher go-ahead: 2026-10-08. Same rules as bulk_ingest: sha256 round-trip,
STOP if anything lands on local disk.
"""
import sys, io, hashlib, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv('.env')

from datetime import UTC, datetime
from pathlib import Path

from app.crawler import register_all_mappers
register_all_mappers()

from app.database import SessionLocal
from app.models.provenance import SourceDocument, ReportType, ReviewStatus, SourceType
from app.models.institution import Institution
from app.crawler.validate import validate_pdf
from app.services.storage import _r2_client, R2Settings, r2_enabled
from app.crawler.config import MANIFEST_PATH
from sqlalchemy import select

assert r2_enabled(), "STOP: R2 not enabled — writes would go to local disk"
cfg = R2Settings()
client = _r2_client()
print(f"R2 enabled: bucket={cfg.bucket}")

source_dir = Path(r"E:\9. Verity\storage\reports")

ROUTING = [
    # (filename, slug, fiscal_year, forced_type)
    # SABIC Agri-Nutrients
    ('SABIC Annual Report 2020.pdf', 'saudi-arabian-fertilizer-company', 2020, 'annual'),
    ('SABIC Annual Report 2021.pdf', 'saudi-arabian-fertilizer-company', 2021, 'annual'),
    ('SABIC Annual Report 2022.pdf', 'saudi-arabian-fertilizer-company', 2022, 'annual'),
    ('SABIC Annual Report 2023.pdf', 'saudi-arabian-fertilizer-company', 2023, 'annual'),
    ('SABIC Annual Report 2024.pdf', 'saudi-arabian-fertilizer-company', 2024, 'annual'),
    ('SABIC Annual Report 2025.pdf', 'saudi-arabian-fertilizer-company', 2025, 'annual'),
    # SABIC proper
    ('SABIC_Annual_Report_2021.pdf',            'sabic', 2021, 'annual'),
    ('SABIC-Integrated-Annual-Report-2023.pdf', 'sabic', 2023, 'integrated'),
    ('SABIC-Integrated-Annual-Report-2024.pdf', 'sabic', 2024, 'integrated'),
]

db = SessionLocal()
insts_by_slug = {i.slug: i for i in db.execute(select(Institution)).scalars().all()}
existing_sha256 = {d.sha256 for d in db.execute(select(SourceDocument)).scalars().all()}
db.close()

results = []
n_ok = 0
n_errors = 0

for fname, slug, year, forced_type in ROUTING:
    fpath = source_dir / fname
    if not fpath.exists():
        print(f"  ERROR {fname}: not found at {fpath}")
        n_errors += 1
        results.append({'file': fname, 'ok': False, 'status': 'FILE_MISSING'})
        continue

    inst = insts_by_slug.get(slug)
    if inst is None:
        print(f"  ERROR {fname}: slug {slug!r} not in DB")
        n_errors += 1
        results.append({'file': fname, 'ok': False, 'status': f'SLUG_MISSING: {slug}'})
        continue

    body = fpath.read_bytes()
    sha = hashlib.sha256(body).hexdigest()

    if sha in existing_sha256:
        print(f"  SKIP {fname}: sha256 already in source_documents")
        results.append({'file': fname, 'ok': True, 'status': 'already_in_db'})
        continue

    # Validate
    val = validate_pdf(body, source_filename=fname, expected_year=year)
    if not val.ok:
        print(f"  REJECT {fname}: {val.reason}")
        n_errors += 1
        results.append({'file': fname, 'ok': False, 'status': f'REJECTED: {val.reason}'})
        continue

    classifier_type = val.report_type
    r2_key = f"{slug}/{year}_{forced_type}_{sha[:8]}.pdf"

    # Upload to R2
    try:
        client.put_object(Bucket=cfg.bucket, Key=r2_key, Body=body, ContentType='application/pdf')
    except Exception as e:
        print(f"  UPLOAD_ERROR {fname}: {e}")
        n_errors += 1
        results.append({'file': fname, 'ok': False, 'status': f'UPLOAD_ERROR: {e}'})
        continue

    # sha256 round-trip
    try:
        obj = client.get_object(Bucket=cfg.bucket, Key=r2_key)
        r2_sha = hashlib.sha256(obj['Body'].read()).hexdigest()
    except Exception as e:
        print(f"  ROUNDTRIP_ERROR {fname}: {e}")
        n_errors += 1
        results.append({'file': fname, 'ok': False, 'status': f'ROUNDTRIP_ERROR: {e}'})
        continue

    if r2_sha != sha:
        print(f"  ROUNDTRIP_MISMATCH {fname}: r2={r2_sha[:16]} local={sha[:16]}")
        n_errors += 1
        results.append({'file': fname, 'ok': False, 'status': 'ROUNDTRIP_MISMATCH'})
        continue

    # Manifest
    note = f'researcher-confirmed {forced_type} 2026-10-08; classifier_type={classifier_type}'
    if classifier_type not in ('annual', 'integrated'):
        note += f' (classifier disagreed)'
    manifest_row = {
        'source': 'manual', 'institution_slug': slug, 'fiscal_year': year,
        'source_url': f'manual:{fname}', 'final_url': None, 'http_status': None,
        'retrieved_at': datetime.now(UTC).isoformat(timespec='seconds'),
        'sha256': sha, 'bytes': val.byte_count, 'content_type': 'application/pdf',
        'file_path': r2_key, 'report_type': forced_type, 'page_count': val.page_count,
        'includes_financial_statements': val.includes_financial_statements,
        'review_status': 'auto_ok',
        'note': note,
        'written_at': datetime.now(UTC).isoformat(timespec='seconds'),
    }
    with MANIFEST_PATH.open('a', encoding='utf-8') as fh:
        fh.write(json.dumps(manifest_row, ensure_ascii=False) + '\n')

    # DB record
    review_note = note
    if val.reason:
        review_note += f'; validator: {val.reason}'

    db2 = SessionLocal()
    doc = SourceDocument(
        institution_id=inst.id,
        fiscal_year=year,
        report_type=ReportType(forced_type),
        source=SourceType.manual,
        source_url=f'manual:{fname}',
        final_url=None,
        http_status=None,
        retrieved_at=datetime.now(UTC),
        sha256=sha,
        bytes=val.byte_count,
        content_type='application/pdf',
        page_count=val.page_count,
        includes_financial_statements=val.includes_financial_statements,
        file_path=r2_key,
        review_status=ReviewStatus.auto_ok,
        review_note=review_note,
    )
    db2.add(doc)
    db2.commit()
    new_id = doc.id
    db2.close()

    n_ok += 1
    print(f"  OK {fname} -> {slug} FY{year} type={classifier_type}->{forced_type} pages={val.page_count} id={new_id}")
    results.append({'file': fname, 'slug': slug, 'year': year, 'id': new_id,
                    'r2_key': r2_key, 'pages': val.page_count,
                    'classifier': classifier_type, 'final': forced_type, 'ok': True})

print(f"\n=== SABIC ROUTING SUMMARY ===")
print(f"OK: {n_ok}  Errors: {n_errors}")
for r in results:
    if not r['ok']:
        print(f"  ERROR {r['file']}: {r['status']}")
