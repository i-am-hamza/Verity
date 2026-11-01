"""Company-year metrics that live outside the ESG score itself.

Governance (board size) and firm-age metrics are per (institution, fiscal_year),
not per Report row — a given fiscal year has only one authoritative value even
when the pipeline rescores the underlying PDF under a new taxonomy. Keeping
them in their own table also makes clear they are NOT part of the Verity ESG
score (the project rules Method).
"""
from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Enum, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.institution import Institution


class BoardSizeBasis(enum.StrEnum):
    stated_number_and_list = "stated_number_and_list"
    list = "list"
    report_date = "report_date"
    not_found = "not_found"
    researcher_review = "researcher_review"


class BoardSizeConfidence(enum.StrEnum):
    high = "high"
    low = "low"


class CompanyYearData(Base):
    """One row per (active institution, fiscal_year) in the 390-report pool.

    - board_size, basis, pages, names: read from the annual report by the
      researcher using the assisted-reading process (see docs/methodology/
      website_methodology.md). Not part of the ESG score.
    - age_since_established, age_since_listed: supplied by the researcher
      in incoming/company_ages_board_2020_2025.xlsx. Not part of the ESG
      score.
    """
    __tablename__ = "company_year_data"
    __table_args__ = (
        UniqueConstraint("institution_id", "fiscal_year", name="uq_cyd_inst_year"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    institution_id: Mapped[int] = mapped_column(
        ForeignKey("institutions.id"), nullable=False, index=True
    )
    fiscal_year: Mapped[int] = mapped_column(nullable=False, index=True)

    # Board size (read from the annual report).
    board_size: Mapped[int | None] = mapped_column(nullable=True)
    board_size_basis: Mapped[BoardSizeBasis] = mapped_column(
        Enum(BoardSizeBasis), nullable=False, default=BoardSizeBasis.not_found
    )
    board_size_confidence: Mapped[BoardSizeConfidence] = mapped_column(
        Enum(BoardSizeConfidence), nullable=False, default=BoardSizeConfidence.low
    )
    board_size_pages: Mapped[str | None] = mapped_column(String, nullable=True)
    board_size_names: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    board_size_stated_number: Mapped[int | None] = mapped_column(nullable=True)
    board_size_list_count: Mapped[int | None] = mapped_column(nullable=True)
    board_size_flag: Mapped[str | None] = mapped_column(String, nullable=True)
    board_size_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 'read'   — researcher read the annual report
    # 'pending' — awaiting researcher review (placeholder)
    board_size_method: Mapped[str | None] = mapped_column(String, nullable=True)

    # Firm ages (supplied by the researcher).
    age_since_established: Mapped[int | None] = mapped_column(nullable=True)
    age_since_listed: Mapped[int | None] = mapped_column(nullable=True)

    # Financials (supplied by the researcher). Not part of the ESG score.
    # Market cap, total assets and total liabilities are USD millions; EPS is
    # the local-currency per-share figure; leverage is debt/equity; net_margin,
    # roe and roa are percentages. tobins_q and price_to_book are derived in
    # the loader so the DB mirrors the research dataset.
    market_cap_usd_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    eps: Mapped[float | None] = mapped_column(Float, nullable=True)
    leverage: Mapped[float | None] = mapped_column(Float, nullable=True)
    net_margin: Mapped[float | None] = mapped_column(Float, nullable=True)
    roe: Mapped[float | None] = mapped_column(Float, nullable=True)
    roa: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_assets_usd_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_liabilities_usd_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    tobins_q: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_to_book: Mapped[float | None] = mapped_column(Float, nullable=True)

    institution: Mapped[Institution] = relationship(
        "Institution", back_populates="company_year_data"
    )
