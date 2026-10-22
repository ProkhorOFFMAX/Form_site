"""create initial tables

Revision ID: ce3be7f789af
Revises: 
Create Date: 2026-10-22 17:30:00.221933

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'ce3be7f789af'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'templates',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('fields', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    # GIN-индекс для JSONB
    op.create_index(
        'idx_templates_fields',
        'templates',
        ['fields'],
        postgresql_using='gin'
    )

    op.create_table(
        'responses',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('template_id', sa.Integer(), sa.ForeignKey('templates.id', ondelete='CASCADE'), nullable=False),
        sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('submitted_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    pass


def downgrade() -> None:
    op.drop_table('responses')
    op.drop_index('idx_templates_fields', table_name='templates')
    op.drop_table('templates')
    pass