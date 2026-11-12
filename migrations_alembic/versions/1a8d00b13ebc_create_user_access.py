"""create user access

Revision ID: 1a8d00b13ebc
Revises: 3c77319147d9
Create Date: 2026-11-10 17:12:22.508738

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a8d00b13ebc'
down_revision: Union[str, Sequence[str], None] = '3c77319147d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'template_access',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('template_id', sa.Integer(),
                  sa.ForeignKey('templates.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Integer(),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('granted_at', sa.TIMESTAMP(timezone=True),
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('template_id', 'user_id', name='uq_template_access')
    )
    op.create_index('idx_template_access_user', 'template_access', ['user_id'])

def downgrade():
    op.drop_index('idx_template_access_user', table_name='template_access')
    op.drop_table('template_access')