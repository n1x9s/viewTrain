"""Cleanup users table

Revision ID: cleanup_users_table
Revises: 1a8ce7aee925
Create Date: 2025-03-05 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cleanup_users_table'
down_revision: Union[str, None] = '1a8ce7aee925'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Удаляем все записи из таблицы users
    op.execute('TRUNCATE TABLE users CASCADE')


def downgrade() -> None:
    pass 