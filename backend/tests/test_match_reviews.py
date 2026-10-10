"""Session 7 hardening: tests for the match_reviews reviewer flow added
tonight. The flow has no existing tests — it was built as part of the
dashboard evidence view. These lock in:

  * posting a verdict creates (then updates) a MatchReview row
  * precision tally per term reflects the stored reviews
  * verdict validation rejects anything outside the three allowed labels
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    url = f"sqlite:///{(tmp_path / 'r.db').as_posix()}"
    from app import database as database_mod
    from app.models import institution, provenance, report, review, run, score, taxonomy  # noqa: F401

    engine = create_engine(url, connect_args={"check_same_thread": False})
    LocalSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    database_mod.Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(database_mod, "engine", engine)
    monkeypatch.setattr(database_mod, "SessionLocal", LocalSession)

    db = LocalSession()
    from app.models.institution import Institution
    from app.models.report import Report, ReportStatus
    from app.models.score import MatchEvidence
    from app.models.taxonomy import Category, TaxonomyVersion, Term
    from app.services.pipeline import PIPELINE_VERSION

    inst = Institution(name="Testco", country="Qatar", sector="banking",
                       slug="testco", is_financial=True, active=True)
    db.add(inst)
    cat = Category(name="Governance", pillar="Governance", weight=1.0)
    db.add(cat)
    db.flush()
    term = Term(category_id=cat.id, phrase="governance",
                weight=1.0, lemma_based=True)
    db.add(term)
    tv = TaxonomyVersion(hash="h" * 64, note="test")
    db.add(tv)
    db.flush()
    rpt = Report(institution_id=inst.id, fiscal_year=2023,
                 file_path="/dev/null", status=ReportStatus.scored,
                 page_count=10, taxonomy_version=tv.hash,
                 pipeline_version=PIPELINE_VERSION)
    db.add(rpt)
    db.flush()
    # 4 evidence rows for the same term so we can review some + leave some.
    ev_ids = []
    for pg in (3, 5, 7, 9):
        me = MatchEvidence(report_id=rpt.id, term_id=term.id,
                           page_number=pg, sentence_text="Governance stuff.",
                           taxonomy_version_id=tv.id, pipeline_version=PIPELINE_VERSION)
        db.add(me)
        db.flush()
        ev_ids.append(me.id)
    db.commit()
    db.close()

    from app.main import app
    with TestClient(app) as c:
        yield c, ev_ids
    engine.dispose()


def test_posting_review_persists(api_client):
    client, ev_ids = api_client
    r = client.post("/dashboard/evidence/review", json={
        "evidence_id": ev_ids[0], "reviewer": "ana", "verdict": "valid",
    })
    assert r.status_code == 200, r.text
    # Re-fetch evidence list and confirm the review was recorded.
    r2 = client.get("/dashboard/evidence?institution_slug=testco")
    rows = r2.json()["rows"]
    reviewed = [row for row in rows if row["evidence_id"] == ev_ids[0]]
    assert reviewed and reviewed[0]["reviewed"] is True
    assert reviewed[0]["reviewer_verdict"] == "valid"
    assert reviewed[0]["reviewer"] == "ana"


def test_posting_review_updates_existing(api_client):
    client, ev_ids = api_client
    client.post("/dashboard/evidence/review", json={
        "evidence_id": ev_ids[0], "reviewer": "ana", "verdict": "valid",
    })
    client.post("/dashboard/evidence/review", json={
        "evidence_id": ev_ids[0], "reviewer": "ana", "verdict": "false_positive",
    })
    rows = client.get("/dashboard/evidence?institution_slug=testco").json()["rows"]
    row = next(r for r in rows if r["evidence_id"] == ev_ids[0])
    # One row, latest verdict wins — append-only would create two.
    assert row["reviewer_verdict"] == "false_positive"


def test_bad_verdict_rejected(api_client):
    client, ev_ids = api_client
    r = client.post("/dashboard/evidence/review", json={
        "evidence_id": ev_ids[0], "reviewer": "ana", "verdict": "lgtm",
    })
    assert r.status_code == 422, r.text


def test_precision_tally_counts_only_reviewed(api_client):
    client, ev_ids = api_client
    # Review three of four: 2 valid, 1 false_positive.
    for eid, verdict in zip(ev_ids[:3],
                            ["valid", "valid", "false_positive"],
                            strict=False):
        client.post("/dashboard/evidence/review", json={
            "evidence_id": eid, "reviewer": "ana", "verdict": verdict,
        })
    p = client.get("/dashboard/evidence/precision?group=term").json()
    row = next(x for x in p if x["term_or_category"] == "governance")
    assert row["reviewed"] == 3
    assert row["valid"] == 2
    assert row["false_positive"] == 1
    assert row["unsure"] == 0
    assert row["precision_point"] == pytest.approx(2 / 3, rel=1e-3)
