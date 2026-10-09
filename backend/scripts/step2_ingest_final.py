"""Step 2 — Upload and register the 390 researcher-verified annual reports.

For each file:
  - validate_pdf for page_count, report_type, includes_financial_statements
  - report_type: integrated if classifier says integrated, else annual
  - review_status: always auto_ok (researcher has verified everything)
  - Upload to R2; sha256 round-trip verify before any DB write
  - Insert new source_document (or update existing row if sha256 already in DB)
  - Write manifest row
  - Flag if text is mostly Arabic (still registers)

STOP if R2 is unavailable or any write lands on local disk.
"""
import sys, io, hashlib, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv('.env')

from datetime import UTC, datetime
from pathlib import Path

import pymupdf

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

SOURCE_ROOT = Path(r"E:\9. Verity\storage\reports")
REVIEW_NOTE = "researcher-verified final set, 2026-10-09"
TARGET_YEARS = {2020, 2021, 2022, 2023, 2024, 2025}
YEAR_RX = re.compile(r'(?<!\d)(202[0-5])(?!\d)')

# ── folder name → institution slug ────────────────────────────────────────────
FOLDER_TO_SLUG: dict[str, str] = {
    # Bahrain
    'Aluminium Bahrain (Alba)':                             'aluminium-bahrain-alba',
    'Bahrain Telecommunications BEYON':                     'bahrain-telecommunications-beyon',
    'Gulf Hotels Group':                                    'gulf-hotels-group',
    'National Bank of Bahrain':                             'national-bank-of-bahrain',
    # Kuwait
    'Boubyan Bank':                                         'boubyan-bank',
    'Jazeera Airways':                                      'jazeera-airways',
    'Kuwait Finance House':                                 'kuwait-finance-house',
    'Kuwait Telecommunications Company':                    'kuwait-telecommunications-company',
    'National Bank of Kuwait':                              'national-bank-of-kuwait',
    'Tamdeen Real Estate Company':                          'tamdeen-real-estate-company',
    'Zain (Mobile Telecommunications Company)':             'zain-mobile-telecommunications-company',
    # Oman
    'Bank Dhofar':                                          'bank-dhofar',
    'Bank Muscat BKMB':                                     'bank-muscat-bkmb',
    'Jazeera Steel':                                        'jazeera-steel',
    'Oman International Development and Investment Company': 'oman-international-development-and-investment-company',
    'Oman Telecommunications Company OTEL':                 'oman-telecommunications-company-otel',
    'Sohar International Bank':                             'sohar-international-bank',
    # Qatar
    'Baladna':                                              'baladna',
    'Barwa Real Estate':                                    'barwa-real-estate',
    'Gulf International Services':                          'gulf-international-services',
    'Industries Qatar':                                     'industries-qatar',
    'Ooredoo Q.P.S.C':                                      'ooredoo-q-p-s-c',
    'Qatar Fuel Company (WOQOD)':                           'qatar-fuel-company-woqod',
    'Qatar Gas Transport Co (Nakilat)':                     'qatar-gas-transport-co-nakilat',
    'Qatar National Bank (QNB)':                            'qnb-qatar-national-bank',
    'Salam International Investment':                       'salam-international-investment',
    # Saudi Arabia
    'Abdullah Al Othaim Markets 4001':                      'abdullah-al-othaim-markets',
    'Advanced Petrochemical 2330':                          'advanced-petrochemical',
    'Al Rajhi Bank 1120':                                   'al-rajhi-bank',
    'Alinma Bank 1150':                                     'alinma-bank',
    'Almarai 2280':                                         'almarai',
    'Bank Albilad 1140':                                    'bank-albilad',
    'Dar Al Arkan Real Estate Development Company 4300':    'dar-al-arkan-real-estate-development-company',
    'Etihad Etisalat (Mobily) 7020':                        'etihad-etisalat-mobily',
    'Jarir Marketing Co 4190':                              'jarir-marketing-co',
    'Maaden 1211':                                          'maaden',
    'Mobile Telecommunications Co. Saudi Arabia (Zain) 7030': 'mobile-telecommunications-co-saudi-arabia-zain',
    'Mouwasat Medical Services Company 4002':               'mouwasat-medical-services-company',
    'National Industrialization Co 2060':                   'national-industrialization-co',
    'Rabigh Refining & Petrochemical Co. 2380':             'rabigh-refining-petrochemical-co',
    'Riyadh Bank 1010':                                     'riyad-bank',
    'SABIC 2010':                                           'sabic',
    'SABIC Agri-Nutrients Company 2020':                    'saudi-arabian-fertilizer-company',
    'Sahara International Petrochemical Co. 2310':          'sahara-international-petrochemical-co',
    'Saudi Airlines Catering Company CATRION 6004':         'saudi-airlines-catering-company-catrion',
    'Saudi Aramco 2222':                                    'saudi-aramco',
    'Saudi Cement 3030':                                    'saudi-cement',
    'Saudi Industrial Investment Group 2250':               'saudi-industrial-investment-group',
    'Saudi Telecom 7010':                                   'saudi-telecom-company',
    'Savola Group 2050':                                    'savola-group',
    'The Saudi National Bank 1180':                         'the-saudi-national-bank',
    'Yanbu Cement Company 3060':                            'yanbu-cement-company',
    'Yanbu National Petrochemical 2290':                    'yanbu-national-petrochemical',
    # UAE
    'Abu Dhabi Commercial Bank':                            'abu-dhabi-commercial-bank',
    'Abu Dhabi National Energy Company':                    'abu-dhabi-national-energy-company',
    'Abu Dhabi National Oil Company For Distribution':      'abu-dhabi-national-oil-company-for-distribution',
    'Air Arabia PJSC':                                      'air-arabia-pjsc',
    'Aldar Properties PJSC':                                'aldar-properties-pjsc',
    'Dubai Investments PJSC':                               'dubai-investment',
    'Dubai Islamic Bank':                                   'dubai-islamic-bank',
    'Emaar Properties':                                     'emaar-properties',
    'Emirates NBD PJSC':                                    'emirates-nbd-pjsc',
    'Emirates Telecom (Etisalat Group)':                    'emirates-telecom-etisalat-group',
    'First Abu Dhabi Bank':                                 'first-abu-dhabi-bank',
    'The National Bank of Ras Al Khaimah':                  'the-national-bank-of-ras-al-khaimah',
}

# ── load institutions ─────────────────────────────────────────────────────────
db = SessionLocal()
inst_by_slug = {i.slug: i for i in db.execute(select(Institution)).scalars().all()}
existing_by_sha256 = {d.sha256: d for d in db.execute(select(SourceDocument)).scalars().all()}
db.close()

# Verify all slugs map to real institutions
unmatched = [s for s in FOLDER_TO_SLUG.values() if s not in inst_by_slug]
if unmatched:
    print(f"STOP: slugs not in DB: {unmatched}")
    sys.exit(1)
assert len(FOLDER_TO_SLUG) == 65, f"Expected 65 entries, got {len(FOLDER_TO_SLUG)}"

# ── build work list ───────────────────────────────────────────────────────────
all_pdfs = sorted(SOURCE_ROOT.rglob("*.pdf"))
work: list[tuple[Path, str, int]] = []  # (path, slug, year)

for p in all_pdfs:
    folder = p.parent.name
    slug = FOLDER_TO_SLUG.get(folder)
    if not slug:
        print(f"STOP: unmapped folder: {folder}")
        sys.exit(1)
    m = YEAR_RX.search(p.name)
    if not m:
        print(f"STOP: no year in filename: {p.name}")
        sys.exit(1)
    work.append((p, slug, int(m.group(1))))

assert len(work) == 390, f"Expected 390 work items, got {len(work)}"
work.sort(key=lambda x: (x[1], x[2]))  # sort by slug, year


def _arabic_ratio(body: bytes) -> float:
    """Return fraction of text chars that are Arabic (U+0600–U+06FF)."""
    try:
        pdf = pymupdf.open(stream=body, filetype="pdf")
        text = ""
        for i in range(min(10, pdf.page_count)):
            try:
                text += pdf[i].get_text("text") or ""
            except Exception:
                pass
        pdf.close()
    except Exception:
        return 0.0
    if not text.strip():
        return 0.0
    arabic = sum(1 for c in text if '؀' <= c <= 'ۿ')
    latin = sum(1 for c in text if c.isalpha() and c.isascii())
    total = arabic + latin
    return arabic / total if total > 0 else 0.0


# ── upload and register ───────────────────────────────────────────────────────
n_ok = n_errors = n_updated = n_inserted = 0
arabic_flagged: list[str] = []
new_doc_ids: list[int] = []
results: list[dict] = []

print(f"\nProcessing {len(work)} files...\n")

for i, (fpath, slug, year) in enumerate(work, 1):
    inst = inst_by_slug[slug]
    body = fpath.read_bytes()
    sha = hashlib.sha256(body).hexdigest()

    # validate_pdf for type / page count / includes_financial_statements
    val = validate_pdf(body, source_filename=fpath.name, expected_year=year)
    if not val.ok:
        # Shouldn't happen for researcher-verified files; treat as error
        print(f"  [{i:03d}] REJECT {fpath.name}: {val.reason}")
        n_errors += 1
        results.append({'file': fpath.name, 'ok': False, 'reason': val.reason})
        continue

    # Force report_type: integrated only if classifier says so, else annual
    final_type = 'integrated' if val.report_type == 'integrated' else 'annual'
    report_type_enum = ReportType.integrated if final_type == 'integrated' else ReportType.annual

    # Arabic check
    ar_ratio = _arabic_ratio(body)
    if ar_ratio > 0.5:
        arabic_flagged.append(f"{slug} FY{year} ({fpath.name}) arabic_ratio={ar_ratio:.2f}")

    # R2 upload (always upload fresh — old objects will be cleaned in step 4)
    r2_key = f"{slug}/{year}_{final_type}_{sha[:8]}.pdf"
    try:
        client.put_object(Bucket=cfg.bucket, Key=r2_key, Body=body, ContentType='application/pdf')
    except Exception as e:
        print(f"  [{i:03d}] UPLOAD_ERROR {fpath.name}: {e}")
        n_errors += 1
        continue

    # sha256 round-trip
    try:
        obj = client.get_object(Bucket=cfg.bucket, Key=r2_key)
        r2_sha = hashlib.sha256(obj['Body'].read()).hexdigest()
    except Exception as e:
        print(f"  [{i:03d}] ROUNDTRIP_ERROR {fpath.name}: {e}")
        n_errors += 1
        continue

    if r2_sha != sha:
        print(f"  [{i:03d}] ROUNDTRIP_MISMATCH {fpath.name}")
        n_errors += 1
        continue

    # Manifest row
    manifest_row = {
        'source': 'manual',
        'institution_slug': slug,
        'fiscal_year': year,
        'source_url': f'manual:{fpath.name}',
        'final_url': None,
        'http_status': None,
        'retrieved_at': datetime.now(UTC).isoformat(timespec='seconds'),
        'sha256': sha,
        'bytes': val.byte_count,
        'content_type': 'application/pdf',
        'file_path': r2_key,
        'report_type': final_type,
        'page_count': val.page_count,
        'includes_financial_statements': val.includes_financial_statements,
        'review_status': 'auto_ok',
        'note': REVIEW_NOTE,
        'written_at': datetime.now(UTC).isoformat(timespec='seconds'),
    }
    with MANIFEST_PATH.open('a', encoding='utf-8') as fh:
        fh.write(json.dumps(manifest_row, ensure_ascii=False) + '\n')

    # DB write: insert new OR update existing if sha256 collision
    db3 = SessionLocal()
    existing = db3.execute(
        select(SourceDocument).where(SourceDocument.sha256 == sha)
    ).scalar_one_or_none()

    if existing is not None:
        # Update existing record to reflect new verified set
        existing.institution_id = inst.id
        existing.fiscal_year = year
        existing.report_type = report_type_enum
        existing.review_status = ReviewStatus.auto_ok
        existing.review_note = REVIEW_NOTE
        existing.file_path = r2_key
        existing.page_count = val.page_count
        existing.includes_financial_statements = val.includes_financial_statements
        existing.superseded_by_id = None
        existing.source = SourceType.manual
        existing.source_url = f'manual:{fpath.name}'
        db3.add(existing)
        db3.commit()
        doc_id = existing.id
        n_updated += 1
        action = 'UPDATED'
    else:
        new_doc = SourceDocument(
            institution_id=inst.id,
            fiscal_year=year,
            report_type=report_type_enum,
            source=SourceType.manual,
            source_url=f'manual:{fpath.name}',
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
            review_note=REVIEW_NOTE,
        )
        db3.add(new_doc)
        db3.commit()
        doc_id = new_doc.id
        n_inserted += 1
        action = 'INSERTED'

    new_doc_ids.append(doc_id)
    db3.close()

    n_ok += 1
    ar_note = f" [ARABIC {ar_ratio:.0%}]" if ar_ratio > 0.5 else ""
    if i % 30 == 0 or action == 'UPDATED':
        print(f"  [{i:03d}] {action} {slug} FY{year} pages={val.page_count} "
              f"type={final_type} id={doc_id}{ar_note}")

    results.append({'slug': slug, 'year': year, 'id': doc_id, 'pages': val.page_count,
                    'type': final_type, 'ok': True, 'action': action})

print(f"\n=== STEP 2 SUMMARY ===")
print(f"OK: {n_ok}  Inserted: {n_inserted}  Updated: {n_updated}  Errors: {n_errors}")
print(f"New doc IDs range: {min(new_doc_ids) if new_doc_ids else '?'} – {max(new_doc_ids) if new_doc_ids else '?'}")

if arabic_flagged:
    print(f"\n=== ARABIC-DOMINANT DOCUMENTS ({len(arabic_flagged)}) ===")
    for a in arabic_flagged:
        print(f"  {a}")
else:
    print("\nNo Arabic-dominant documents.")

if n_errors:
    print(f"\nERRORS:")
    for r in results:
        if not r.get('ok'):
            print(f"  {r['file']}: {r.get('reason', 'unknown')}")
    sys.exit(1)

# Write new_doc_ids to a temp file for use by verification and deletion steps
ids_path = Path(__file__).parent / '_step2_new_doc_ids.json'
ids_path.write_text(json.dumps({'ids': new_doc_ids}), encoding='utf-8')
print(f"\nNew doc IDs saved to {ids_path} ({len(new_doc_ids)} ids)")
print("Step 2 complete. Proceed to step 3 verification.")
