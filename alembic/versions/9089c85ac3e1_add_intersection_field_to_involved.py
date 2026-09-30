"""add intersection field to involved and index on intersection fields

Revision ID: 9089c85ac3e1
Revises: c1a2b3d4e5f6
Create Date: 2026-09-28 10:16:50.837408

"""

# revision identifiers, used by Alembic.
revision = '9089c85ac3e1'
down_revision = 'c1a2b3d4e5f6'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

index_tables = ["involved_markers_hebrew", "markers_hebrew", "vehicles_markers_hebrew"]
fields = ["intersection", "intersection_hebrew"]

def upgrade():
    # Add intersection fields
    op.add_column("involved_markers_hebrew", sa.Column("intersection", sa.Integer(), nullable=True))
    op.add_column("involved_markers_hebrew", sa.Column("intersection_hebrew", sa.Text(), nullable=True))

    for table in index_tables:
        op.create_index(f'ix_{table}_intersection',
                        table,
                        ['intersection'], unique=False
                        )


def downgrade():
    # Remove intersection fields
    for table in index_tables:
        op.drop_index(op.f(f'ix_{table}_intersection'), table_name=table)

    op.drop_column("involved_markers_hebrew", "intersection")
    op.drop_column("involved_markers_hebrew", "intersection_hebrew")
