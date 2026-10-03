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
connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}

engine = create_engine(DB_URL, connect_args=connect_args)
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
