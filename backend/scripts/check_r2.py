"""Check which source_documents are present in R2."""
from dotenv import load_dotenv
load_dotenv(".env")

from app.crawler import register_all_mappers
register_all_mappers()
from app.database import SessionLocal
from app.models.provenance import SourceDocument
from app.models.institution import Institution
from app.services.storage import _r2_client, R2Settings, file_path_to_r2_key
from sqlalchemy import select

db = SessionLocal()
docs = db.execute(
    select(SourceDocument, Institution.slug)
    .join(Institution, SourceDocument.institution_id == Institution.id)
).all()
db.close()

cfg = R2Settings()
client = _r2_client()

in_r2 = 0
not_in_r2 = 0

print(f"{'ID':<5} {'slug':<45} {'FY':<6} {'type':<22} {'R2 key':<60} {'R2?'}")
print("-" * 150)

missing_list = []
for doc, slug in sorted(docs, key=lambda x: (x[1], x[0].fiscal_year)):
    d = doc
    key = d.file_path
    if not key:
        print(f"{d.id:<5} {slug:<45} {d.fiscal_year:<6} {'NO_FILE_PATH':<22} {'':60} N/A")
        continue

    r2_key = file_path_to_r2_key(key)

    try:
        client.head_object(Bucket=cfg.bucket, Key=r2_key)
        r2_status = "YES"
        in_r2 += 1
    except Exception:
        r2_status = "NO"
        not_in_r2 += 1
        missing_list.append((d.id, slug, d.fiscal_year, str(d.report_type), r2_key))

    rt = str(d.report_type) if d.report_type else "None"
    print(f"{d.id:<5} {slug:<45} {d.fiscal_year:<6} {rt:<22} {r2_key:<60} {r2_status}")

print()
print(f"Total: {in_r2 + not_in_r2}  In R2: {in_r2}  NOT in R2: {not_in_r2}")
print()
if missing_list:
    print("=== NOT IN R2 ===")
    for row in missing_list:
        print(f"  id={row[0]:<5} {row[1]:<45} FY{row[2]} {row[3]:<22} key={row[4]}")
