"""create reference_text

Revision ID: 689c78c454d0
Revises: 7046456d3280
Create Date: 2026-11-09 15:09:33.998322

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# Поля со словарями. Заполнять словарь заранее не обязательно. Заполнение может происходить с ошибками
# Новые значения могут сохраняться в словарь
# revision identifiers, used by Alembic.
revision: str = '689c78c454d0'
down_revision: Union[str, Sequence[str], None] = '7046456d3280'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Словари
    op.create_table(
        'reference_dicts',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    # Значения словарей
    op.create_table(
        'reference_items',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('dict_id', sa.Integer(),
                  sa.ForeignKey('reference_dicts.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('label', sa.String(500), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('dict_id', 'label', name='uq_reference_items_dict_label') #UNIQUE(dict_id, label)
    )
    #Индекс ускоряет чтение из БД - будут найдены строки для нужного словаря без просмотра всей таблицы
    op.create_index('idx_reference_items_dict_id', 'reference_items', ['dict_id'])

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_reference_items_dict_id', table_name='reference_items')
    op.drop_table('reference_items')
    op.drop_table('reference_dicts')

