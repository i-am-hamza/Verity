from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.institution import Institution
    from app.models.provenance import SourceDocument
    from app.models.score import CategoryScore, MatchEvidence


class ReportStatus(enum.StrEnum):
    uploaded = "uploaded"
    processing = "processing"
    scored = "scored"
    error = "error"


class Report(Base):
    """One PROCESSED source_document, under one taxonomy_version and one
    pipeline_version. Reprocessing a source_document under a new version
    adds a new Report row rather than mutating the previous one — old
    scores stay intact so cross-version comparisons are possible.
    """
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    institution_id: Mapped[int] = mapped_column(ForeignKey("institutions.id"), nullable=False)
    # source_document is nullable during migration from legacy single-file
    # uploads; new pipeline runs must always attach one.
    source_document_id: Mapped[int | None] = mapped_column(
        ForeignKey("source_documents.id"), nullable=True, index=True
    )
    fiscal_year: Mapped[int] = mapped_column(nullable=False)
    language: Mapped[str] = mapped_column(String, default="en")  # en, ar, bilingual
    file_path: Mapped[str] = mapped_column(String, nullable=False)

    total_word_count: Mapped[int] = mapped_column(default=0)
    # Latin-script tokens only. Density uses this: Arabic text must not
    # dilute an English taxonomy (see CLAUDE.md, Method).
    latin_word_count: Mapped[int] = mapped_column(default=0)
    arabic_word_count: Mapped[int] = mapped_column(default=0)
    page_count: Mapped[int] = mapped_column(default=0)
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus), default=ReportStatus.uploaded
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Version tags so scores from an older taxonomy/pipeline stay traceable.
    # taxonomy_version is a *display* string; the canonical version link is
    # via CategoryScore.taxonomy_version_id.
    taxonomy_version: Mapped[str | None] = mapped_column(String, nullable=True)
    pipeline_version: Mapped[str | None] = mapped_column(String, nullable=True)

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # --- Session 5 processing audit -----------------------------------------
    # Timings in seconds. extract/segment/match are the slow stages;
    # total_seconds includes DB write.
    extract_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    segment_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    match_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    # OCR cap bookkeeping. ocr_page_count is pages that actually went
    # through OCR (could be 0 if the report is natively text). ocr_page_ratio
    # is the fraction of pages that would have NEEDED OCR before the cap kicks
    # in — compared against config.ocr_max_page_ratio to decide heavily-scanned.
    ocr_page_count: Mapped[int] = mapped_column(default=0)
    ocr_page_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Text-quality switches: what was removed BEFORE matching ran.
    repeated_lines_removed: Mapped[int] = mapped_column(default=0)
    excluded_contents_pages: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    pages_mostly_arabic: Mapped[int] = mapped_column(default=0)

    # Financial-statements exclusion (Ferjancic et al. 2024, Patch A).
    # financial_statements_start_page is 1-indexed; everything from that
    # page onward was dropped from matching. Null means we did NOT detect
    # a boundary; if includes_financial_statements on SourceDocument is
    # true and this is null, the report is a detector miss → needs_review.
    financial_statements_start_page: Mapped[int | None] = mapped_column(nullable=True)
    financial_statements_excluded_pages: Mapped[int] = mapped_column(default=0)

    # Matching diagnostic. matches_count is longest-mode (what we scored).
    # all_mode_extra_matches is how many MORE the diagnostic all-mode would
    # have produced (overlapping nested-phrase hits). Logged, not scored.
    matches_count: Mapped[int] = mapped_column(default=0)
    all_mode_extra_matches: Mapped[int | None] = mapped_column(nullable=True)
    composite_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # v4 scoring fields -------------------------------------------------------
    # narrative_word_count: Latin words on the pages the matcher actually
    # searched (i.e. after text-quality cleaning: FS excluded, ToC excluded).
    # This is the denominator for all v4 density calculations.
    narrative_word_count: Mapped[int] = mapped_column(default=0)

    # Pillar densities: (sum of weighted core-term matches for pillar)
    # / narrative_word_count * 1000. None until scored.
    e_density: Mapped[float | None] = mapped_column(Float, nullable=True)
    s_density: Mapped[float | None] = mapped_column(Float, nullable=True)
    g_density: Mapped[float | None] = mapped_column(Float, nullable=True)

    # 0-10 rank scores across all 390 company-years pooled (ascending rank).
    # Set by compute_ranks.py after the full run completes.
    e_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    s_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    g_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    # composite_score repurposed as simple average(e_score, s_score, g_score).

    # Generic terms (ESG, sustainability, GRI, sustainable development, CSR):
    # counted separately, excluded from pillars and composite.
    generic_density: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Financial add-on terms: only populated for the 19 financial companies.
    addon_density: Mapped[float | None] = mapped_column(Float, nullable=True)
    addon_rank: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Report type carried from source_document for use as a control variable.
    report_type: Mapped[str | None] = mapped_column(String, nullable=True)

    # Processing review bookkeeping. The source_documents table also has a
    # review_status; this one is specific to the SCORING pass (e.g. an IQR
    # outlier that validated-fine but scored way off its cohort).
    processing_review_status: Mapped[str] = mapped_column(String, default="auto_ok")
    processing_review_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    institution: Mapped[Institution] = relationship("Institution", back_populates="reports")
    source_document: Mapped[SourceDocument | None] = relationship(
        "SourceDocument", back_populates="reports"
    )
    category_scores: Mapped[list[CategoryScore]] = relationship(
        "CategoryScore", back_populates="report", cascade="all, delete-orphan"
    )
    matches: Mapped[list[MatchEvidence]] = relationship(
        "MatchEvidence", back_populates="report", cascade="all, delete-orphan"
    )
