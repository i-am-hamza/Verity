"""
Reprocessing invariant: running the pipeline twice under DIFFERENT
(taxonomy_version, pipeline_version) pairs must APPEND CategoryScore and
MatchEvidence rows, not overwrite the first run.

The test exercises the pipeline's persistence layer only — we swap out
extraction, segmentation and matching for pure fakes so the assertion is
about database behaviour, not spaCy behaviour.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))


@dataclass
class _FakeMatch:
    term_id: int
    page_number: int
    sentence_text: str


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    db_path = tmp_path / "reprocess.db"
    url = f"sqlite:///{db_path.as_posix()}"

    from app import database as database_mod
    from app.models import institution as _institution  # noqa: F401
    from app.models import provenance as _provenance  # noqa: F401
    from app.models import report as _report  # noqa: F401
    from app.models import score as _score  # noqa: F401
    from app.models import taxonomy as _taxonomy  # noqa: F401

    engine = create_engine(url, connect_args={"check_same_thread": False})
    LocalSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    database_mod.Base.metadata.create_all(bind=engine)

    monkeypatch.setattr(database_mod, "engine", engine)
    monkeypatch.setattr(database_mod, "SessionLocal", LocalSession)

    yield LocalSession
    engine.dispose()


def test_reprocessing_under_a_new_version_appends_rows(isolated_db, monkeypatch):
    from app.models.institution import Institution
    from app.models.report import Report, ReportStatus
    from app.models.score import CategoryScore, MatchEvidence
    from app.models.taxonomy import Category, Term
    from app.services import pipeline as pipeline_mod
    from app.services.pdf_extraction import PageText, WordCounts
    from app.services.text_processing import Sentence

    db = isolated_db()
    try:
        inst = Institution(name="Testco", country="Qatar", sector="banking", slug="testco")
        db.add(inst)
        db.commit()
        db.refresh(inst)

        cat = Category(name="Governance", pillar="Governance", weight=1.0)
        db.add(cat)
        db.flush()
        term = Term(category_id=cat.id, phrase="governance", weight=1.0, lemma_based=True)
        db.add(term)
        db.commit()
        db.refresh(term)

        report = Report(
            institution_id=inst.id,
            fiscal_year=2023,
            language="en",
            file_path="unused.pdf",
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        # Stub extraction / segmentation / matching entirely.
        pages = [PageText(page_number=1, text="governance framework here.", used_ocr=False)]

        def fake_extract(_path):
            return pages

        def fake_count(_pages):
            return WordCounts(latin=1000, arabic=0)

        def fake_segment(_pages):
            return [Sentence(page_number=1, text="governance framework here.")]

        class _FakeMatcher:
            def __init__(self, _terms):
                self._term_id = term.id
            def match_sentences(self, _sents):
                return [_FakeMatch(term_id=self._term_id, page_number=1,
                                   sentence_text="governance framework here.")]

        monkeypatch.setattr(pipeline_mod, "extract_pdf_pages", fake_extract)
        monkeypatch.setattr(pipeline_mod, "count_words", fake_count)
        monkeypatch.setattr(pipeline_mod, "count_latin_words_in_text", lambda _t: 1000)
        monkeypatch.setattr(pipeline_mod, "segment_sentences", fake_segment)
        # Bypass the sentence quality filter so the stub sentence (which
        # intentionally doesn't meet the filter criteria) still reaches the matcher.
        monkeypatch.setattr(pipeline_mod, "filter_sentences", lambda sents: sents)
        monkeypatch.setattr(pipeline_mod, "TaxonomyMatcher", _FakeMatcher)
        # Session 5 added an OCR pre-check that opens the PDF before
        # extract_pdf_pages fires. Stub it so the test's fake file path
        # ("unused.pdf") doesn't need to exist on disk.
        monkeypatch.setattr(pipeline_mod, "estimate_ocr_fraction",
                            lambda _p, _t: (0.0, 1))
        # Session 9 moved PDF bytes behind read_pdf_bytes (R2 in prod,
        # local disk in dev). The reprocessing invariant doesn't care
        # about actual bytes — the fake extractor ignores its argument —
        # so return a dummy buffer for the fake file path.
        monkeypatch.setattr(pipeline_mod, "read_pdf_bytes", lambda _p: b"")
        # Also stub text-quality so we don't try to detect FS boundary / ToC
        # in text that was invented for a database-behaviour test.
        from app.services import text_quality as tq_mod
        from app.services.text_quality import CleanedPages
        monkeypatch.setattr(pipeline_mod, "apply_text_quality",
                            lambda ps, _cfg: CleanedPages(pages=ps))
        # tq_mod reference kept so the import doesn't become unused.
        _ = tq_mod

        # --- Run 1 under an initial pipeline_version.
        monkeypatch.setattr(pipeline_mod, "PIPELINE_VERSION", "0.1.0")
        pipeline_mod.process_report(db, report)

        first_scores = db.query(CategoryScore).filter(CategoryScore.report_id == report.id).all()
        first_evidence = db.query(MatchEvidence).filter(MatchEvidence.report_id == report.id).all()
        assert len(first_scores) == 1
        assert first_scores[0].pipeline_version == "0.1.0"
        assert len(first_evidence) == 1

        # --- Run 2 under a bumped pipeline_version. Same taxonomy hash,
        # so it should reuse the same TaxonomyVersion row; different
        # pipeline_version, so score rows must APPEND rather than overwrite.
        monkeypatch.setattr(pipeline_mod, "PIPELINE_VERSION", "0.2.0")
        report.status = ReportStatus.uploaded
        db.commit()
        pipeline_mod.process_report(db, report)

        all_scores = db.query(CategoryScore).filter(CategoryScore.report_id == report.id).all()
        all_evidence = db.query(MatchEvidence).filter(MatchEvidence.report_id == report.id).all()

        assert len(all_scores) == 2, "old score row must survive; new one is appended"
        assert sorted(cs.pipeline_version for cs in all_scores) == ["0.1.0", "0.2.0"]
        assert len(all_evidence) == 2, "old evidence must survive; new evidence appended"
    finally:
        db.close()
