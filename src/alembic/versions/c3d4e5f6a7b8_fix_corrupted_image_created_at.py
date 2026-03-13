"""Fix image_created_at values corrupted to year-only integers

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-13 00:02:00.000000

A previous version of migration b2c3d4e5f6a7 used batch_alter_table
alter_column which caused SQLite's DATETIME numeric affinity to coerce
string values to integers (just the year) during the table copy. This
migration nulls out any values that were corrupted to a bare 4-digit year.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # A corrupted value is a bare year integer (4 digits, e.g. 2026).
    # NULL these out — they've lost their original data and are unusable.
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE diun_updates
        SET image_created_at = NULL
        WHERE image_created_at IS NOT NULL
          AND CAST(image_created_at AS TEXT) GLOB '[0-9][0-9][0-9][0-9]'
    """))


def downgrade() -> None:
    pass
