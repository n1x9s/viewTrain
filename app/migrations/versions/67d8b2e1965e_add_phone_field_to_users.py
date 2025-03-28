"""add phone field to users

Revision ID: 67d8b2e1965e
Revises: e691b5ae077e
Create Date: 2025-03-28 18:31:48.353525

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '67d8b2e1965e'
down_revision: Union[str, None] = 'e691b5ae077e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
