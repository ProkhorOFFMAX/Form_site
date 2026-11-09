"""create users

Revision ID: 3c77319147d9
Revises: 689c78c454d0
Create Date: 2026-11-09 20:42:05.210437

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c77319147d9'
down_revision: Union[str, Sequence[str], None] = '689c78c454d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1. Таблица пользователей
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(256), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, server_default='user'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True),
                  server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    # 2. Привязка заявок к пользователю
    op.add_column('responses', sa.Column('user_id', sa.Integer(),
                                         sa.ForeignKey('users.id'), nullable=True))
    op.create_index('idx_responses_user_id', 'responses', ['user_id'])


def downgrade():
    op.drop_index('idx_responses_user_id', table_name='responses')
    op.drop_column('responses', 'user_id')
    op.drop_table('users')