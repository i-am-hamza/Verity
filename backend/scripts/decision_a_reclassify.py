"""Decision A: Reclassify 6 existing source_documents as annual reports.
Emirates Telecom 2024/25, Aldar 2023/25, Rabigh 2025, Saudi Aramco 2024.
All confirmed as annual reports by researcher on 2026-10-08.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv('.env')
from app.crawler import register_all_mappers
register_all_mappers()
from app.database import SessionLocal
from app.models.provenance import SourceDocument, ReportType, ReviewStatus
from sqlalchemy import select

RECLASSIFY = [
    # (id, slug_hint, fiscal_year, old_type_expected)
    (156, 'emirates-telecom-etisalat-group', 2024, 'sustainability'),
    (157, 'emirates-telecom-etisalat-group', 2025, 'sustainability'),
    (117, 'aldar-properties-pjsc', 2023, 'sustainability'),
    (119, 'aldar-properties-pjsc', 2025, 'sustainability'),
    (202, 'rabigh-refining-petrochemical-co', 2025, 'sustainability'),
    (207, 'saudi-aramco', 2024, 'unknown'),
]

NOTE = "reclassified from {old} to annual: confirmed as annual report by researcher 2026-10-08"

db = SessionLocal()
results = []
for doc_id, slug_hint, fy, old_type in RECLASSIFY:
    doc = db.get(SourceDocument, doc_id)
    if doc is None:
        results.append(f"ERROR: id={doc_id} not found")
        continue
    actual_old = str(doc.report_type)
    if actual_old != old_type:
        results.append(f"WARNING: id={doc_id} expected type={old_type} but found type={actual_old}")

    old_note = doc.review_note or ""
    doc.report_type = ReportType.annual
    doc.review_status = ReviewStatus.auto_ok
    doc.review_note = (NOTE.format(old=actual_old) + (" | " + old_note if old_note else ""))
    db.add(doc)
    results.append(f"OK: id={doc_id} {slug_hint} FY{fy}: {actual_old} -> annual")

db.commit()
db.close()

for r in results:
    print(r)
print("\nDone. 6 records updated.")
