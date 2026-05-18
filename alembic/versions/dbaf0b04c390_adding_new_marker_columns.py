"""adding new marker columns

Revision ID: dbaf0b04c390
Revises: 205025444ebe
Create Date: 2026-02-13 20:59:31.150034
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "dbaf0b04c390"
down_revision = "205025444ebe"
branch_labels = None
depends_on = None


def upgrade():
    # markers (AccidentMarker)
    op.add_column("markers", sa.Column("yishuv2_symbol", sa.Integer(), nullable=True))
    op.add_column("markers", sa.Column("yishuv2_name", sa.Text(), nullable=True))
    op.add_column("markers", sa.Column("entrance_exit", sa.Integer(), nullable=True))
    op.add_column("markers", sa.Column("road_alignment", sa.Integer(), nullable=True))
    op.add_column("markers", sa.Column("road_geometry", sa.Integer(), nullable=True))
    op.add_column("markers", sa.Column("infrastructure_type", sa.Integer(), nullable=True))

    # markers_hebrew (AccidentMarkerView)
    op.add_column("markers_hebrew", sa.Column("yishuv2_symbol", sa.Integer(), nullable=True))
    op.add_column("markers_hebrew", sa.Column("yishuv2_name", sa.Text(), nullable=True))
    op.add_column("markers_hebrew", sa.Column("entrance_exit", sa.Integer(), nullable=True))
    op.add_column("markers_hebrew", sa.Column("entrance_exit_hebrew", sa.Text(), nullable=True))
    op.add_column("markers_hebrew", sa.Column("road_alignment", sa.Integer(), nullable=True))
    op.add_column("markers_hebrew", sa.Column("road_alignment_hebrew", sa.Text(), nullable=True))
    op.add_column("markers_hebrew", sa.Column("road_geometry", sa.Integer(), nullable=True))
    op.add_column("markers_hebrew", sa.Column("road_geometry_hebrew", sa.Text(), nullable=True))
    op.add_column("markers_hebrew", sa.Column("infrastructure_type", sa.Integer(), nullable=True))
    op.add_column("markers_hebrew", sa.Column("infrastructure_type_hebrew", sa.Text(), nullable=True))

    # involved_markers_hebrew (InvolvedMarkerView)
    op.add_column("involved_markers_hebrew", sa.Column("accident_yishuv2_symbol", sa.Integer(), nullable=True))
    op.add_column("involved_markers_hebrew", sa.Column("accident_yishuv2_name", sa.Text(), nullable=True))
    op.add_column("involved_markers_hebrew", sa.Column("entrance_exit", sa.Integer(), nullable=True))
    op.add_column("involved_markers_hebrew", sa.Column("entrance_exit_hebrew", sa.Text(), nullable=True))
    op.add_column("involved_markers_hebrew", sa.Column("road_alignment", sa.Integer(), nullable=True))
    op.add_column("involved_markers_hebrew", sa.Column("road_alignment_hebrew", sa.Text(), nullable=True))
    op.add_column("involved_markers_hebrew", sa.Column("road_geometry", sa.Integer(), nullable=True))
    op.add_column("involved_markers_hebrew", sa.Column("road_geometry_hebrew", sa.Text(), nullable=True))
    op.add_column("involved_markers_hebrew", sa.Column("infrastructure_type", sa.Integer(), nullable=True))
    op.add_column("involved_markers_hebrew", sa.Column("infrastructure_type_hebrew", sa.Text(), nullable=True))

    # vehicles_markers_hebrew (VehicleMarkerView)
    op.add_column("vehicles_markers_hebrew", sa.Column("accident_yishuv2_symbol", sa.Integer(), nullable=True))
    op.add_column("vehicles_markers_hebrew", sa.Column("accident_yishuv2_name", sa.Text(), nullable=True))
    op.add_column("vehicles_markers_hebrew", sa.Column("entrance_exit", sa.Integer(), nullable=True))
    op.add_column("vehicles_markers_hebrew", sa.Column("entrance_exit_hebrew", sa.Text(), nullable=True))
    op.add_column("vehicles_markers_hebrew", sa.Column("road_alignment", sa.Integer(), nullable=True))
    op.add_column("vehicles_markers_hebrew", sa.Column("road_alignment_hebrew", sa.Text(), nullable=True))
    op.add_column("vehicles_markers_hebrew", sa.Column("road_geometry", sa.Integer(), nullable=True))
    op.add_column("vehicles_markers_hebrew", sa.Column("road_geometry_hebrew", sa.Text(), nullable=True))
    op.add_column("vehicles_markers_hebrew", sa.Column("infrastructure_type", sa.Integer(), nullable=True))
    op.add_column("vehicles_markers_hebrew", sa.Column("infrastructure_type_hebrew", sa.Text(), nullable=True))


def downgrade():
    # vehicles_markers_hebrew
    op.drop_column("vehicles_markers_hebrew", "infrastructure_type_hebrew")
    op.drop_column("vehicles_markers_hebrew", "infrastructure_type")
    op.drop_column("vehicles_markers_hebrew", "road_geometry_hebrew")
    op.drop_column("vehicles_markers_hebrew", "road_geometry")
    op.drop_column("vehicles_markers_hebrew", "road_alignment_hebrew")
    op.drop_column("vehicles_markers_hebrew", "road_alignment")
    op.drop_column("vehicles_markers_hebrew", "entrance_exit_hebrew")
    op.drop_column("vehicles_markers_hebrew", "entrance_exit")
    op.drop_column("vehicles_markers_hebrew", "accident_yishuv2_name")
    op.drop_column("vehicles_markers_hebrew", "accident_yishuv2_symbol")

    # involved_markers_hebrew
    op.drop_column("involved_markers_hebrew", "infrastructure_type_hebrew")
    op.drop_column("involved_markers_hebrew", "infrastructure_type")
    op.drop_column("involved_markers_hebrew", "road_geometry_hebrew")
    op.drop_column("involved_markers_hebrew", "road_geometry")
    op.drop_column("involved_markers_hebrew", "road_alignment_hebrew")
    op.drop_column("involved_markers_hebrew", "road_alignment")
    op.drop_column("involved_markers_hebrew", "entrance_exit_hebrew")
    op.drop_column("involved_markers_hebrew", "entrance_exit")
    op.drop_column("involved_markers_hebrew", "accident_yishuv2_name")
    op.drop_column("involved_markers_hebrew", "accident_yishuv2_symbol")

    # markers_hebrew
    op.drop_column("markers_hebrew", "infrastructure_type_hebrew")
    op.drop_column("markers_hebrew", "infrastructure_type")
    op.drop_column("markers_hebrew", "road_geometry_hebrew")
    op.drop_column("markers_hebrew", "road_geometry")
    op.drop_column("markers_hebrew", "road_alignment_hebrew")
    op.drop_column("markers_hebrew", "road_alignment")
    op.drop_column("markers_hebrew", "entrance_exit_hebrew")
    op.drop_column("markers_hebrew", "entrance_exit")
    op.drop_column("markers_hebrew", "yishuv2_name")
    op.drop_column("markers_hebrew", "yishuv2_symbol")

    # markers
    op.drop_column("markers", "infrastructure_type")
    op.drop_column("markers", "road_geometry")
    op.drop_column("markers", "road_alignment")
    op.drop_column("markers", "entrance_exit")
    op.drop_column("markers", "yishuv2_name")
    op.drop_column("markers", "yishuv2_symbol")
