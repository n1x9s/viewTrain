"""add_current_question_id_to_interviews

Revision ID: 32a8c1b7a322
Revises: manual_recreate_tables
Create Date: 2025-03-31 02:22:48.120390

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '32a8c1b7a322'
down_revision: Union[str, None] = 'manual_recreate_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
