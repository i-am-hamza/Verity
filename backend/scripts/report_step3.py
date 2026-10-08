"""Step 3 report: coverage matrix, R2 verification, needs_review, page-count anomalies, missing."""
import sys, io, hashlib, statistics
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv('.env')

from app.crawler import register_all_mappers
register_all_mappers()

from app.database import SessionLocal
from app.models.provenance import SourceDocument, ReviewStatus
from app.models.institution import Institution
from app.services.storage import _r2_client, R2Settings, file_path_to_r2_key
from sqlalchemy import select

TARGET_YEARS = [2020, 2021, 2022, 2023, 2024, 2025]

db = SessionLocal()
institutions = db.execute(
    select(Institution).where(Institution.active == True).order_by(Institution.slug)
).scalars().all()

docs = db.execute(select(SourceDocument)).scalars().all()
db.close()

# Index docs by (institution_id, fiscal_year) — keep all, note duplicates
doc_map = {}  # (inst_id, year) -> list of docs
for d in docs:
    key = (d.institution_id, d.fiscal_year)
    doc_map.setdefault(key, []).append(d)

inst_by_id = {i.id: i for i in institutions}

cfg = R2Settings()
client = _r2_client()

# ---- R2 verification (sample all docs) -----------------------------------
print("Verifying R2 presence for all source_documents...")
r2_ok = 0
r2_missing = 0
r2_missing_list = []
for d in docs:
    key = file_path_to_r2_key(d.file_path)
    try:
        client.head_object(Bucket=cfg.bucket, Key=key)
        r2_ok += 1
    except Exception:
        r2_missing += 1
        inst = inst_by_id.get(d.institution_id)
        slug = inst.slug if inst else f'inst_id={d.institution_id}'
        r2_missing_list.append(f"  id={d.id} {slug} FY{d.fiscal_year}: {key}")

print(f"R2: {r2_ok} present, {r2_missing} missing")
if r2_missing_list:
    print("Missing from R2:")
    for m in r2_missing_list:
        print(m)

# ---- Coverage matrix -------------------------------------------------------
print("\n" + "=" * 100)
print("COVERAGE MATRIX (65 companies × 6 years)")
print("=" * 100)
print(f"{'Company':<50} {'ID':>5}  " + "  ".join(str(y) for y in TARGET_YEARS))
print("-" * 100)

covered = 0
missing = 0
missing_list = []
needs_review_list = []

for inst in sorted(institutions, key=lambda i: i.slug):
    row_cells = []
    for year in TARGET_YEARS:
        cell_docs = doc_map.get((inst.id, year), [])
        if not cell_docs:
            row_cells.append('--')
            missing += 1
            missing_list.append((inst.slug, year))
        else:
            # prefer annual over others
            annual = [d for d in cell_docs if str(d.report_type) == 'annual']
            d = annual[0] if annual else cell_docs[0]
            rs = str(d.review_status)
            if rs == 'needs_review':
                mark = 'NR'
                needs_review_list.append({
                    'slug': inst.slug, 'year': year, 'id': d.id,
                    'pages': d.page_count, 'type': str(d.report_type),
                    'note': d.review_note or ''
                })
            elif rs == 'auto_ok':
                mark = 'OK'
            else:
                mark = rs[:2].upper()
            covered += 1
            row_cells.append(mark)
    print(f"{inst.slug:<50} {inst.id:>5}  " + "   ".join(row_cells))

print("-" * 100)
total_cells = len(institutions) * len(TARGET_YEARS)
print(f"\nTotal cells: {total_cells}  Covered: {covered}  Missing: {missing}")
print(f"Coverage: {covered/total_cells*100:.1f}%")

# ---- Needs review list -------------------------------------------------------
print(f"\n=== NEEDS REVIEW ({len(needs_review_list)}) ===")
for nr in sorted(needs_review_list, key=lambda x: (x['slug'], x['year'])):
    print(f"  {nr['slug']:<50} FY{nr['year']}  id={nr['id']}  pages={nr['pages']}  {nr['note'][:80]}")

# ---- Missing company-years -------------------------------------------------------
print(f"\n=== MISSING COMPANY-YEARS ({len(missing_list)}) ===")
for slug, year in sorted(missing_list):
    print(f"  {slug:<50} FY{year}")

# ---- Page-count anomalies -------------------------------------------------------
print("\n=== PAGE-COUNT ANOMALY ANALYSIS ===")
print("(Files < half of company's median page count, using all docs per company)")
anomalies = []
for inst in institutions:
    inst_docs = [d for d in docs if d.institution_id == inst.id and d.page_count and d.page_count > 0]
    if len(inst_docs) < 2:
        continue
    pages = [d.page_count for d in inst_docs]
    med = statistics.median(pages)
    if med < 40:  # skip if median is very small — anomaly not meaningful
        continue
    for d in inst_docs:
        if d.page_count < med / 2:
            anomalies.append({
                'slug': inst.slug, 'year': d.fiscal_year, 'id': d.id,
                'pages': d.page_count, 'median': med, 'ratio': d.page_count / med,
                'type': str(d.report_type), 'status': str(d.review_status)
            })

anomalies.sort(key=lambda x: (x['slug'], x['year']))
if anomalies:
    print(f"{'Company':<50} {'FY':>4}  {'pages':>6}  {'median':>7}  {'ratio':>6}  status")
    for a in anomalies:
        print(f"  {a['slug']:<50} {a['year']:>4}  {a['pages']:>6}  {a['median']:>7.0f}  {a['ratio']:>6.2f}  {a['status']}")
else:
    print("  No anomalies found.")

# ---- DB summary -------------------------------------------------------
print("\n=== DATABASE SUMMARY ===")
from collections import Counter
type_counts = Counter(str(d.report_type) for d in docs)
status_counts = Counter(str(d.review_status) for d in docs)
print(f"Total source_documents: {len(docs)}")
print(f"By report_type: {dict(type_counts)}")
print(f"By review_status: {dict(status_counts)}")
