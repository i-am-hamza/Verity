"""Ingest 6 Bank Aljazira annual reports (FY2020-FY2025).

Source folder: E:\\9. Verity\\storage\\reports\\Aljazira Bank Annual Reports\\

Validations per file:
  - company name present in first pages
  - fiscal year from filename matches year in document
  - English annual report
  - page count >= 30
  - sha256 round-trip to R2

STOP on any failure.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND / ".env")

from app.crawler import register_all_mappers  # noqa: E402

register_all_mappers()

from app.crawler.config import MANIFEST_PATH  # noqa: E402
from app.crawler.validate import validate_pdf  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models.institution import Institution  # noqa: E402
from app.models.provenance import (  # noqa: E402
    ReportType,
    ReviewStatus,
    SourceDocument,
    SourceType,
)
from app.services.storage import R2Settings, _r2_client, r2_enabled  # noqa: E402
from sqlalchemy import select  # noqa: E402

SOURCE_DIR = REPO_ROOT / "storage" / "reports" / "Aljazira Bank Annual Reports"
REVIEW_NOTE = "researcher-verified replacement for SIIG, 2026-10-21"
SLUG = "bank-aljazira"
TARGET_YEARS = {2020, 2021, 2022, 2023, 2024, 2025}

assert r2_enabled(), "STOP: R2 not enabled"
cfg = R2Settings()
client = _r2_client()
print(f"R2 enabled: bucket={cfg.bucket}")

db = SessionLocal()
inst = db.execute(select(Institution).where(Institution.slug == SLUG)).scalar_one_or_none()
if inst is None:
    print(f"ERROR: institution {SLUG!r} not in DB — run add_aljazira.py first")
    db.close()
    sys.exit(1)
print(f"Institution: {inst.name!r} id={inst.id} is_financial={inst.is_financial}")

existing_sha256 = {
    d.sha256: d
    for d in db.execute(
        select(SourceDocument).where(SourceDocument.institution_id == inst.id)
    ).scalars().all()
}
db.close()
print(f"Existing docs for {SLUG}: {len(existing_sha256)}")

# ── scan source directory ─────────────────────────────────────────────────────
pdfs = sorted(SOURCE_DIR.glob("*.pdf"))
if not pdfs:
    print(f"ERROR: no PDFs in {SOURCE_DIR}")
    sys.exit(1)

print(f"\nFound {len(pdfs)} PDF(s) in {SOURCE_DIR}:")
for p in pdfs:
    print(f"  {p.name}  ({p.stat().st_size:,} bytes)")

if len(pdfs) != 6:
    print(f"\nWARNING: expected 6 files, found {len(pdfs)}")

# ── extract year from filename ────────────────────────────────────────────────
import re  # noqa: E402

YEAR_RX = re.compile(r"(?<!\d)(202[0-5])(?!\d)")


def extract_year(fname: str) -> int | None:
    m = YEAR_RX.search(fname)
    return int(m.group(1)) if m else None


# ── process each file ─────────────────────────────────────────────────────────
results: list[dict] = []
new_doc_ids: list[int] = []
n_ok = n_errors = 0

print()
for pdf_path in pdfs:
    fname = pdf_path.name
    year = extract_year(fname)
    if year is None:
        print(f"STOP: no year in filename: {fname}")
        sys.exit(1)
    if year not in TARGET_YEARS:
        print(f"STOP: year {year} not in target set {TARGET_YEARS}: {fname}")
        sys.exit(1)

    print(f"[{year}] {fname}")

    body = pdf_path.read_bytes()
    sha = hashlib.sha256(body).hexdigest()
    print(f"  sha256: {sha[:16]}…  bytes: {len(body):,}")

    # ---- sha256 dedup check ----
    if sha in existing_sha256:
        doc = existing_sha256[sha]
        print(f"  SKIP: already in DB (id={doc.id})")
        new_doc_ids.append(doc.id)
        results.append({"file": fname, "year": year, "id": doc.id, "status": "dedup_ok"})
        n_ok += 1
        continue

    # ---- validate ----
    val = validate_pdf(body, source_filename=fname, expected_year=year)
    print(f"  validate: ok={val.ok}  type={val.report_type}  pages={val.page_count}"
          f"  includes_fs={val.includes_financial_statements}  reason={val.reason!r}")

    if not val.ok:
        print(f"  STOP: validation failed: {val.reason}")
        sys.exit(1)

    if val.page_count < 30:
        print(f"  STOP: only {val.page_count} pages — below minimum 30")
        sys.exit(1)

    final_type = "integrated" if val.report_type == "integrated" else "annual"

    # ---- company check: confirm "Aljazira" appears in first 20 pages ----
    # (Cover pages are often image-only; narrative text starts around page 8-10)
    import pymupdf  # noqa: E402

    doc_pdf = pymupdf.open(stream=body, filetype="pdf")
    first_pages_text = ""
    for i in range(min(20, doc_pdf.page_count)):
        first_pages_text += (doc_pdf[i].get_text("text") or "").lower()
    doc_pdf.close()

    if "aljazira" not in first_pages_text and "al jazira" not in first_pages_text:
        print(f"  STOP: company name 'Aljazira' not found in first 20 pages of {fname}")
        sys.exit(1)
    print("  company check: OK (Aljazira found in first 20 pages)")

    # ---- R2 upload ----
    r2_key = f"{SLUG}/{year}_{final_type}_{sha[:8]}.pdf"
    try:
        client.put_object(
            Bucket=cfg.bucket, Key=r2_key, Body=body, ContentType="application/pdf"
        )
    except Exception as e:
        print(f"  STOP: R2 upload error: {e}")
        sys.exit(1)

    # ---- sha256 round-trip ----
    try:
        obj = client.get_object(Bucket=cfg.bucket, Key=r2_key)
        r2_body = obj["Body"].read()
        r2_sha = hashlib.sha256(r2_body).hexdigest()
    except Exception as e:
        print(f"  STOP: R2 round-trip error: {e}")
        sys.exit(1)

    if r2_sha != sha:
        print(f"  STOP: sha256 mismatch — local={sha[:16]} r2={r2_sha[:16]}")
        sys.exit(1)
    print(f"  R2 round-trip: OK  key={r2_key}")

    # ---- manifest row ----
    manifest_row = {
        "source": "manual",
        "institution_slug": SLUG,
        "fiscal_year": year,
        "source_url": f"manual:{fname}",
        "final_url": None,
        "http_status": None,
        "retrieved_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "sha256": sha,
        "bytes": val.byte_count,
        "content_type": "application/pdf",
        "file_path": r2_key,
        "report_type": final_type,
        "page_count": val.page_count,
        "includes_financial_statements": val.includes_financial_statements,
        "review_status": "auto_ok",
        "note": REVIEW_NOTE,
        "written_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    with MANIFEST_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(manifest_row, ensure_ascii=False) + "\n")

    # ---- DB insert ----
    db2 = SessionLocal()
    new_doc = SourceDocument(
        institution_id=inst.id,
        fiscal_year=year,
        report_type=ReportType.annual if final_type == "annual" else ReportType.integrated,
        source=SourceType.manual,
        source_url=f"manual:{fname}",
        final_url=None,
        http_status=None,
        retrieved_at=datetime.now(UTC),
        sha256=sha,
        bytes=val.byte_count,
        content_type="application/pdf",
        page_count=val.page_count,
        includes_financial_statements=val.includes_financial_statements,
        file_path=r2_key,
        review_status=ReviewStatus.auto_ok,
        review_note=REVIEW_NOTE,
    )
    db2.add(new_doc)
    db2.commit()
    doc_id = new_doc.id
    db2.close()

    print(f"  DB: inserted id={doc_id}")
    new_doc_ids.append(doc_id)
    results.append({
        "file": fname, "year": year, "id": doc_id, "pages": val.page_count,
        "type": final_type, "r2_key": r2_key, "status": "ingested_ok",
    })
    n_ok += 1

# ── summary ───────────────────────────────────────────────────────────────────
print()
print("=" * 60)
print("INGEST SUMMARY")
print(f"  Files processed : {len(pdfs)}")
print(f"  Ingested OK     : {n_ok}")
print(f"  Errors          : {n_errors}")
print()

years_done = {r["year"] for r in results if r.get("status", "").endswith("ok")}
missing_years = TARGET_YEARS - years_done
if missing_years:
    print(f"  MISSING YEARS: {sorted(missing_years)}")
    sys.exit(1)
else:
    print("  All 6 fiscal years present: OK")

print()
for r in results:
    status = r["status"]
    pages_info = f"  pages={r['pages']}" if "pages" in r else ""
    print(f"  FY{r['year']}  id={r['id']}  {status}{pages_info}")

print()
print("Ingest complete. Proceed to batch scoring.")
