"""adding intersection columns

Revision ID: c5d5e94fb059
Revises: 333a785776cd
Create Date: 2026-02-10 15:27:18.724028

"""

# revision identifiers, used by Alembic.
revision = 'c5d5e94fb059'
down_revision = '333a785776cd'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Add intersection fields
    op.add_column("markers", sa.Column("intersection", sa.Integer(), nullable=True))
    op.add_column("markers", sa.Column("intersection_hebrew", sa.Text(), nullable=True))

    op.add_column("markers_hebrew", sa.Column("intersection", sa.Integer(), nullable=True))
    op.add_column("markers_hebrew", sa.Column("intersection_hebrew", sa.Text(), nullable=True))

    op.add_column("vehicles_markers_hebrew", sa.Column("intersection", sa.Integer(), nullable=True))
    op.add_column("vehicles_markers_hebrew", sa.Column("intersection_hebrew", sa.Text(), nullable=True))


def downgrade():
    # Remove intersection fields
    op.drop_column("vehicles_markers_hebrew", "intersection_hebrew")
    op.drop_column("vehicles_markers_hebrew", "intersection")

    op.drop_column("markers_hebrew", "intersection_hebrew")
    op.drop_column("markers_hebrew", "intersection")

    op.drop_column("markers", "intersection_hebrew")
    op.drop_column("markers", "intersection")