"""Add unique constraint on (hostname, image_name) for atomic upsert

Revision ID: a1b2c3d4e5f6
Revises: f62e201ae66b
Create Date: 2026-03-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f62e201ae66b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Deduplicate: keep the latest record for each (hostname, image_name) pair
    conn = op.get_bind()
    conn.execute(sa.text("""
        DELETE FROM diun_updates
        WHERE id NOT IN (
            SELECT MAX(id) FROM diun_updates
            GROUP BY hostname, image_name
        )
    """))

    with op.batch_alter_table('diun_updates') as batch_op:
        batch_op.create_unique_constraint('uq_hostname_image_name', ['hostname', 'image_name'])


def downgrade() -> None:
    with op.batch_alter_table('diun_updates') as batch_op:
        batch_op.drop_constraint('uq_hostname_image_name', type_='unique')
