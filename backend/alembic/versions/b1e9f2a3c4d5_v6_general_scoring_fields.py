"""v6_general_scoring_fields

Revision ID: b1e9f2a3c4d5
Revises: 4dac1c5bae78
Create Date: 2026-10-20 00:00:00.000000

Adds four columns to reports for taxonomy v6:
  general_density       — weighted General-pillar matches per 1,000 narrative words
  general_score         — 0-100 rank-normalised General score (set by compute_ranks.py)
  composite_3pillar     — robustness: composite from E/S/G only (0-100)
  composite_general_no_new3 — robustness: composite where General excludes
                               innovation/feedback/digital_services (0-100)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1e9f2a3c4d5'
down_revision: Union[str, Sequence[str], None] = '4dac1c5bae78'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('reports', schema=None) as batch_op:
        batch_op.add_column(sa.Column('general_density', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('general_score', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('composite_3pillar', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('composite_general_no_new3', sa.Float(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('reports', schema=None) as batch_op:
        batch_op.drop_column('composite_general_no_new3')
        batch_op.drop_column('composite_3pillar')
        batch_op.drop_column('general_score')
        batch_op.drop_column('general_density')
