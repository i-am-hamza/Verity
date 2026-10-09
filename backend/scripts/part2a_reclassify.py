"""Part 2a: Reclassify 8 existing source_documents as annual reports.
Researcher opened and confirmed each one, 2026-10-09.

Reclassifies report_type to annual and review_status to auto_ok.
For each reclassified doc, marks any OTHER doc for the same (institution, FY)
as superseded_by_id = reclassified_doc.id, so it can never be scored.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv('.env')

from app.crawler import register_all_mappers
register_all_mappers()
from app.database import SessionLocal
from app.models.provenance import SourceDocument, ReportType, ReviewStatus
from app.models.institution import Institution
from sqlalchemy import select

# (slug, fiscal_year, hint about old type — for audit)
RECLASSIFY = [
    ('al-rajhi-bank',           2024, 'unknown'),
    ('the-saudi-national-bank', 2024, 'unknown'),
    ('kuwait-finance-house',    2023, 'unknown'),
    ('national-bank-of-kuwait', 2021, 'unknown'),
    ('national-bank-of-bahrain', 2020, 'sustainability'),
    ('national-bank-of-bahrain', 2022, 'sustainability'),
    ('abdullah-al-othaim-markets', 2021, 'annual'),   # already annual; add note only
    ('emirates-nbd-pjsc',        2020, 'annual'),      # already annual; add note only
]

NOTE = "confirmed as annual report by researcher 2026-10-09; reclassified from {old}"
ANNUAL_TYPES = {'annual', 'integrated'}

db = SessionLocal()
inst_by_slug = {i.slug: i for i in db.execute(select(Institution)).scalars().all()}
all_docs = db.execute(select(SourceDocument)).scalars().all()

doc_map: dict[tuple[int, int], list[SourceDocument]] = {}
for d in all_docs:
    doc_map.setdefault((d.institution_id, d.fiscal_year), []).append(d)

results = []
superseded_total = 0

for slug, fy, old_type_hint in RECLASSIFY:
    inst = inst_by_slug.get(slug)
    if inst is None:
        results.append(f"ERROR: slug {slug!r} not found")
        continue

    cell = sorted(doc_map.get((inst.id, fy), []),
                  key=lambda d: (d.page_count or 0), reverse=True)
    if not cell:
        results.append(f"ERROR: no docs for {slug} FY{fy}")
        continue

    # Pick the best doc — researcher reviewed the highest-page-count doc
    annual = [d for d in cell if str(d.report_type) in ANNUAL_TYPES]
    # Prefer existing annual/integrated; fallback to highest-page-count
    target = annual[0] if annual else cell[0]

    old_type = str(target.report_type)
    target.report_type = ReportType.annual
    target.review_status = ReviewStatus.auto_ok
    note_append = NOTE.format(old=old_type)
    target.review_note = (note_append + " | " + target.review_note) if target.review_note else note_append
    db.add(target)

    # Mark all other docs for this cell superseded by this one
    others = [d for d in cell if d.id != target.id]
    for other in others:
        if other.superseded_by_id is None:  # only set once
            other.superseded_by_id = target.id
            db.add(other)
            superseded_total += 1
            results.append(f"  SUPERSEDE: id={other.id} {slug} FY{fy} "
                           f"(pages={other.page_count} type={other.report_type}) "
                           f"→ superseded_by id={target.id}")

    results.append(f"OK: id={target.id} {slug} FY{fy}: {old_type} → annual "
                   f"(pages={target.page_count}, {len(others)} others superseded)")

db.commit()
db.close()

print("=== PART 2a: RECLASSIFICATION ===")
for r in results:
    print(r)
print(f"\nTotal superseded: {superseded_total}")
print("Done.")
