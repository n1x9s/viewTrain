"""manual_add_user_interview_id

Revision ID: manual_add_user_interview_id
Revises: manual_add_question_ids
Create Date: 2025-03-11 03:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'manual_add_user_interview_id'
down_revision: Union[str, None] = 'manual_add_question_ids'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем поле user_interview_id в таблицу interviews
    op.add_column('interviews', sa.Column('user_interview_id', sa.Integer(), nullable=True))
    
    # Обновляем существующие записи, устанавливая user_interview_id
    # Для каждого пользователя нумеруем его интервью по порядку
    op.execute("""
    WITH numbered_interviews AS (
        SELECT 
            id, 
            user_id, 
            ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY id) as row_num
        FROM interviews
    )
    UPDATE interviews
    SET user_interview_id = numbered_interviews.row_num
    FROM numbered_interviews
    WHERE interviews.id = numbered_interviews.id;
    """)


def downgrade() -> None:
    # Удаляем поле user_interview_id из таблицы interviews
    op.drop_column('interviews', 'user_interview_id') 