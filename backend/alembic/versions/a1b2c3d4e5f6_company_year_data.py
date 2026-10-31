"""company_year_data

Revision ID: a1b2c3d4e5f6
Revises: b1e9f2a3c4d5
Create Date: 2026-10-31 00:00:00.000000

Adds company_year_data: one row per (active institution, fiscal_year) with
board size (read from the annual report by the researcher) and firm ages
(researcher-supplied). Neither is part of the Verity ESG score; stored
separately for that reason.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'b1e9f2a3c4d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


BASIS_ENUM = sa.Enum(
    'stated_number_and_list', 'list', 'report_date', 'not_found',
    name='boardsizebasis',
)
CONFIDENCE_ENUM = sa.Enum('high', 'low', name='boardsizeconfidence')


def upgrade() -> None:
    op.create_table(
        'company_year_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institution_id', sa.Integer(), nullable=False),
        sa.Column('fiscal_year', sa.Integer(), nullable=False),
        sa.Column('board_size', sa.Integer(), nullable=True),
        sa.Column('board_size_basis', BASIS_ENUM, nullable=False,
                  server_default='not_found'),
        sa.Column('board_size_confidence', CONFIDENCE_ENUM, nullable=False,
                  server_default='low'),
        sa.Column('board_size_pages', sa.String(), nullable=True),
        sa.Column('board_size_names', sa.JSON(), nullable=True),
        sa.Column('board_size_stated_number', sa.Integer(), nullable=True),
        sa.Column('board_size_list_count', sa.Integer(), nullable=True),
        sa.Column('board_size_flag', sa.String(), nullable=True),
        sa.Column('board_size_note', sa.Text(), nullable=True),
        sa.Column('board_size_method', sa.String(), nullable=True),
        sa.Column('age_since_established', sa.Integer(), nullable=True),
        sa.Column('age_since_listed', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('institution_id', 'fiscal_year',
                            name='uq_cyd_inst_year'),
    )
    op.create_index(op.f('ix_company_year_data_id'), 'company_year_data',
                    ['id'], unique=False)
    op.create_index(op.f('ix_company_year_data_institution_id'),
                    'company_year_data', ['institution_id'], unique=False)
    op.create_index(op.f('ix_company_year_data_fiscal_year'),
                    'company_year_data', ['fiscal_year'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_company_year_data_fiscal_year'),
                  table_name='company_year_data')
    op.drop_index(op.f('ix_company_year_data_institution_id'),
                  table_name='company_year_data')
    op.drop_index(op.f('ix_company_year_data_id'),
                  table_name='company_year_data')
    op.drop_table('company_year_data')
    BASIS_ENUM.drop(op.get_bind(), checkfirst=True)
    CONFIDENCE_ENUM.drop(op.get_bind(), checkfirst=True)
