"""Coverage matrix: usable / short / truncated / wrong-type / missing per cell.

usable    = annual or integrated, auto_ok, 30+ pages
short     = annual or integrated, <30 pages
truncated = <10 pages (regardless of type or status)
wrong_type = best doc is not annual/integrated
missing   = no source_document for that cell
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv('.env')

from app.crawler import register_all_mappers
register_all_mappers()

from app.database import SessionLocal
from app.models.provenance import SourceDocument
from app.models.institution import Institution
from app.services.storage import file_path_to_r2_key
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


def best_doc(doc_list):
    """Return the best doc for a cell: prefer annual/integrated, then highest page count."""
    annual = [d for d in doc_list if str(d.report_type) in ANNUAL_TYPES]
    pool = annual if annual else doc_list
    return max(pool, key=lambda d: (d.page_count or 0))


def cell_status(doc_list):
    """Return (status, doc) for a cell."""
    if not doc_list:
        return 'missing', None
    d = best_doc(doc_list)
    pages = d.page_count or 0
    rtype = str(d.report_type)
    # truncated overrides everything if < 10 pages
    if pages < 10:
        return 'truncated', d
    if rtype not in ANNUAL_TYPES:
        return 'wrong_type', d
    if pages < 30:
        return 'short', d
    return 'usable', d


# Build doc map: (inst_id, year) -> list
doc_map = {}
for d in all_docs:
    doc_map.setdefault((d.institution_id, d.fiscal_year), []).append(d)

# Coverage matrix
print("=" * 110)
print("COVERAGE MATRIX — usability status per cell")
print("=" * 110)
header = f"{'Company':<52} " + "  ".join(f"{y}" for y in TARGET_YEARS)
print(header)
print("-" * 110)

STATUS_ABBR = {'usable': 'OK', 'short': 'SH', 'truncated': 'TR', 'wrong_type': 'WT', 'missing': '--'}
counts = {s: 0 for s in STATUS_ABBR}
not_usable = []

for inst in institutions:
    cells = []
    for year in TARGET_YEARS:
        doc_list = doc_map.get((inst.id, year), [])
        status, d = cell_status(doc_list)
        counts[status] += 1
        cells.append(STATUS_ABBR[status])
        if status != 'usable':
            fname = ''
            pages = 0
            rtype = ''
            if d:
                # get file base name from file_path
                fp = d.file_path or ''
                # R2 key format: slug/year_type_sha8.pdf — take last segment
                fname = fp.split('/')[-1] if '/' in fp else fp
                pages = d.page_count or 0
                rtype = str(d.report_type)
            not_usable.append({
                'slug': inst.slug, 'year': year, 'status': status,
                'pages': pages, 'type': rtype, 'fname': fname,
                'id': d.id if d else None
            })
    print(f"{inst.slug:<52} " + "   ".join(cells))

print("-" * 110)
total = sum(counts.values())
print(f"\nTotals: " + "  ".join(f"{k}={v}" for k, v in counts.items()) + f"  total={total}")
print(f"\nOK={counts['usable']}  Not-usable={total - counts['usable']}  "
      f"(SH={counts['short']} TR={counts['truncated']} WT={counts['wrong_type']} missing={counts['missing']})")

print()
print("=" * 110)
print("NON-USABLE CELLS — for sourcing")
print("=" * 110)
print(f"{'Company':<52} {'FY':>4}  {'Status':<10}  {'pages':>6}  {'type':<12}  key / note")
print("-" * 110)

for item in sorted(not_usable, key=lambda x: (x['status'], x['slug'], x['year'])):
    st = item['status']
    pages_str = str(item['pages']) if item['pages'] else '-'
    print(f"  {item['slug']:<52} {item['year']:>4}  {st:<10}  {pages_str:>6}  {item['type']:<12}  {item['fname'][:50]}")

print()
print("=" * 110)
print("SUMMARY BY STATUS")
print("=" * 110)
for status, count in counts.items():
    print(f"  {status:<12} {count:>3}")
