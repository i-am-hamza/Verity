"""Part 2c verification: confirm each of the 390 company-years has exactly
one eligible document (type in annual/integrated, review_status=auto_ok,
superseded_by_id IS NULL). Also run updated usability matrix.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv('.env')

from app.crawler import register_all_mappers
register_all_mappers()
from app.database import SessionLocal
from app.models.provenance import SourceDocument, ReviewStatus
from app.models.institution import Institution
from sqlalchemy import select

TARGET_YEARS = [2020, 2021, 2022, 2023, 2024, 2025]
ANNUAL_TYPES = {'annual', 'integrated'}

db = SessionLocal()
institutions = sorted(
    db.execute(select(Institution).where(Institution.active == True)).scalars().all(),
    key=lambda i: i.slug
)
all_docs = db.execute(select(SourceDocument)).scalars().all()
db.close()

doc_map: dict[tuple[int, int], list[SourceDocument]] = {}
for d in all_docs:
    doc_map.setdefault((d.institution_id, d.fiscal_year), []).append(d)


def best_doc(doc_list):
    annual = [d for d in doc_list if str(d.report_type) in ANNUAL_TYPES]
    pool = annual if annual else doc_list
    return max(pool, key=lambda d: (d.page_count or 0))


def cell_status(doc_list):
    if not doc_list:
        return 'missing', None
    d = best_doc(doc_list)
    pages = d.page_count or 0
    rtype = str(d.report_type)
    if pages < 10:
        return 'truncated', d
    if rtype not in ANNUAL_TYPES:
        return 'wrong_type', d
    if pages < 30:
        return 'short', d
    return 'usable', d


STATUS_ABBR = {'usable': 'OK', 'short': 'SH', 'truncated': 'TR',
               'wrong_type': 'WT', 'missing': '--'}
counts = {s: 0 for s in STATUS_ABBR}
not_usable = []

multi_eligible = []   # (slug, year, eligible_docs) where len > 1
zero_eligible = []    # (slug, year) where no eligible doc

print("=" * 110)
print("UPDATED COVERAGE MATRIX")
print("=" * 110)
hdr = f"{'Company':<52} " + "  ".join(str(y) for y in TARGET_YEARS)
print(hdr)
print("-" * 110)

for inst in institutions:
    cells = []
    for year in TARGET_YEARS:
        doc_list = doc_map.get((inst.id, year), [])
        status, d = cell_status(doc_list)
        counts[status] += 1
        cells.append(STATUS_ABBR[status])
        if status != 'usable':
            fname = (d.file_path or '').split('/')[-1] if d else ''
            not_usable.append({
                'slug': inst.slug, 'year': year, 'status': status,
                'pages': d.page_count if d else 0, 'type': str(d.report_type) if d else '',
                'fname': fname, 'id': d.id if d else None
            })

        # Eligible = auto_ok, annual/integrated type, not superseded
        eligible = [
            x for x in doc_list
            if str(x.review_status) == 'auto_ok'
            and str(x.report_type) in ANNUAL_TYPES
            and x.superseded_by_id is None
        ]
        if len(eligible) == 0:
            zero_eligible.append((inst.slug, year))
        elif len(eligible) > 1:
            multi_eligible.append((inst.slug, year, [(x.id, x.page_count) for x in eligible]))

    print(f"{inst.slug:<52} " + "   ".join(cells))

print("-" * 110)
total = sum(counts.values())
print(f"\nTotals: " + "  ".join(f"{k}={v}" for k, v in counts.items()))
print(f"\n{'='*80}")
print(f"ELIGIBILITY CHECK (auto_ok + annual/integrated + not superseded)")
print(f"{'='*80}")
print(f"Cells with 0 eligible docs: {len(zero_eligible)}")
for s, y in zero_eligible:
    print(f"  {s} FY{y}")
print(f"Cells with >1 eligible docs: {len(multi_eligible)}")
for s, y, ids in multi_eligible:
    print(f"  {s} FY{y}: {ids}")

if not_usable:
    print(f"\n{'='*80}")
    print(f"NON-USABLE CELLS ({len(not_usable)})")
    print(f"{'='*80}")
    for item in sorted(not_usable, key=lambda x: (x['status'], x['slug'], x['year'])):
        print(f"  {item['slug']:<52} FY{item['year']}  {item['status']:<10}  "
              f"pages={item['pages'] or '-':>5}  type={item['type']:<12}  {item['fname'][:45]}")
