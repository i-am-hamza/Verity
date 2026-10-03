"""Provenance model: where every PDF came from, why some are missing, and
what the crawler tried.

A Report (see app.models.report.Report) is one PROCESSED source_document,
scored under one pipeline_version and one taxonomy_version. The
source_document row is the immutable evidence that the file exists as far
as the pipeline is concerned (CLAUDE.md, data acquisition rule 6).
"""
from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.institution import Institution
    from app.models.report import Report


class ReportType(enum.StrEnum):
    annual = "annual"
    integrated = "integrated"
    sustainability = "sustainability"
    financial_statements = "financial_statements"
    other = "other"
    unknown = "unknown"


class SourceType(enum.StrEnum):
    # `crawler` = the institution's own IR page.
    # `exchange` = the listing exchange's disclosure portal (added by Patch A).
    # `wayback` = Wayback Machine capture, via the approved-ingest flow.
    # `manual` = human-dropped file or human-handed URL.
    # `targeted_search` = DEPRECATED. The stage and its CLI were removed —
    #   every public search endpoint we tried refused the honest UA, and
    #   CLAUDE.md rules 1/2 forbid credentials and evasion. The enum member
    #   stays only so the Postgres enum type (added by migration
    #   93a446552d20) doesn't need an irreversible drop. No code paths
    #   emit this value anymore and no SourceDocument rows carry it.
    crawler = "crawler"
    exchange = "exchange"
    wayback = "wayback"
    manual = "manual"
    targeted_search = "targeted_search"


class ReviewStatus(enum.StrEnum):
    auto_ok = "auto_ok"
    needs_review = "needs_review"
    rejected = "rejected"


class GapReason(enum.StrEnum):
    not_found = "not_found"
    blocked = "blocked"
    robots_disallowed = "robots_disallowed"
    year_mismatch = "year_mismatch"
    unreachable = "unreachable"
    other = "other"


class SourceDocument(Base):
    """One downloaded PDF, uniquely identified by its sha256.

    Provenance is separate from Report on purpose:
    - The same PDF can be reprocessed under multiple taxonomy/pipeline
      versions (each producing a Report row).
    - A file that a human rejects (wrong year, wrong company) still leaves
      a source_documents trace so we don't re-download it.
    """
    __tablename__ = "source_documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    institution_id: Mapped[int] = mapped_column(ForeignKey("institutions.id"), nullable=False)
    fiscal_year: Mapped[int] = mapped_column(nullable=False)
    report_type: Mapped[ReportType] = mapped_column(
        Enum(ReportType), default=ReportType.unknown
    )

    source: Mapped[SourceType] = mapped_column(Enum(SourceType), nullable=False)
    source_url: Mapped[str] = mapped_column(String, nullable=False)
    final_url: Mapped[str | None] = mapped_column(String, nullable=True)
    http_status: Mapped[int | None] = mapped_column(nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # sha256 is the identity of a file; every downstream step is keyed by it.
    sha256: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    bytes: Mapped[int] = mapped_column(nullable=False)
    content_type: Mapped[str | None] = mapped_column(String, nullable=True)
    page_count: Mapped[int | None] = mapped_column(nullable=True)
    includes_financial_statements: Mapped[bool | None] = mapped_column(nullable=True)

    file_path: Mapped[str] = mapped_column(String, nullable=False)

    review_status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus), default=ReviewStatus.needs_review
    )
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Session 6: colleague's hand-supplied reports supersede any earlier
    # source (crawler / wayback / manual) for the same (institution, FY).
    # The older row stays for audit trail; `superseded_by_id` points to
    # the authoritative newer SourceDocument. Batch runner filters out
    # anything with a non-null superseded_by_id so it isn't rescored.
    superseded_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("source_documents.id"), nullable=True, index=True
    )

    institution: Mapped[Institution] = relationship(
        "Institution", back_populates="source_documents"
    )
    reports: Mapped[list[Report]] = relationship(
        "Report", back_populates="source_document"
    )


class Gap(Base):
    """A year/institution combination we could not (or chose not to) obtain.
    One row per (institution_id, fiscal_year) — updated as the situation
    changes, not appended to."""
    __tablename__ = "gaps"
    __table_args__ = (UniqueConstraint("institution_id", "fiscal_year", name="uq_gap_inst_year"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    institution_id: Mapped[int] = mapped_column(ForeignKey("institutions.id"), nullable=False)
    fiscal_year: Mapped[int] = mapped_column(nullable=False)
    reason: Mapped[GapReason] = mapped_column(Enum(GapReason), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    tier_tried: Mapped[str | None] = mapped_column(String, nullable=True)
    next_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    institution: Mapped[Institution] = relationship("Institution", back_populates="gaps")


class CrawlLog(Base):
    """Append-only trace of what the crawler tried.

    Runs are grouped by run_id (any string the crawler picks — usually a
    timestamped uuid). One row per (url, action) so a failed run can be
    diffed against a subsequent successful one.
    """
    __tablename__ = "crawl_log"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    run_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    institution_id: Mapped[int | None] = mapped_column(
        ForeignKey("institutions.id"), nullable=True
    )
    url: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    outcome: Mapped[str] = mapped_column(String, nullable=False)
    at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    institution: Mapped[Institution | None] = relationship(
        "Institution", back_populates="crawl_log_entries"
    )
