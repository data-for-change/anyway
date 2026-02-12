"""removing cross columns from markers

Revision ID: 205025444ebe
Revises: 237ab8f171d0
Create Date: 2026-02-12 21:29:57.945021
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "205025444ebe"
down_revision = "237ab8f171d0"
branch_labels = None
depends_on = None


def upgrade():
    # markers
    op.drop_column("markers", "cross_location")
    op.drop_column("markers", "cross_direction")
    op.drop_column("markers", "didnt_cross")
    op.drop_column("markers", "cross_mode")

    # markers_hebrew
    op.drop_column("markers_hebrew", "cross_location")
    op.drop_column("markers_hebrew", "cross_direction")
    op.drop_column("markers_hebrew", "didnt_cross")
    op.drop_column("markers_hebrew", "cross_mode")

    op.drop_column("markers_hebrew", "cross_location_hebrew")
    op.drop_column("markers_hebrew", "cross_direction_hebrew")
    op.drop_column("markers_hebrew", "didnt_cross_hebrew")
    op.drop_column("markers_hebrew", "cross_mode_hebrew")

    # vehicles_markers_hebrew
    op.drop_column("vehicles_markers_hebrew", "cross_location")
    op.drop_column("vehicles_markers_hebrew", "cross_direction")
    op.drop_column("vehicles_markers_hebrew", "didnt_cross")
    op.drop_column("vehicles_markers_hebrew", "cross_mode")

    op.drop_column("vehicles_markers_hebrew", "cross_location_hebrew")
    op.drop_column("vehicles_markers_hebrew", "cross_direction_hebrew")
    op.drop_column("vehicles_markers_hebrew", "didnt_cross_hebrew")
    op.drop_column("vehicles_markers_hebrew", "cross_mode_hebrew")


def downgrade():
    # markers
    op.add_column("markers", sa.Column("cross_location", sa.Integer(), nullable=True))
    op.add_column("markers", sa.Column("cross_direction", sa.Integer(), nullable=True))
    op.add_column("markers", sa.Column("didnt_cross", sa.Integer(), nullable=True))
    op.add_column("markers", sa.Column("cross_mode", sa.Integer(), nullable=True))

    # markers_hebrew
    op.add_column("markers_hebrew", sa.Column("cross_location", sa.Integer(), nullable=True))
    op.add_column("markers_hebrew", sa.Column("cross_direction", sa.Integer(), nullable=True))
    op.add_column("markers_hebrew", sa.Column("didnt_cross", sa.Integer(), nullable=True))
    op.add_column("markers_hebrew", sa.Column("cross_mode", sa.Integer(), nullable=True))

    op.add_column("markers_hebrew", sa.Column("cross_location_hebrew", sa.Text(), nullable=True))
    op.add_column("markers_hebrew", sa.Column("cross_direction_hebrew", sa.Text(), nullable=True))
    op.add_column("markers_hebrew", sa.Column("didnt_cross_hebrew", sa.Text(), nullable=True))
    op.add_column("markers_hebrew", sa.Column("cross_mode_hebrew", sa.Text(), nullable=True))

    # vehicles_markers_hebrew
    op.add_column("vehicles_markers_hebrew", sa.Column("cross_location", sa.Integer(), nullable=True))
    op.add_column("vehicles_markers_hebrew", sa.Column("cross_direction", sa.Integer(), nullable=True))
    op.add_column("vehicles_markers_hebrew", sa.Column("didnt_cross", sa.Integer(), nullable=True))
    op.add_column("vehicles_markers_hebrew", sa.Column("cross_mode", sa.Integer(), nullable=True))

    op.add_column("vehicles_markers_hebrew", sa.Column("cross_location_hebrew", sa.Text(), nullable=True))
    op.add_column("vehicles_markers_hebrew", sa.Column("cross_direction_hebrew", sa.Text(), nullable=True))
    op.add_column("vehicles_markers_hebrew", sa.Column("didnt_cross_hebrew", sa.Text(), nullable=True))
    op.add_column("vehicles_markers_hebrew", sa.Column("cross_mode_hebrew", sa.Text(), nullable=True))
