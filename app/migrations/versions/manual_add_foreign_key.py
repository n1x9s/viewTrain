"""manual_add_foreign_key

Revision ID: manual_add_foreign_key
Revises: manual_create_interview_tables
Create Date: 2025-03-11 01:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'manual_add_foreign_key'
down_revision: Union[str, None] = 'manual_create_interview_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем внешний ключ от user_answers.question_id к pythonn.id
    # Обратите внимание, что оба поля имеют тип double precision (Float)
    op.create_foreign_key(
        'user_answers_question_id_fkey',
        'user_answers', 'pythonn',
        ['question_id'], ['id']
    )


def downgrade() -> None:
    # Удаляем внешний ключ
    op.drop_constraint('user_answers_question_id_fkey', 'user_answers', type_='foreignkey') 