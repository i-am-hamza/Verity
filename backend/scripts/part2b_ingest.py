"""Part 2b+2c: Ingest 36 full annual reports; supersede old docs for same cells.

Files are in E:\9. Verity\storage\reports\ with researcher-given names.
Mapping (actual filename → slug, year) is hardcoded below.

Rules:
- R2 upload with sha256 round-trip; STOP if anything lands on local disk.
- Force report_type=annual (researcher-confirmed).
- Flag files under 30 pages or under half company median page count.
- After ingesting each new file, mark ALL other source_documents for the
  same (institution, fiscal_year) as superseded_by_id = new_doc.id.
"""
import sys, io, hashlib, json, statistics
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

SOURCE_DIR = Path(r"E:\9. Verity\storage\reports")

# Explicit mapping: actual filename → (slug, year)
# Flag: Bank_Albilad_Financial_Statements_2021_English.pdf — name says
# "Financial Statements" but researcher's spreadsheet row says this is the
# full annual report for Bank Albilad FY2021. Ingesting as annual per
# researcher instruction; classifier type will be recorded.
FILE_ROUTING = {
    'ADCB_Annual_Report_2022_English.pdf':                          ('abu-dhabi-commercial-bank',                             2022),
    'ADCB_Annual_Report_2023_English.pdf':                          ('abu-dhabi-commercial-bank',                             2023),
    'Air_Arabia_PJSC_Annual_Report_2020_English.pdf':               ('air-arabia-pjsc',                                       2020),
    'Air_Arabia_PJSC_Annual_Report_2021_English.pdf':               ('air-arabia-pjsc',                                       2021),
    'Bank_Albilad_Annual_Report_2023_English.pdf':                  ('bank-albilad',                                          2023),
    'Bank_Albilad_Financial_Statements_2021_English.pdf':           ('bank-albilad',                                          2021),
    'Bank_Dhofar_Annual_Report_2021_English.pdf':                   ('bank-dhofar',                                           2021),
    'Bank_Dhofar_Annual_Report_2022_English.pdf':                   ('bank-dhofar',                                           2022),
    'Bank_Dhofar_Annual_Report_2023_English.pdf':                   ('bank-dhofar',                                           2023),
    'Bank_Dhofar_Annual_Report_2024_English.pdf':                   ('bank-dhofar',                                           2024),
    'Bank_Muscat_Annual_Report_2021_English.pdf':                   ('bank-muscat-bkmb',                                      2021),
    'Bank_Muscat_Annual_Report_2022_English.pdf':                   ('bank-muscat-bkmb',                                      2022),
    'Bank_Muscat_Annual_Report_2024_English.pdf':                   ('bank-muscat-bkmb',                                      2024),
    'Boubyan_Bank_Annual_Report_2021_English.pdf':                  ('boubyan-bank',                                          2021),
    'Boubyan_Bank_Annual_Report_2022_English.pdf':                  ('boubyan-bank',                                          2022),
    'Boubyan_Bank_Annual_Report_2023_English.pdf':                  ('boubyan-bank',                                          2023),
    'Boubyan_Bank_Annual_Report_2024_English.pdf':                  ('boubyan-bank',                                          2024),
    'Boubyan_Bank_Annual_Report_2025_English.pdf':                  ('boubyan-bank',                                          2025),
    'DIB_Annual_Report_2024_English.pdf':                           ('dubai-islamic-bank',                                    2024),
    'Dubai_Investments_PJSC_Annual_Report_2021_English.pdf':        ('dubai-investment',                                      2021),
    'Dubai_Investments_PJSC_Annual_Report_2024_English.pdf':        ('dubai-investment',                                      2024),
    'Emirates_NBD_Annual_Report_2022_English.pdf':                  ('emirates-nbd-pjsc',                                     2022),
    'KFH_Annual_Report_2021_English.pdf':                           ('kuwait-finance-house',                                  2021),
    'OMINVEST_Annual_Report_2025_English.pdf':                      ('oman-international-development-and-investment-company', 2025),
    'QNB_Annual_Report_2021_English.pdf':                           ('qnb-qatar-national-bank',                               2021),
    'RAKBANK_Annual_Integrated_Report_2023_English.pdf':            ('the-national-bank-of-ras-al-khaimah',                   2023),
    'RAKBANK_Annual_Report_2022_English.pdf':                       ('the-national-bank-of-ras-al-khaimah',                   2022),
    'Riyad_Bank_Annual_Report_2021_English.pdf':                    ('riyad-bank',                                            2021),
    'Riyad_Bank_Annual_Report_2023_English.pdf':                    ('riyad-bank',                                            2023),
    'Riyad_Bank_Annual_Report_2024_English.pdf':                    ('riyad-bank',                                            2024),
    'Riyad_Bank_Annual_Report_2025_English.pdf':                    ('riyad-bank',                                            2025),
    'SIIG_Annual_Report_2021_English.pdf':                          ('saudi-industrial-investment-group',                     2021),
    'SNB-Annual Repor-2023-EN.pdf':                                 ('the-saudi-national-bank',                               2023),
    'Salam_International_Investment_Annual_Report_2020.pdf':        ('salam-international-investment',                        2020),
    'Salam_International_Investment_Annual_Report_2021.pdf':        ('salam-international-investment',                        2021),
    'Saudi_National_Bank_Annual_Report_2021_English.pdf':           ('the-saudi-national-bank',                               2021),
}

db = SessionLocal()
inst_by_slug = {i.slug: i for i in db.execute(select(Institution)).scalars().all()}
existing_sha256 = {d.sha256: d for d in db.execute(select(SourceDocument)).scalars().all()}

# Pre-compute per-company median page count for anomaly detection
all_docs = list(existing_sha256.values())
company_pages: dict[int, list[int]] = {}
for d in all_docs:
    if d.page_count and d.page_count > 0:
        company_pages.setdefault(d.institution_id, []).append(d.page_count)
db.close()

# Build doc_map fresh (includes docs just added by part2a)
db2 = SessionLocal()
doc_map: dict[tuple[int, int], list[SourceDocument]] = {}
for d in db2.execute(select(SourceDocument)).scalars().all():
    doc_map.setdefault((d.institution_id, d.fiscal_year), []).append(d)
db2.close()

flags = []
results = []
n_ok = n_errors = n_superseded = 0

for fname, (slug, year) in sorted(FILE_ROUTING.items(), key=lambda x: x[0]):
    fpath = SOURCE_DIR / fname
    if not fpath.exists():
        print(f"  ERROR: file not found: {fpath}")
        n_errors += 1
        results.append({'file': fname, 'ok': False, 'status': 'FILE_MISSING'})
        continue

    inst = inst_by_slug.get(slug)
    if inst is None:
        print(f"  ERROR: slug {slug!r} not in DB")
        n_errors += 1
        continue

    body = fpath.read_bytes()
    sha = hashlib.sha256(body).hexdigest()

    # sha256 dedup
    if sha in existing_sha256:
        existing = existing_sha256[sha]
        print(f"  SKIP (already in DB id={existing.id}): {fname}")
        results.append({'file': fname, 'ok': True, 'status': f'already_in_db id={existing.id}'})
        continue

    val = validate_pdf(body, source_filename=fname, expected_year=year)
    if not val.ok:
        print(f"  REJECT {fname}: {val.reason}")
        n_errors += 1
        results.append({'file': fname, 'ok': False, 'status': f'REJECTED: {val.reason}'})
        continue

    classifier_type = val.report_type
    pages = val.page_count or 0

    # Page-count flags
    if pages < 30:
        flags.append(f"FLAG short: {fname} → {slug} FY{year} pages={pages} (<30)")
    med_pages = statistics.median(company_pages.get(inst.id, [pages])) if company_pages.get(inst.id) else pages
    if med_pages >= 40 and pages < med_pages / 2:
        flags.append(f"FLAG below-half-median: {fname} → {slug} FY{year} pages={pages} median={med_pages:.0f}")

    # Filename naming flag
    if 'financial_statements' in fname.lower() or 'financial statements' in fname.lower():
        flags.append(f"FLAG filename: {fname} — name says 'Financial Statements'; "
                     f"researcher confirmed annual; classifier_type={classifier_type}; "
                     f"ingesting as annual per instruction")

    final_type = 'annual'
    r2_key = f"{slug}/{year}_{final_type}_{sha[:8]}.pdf"

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
        print(f"  ROUNDTRIP_MISMATCH {fname}")
        n_errors += 1
        results.append({'file': fname, 'ok': False, 'status': 'ROUNDTRIP_MISMATCH'})
        continue

    # Manifest
    note = (f"researcher-confirmed annual 2026-10-09; classifier_type={classifier_type}")
    if classifier_type not in ('annual', 'integrated'):
        note += ' (classifier disagreed)'
    manifest_row = {
        'source': 'manual', 'institution_slug': slug, 'fiscal_year': year,
        'source_url': f'manual:{fname}', 'final_url': None, 'http_status': None,
        'retrieved_at': datetime.now(UTC).isoformat(timespec='seconds'),
        'sha256': sha, 'bytes': val.byte_count, 'content_type': 'application/pdf',
        'file_path': r2_key, 'report_type': final_type, 'page_count': pages,
        'includes_financial_statements': val.includes_financial_statements,
        'review_status': 'auto_ok', 'note': note,
        'written_at': datetime.now(UTC).isoformat(timespec='seconds'),
    }
    with MANIFEST_PATH.open('a', encoding='utf-8') as fh:
        fh.write(json.dumps(manifest_row, ensure_ascii=False) + '\n')

    # DB insert
    review_note = note
    if val.reason:
        review_note += f'; validator: {val.reason}'

    db3 = SessionLocal()
    new_doc = SourceDocument(
        institution_id=inst.id,
        fiscal_year=year,
        report_type=ReportType.annual,
        source=SourceType.manual,
        source_url=f'manual:{fname}',
        final_url=None,
        http_status=None,
        retrieved_at=datetime.now(UTC),
        sha256=sha,
        bytes=val.byte_count,
        content_type='application/pdf',
        page_count=pages,
        includes_financial_statements=val.includes_financial_statements,
        file_path=r2_key,
        review_status=ReviewStatus.auto_ok,
        review_note=review_note,
    )
    db3.add(new_doc)
    db3.flush()  # get new_doc.id before supersession loop

    # Part 2c: supersede all other docs for this (inst, FY)
    old_docs = doc_map.get((inst.id, year), [])
    cell_superseded = 0
    for old in old_docs:
        if old.superseded_by_id is None:
            old_fresh = db3.get(SourceDocument, old.id)
            if old_fresh and old_fresh.superseded_by_id is None:
                old_fresh.superseded_by_id = new_doc.id
                db3.add(old_fresh)
                cell_superseded += 1
                n_superseded += 1

    db3.commit()
    new_id = new_doc.id
    db3.close()

    n_ok += 1
    print(f"  OK [{n_ok:02d}] {fname[:60]} → {slug} FY{year} "
          f"pages={pages} classifier={classifier_type} id={new_id} "
          f"superseded={cell_superseded}")
    results.append({'file': fname, 'slug': slug, 'year': year, 'id': new_id,
                    'pages': pages, 'classifier': classifier_type, 'ok': True,
                    'superseded': cell_superseded})

print(f"\n=== PART 2b+2c SUMMARY ===")
print(f"Uploaded + verified: {n_ok}  Errors: {n_errors}  Old docs superseded: {n_superseded}")

if flags:
    print(f"\n=== FLAGS ({len(flags)}) ===")
    for f in flags:
        print(f"  {f}")
else:
    print("\nNo flags.")

if n_errors:
    print("\nERRORS:")
    for r in results:
        if not r.get('ok'):
            print(f"  {r['file']}: {r['status']}")
