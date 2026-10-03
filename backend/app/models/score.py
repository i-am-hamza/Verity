from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.report import Report
    from app.models.taxonomy import Category, TaxonomyVersion, Term


class CategoryScore(Base):
    """The score for one category, on one report, under one taxonomy/pipeline
    version. Reprocessing under a new version APPENDS a new row rather than
    overwriting — old scores stay traceable (CLAUDE.md, Method)."""
    __tablename__ = "category_scores"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)

    raw_weighted_count: Mapped[float] = mapped_column(default=0.0)
    density_per_1000_words: Mapped[float] = mapped_column(default=0.0)

    # Canonical version link (nullable during migration from legacy runs).
    taxonomy_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("taxonomy_versions.id"), nullable=True, index=True
    )
    # pipeline_version is a code constant (see app.services.pipeline.PIPELINE_VERSION),
    # bumped whenever cleaning or matching logic changes. Stored as a string
    # rather than a FK because there is no runtime table of pipeline versions.
    pipeline_version: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    # Legacy string mirror of taxonomy_version_id for humans reading rows.
    taxonomy_version: Mapped[str | None] = mapped_column(String, nullable=True)

    report: Mapped[Report] = relationship("Report", back_populates="category_scores")
    category: Mapped[Category] = relationship("Category")
    taxonomy_version_ref: Mapped[TaxonomyVersion | None] = relationship("TaxonomyVersion")

    __table_args__ = (
        Index("ix_category_scores_versioning", "report_id", "taxonomy_version_id", "pipeline_version"),
    )


class MatchEvidence(Base):
    """One matched occurrence of a term in a report under a specific
    (taxonomy_version, pipeline_version). Also append-only."""
    __tablename__ = "match_evidence"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), nullable=False)
    term_id: Mapped[int] = mapped_column(ForeignKey("terms.id"), nullable=False)

    page_number: Mapped[int] = mapped_column(nullable=False)
    sentence_text: Mapped[str] = mapped_column(String, nullable=False)

    taxonomy_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("taxonomy_versions.id"), nullable=True, index=True
    )
    pipeline_version: Mapped[str | None] = mapped_column(String, nullable=True, index=True)

    report: Mapped[Report] = relationship("Report", back_populates="matches")
    term: Mapped[Term] = relationship("Term")
    taxonomy_version_ref: Mapped[TaxonomyVersion | None] = relationship("TaxonomyVersion")
