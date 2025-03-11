"""manual_add_question_ids

Revision ID: manual_add_question_ids
Revises: manual_create_interview_tables
Create Date: 2025-03-11 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'manual_add_question_ids'
down_revision: Union[str, None] = 'manual_create_interview_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем поле question_ids в таблицу interviews
    op.add_column('interviews', sa.Column('question_ids', sa.Text(), nullable=True))


def downgrade() -> None:
    # Удаляем поле question_ids из таблицы interviews
    op.drop_column('interviews', 'question_ids') 