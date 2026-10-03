from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

# The three ESG pillars. A Category always rolls up into exactly one of
# these. Today there's a 1:1 mapping (one category per pillar), but the
# schema supports splitting a pillar into several categories later
# (e.g. Governance -> "Board & Ethics" + "Internal Controls" + "IT & Security")
# without any migration — pillar aggregation groups by this field, not by
# category identity.
PILLARS = ("Environmental", "Social", "Governance")


class Category(Base):
    """A scoring dimension. Currently one per ESG pillar (Environmental,
    Social, Governance); can be split into finer sub-categories later."""
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    pillar: Mapped[str] = mapped_column(String, nullable=False)  # one of PILLARS
    weight: Mapped[float] = mapped_column(default=1.0)

    terms: Mapped[list[Term]] = relationship(
        "Term", back_populates="category", cascade="all, delete-orphan"
    )


class Term(Base):
    """A single word/phrase tracked within a category."""
    __tablename__ = "terms"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    phrase: Mapped[str] = mapped_column(String, nullable=False)
    weight: Mapped[float] = mapped_column(default=1.0)
    # match "governed/governing/governance" as one hit
    lemma_based: Mapped[bool] = mapped_column(default=True)

    category: Mapped[Category] = relationship("Category", back_populates="terms")


class TaxonomyVersion(Base):
    """Snapshot of the taxonomy at a point in time, identified by a stable hash.

    The hash is sha256 of the canonical JSON of (category name, pillar,
    weight, terms[phrase, weight, lemma_based]) — see
    app.services.taxonomy_hash.compute_taxonomy_hash — so two taxonomies
    with the same content but different key ordering collapse to the same
    version. Any edit to a weight, term or lemma flag produces a new row.

    Reprocessing a report under a new taxonomy_version APPENDS score rows;
    it never overwrites older ones. Queries take an explicit version and
    default to the latest by created_at.
    """
    __tablename__ = "taxonomy_versions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    hash: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
