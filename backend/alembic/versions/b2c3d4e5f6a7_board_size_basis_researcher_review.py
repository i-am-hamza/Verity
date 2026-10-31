"""add 'researcher_review' to BoardSizeBasis enum

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-10-31 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Append a new value to the boardsizebasis Postgres enum."""
    # ALTER TYPE ... ADD VALUE must run outside a transaction block.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE boardsizebasis ADD VALUE IF NOT EXISTS 'researcher_review'")


def downgrade() -> None:
    """No safe downgrade — Postgres cannot drop enum members without rebuilding
    the type and every column that uses it, and no committed rows should carry
    the new value at downgrade time anyway. Leave the extra member in place."""
