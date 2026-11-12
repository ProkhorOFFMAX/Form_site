"""create response_history table

Revision ID: b50d76b7de8e
Revises: 1a8d00b13ebc
Create Date: 2026-11-12 16:42:23.715644

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b50d76b7de8e'
down_revision: Union[str, Sequence[str], None] = '1a8d00b13ebc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'response_history',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('response_id', sa.Integer(),
                  sa.ForeignKey('responses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('changed_by', sa.Integer(),
                  sa.ForeignKey('users.id'), nullable=False),
        sa.Column('changed_at', sa.TIMESTAMP(timezone=True),
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('field_id', sa.String(50), nullable=False),
        sa.Column('old_value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_value', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('change_reason', sa.String(500), nullable=True)
    )
    op.create_index('idx_response_history_response', 'response_history', ['response_id'])


def downgrade():
    op.drop_index('idx_response_history_response', table_name='response_history')
    op.drop_table('response_history')
