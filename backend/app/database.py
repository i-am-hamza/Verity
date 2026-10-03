from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


def _normalise_url(url: str) -> str:
    """Keep SQLite URLs untouched; rewrite bare `postgresql://` to the
    `postgresql+psycopg://` form so SQLAlchemy picks the psycopg 3 driver
    we actually install (not the legacy psycopg2 which is unmaintained
    and we deliberately don't ship). Session 9: lets production DATABASE_URL
    stay in the standard Postgres format Supabase hands out of the dashboard
    without the user needing to remember a driver prefix."""
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


DB_URL = _normalise_url(settings.database_url)


def _engine_kwargs(url: str) -> dict:
    """Build create_engine kwargs that are safe for the DSN we were handed.

    SQLite in this project is always file-backed and single-process, so
    we only need `check_same_thread=False`.

    For Postgres we assume Supabase's **transaction** pooler (port 6543),
    which is what the production DATABASE_URL points at. Transaction
    pooling means a given server-side connection is handed to a request
    at BEGIN and released at COMMIT, so prepared statements and
    session-scoped state do NOT survive across transactions. Two
    engine-level consequences:

    1. `prepare_threshold=None` on the psycopg3 connect args disables
       automatic prepared statements. Without this, psycopg3 attempts
       to re-use statement names (`_pg3_0`, …) across pooled connections
       and the pooler returns `DuplicatePreparedStatement` once a
       prepared statement from a previous session is already registered
       on the physical connection you were handed.

    2. `pool_pre_ping=True` + a short `pool_recycle` so SQLAlchemy's own
       pool quietly drops any connection the pooler has rotated out from
       under us. 1800 s = 30 min, well below Supabase's idle timeout
       and the pooler's connection-reuse window.

    These are belt-and-braces for pooler mode specifically; session-mode
    DSNs (port 5432) would be fine without either, but then the free
    plan's lower connection ceiling bites.
    """
    if url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    # Postgres (assumed pooler-mode in prod).
    return {
        "connect_args": {"prepare_threshold": None},
        "pool_pre_ping": True,
        "pool_recycle": 1800,
    }


engine = create_engine(DB_URL, **_engine_kwargs(DB_URL))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Root of the SQLAlchemy 2.0 declarative hierarchy — models inherit from this.

    Using DeclarativeBase (not the legacy declarative_base() call) keeps
    ORM attributes properly typed via Mapped[T], so mypy sees the runtime
    value on an instance rather than Column[T].
    """


def get_db():
    """FastAPI dependency — yields a DB session and guarantees it closes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Fine for the pilot; use Alembic migrations once
    the schema stabilizes and you're running against Postgres."""
    from app.models import (  # noqa: F401
        institution,
        provenance,
        report,
        score,
        taxonomy,
    )
    Base.metadata.create_all(bind=engine)
