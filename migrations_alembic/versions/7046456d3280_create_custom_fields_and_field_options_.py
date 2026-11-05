"""create custom_fields and field_options tables

Revision ID: 7046456d3280
Revises: 0f004aa6a596
Create Date: 2026-11-05 15:45:34.350795

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7046456d3280'
down_revision: Union[str, Sequence[str], None] = '0f004aa6a596'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Справочник переиспользуемых полей с вариантами ответов
    op.create_table(
        'custom_fields',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('label', sa.String(255), nullable=False),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    # Варианты ответов
    op.create_table(
        'field_options',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('field_id', sa.Integer(),
                  sa.ForeignKey('custom_fields.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('label', sa.String(255), nullable=False),
        sa.Column('sort_order', sa.Integer, nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    # Индекс для быстрого поиска варианта по полю
    op.create_index('idx_field_options_field_id', 'field_options', ['field_id'])



def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_field_options_field_id', table_name='field_options')
    op.drop_table('field_options')
    op.drop_table('custom_fields')
