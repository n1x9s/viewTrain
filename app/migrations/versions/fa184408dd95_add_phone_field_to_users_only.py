"""add phone field to users only

Revision ID: fa184408dd95
Revises: 584e7b9763a8
Create Date: 2025-03-28 18:32:13.782654

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fa184408dd95'
down_revision: Union[str, None] = '584e7b9763a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
