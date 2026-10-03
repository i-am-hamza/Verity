"""The ALAFCO gap-row importer: rows land where Session 4 expects them,
and re-running updates in place rather than duplicating.
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
def isolated_db(tmp_path, monkeypatch):
    db_path = tmp_path / "alafco_import.db"
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
    from seed import import_alafco_gaps as import_mod
    monkeypatch.setattr(import_mod, "SessionLocal", LocalSession)

    yield LocalSession
    engine.dispose()


def _seed_alafco(session):
    """The importer requires the institution to exist in the DB first."""
    from app.models.institution import Institution, InstitutionType, Wave
    inst = Institution(
        name="ALAFCO Aviation Lease and Finance Company",
        country="Kuwait",
        sector="banking",
        slug="alafco-aviation-lease-and-finance-company",
        wave=Wave.financial,
        is_financial=True,
        institution_type=InstitutionType.leasing,
    )
    db = session()
    try:
        db.add(inst)
        db.commit()
        db.refresh(inst)
        return inst.id
    finally:
        db.close()


def test_imports_five_rows_and_is_idempotent(isolated_db):
    from app.models.provenance import Gap, GapReason
    from seed.import_alafco_gaps import import_rows

    inst_id = _seed_alafco(isolated_db)

    summary = import_rows()
    assert summary == {"total": 5, "created": 5, "updated": 0}

    db = isolated_db()
    try:
        gaps = (
            db.query(Gap)
            .filter(Gap.institution_id == inst_id)
            .order_by(Gap.fiscal_year)
            .all()
        )
        assert [g.fiscal_year for g in gaps] == [2021, 2022, 2023, 2024, 2025]
        # Every gap uses the `unreachable` enum value — including FY2025, where
        # the "confirmed non-existent" reasoning lives in next_action, not in
        # the reason enum.
        assert all(g.reason == GapReason.unreachable for g in gaps)
        # FY2021-FY2024 go to Wayback.
        for g in gaps[:4]:
            assert "Wayback" in (g.next_action or "")
        # FY2025 is a confirmed non-existence, not a Wayback target.
        assert "Confirmed non-existent" in (gaps[4].next_action or "")
    finally:
        db.close()

    # Second run: 0 created, 5 updated.
    summary2 = import_rows()
    assert summary2 == {"total": 5, "created": 0, "updated": 5}
    db = isolated_db()
    try:
        assert db.query(Gap).count() == 5
    finally:
        db.close()


def test_fails_fast_if_institution_missing(isolated_db):
    """The importer should refuse to run if the institution isn't loaded
    yet — otherwise FK violations would silently roll back and leave an
    inconsistent DB."""
    from seed.import_alafco_gaps import import_rows

    with pytest.raises(RuntimeError, match="not in DB"):
        import_rows()
