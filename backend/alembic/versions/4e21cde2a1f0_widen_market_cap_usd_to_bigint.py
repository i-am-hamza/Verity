"""widen institutions.market_cap_usd to BIGINT

Revision ID: 4e21cde2a1f0
Revises: aa84e886807c
Create Date: 2026-10-04 00:00:00.000000

Session 9: Saudi Aramco's market cap (≈ 1.9 × 10^12 USD) overflows the
original INTEGER (int32) column on Postgres. SQLite's INTEGER was
variable-width so this latent bug surfaced only when migrating. BIGINT
is 8 bytes on Postgres and still fits the SQLAlchemy `Mapped[int]`
type, so no model surgery is needed beyond the explicit `BigInteger`
column spec.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "4e21cde2a1f0"
down_revision: Union[str, Sequence[str], None] = "aa84e886807c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("institutions") as batch_op:
        batch_op.alter_column(
            "market_cap_usd",
            existing_type=sa.Integer(),
            type_=sa.BigInteger(),
            existing_nullable=True,
        )


def downgrade() -> None:
    with op.batch_alter_table("institutions") as batch_op:
        batch_op.alter_column(
            "market_cap_usd",
            existing_type=sa.BigInteger(),
            type_=sa.Integer(),
            existing_nullable=True,
        )
