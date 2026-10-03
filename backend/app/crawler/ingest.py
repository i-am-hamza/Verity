"""Human-approved ingest paths.

- `ingest_approved`: downloads only URLs listed in data/approved_downloads.json
  with source=wayback. Same validation + manifest as a live crawl.
- `ingest_manual`: scans storage/manual_inbox/<slug>/*.pdf for files the
  user dropped in. Validates and records with source=manual. The user's
  note (if any) in a `.note` file next to the PDF is captured as review_note.
"""
from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.crawler.config import APPROVED_DOWNLOADS_PATH, MANUAL_INBOX_DIR
from app.crawler.fetch import Fetcher, FetchResult
from app.crawler.manifest import save_pdf
from app.crawler.validate import validate_pdf
from app.models.institution import Institution
from app.models.provenance import ReportType, ReviewStatus, SourceDocument, SourceType

log = logging.getLogger("verity.crawler.ingest")


def _record(
    db: Session,
    *,
    inst: Institution,
    source_type: SourceType,
    source_url: str,
    body: bytes,
    final_url: str | None,
    http_status: int | None,
    content_type: str | None,
    suspected_year: int | None,
    note_prefix: str = "",
) -> tuple[SourceDocument | None, str]:
    val = validate_pdf(body, source_filename=source_url.rsplit("/", 1)[-1],
                       expected_year=suspected_year)
    if not val.ok:
        return None, f"rejected: {val.reason}"

    year = suspected_year or val.inferred_year
    if not year:
        return None, "no fiscal year attributable from text; manual review needed"

    existing = (
        db.query(SourceDocument)
        .filter(SourceDocument.sha256 == val.sha256)
        .one_or_none()
    )
    if existing:
        return existing, f"deduped against existing sha256 {val.sha256[:8]} (first seen as source={existing.source.value})"

    manifest_row = {
        "source": source_type.value,
        "institution_slug": inst.slug,
        "fiscal_year": year,
        "source_url": source_url,
        "final_url": final_url,
        "http_status": http_status,
        "retrieved_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "bytes": val.byte_count,
        "content_type": content_type,
        "report_type": val.report_type,
        "page_count": val.page_count,
        "includes_financial_statements": val.includes_financial_statements,
        "review_status": val.review_status,
        "note": note_prefix or None,
    }
    dest, _created = save_pdf(
        slug=inst.slug, fiscal_year=year, report_type=val.report_type,
        sha256=val.sha256, body=body, manifest_row=manifest_row,
    )

    try:
        rt = ReportType(val.report_type)
    except ValueError:
        rt = ReportType.unknown

    doc = SourceDocument(
        institution_id=inst.id,
        fiscal_year=year,
        report_type=rt,
        source=source_type,
        source_url=source_url,
        final_url=final_url,
        http_status=http_status,
        retrieved_at=datetime.now(UTC),
        sha256=val.sha256,
        bytes=val.byte_count,
        content_type=content_type,
        page_count=val.page_count,
        includes_financial_statements=val.includes_financial_statements,
        file_path=str(dest),
        review_status=ReviewStatus(val.review_status),
        review_note=(note_prefix + (val.reason or "")) or None,
    )
    db.add(doc)
    db.commit()
    return doc, f"ingested -> {dest}"


def ingest_approved(db: Session) -> list[dict]:
    """Read data/approved_downloads.json. Each entry needs:
       {institution_slug, fiscal_year, source_url, note?}
    """
    if not APPROVED_DOWNLOADS_PATH.exists():
        return [{"status": "no_file", "path": str(APPROVED_DOWNLOADS_PATH)}]
    rows = json.loads(APPROVED_DOWNLOADS_PATH.read_text(encoding="utf-8"))
    out: list[dict] = []
    fetcher = Fetcher()
    for row in rows:
        slug = row["institution_slug"]
        inst = db.query(Institution).filter(Institution.slug == slug).one_or_none()
        if inst is None:
            out.append({"slug": slug, "status": f"institution {slug!r} not in DB"})
            continue
        url = row["source_url"]
        fetched: FetchResult = fetcher.get(url)
        if fetched.outcome != "ok":
            out.append({"slug": slug, "url": url, "status": f"fetch failed: {fetched.outcome} {fetched.detail or ''}"})
            continue
        _doc, status = _record(
            db, inst=inst, source_type=SourceType.wayback,
            source_url=url, body=fetched.body, final_url=fetched.final_url,
            http_status=fetched.status, content_type=fetched.content_type,
            suspected_year=row.get("fiscal_year"),
            note_prefix=f"[approved: {row.get('note','')}] " if row.get("note") else "",
        )
        out.append({"slug": slug, "url": url, "status": status})
    return out


_FILENAME_YEAR_RX = __import__("re").compile(r"(?<!\d)(20[12]\d)(?!\d)")


def _year_from_filename(name: str) -> int | None:
    """Pick a 4-digit year 2010-2029 from the filename if present. Used by
    manual ingest so a reliable file-naming convention
    ('<Company> Annual Report 2024.pdf') isn't overridden by a stray
    year on a glossy title page's chairman quote. The validator's
    year-mismatch check still catches genuine mislabels — this just
    makes the filename an authoritative *suggestion* instead of being
    ignored."""
    for m in _FILENAME_YEAR_RX.findall(name):
        y = int(m)
        if 2015 <= y <= 2030:
            return y
    return None


def ingest_manual(db: Session) -> list[dict]:
    """Scan storage/manual_inbox/<slug>/*.pdf (plus sibling .note files)."""
    MANUAL_INBOX_DIR.mkdir(parents=True, exist_ok=True)
    out: list[dict] = []
    for slug_dir in sorted(p for p in MANUAL_INBOX_DIR.iterdir() if p.is_dir()):
        slug = slug_dir.name
        inst = db.query(Institution).filter(Institution.slug == slug).one_or_none()
        if inst is None:
            out.append({"slug": slug, "status": "institution not in DB — skipping"})
            continue
        for pdf in sorted(slug_dir.glob("*.pdf")):
            note_file = pdf.with_suffix(".note")
            user_note = note_file.read_text(encoding="utf-8").strip() if note_file.exists() else ""
            body = pdf.read_bytes()
            suspected = _year_from_filename(pdf.name)
            _doc, status = _record(
                db, inst=inst, source_type=SourceType.manual,
                source_url=f"manual_inbox:{pdf.name}",
                body=body, final_url=None, http_status=None,
                content_type="application/pdf",
                suspected_year=suspected,
                note_prefix=f"[manual: {user_note}] " if user_note else "[manual] ",
            )
            out.append({"slug": slug, "file": pdf.name, "status": status})
    return out
