"""add non_urban_intersection indexes

Revision ID: fe08b885a23f
Revises: 7ea883c8a245
Create Date: 2023-12-22 07:18:15.227413

"""

# revision identifiers, used by Alembic.
revision = 'fe08b885a23f'
down_revision = '7ea883c8a245'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


tables = ["vehicles_markers_hebrew", "involved_markers_hebrew", "markers_hebrew"]


def upgrade():
    for table in tables:
        op.create_index(f'ix_{table}_non_urban_intersection',
                        table,
                        ['non_urban_intersection'], unique=False
                        )


def downgrade():
    for table in tables:
        op.drop_index(op.f(f'ix_{table}_non_urban_intersection'), table_name=table)
