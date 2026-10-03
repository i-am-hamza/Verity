from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args)
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
