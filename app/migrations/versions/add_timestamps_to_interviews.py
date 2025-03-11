"""add_timestamps_to_interviews

Revision ID: add_timestamps_to_interviews
Revises: manual_add_user_interview_id
Create Date: 2025-03-11 08:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision: str = 'add_timestamps_to_interviews'
down_revision: Union[str, None] = 'manual_add_user_interview_id'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем поля created_at и updated_at
    op.add_column('interviews', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.add_column('interviews', sa.Column('updated_at', sa.DateTime(), nullable=True))
    
    # Устанавливаем текущее время для существующих записей
    op.execute("""
    UPDATE interviews 
    SET created_at = now(),
        updated_at = now()
    WHERE created_at IS NULL
    """)
    
    # Делаем поля not null
    op.alter_column('interviews', 'created_at',
                    existing_type=sa.DateTime(),
                    nullable=False)
    op.alter_column('interviews', 'updated_at',
                    existing_type=sa.DateTime(),
                    nullable=False)


def downgrade() -> None:
    # Удаляем поля created_at и updated_at
    op.drop_column('interviews', 'updated_at')
    op.drop_column('interviews', 'created_at') 