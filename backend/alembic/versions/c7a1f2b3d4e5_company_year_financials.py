"""company_year_data: add financial columns

Revision ID: c7a1f2b3d4e5
Revises: b2c3d4e5f6a7
Create Date: 2026-11-01 00:00:00.000000

Adds the researcher-supplied financial measures to company_year_data so the
public research dataset and ESG & Financials analysis can be reproduced from
the database:

    market_cap_usd_m, eps, leverage, net_margin, roe, roa
        from incoming/Data_20_10_2026.xlsx (sheet "Ali Data"); applies the
        four researcher corrections before the DB write.
    total_assets_usd_m, total_liabilities_usd_m
        from incoming/company_assets_liabilities_2020_2025_USD.xlsx.
    tobins_q      = (market cap + total liabilities) / total assets
    price_to_book = market cap / (total assets - total liabilities), or NULL if
                    equity is zero or negative

All amounts are USD millions; the ratios are unitless.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c7a1f2b3d4e5"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_COLS = [
    ("market_cap_usd_m", sa.Float()),
    ("eps", sa.Float()),
    ("leverage", sa.Float()),
    ("net_margin", sa.Float()),
    ("roe", sa.Float()),
    ("roa", sa.Float()),
    ("total_assets_usd_m", sa.Float()),
    ("total_liabilities_usd_m", sa.Float()),
    ("tobins_q", sa.Float()),
    ("price_to_book", sa.Float()),
]


def upgrade() -> None:
    with op.batch_alter_table("company_year_data") as batch_op:
        for name, type_ in _COLS:
            batch_op.add_column(sa.Column(name, type_, nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("company_year_data") as batch_op:
        for name, _type in _COLS:
            batch_op.drop_column(name)
