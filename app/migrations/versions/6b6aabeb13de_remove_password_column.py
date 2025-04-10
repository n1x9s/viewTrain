"""Remove password column

Revision ID: 6b6aabeb13de
Revises: 32a8c1b7a322
Create Date: 2025-03-05 00:50:15.513017

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6b6aabeb13de"
down_revision: Union[str, None] = "32a8c1b7a322"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Проверяем существование колонки password перед удалением
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col["name"] for col in inspector.get_columns("users")]

    if "password" in columns:
        op.drop_column("users", "password")


def downgrade() -> None:
    # Добавляем обратно колонку password
    op.add_column("users", sa.Column("password", sa.String(), nullable=False))
