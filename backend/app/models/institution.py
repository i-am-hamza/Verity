from __future__ import annotations

import enum
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Date, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.provenance import CrawlLog, Gap, SourceDocument
    from app.models.report import Report


class InstitutionType(enum.StrEnum):
    """Nullable in the DB — populated only from confirmed rows in
    data/institution_types_proposed.csv, never guessed silently."""
    bank = "bank"
    insurer = "insurer"
    investment_holding = "investment_holding"
    leasing = "leasing"
    other = "other"


class Wave(enum.StrEnum):
    financial = "financial"
    other = "other"


class Institution(Base):
    __tablename__ = "institutions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    country: Mapped[str] = mapped_column(String, nullable=False)
    # Retained for the legacy read path (crawler config, older code).
    # For the current dataset use industry + institution_type instead.
    sector: Mapped[str] = mapped_column(String, default="banking")

    # Fields sourced from data/List of Companies.xlsx.
    rank: Mapped[int | None] = mapped_column(nullable=True, unique=True)
    ticker: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    # BIGINT because Saudi Aramco's market cap (≈ 1.9T USD) overflows int32
    # on Postgres. SQLite's INTEGER is variable-width so this was invisible
    # until Session 9's Postgres migration.
    market_cap_usd: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    market_cap_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    industry: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    # slug is populated by seed/load_institutions.py from the company name;
    # Session 4 relies on it in dozens of places. Non-null at the type level.
    slug: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    is_financial: Mapped[bool] = mapped_column(default=False)
    wave: Mapped[Wave] = mapped_column(Enum(Wave), default=Wave.other, index=True)
    institution_type: Mapped[InstitutionType | None] = mapped_column(
        Enum(InstitutionType), nullable=True
    )
    # Session 6 scope correction: 5 of the original 65 institutions were
    # dropped from the active universe. Their rows stay for audit (prior
    # scored reports, Wayback picks, Gap rows) but any downstream query
    # that cares about "active universe" filters on this flag.
    active: Mapped[bool] = mapped_column(default=True, index=True)

    # v4 materiality: SASB industry from Verity_SASB_Mapping_Signed.xlsx.
    # Used at scoring time to decide which SASB categories are material
    # (weight 1.5) vs non-material (weight 1.0) for this institution.
    sasb_industry: Mapped[str | None] = mapped_column(String, nullable=True, index=True)

    reports: Mapped[list[Report]] = relationship(
        "Report", back_populates="institution", cascade="all, delete-orphan"
    )
    source_documents: Mapped[list[SourceDocument]] = relationship(
        "SourceDocument", back_populates="institution", cascade="all, delete-orphan"
    )
    gaps: Mapped[list[Gap]] = relationship(
        "Gap", back_populates="institution", cascade="all, delete-orphan"
    )
    crawl_log_entries: Mapped[list[CrawlLog]] = relationship(
        "CrawlLog", back_populates="institution", cascade="all, delete-orphan"
    )
