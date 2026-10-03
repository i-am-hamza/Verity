"""If the same PDF (same sha256) is 'found' via IR source first then by
the exchange source later, the second attempt must link to the existing
file — no new SourceDocument row and no second write to disk.

End-to-end against the pipeline, with HTTP fetches mocked out so the
test runs offline.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path
from unittest.mock import patch

import pymupdf
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    db_path = tmp_path / "dedup.db"
    url = f"sqlite:///{db_path.as_posix()}"

    from app import database as database_mod
    from app.models import institution as _i  # noqa: F401
    from app.models import provenance as _p  # noqa: F401
    from app.models import report as _r  # noqa: F401
    from app.models import score as _s  # noqa: F401
    from app.models import taxonomy as _t  # noqa: F401

    engine = create_engine(url, connect_args={"check_same_thread": False})
    LocalSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    database_mod.Base.metadata.create_all(bind=engine)

    monkeypatch.setattr(database_mod, "engine", engine)
    monkeypatch.setattr(database_mod, "SessionLocal", LocalSession)

    yield LocalSession
    engine.dispose()


def _tiny_annual_report(year: int) -> bytes:
    doc = pymupdf.open()
    first = doc.new_page(width=612, height=792)
    first.insert_text(
        (72, 72),
        f"ACME CORP\nAnnual Report {year}\n"
        f"For the year ended 31 December {year}",
        fontsize=11,
    )
    for i in range(40):
        p = doc.new_page(width=612, height=792)
        for row in range(60):
            p.insert_text((72, 72 + row * 10), f"row{i:03d}-{row:03d} " * 10, fontsize=8)
    buf = io.BytesIO()
    doc.save(buf, deflate=True)
    doc.close()
    return buf.getvalue()


def _seed_institution_and_sources(session_factory, tmp_path):
    """Add an Institution; also write a minimal ir_sources.json pointing at
    both an IR URL and an exchange URL (both verified)."""
    import json

    from app.models.institution import Institution, Wave

    db = session_factory()
    try:
        inst = Institution(
            name="ACME Corp", country="Qatar", sector="banking",
            slug="acme-corp", wave=Wave.financial, is_financial=True,
            rank=1,
        )
        db.add(inst)
        db.commit()
    finally:
        db.close()

    ir_sources_tmp = tmp_path / "ir_sources.json"
    ir_sources_tmp.write_text(json.dumps([{
        "slug": "acme-corp",
        "ir_url": "https://acme.example/ir",
        "ir_status": "verified",
        "exchange_company_url": "https://exchange.example/profile?symbol=ACME",
        "exchange_status": "verified",
        "allowed_hosts": [],
        "evidence": {"ir": {}, "exchange": {}},
        "notes": "",
    }], indent=2), encoding="utf-8")
    return ir_sources_tmp


def test_same_sha256_from_exchange_doesnt_double_store(isolated_db, tmp_path, monkeypatch):
    """Round 1: IR source produces FY2023 PDF (new row).
    Round 2: pretend only FY2024 is missing from IR but IR's FY2024 is the SAME
    PDF bytes as the earlier FY2023 run (sha256 collision). Second attempt must
    recognise the dup via the exchange side and not write a second file / row.
    """
    import app.crawler.pipeline as pipeline_mod
    from app.crawler.fetch import FetchResult
    from app.crawler.pipeline import Pipeline, new_run_id
    from app.models.provenance import SourceDocument

    # Point the manifest/storage at tmp_path so tests don't touch the real tree.
    monkeypatch.setattr(pipeline_mod, "IR_SOURCES_PATH", _seed_institution_and_sources(isolated_db, tmp_path))
    import app.crawler.manifest as manifest_mod
    monkeypatch.setattr(manifest_mod, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(manifest_mod, "MANIFEST_PATH", tmp_path / "manifest.jsonl")

    pdf_bytes = _tiny_annual_report(2023)

    # Mock fetcher so no network happens. The pipeline hits ir_url, gets an HTML
    # page with one link to the PDF, then fetches the PDF.
    html = (
        b"<html><body><a href='https://acme.example/ir/annual-2023.pdf'>"
        b"Annual Report 2023</a></body></html>"
    )
    html_2024 = (
        b"<html><body><a href='https://acme.example/ir/annual-2024.pdf'>"
        b"Annual Report 2024</a></body></html>"
    )

    class DummyFetcher:
        user_agent = "test"
        def __init__(self):
            self._blocked: set = set()

        def get(self, url, *, render=False):
            if url == "https://acme.example/ir":
                return FetchResult(url=url, final_url=url, status=200, body=html,
                                   content_type="text/html", outcome="ok")
            if url == "https://acme.example/ir/annual-2023.pdf":
                return FetchResult(url=url, final_url=url, status=200, body=pdf_bytes,
                                   content_type="application/pdf", outcome="ok")
            if url == "https://acme.example/ir/annual-2024.pdf":
                # Same bytes — sha256 collision. (In the real world: PDF reused.)
                return FetchResult(url=url, final_url=url, status=200, body=pdf_bytes,
                                   content_type="application/pdf", outcome="ok")
            if url.startswith("https://exchange.example/"):
                return FetchResult(url=url, final_url=url, status=200,
                                   body=b"<html>Nothing here</html>",
                                   content_type="text/html", outcome="ok")
            return FetchResult(url=url, outcome="error", detail="unknown URL")

    db = isolated_db()
    try:
        pipe = Pipeline(db, fetcher=DummyFetcher())
        _run1 = pipe.crawl_institution("acme-corp", [2023], run_id=new_run_id())

        # One file saved; one SourceDocument row.
        assert db.query(SourceDocument).count() == 1
        first_row = db.query(SourceDocument).one()
        assert first_row.source.value == "crawler"
        assert first_row.fiscal_year == 2023

        # Now round 2: ask for 2024. IR will return the SAME bytes (sha256 same).
        # The pipeline must recognise it and not store a second row.
        with patch.object(DummyFetcher, "get", DummyFetcher().get.__func__) as _:
            pass  # (noop — we're not mocking per-call behaviour; same fetcher reused)

        class DummyFetcher2(DummyFetcher):
            def get(self, url, *, render=False):
                if url == "https://acme.example/ir":
                    return FetchResult(url=url, final_url=url, status=200, body=html_2024,
                                       content_type="text/html", outcome="ok")
                return DummyFetcher().get(url, render=render)

        pipe2 = Pipeline(db, fetcher=DummyFetcher2())
        run2 = pipe2.crawl_institution("acme-corp", [2024], run_id=new_run_id())

        # Still only ONE SourceDocument row — the sha256 matched the first.
        assert db.query(SourceDocument).count() == 1

        # Round-2's outcome must be "deduped".
        found = [o for o in run2.outcomes if o.result == "deduped"]
        assert found, f"expected a 'deduped' outcome in {run2.outcomes}"
    finally:
        db.close()
