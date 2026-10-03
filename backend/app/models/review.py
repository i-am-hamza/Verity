"""Session 7: human reviews of individual match-evidence rows.

Append-only: once a reviewer records a verdict for an evidence row, we
update the existing row (verdict + reviewer + reviewed_at) rather than
accumulating multiple review entries per row. The dashboard precision
chart is a running tally of unique-evidence verdicts, so this schema is
intentionally one-row-per-evidence.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MatchReview(Base):
    __tablename__ = "match_reviews"
    __table_args__ = (
        UniqueConstraint("evidence_id", name="uq_match_reviews_evidence_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    evidence_id: Mapped[int] = mapped_column(
        ForeignKey("match_evidence.id"), nullable=False, index=True
    )
    reviewer: Mapped[str] = mapped_column(String, nullable=False)
    verdict: Mapped[str] = mapped_column(String, nullable=False)
    # ISO 8601 UTC timestamp of the review.
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
