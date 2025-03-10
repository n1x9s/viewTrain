"""manual_recreate_tables

Revision ID: manual_recreate_tables
Revises: manual_create_interview_tables
Create Date: 2025-03-11 01:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'manual_recreate_tables'
down_revision: Union[str, None] = 'manual_create_interview_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Удаляем таблицу user_answers, если она существует
    op.execute("DROP TABLE IF EXISTS user_answers")
    
    # Создаем таблицу pythonn
    op.execute("""
    CREATE TABLE IF NOT EXISTS pythonn (
        id DOUBLE PRECISION PRIMARY KEY,
        chance DOUBLE PRECISION,
        question TEXT NOT NULL,
        tag TEXT,
        answer TEXT NOT NULL,
        created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL,
        updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL
    )
    """)
    
    # Создаем индекс для pythonn.id
    op.execute("CREATE INDEX IF NOT EXISTS ix_pythonn_id ON pythonn (id)")
    
    # Создаем таблицу user_answers с правильным типом для question_id
    op.execute("""
    CREATE TABLE IF NOT EXISTS user_answers (
        id SERIAL PRIMARY KEY,
        interview_id INTEGER NOT NULL REFERENCES interviews(id),
        question_id DOUBLE PRECISION NOT NULL REFERENCES pythonn(id),
        user_answer TEXT NOT NULL,
        score DOUBLE PRECISION,
        feedback TEXT,
        created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL,
        updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL
    )
    """)
    
    # Создаем индекс для user_answers.id
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_answers_id ON user_answers (id)")


def downgrade() -> None:
    # Удаляем таблицы в обратном порядке
    op.execute("DROP TABLE IF EXISTS user_answers")
    op.execute("DROP TABLE IF EXISTS pythonn") 