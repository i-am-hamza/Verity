"""Ingest a single PDF URL that a human found by hand.

Different from `ingest_approved` (which reads a batch from JSON) and from
`ingest_manual` (which scans a directory) — this is for a one-off URL the
user hands me directly. Writes `source=manual` + `source_url=<url>`
through the same validation and manifest pipeline as the live crawler.

Usage (from backend/):
    python scripts/ingest_url.py <slug> <fiscal_year> <url>
"""
from __future__ import annotations

import argparse
import sys
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.crawler import register_all_mappers
from app.crawler.fetch import Fetcher
from app.crawler.ingest import _record
from app.database import SessionLocal
from app.models.institution import Institution
from app.models.provenance import SourceType


def strip_tracking(url: str) -> str:
    """Remove utm_* / gclid / fbclid tracking query params."""
    parts = urlsplit(url)
    cleaned = [
        (k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if not (k.lower().startswith("utm_") or k.lower() in ("gclid", "fbclid"))
    ]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(cleaned), parts.fragment))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("slug")
    parser.add_argument("fiscal_year", type=int)
    parser.add_argument("url")
    parser.add_argument("--note", default="", help="free text captured as the review_note prefix")
    args = parser.parse_args()

    clean_url = strip_tracking(args.url)
    if clean_url != args.url:
        print(f"stripped tracking params -> {clean_url}")

    register_all_mappers()
    fetcher = Fetcher()
    print(f"User-Agent: {fetcher.user_agent}")

    fetched = fetcher.get(clean_url)
    print(f"HTTP: outcome={fetched.outcome} status={fetched.status} bytes={len(fetched.body):,} content_type={fetched.content_type}")
    if fetched.outcome != "ok":
        print(f"  -> aborting; detail: {fetched.detail}", file=sys.stderr)
        return 1

    db = SessionLocal()
    try:
        inst = db.query(Institution).filter(Institution.slug == args.slug).one_or_none()
        if inst is None:
            print(f"institution slug {args.slug!r} not in DB", file=sys.stderr)
            return 2

        note_prefix = f"[manual url: {args.note}] " if args.note else "[manual url] "
        doc, status = _record(
            db, inst=inst, source_type=SourceType.manual,
            source_url=clean_url, body=fetched.body,
            final_url=fetched.final_url, http_status=fetched.status,
            content_type=fetched.content_type,
            suspected_year=args.fiscal_year,
            note_prefix=note_prefix,
        )
        print(f"  -> {status}")
        if doc:
            print(f"    source_document id={doc.id} sha256={doc.sha256[:12]}... "
                  f"report_type={doc.report_type.value} review_status={doc.review_status.value} "
                  f"pages={doc.page_count} includes_fs={doc.includes_financial_statements}")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
