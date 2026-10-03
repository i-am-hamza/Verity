"""Session 7 hardening: tests for the seeded evidence-sample exporter
(scripts/export_evidence_sample.py / app.services.evidence_sample).

The point of the seeded sample is reproducibility — the same seed MUST
produce the same rows across runs, otherwise supervisor review of one
export is uncomparable with the next. These tests pin that invariant.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))


@pytest.fixture
def seeded_db(tmp_path, monkeypatch):
    url = f"sqlite:///{(tmp_path / 'ev.db').as_posix()}"
    from app import database as database_mod
    from app.models import institution, provenance, report, review, run, score, taxonomy  # noqa: F401

    engine = create_engine(url, connect_args={"check_same_thread": False})
    LocalSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    database_mod.Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(database_mod, "engine", engine)
    monkeypatch.setattr(database_mod, "SessionLocal", LocalSession)

    # Seed: one institution, one report, three terms across three pillars,
    # a bunch of evidence rows per term so sampling has pool to pick from.
    db = LocalSession()
    from app.models.institution import Institution
    from app.models.report import Report, ReportStatus
    from app.models.score import MatchEvidence
    from app.models.taxonomy import Category, Term

    inst = Institution(name="Testco", country="Qatar", sector="banking",
                       slug="testco", is_financial=True, active=True)
    db.add(inst)
    db.flush()

    rpt = Report(institution_id=inst.id, fiscal_year=2023,
                 file_path="/dev/null", status=ReportStatus.scored,
                 page_count=50)
    db.add(rpt)
    db.flush()

    cats = {}
    for name, pillar in (("Environmental", "Environmental"),
                        ("Social", "Social"),
                        ("Governance", "Governance")):
        c = Category(name=name, pillar=pillar, weight=1.0)
        db.add(c)
        db.flush()
        cats[pillar] = c

    for pillar in ("Environmental", "Social", "Governance"):
        t = Term(category_id=cats[pillar].id,
                 phrase=f"term_{pillar.lower()}", weight=1.0, lemma_based=True)
        db.add(t)
        db.flush()
        # 120 evidence rows per pillar — above the 50-per-pillar default
        for j in range(120):
            db.add(MatchEvidence(
                report_id=rpt.id, term_id=t.id,
                page_number=((j % 50) + 1),
                sentence_text=f"Sample sentence {j} for {pillar}.",
            ))
    db.commit()
    yield LocalSession
    engine.dispose()


def test_sample_is_deterministic_under_seed(seeded_db, tmp_path):
    """Same seed, same input → identical row set (order-sensitive)."""
    from app.services.evidence_sample import export_evidence_sample

    out1 = tmp_path / "a.csv"
    out2 = tmp_path / "b.csv"
    db1 = seeded_db()
    try:
        export_evidence_sample(db1, out_path=out1)
    finally:
        db1.close()
    db2 = seeded_db()
    try:
        export_evidence_sample(db2, out_path=out2)
    finally:
        db2.close()
    assert out1.read_text(encoding="utf-8") == out2.read_text(encoding="utf-8")


def test_sample_caps_per_pillar_at_configured_size(seeded_db, tmp_path):
    """50 per pillar is the config default; a pool of 120 per pillar must
    produce exactly 150 rows (plus header)."""
    from app.services.evidence_sample import export_evidence_sample

    db = seeded_db()
    try:
        result = export_evidence_sample(db, out_path=tmp_path / "s.csv")
    finally:
        db.close()
    assert result.per_pillar_sampled == {"Environmental": 50,
                                         "Social": 50, "Governance": 50}
    assert result.per_pillar_available == {"Environmental": 120,
                                           "Social": 120, "Governance": 120}
