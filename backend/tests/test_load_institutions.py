"""
Loader tests:
- Counts (65 rows, 23 financial) match the source spreadsheet exactly.
- Second run is idempotent — no new rows, no side effects.
- Human-confirmed institution_type in the CSV flows into the DB;
  unconfirmed rows stay NULL (loader does not guess).

Uses monkeypatched engine + SessionLocal so schema and data are hermetic
per-test — no module reloading (that fights SQLAlchemy's declarative
registry).
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    """Wire the app to a fresh in-memory SQLite for the test's lifetime.

    Uses a file DB (not :memory:) because openpyxl + loader open a
    separate Session; a memory DB would be a different instance per open.
    """
    db_path = tmp_path / "verity_test.db"
    url = f"sqlite:///{db_path.as_posix()}"

    from app import database as database_mod
    from app.models import institution as _institution  # noqa: F401
    from app.models import provenance as _provenance  # noqa: F401
    from app.models import report as _report  # noqa: F401
    from app.models import score as _score  # noqa: F401
    from app.models import taxonomy as _taxonomy  # noqa: F401
    from seed import load_institutions as loader_mod

    engine = create_engine(url, connect_args={"check_same_thread": False})
    LocalSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    database_mod.Base.metadata.create_all(bind=engine)

    monkeypatch.setattr(database_mod, "engine", engine)
    monkeypatch.setattr(database_mod, "SessionLocal", LocalSession)
    monkeypatch.setattr(loader_mod, "SessionLocal", LocalSession)
    # Redirect the loader's CSV output away from data/ so tests can freely
    # write to it without polluting each other or the real project file.
    monkeypatch.setattr(loader_mod, "PROPOSED_CSV", tmp_path / "proposed.csv")

    yield LocalSession
    engine.dispose()


def _rewrite_confirmed(csv_path: Path, slug_to_type: dict[str, str]) -> None:
    rows = list(csv.DictReader(csv_path.open("r", encoding="utf-8", newline="")))
    fieldnames = list(rows[0].keys()) if rows else []
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            if row["slug"] in slug_to_type:
                row["confirmed"] = slug_to_type[row["slug"]]
            writer.writerow(row)


def test_counts_match_spreadsheet_and_second_run_is_noop(isolated_db):
    from app.models.institution import Institution, Wave
    from seed.load_institutions import load

    summary_1 = load()
    assert summary_1["total_rows"] == 65
    assert summary_1["financial_rows"] == 23

    Session = isolated_db
    db = Session()
    try:
        first_count = db.query(Institution).count()
        assert first_count == 65
        financial = db.query(Institution).filter(Institution.is_financial.is_(True)).count()
        assert financial == 23
        assert db.query(Institution).filter(Institution.wave == Wave.financial).count() == 23
        assert db.query(Institution).filter(Institution.wave == Wave.other).count() == 42
    finally:
        db.close()

    # Second run: no new rows.
    load()
    db = Session()
    try:
        assert db.query(Institution).count() == first_count
    finally:
        db.close()


def test_institution_type_is_null_until_confirmed_and_then_applied(isolated_db):
    from app.models.institution import Institution, InstitutionType
    from seed.load_institutions import PROPOSED_CSV, load

    load()
    db = isolated_db()
    try:
        n_typed = db.query(Institution).filter(Institution.institution_type.isnot(None)).count()
        assert n_typed == 0
    finally:
        db.close()

    _rewrite_confirmed(PROPOSED_CSV, {
        "al-rajhi-bank": "bank",
        "bupa-arabia-for-cooperative-insurance-company": "insurer",
        "dubai-investment": "investment_holding",
        "alafco-aviation-lease-and-finance-company": "leasing",
    })
    load()

    db = isolated_db()
    try:
        bupa = (
            db.query(Institution)
            .filter(Institution.slug == "bupa-arabia-for-cooperative-insurance-company")
            .one()
        )
        assert bupa.institution_type == InstitutionType.insurer
        alafco = (
            db.query(Institution)
            .filter(Institution.slug == "alafco-aviation-lease-and-finance-company")
            .one()
        )
        assert alafco.institution_type == InstitutionType.leasing
        # An unconfirmed row still has NULL — loader never guesses.
        sabic = db.query(Institution).filter(Institution.slug == "sabic").one()
        assert sabic.institution_type is None
    finally:
        db.close()
