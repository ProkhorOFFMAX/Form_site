"""create educational_institutions table

Revision ID: 0f004aa6a596
Revises: ce3be7f789af
Create Date: 2026-10-22 17:42:12.221747

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0f004aa6a596'
down_revision: Union[str, Sequence[str], None] = 'ce3be7f789af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'educational_institutions',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('full_name', sa.String(500), nullable=False),
        sa.Column('short_name', sa.String(100), nullable=False),
        sa.Column('type', sa.String(10), nullable=False),
        sa.CheckConstraint("type IN ('ГБОУ', 'ГБДОУ', 'ОДОД')", name='check_ei_type')
    )
    op.create_index('idx_ei_type', 'educational_institutions', ['type'])
    op.create_index('idx_ei_short_name', 'educational_institutions', ['short_name'])


def downgrade() -> None:
    op.drop_index('idx_ei_short_name', table_name='educational_institutions')
    op.drop_index('idx_ei_type', table_name='educational_institutions')
    op.drop_table('educational_institutions')
