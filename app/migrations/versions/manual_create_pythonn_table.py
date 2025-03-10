"""manual_create_pythonn_table

Revision ID: manual_create_pythonn_table
Revises: manual_create_interview_tables
Create Date: 2025-03-11 01:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'manual_create_pythonn_table'
down_revision: Union[str, None] = 'manual_create_interview_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создаем таблицу pythonn
    op.create_table('pythonn',
        sa.Column('id', sa.Float(), nullable=False),
        sa.Column('chance', sa.Float(), nullable=True),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('tag', sa.Text(), nullable=True),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pythonn_id'), 'pythonn', ['id'], unique=False)
    
    # Добавляем внешний ключ от user_answers.question_id к pythonn.id
    op.create_foreign_key(
        'user_answers_question_id_fkey',
        'user_answers', 'pythonn',
        ['question_id'], ['id']
    )


def downgrade() -> None:
    # Удаляем внешний ключ
    op.drop_constraint('user_answers_question_id_fkey', 'user_answers', type_='foreignkey')
    
    # Удаляем таблицу pythonn
    op.drop_index(op.f('ix_pythonn_id'), table_name='pythonn')
    op.drop_table('pythonn') 