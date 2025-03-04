"""Add hashed_password column to users table

Revision ID: 1c6d7302b37f
Revises: cleanup_users_table
Create Date: 2025-03-05 00:50:15.513017

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1c6d7302b37f'
down_revision: Union[str, None] = 'cleanup_users_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем колонку hashed_password
    op.add_column('users', sa.Column('hashed_password', sa.String(), nullable=False))
    
    # Удаляем колонку password
    op.drop_column('users', 'password')


def downgrade() -> None:
    # Восстанавливаем колонку password
    op.add_column('users', sa.Column('password', sa.String(), nullable=False))
    
    # Удаляем колонку hashed_password
    op.drop_column('users', 'hashed_password')
