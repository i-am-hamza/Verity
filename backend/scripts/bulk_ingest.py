"""Bulk ingest all new annual reports from storage/reports/ source folder.

Decision B: All files confirmed annual/integrated by researcher 2026-10-08.
Force report_type=annual for DB and R2 key. Record classifier's label where
it disagrees. STOP if any write lands on local disk.
Excludes: SABIC 9 files (on HOLD) and files already in source_documents (sha256 dedup).
"""
import sys, io, hashlib, re, logging
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from datetime import UTC, datetime
from pathlib import Path
from dotenv import load_dotenv
load_dotenv('.env')

from app.crawler import register_all_mappers
register_all_mappers()

from app.database import SessionLocal
from app.models.provenance import SourceDocument, ReportType, ReviewStatus, SourceType
from app.models.institution import Institution
from app.crawler.validate import validate_pdf
from app.crawler.manifest import save_pdf, load_existing_sha256
from app.services.storage import _r2_client, R2Settings, r2_enabled
from sqlalchemy import select

logging.basicConfig(level=logging.WARNING)

# ---- Safety: abort if R2 is not configured --------------------------------
assert r2_enabled(), "STOP: R2 not enabled — writes would go to local disk"
cfg = R2Settings()
client = _r2_client()
print(f"R2 enabled: bucket={cfg.bucket}")

# ---- Build DB lookups -----------------------------------------------------
db = SessionLocal()
insts_by_slug = {i.slug: i for i in db.execute(select(Institution)).scalars().all()}
existing_sha256_db = {d.sha256: d for d in db.execute(select(SourceDocument)).scalars().all()}
db.close()

# ---- SABIC files to skip (on HOLD) -----------------------------------------
SABIC_HOLD = {
    'SABIC Annual Report 2020.pdf',
    'SABIC Annual Report 2021.pdf',
    'SABIC Annual Report 2022.pdf',
    'SABIC Annual Report 2023.pdf',
    'SABIC Annual Report 2024.pdf',
    'SABIC Annual Report 2025.pdf',
    'SABIC-Integrated-Annual-Report-2023.pdf',
    'SABIC-Integrated-Annual-Report-2024.pdf',
    'SABIC_Annual_Report_2021.pdf',
}

# ---- Name → slug mapping -----------------------------------------------
NAME_TO_SLUG = {
    "abdullah al othaim": "abdullah-al-othaim-markets",
    "abu dhabi commercial bank": "abu-dhabi-commercial-bank",
    "abu dhabi national energy": "abu-dhabi-national-energy-company",
    "abu dhabi national oil": "abu-dhabi-national-oil-company-for-distribution",
    "advanced petrochemical": "advanced-petrochemical",
    "air arabia": "air-arabia-pjsc",
    "al rajhi": "al-rajhi-bank",
    "aldar properties": "aldar-properties-pjsc",
    "alinma bank": "alinma-bank",
    "almarai": "almarai",
    "aluminium bahrain": "aluminium-bahrain-alba",
    "bahrain telecommunications": "bahrain-telecommunications-beyon",
    "baladna": "baladna",
    "bank al bilad": "bank-albilad",
    "bank albilad": "bank-albilad",
    "bank dhofar": "bank-dhofar",
    "bank muscat": "bank-muscat-bkmb",
    "barwa real estate": "barwa-real-estate",
    "boubyan bank": "boubyan-bank",
    "dar al arkan": "dar-al-arkan-real-estate-development-company",
    "dubai investments": "dubai-investment",
    "dubai islamic bank": "dubai-islamic-bank",
    "emirates nbd": "emirates-nbd-pjsc",
    "emirates telecom": "emirates-telecom-etisalat-group",
    "etihad etisalat": "etihad-etisalat-mobily",
    "first abu dhabi bank": "first-abu-dhabi-bank",
    "gulf hotels group": "gulf-hotels-group",
    "gulf international services": "gulf-international-services",
    "industries qatar": "industries-qatar",
    "jarir marketing": "jarir-marketing-co",
    "jazeera airways": "jazeera-airways",
    "jazeera steel": "jazeera-steel",
    "kuwait finance house": "kuwait-finance-house",
    "kuwait telecommunications": "kuwait-telecommunications-company",
    "maa_den": "maaden",
    "ma_aden": "maaden",
    "mobile telecommunications co annual": "mobile-telecommunications-co-saudi-arabia-zain",
    "mouwasat medical": "mouwasat-medical-services-company",
    "national bank of bahrain": "national-bank-of-bahrain",
    "national bank of kuwait": "national-bank-of-kuwait",
    "national industrialization": "national-industrialization-co",
    "oman international development": "oman-international-development-and-investment-company",
    "oman telecommunications": "oman-telecommunications-company-otel",
    "ooredoo": "ooredoo-q-p-s-c",
    "qatar fuel": "qatar-fuel-company-woqod",
    "qatar gas transport": "qatar-gas-transport-co-nakilat",
    "qnb": "qnb-qatar-national-bank",
    "rabigh refining": "rabigh-refining-petrochemical-co",
    "riyadh bank": "riyad-bank",
    "riyad bank": "riyad-bank",
    "sahara international petrochemical": "sahara-international-petrochemical-co",
    "salam international": "salam-international-investment",
    "saudi airlines catering": "saudi-airlines-catering-company-catrion",
    "saudi aramco": "saudi-aramco",
    "saudi cement": "saudi-cement",
    "saudi industrial investment": "saudi-industrial-investment-group",
    "saudi national bank": "the-saudi-national-bank",
    "savola": "savola-group",
    "sohar international": "sohar-international-bank",
    "tamdeen real estate": "tamdeen-real-estate-company",
    "the national bank of ras al khaimah": "the-national-bank-of-ras-al-khaimah",
    "yanbu cement": "yanbu-cement-company",
    "yanbu national petrochemical": "yanbu-national-petrochemical",
    "zain - mobile": "zain-mobile-telecommunications-company",
    "maaden annual": "maaden",
    "ncb": "the-saudi-national-bank",
}
FILENAME_OVERRIDES = {
    "NCB (SNB) -Annual-Report-2020.pdf": ("the-saudi-national-bank", 2020),
    "saudi-aramco-ara-2020-english.pdf": ("saudi-aramco", 2020),
    "saudi-aramco-ara-2021-english.pdf": ("saudi-aramco", 2021),
    "saudi-aramco-ara-2022-english.pdf": ("saudi-aramco", 2022),
    "saudi-aramco-ara-2024-english.pdf": ("saudi-aramco", 2024),
    "saudi-aramco-ara-2025-english.pdf": ("saudi-aramco", 2025),
    "Maa_den Annual Report 2020.pdf": ("maaden", 2020),
    "ma_aden-annual-report-2021.pdf": ("maaden", 2021),
    "STC Annual-Report 2020.pdf": ("saudi-telecom-company", 2020),
    "STC-Annual-Report-2021.pdf": ("saudi-telecom-company", 2021),
    "stc-annual-report-2022.pdf": ("saudi-telecom-company", 2022),
    "stc-annual-report-2023.pdf": ("saudi-telecom-company", 2023),
    "stc_Annual Report-2024.pdf": ("saudi-telecom-company", 2024),
    "Stc-Anuual-Report-2025.pdf": ("saudi-telecom-company", 2025),
    "Saudi National Bank 2022.pdf": ("the-saudi-national-bank", 2022),
    "Mobile Telecommunications Co Annual Report 2020.pdf": ("mobile-telecommunications-co-saudi-arabia-zain", 2020),
    "Mobile Telecommunications Co Annual Report 2021.pdf": ("mobile-telecommunications-co-saudi-arabia-zain", 2021),
    "Mobile Telecommunications Co Annual Report 2022.pdf": ("mobile-telecommunications-co-saudi-arabia-zain", 2022),
    "Mobile Telecommunications Co Annual Report 2023.pdf": ("mobile-telecommunications-co-saudi-arabia-zain", 2023),
    "Mobile Telecommunications Co Annual Report 2024.pdf": ("mobile-telecommunications-co-saudi-arabia-zain", 2024),
    "Mobile Telecommunications Co Annual Report 2025.pdf": ("mobile-telecommunications-co-saudi-arabia-zain", 2025),
    "Zain - Mobile Telecommunications Co - Annual Report 2020.pdf": ("zain-mobile-telecommunications-company", 2020),
    "Zain - Mobile Telecommunications Co - Annual Report 2021.pdf": ("zain-mobile-telecommunications-company", 2021),
    "Zain - Mobile Telecommunications Co - Annual Report 2022.pdf": ("zain-mobile-telecommunications-company", 2022),
    "Zain - Mobile Telecommunications Co - Annual Report 2023.pdf": ("zain-mobile-telecommunications-company", 2023),
    "Zain - Mobile Telecommunications Co - Annual Report 2025.pdf": ("zain-mobile-telecommunications-company", 2025),
}


def guess_slug_year(fname):
    if fname in FILENAME_OVERRIDES:
        return FILENAME_OVERRIDES[fname]
    fname_lower = fname.lower()
    slug = None
    for key, s in NAME_TO_SLUG.items():
        if key.lower() in fname_lower:
            slug = s
            break
    years = re.findall(r"\b(202[0-5])\b", fname)
    year = int(years[0]) if years else None
    return slug, year


# ---- Scan source folder -----------------------------------------------
source_dir = Path(r"E:\9. Verity\storage\reports")
all_pdfs = sorted(source_dir.glob("*.pdf"))
print(f"\nTotal PDFs in source folder: {len(all_pdfs)}")

# ---- Pre-compute sha256 for all files -----------------------------------
print("Computing sha256 for all source files...")
file_info = []
for pdf in all_pdfs:
    if pdf.name in SABIC_HOLD:
        file_info.append({'path': pdf, 'name': pdf.name, 'skip': 'SABIC_HOLD'})
        continue
    slug, year = guess_slug_year(pdf.name)
    if not slug or not year:
        file_info.append({'path': pdf, 'name': pdf.name, 'skip': f'NO_MATCH slug={slug} year={year}'})
        continue
    body = pdf.read_bytes()
    sha = hashlib.sha256(body).hexdigest()
    in_db = sha in existing_sha256_db
    file_info.append({
        'path': pdf, 'name': pdf.name, 'slug': slug, 'year': year,
        'body': body, 'sha256': sha, 'in_db': in_db, 'skip': None
    })

to_ingest = [f for f in file_info if not f.get('skip') and not f.get('in_db')]
skipped_hold = [f for f in file_info if f.get('skip') == 'SABIC_HOLD']
skipped_dedup = [f for f in file_info if not f.get('skip') and f.get('in_db')]
skipped_nomatch = [f for f in file_info if f.get('skip') and f.get('skip') != 'SABIC_HOLD']

print(f"Files to ingest: {len(to_ingest)}")
print(f"Skipped (SABIC HOLD): {len(skipped_hold)}")
print(f"Skipped (already in DB): {len(skipped_dedup)}")
print(f"Skipped (no match): {len(skipped_nomatch)}")

# ---- Ingest each file -----------------------------------------------
results = []
classifier_disagreements = []
n_uploaded = 0
n_deduped = 0
n_errors = 0

for item in to_ingest:
    fname = item['name']
    slug = item['slug']
    year = item['year']
    body = item['body']
    sha = item['sha256']

    inst = insts_by_slug.get(slug)
    if inst is None:
        results.append({'file': fname, 'status': f'ERROR: slug {slug!r} not in DB', 'ok': False})
        n_errors += 1
        print(f"  ERROR {fname}: slug {slug!r} not in DB")
        continue

    # Validate
    val = validate_pdf(body, source_filename=fname, expected_year=year)
    if not val.ok:
        results.append({'file': fname, 'status': f'REJECTED: {val.reason}', 'ok': False})
        n_errors += 1
        print(f"  REJECT {fname}: {val.reason}")
        continue

    classifier_type = val.report_type

    # Decision B: force annual type (record disagreement)
    final_type = 'annual'
    if classifier_type not in ('annual', 'integrated'):
        classifier_disagreements.append({
            'file': fname, 'slug': slug, 'year': year,
            'classifier': classifier_type, 'forced': final_type
        })

    # Build R2 key
    short = sha[:8]
    r2_key = f"{slug}/{year}_{final_type}_{short}.pdf"

    # Check if sha256 already in manifest (would indicate duplicate that somehow
    # wasn't in DB — shouldn't happen normally)
    manifest_existing = load_existing_sha256()
    if sha in manifest_existing:
        results.append({'file': fname, 'slug': slug, 'year': year,
                        'status': f'deduped (manifest): key={manifest_existing[sha]}', 'ok': True})
        n_deduped += 1
        continue

    # Upload to R2
    try:
        client.put_object(
            Bucket=cfg.bucket, Key=r2_key, Body=body,
            ContentType='application/pdf'
        )
    except Exception as e:
        results.append({'file': fname, 'status': f'R2_UPLOAD_ERROR: {e}', 'ok': False})
        n_errors += 1
        print(f"  UPLOAD_ERROR {fname}: {e}")
        continue

    # sha256 round-trip
    try:
        obj = client.get_object(Bucket=cfg.bucket, Key=r2_key)
        r2_body = obj['Body'].read()
        r2_sha = hashlib.sha256(r2_body).hexdigest()
    except Exception as e:
        results.append({'file': fname, 'status': f'ROUNDTRIP_ERROR: {e}', 'ok': False})
        n_errors += 1
        print(f"  ROUNDTRIP_ERROR {fname}: {e}")
        continue

    if r2_sha != sha:
        results.append({'file': fname, 'status': f'ROUNDTRIP_MISMATCH r2={r2_sha[:16]} local={sha[:16]}', 'ok': False})
        n_errors += 1
        print(f"  ROUNDTRIP_MISMATCH {fname}")
        continue

    # Append to manifest
    manifest_row = {
        'source': 'manual', 'institution_slug': slug, 'fiscal_year': year,
        'source_url': f'manual:{fname}', 'final_url': None, 'http_status': None,
        'retrieved_at': datetime.now(UTC).isoformat(timespec='seconds'),
        'bytes': val.byte_count, 'content_type': 'application/pdf',
        'report_type': final_type, 'page_count': val.page_count,
        'includes_financial_statements': val.includes_financial_statements,
        'review_status': 'auto_ok' if final_type in ('annual', 'integrated') and val.page_count >= 30 else 'needs_review',
        'note': f'researcher-confirmed annual 2026-10-08; classifier_type={classifier_type}',
    }
    from app.crawler.config import MANIFEST_PATH
    import json
    row = {**manifest_row, 'sha256': sha, 'file_path': r2_key,
           'written_at': datetime.now(UTC).isoformat(timespec='seconds')}
    with MANIFEST_PATH.open('a', encoding='utf-8') as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + '\n')

    # Determine review_status
    review = 'needs_review' if (final_type == 'annual' and val.page_count < 30) else 'auto_ok'

    # Record in DB
    review_note = f'researcher-confirmed annual 2026-10-08'
    if classifier_type not in ('annual', 'integrated'):
        review_note += f'; classifier said {classifier_type!r}'
    if val.reason:
        review_note += f'; validator note: {val.reason}'

    db2 = SessionLocal()
    doc = SourceDocument(
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
        page_count=val.page_count,
        includes_financial_statements=val.includes_financial_statements,
        file_path=r2_key,
        review_status=ReviewStatus(review),
        review_note=review_note,
    )
    db2.add(doc)
    db2.commit()
    new_id = doc.id
    db2.close()

    n_uploaded += 1
    results.append({
        'file': fname, 'slug': slug, 'year': year, 'db_id': new_id,
        'r2_key': r2_key, 'pages': val.page_count,
        'classifier': classifier_type, 'final': final_type,
        'status': 'ingested_verified', 'ok': True
    })
    print(f"  OK [{n_uploaded:03d}] {fname[:55]} -> {slug} FY{year} pages={val.page_count} type={classifier_type}->{final_type} id={new_id}")

# ---- Final report -------------------------------------------------------
print(f"\n=== BULK INGEST SUMMARY ===")
print(f"Total source files: {len(all_pdfs)}")
print(f"Skipped SABIC HOLD: {len(skipped_hold)}")
print(f"Skipped dedup (already in DB): {len(skipped_dedup)}")
print(f"Skipped no-match: {len(skipped_nomatch)}")
print(f"Attempted ingest: {len(to_ingest)}")
print(f"  Uploaded + verified: {n_uploaded}")
print(f"  Deduped (manifest): {n_deduped}")
print(f"  Errors: {n_errors}")

if classifier_disagreements:
    print(f"\n=== CLASSIFIER DISAGREEMENTS ({len(classifier_disagreements)}) ===")
    print(f"(Files where classifier != annual/integrated, overridden to annual per Decision B)")
    for d in classifier_disagreements:
        print(f"  {d['file'][:65]:65} {d['slug']:45} FY{d['year']}  classifier={d['classifier']}")
else:
    print("\nNo classifier disagreements — all files classified as annual/integrated.")

if n_errors > 0:
    print(f"\n=== ERRORS ({n_errors}) ===")
    for r in results:
        if not r['ok']:
            print(f"  {r['file']}: {r['status']}")
