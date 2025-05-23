"""add_question_type_columns

Revision ID: a5b3c4d5e6f7
Revises: 6b6aabeb13de
Create Date: 2025-05-19 20:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a5b3c4d5e6f7"
down_revision = "6b6aabeb13de"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Добавляем колонку question_type в таблицу interviews, если она еще не существует
    op.execute(
        "ALTER TABLE interviews ADD COLUMN IF NOT EXISTS question_type VARCHAR DEFAULT 'pythonn' NOT NULL"
    )

    # Проверяем наличие колонки question_type в таблице user_answers и добавляем ее, если она не существует
    op.execute(
        "ALTER TABLE user_answers ADD COLUMN IF NOT EXISTS question_type VARCHAR DEFAULT 'pythonn' NOT NULL"
    )


def downgrade() -> None:
    # Удаляем колонку question_type из таблицы interviews
    op.drop_column("interviews", "question_type")

    # Удаляем колонку question_type из таблицы user_answers
    op.drop_column("user_answers", "question_type")
