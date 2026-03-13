"""Change image_created_at from String to DateTime

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-13 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert ISO 8601 strings (e.g. "2020-03-26T12:23:56Z") to the format
    # SQLAlchemy expects for SQLite DateTime ("2020-03-26 12:23:56").
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE diun_updates
        SET image_created_at = REPLACE(REPLACE(image_created_at, 'T', ' '), 'Z', '')
        WHERE image_created_at IS NOT NULL
    """))

    with op.batch_alter_table('diun_updates') as batch_op:
        batch_op.alter_column(
            'image_created_at',
            existing_type=sa.String(),
            type_=sa.DateTime(),
            existing_nullable=True,
        )


def downgrade() -> None:
    with op.batch_alter_table('diun_updates') as batch_op:
        batch_op.alter_column(
            'image_created_at',
            existing_type=sa.DateTime(),
            type_=sa.String(),
            existing_nullable=True,
        )
