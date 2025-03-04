"""remove_password_column

Revision ID: 6b6aabeb13de
Revises: 1c6d7302b37f
Create Date: 2025-03-05 00:58:15.513017

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6b6aabeb13de'
down_revision: Union[str, None] = '1c6d7302b37f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Удаляем колонку password
    op.drop_column('users', 'password')


def downgrade() -> None:
    # Восстанавливаем колонку password
    op.add_column('users', sa.Column('password', sa.String(), nullable=True))
