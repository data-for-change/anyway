"""removing old intersection columns

Revision ID: 548f002e20d6
Revises: 39966aa5db4d
Create Date: 2026-02-11 21:35:00.576330
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "548f002e20d6"
down_revision = "39966aa5db4d"
branch_labels = None
depends_on = None


def upgrade():
    # markers (AccidentMarker)
    op.drop_column("markers", "urban_intersection")
    op.drop_column("markers", "non_urban_intersection")
    op.drop_column("markers", "non_urban_intersection_hebrew")
    op.drop_column("markers", "non_urban_intersection_by_junction_number")

    # markers_hebrew (AccidentMarkerView)
    op.drop_column("markers_hebrew", "urban_intersection")
    op.drop_column("markers_hebrew", "non_urban_intersection")
    op.drop_column("markers_hebrew", "non_urban_intersection_hebrew")
    op.drop_column("markers_hebrew", "non_urban_intersection_by_junction_number")

    # involved_markers_hebrew (InvolvedMarkerView)
    op.drop_column("involved_markers_hebrew", "urban_intersection")
    op.drop_column("involved_markers_hebrew", "non_urban_intersection")
    op.drop_column("involved_markers_hebrew", "non_urban_intersection_hebrew")
    op.drop_column("involved_markers_hebrew", "non_urban_intersection_by_junction_number")

    # vehicles_markers_hebrew (VehicleMarkerView)
    op.drop_column("vehicles_markers_hebrew", "urban_intersection")
    op.drop_column("vehicles_markers_hebrew", "non_urban_intersection")
    op.drop_column("vehicles_markers_hebrew", "non_urban_intersection_hebrew")
    op.drop_column("vehicles_markers_hebrew", "non_urban_intersection_by_junction_number")


def downgrade():
    # vehicles_markers_hebrew (VehicleMarkerView)
    op.add_column(
        "vehicles_markers_hebrew",
        sa.Column("non_urban_intersection_by_junction_number", sa.Text(), nullable=True),
    )
    op.add_column(
        "vehicles_markers_hebrew",
        sa.Column("non_urban_intersection_hebrew", sa.Text(), nullable=True),
    )
    op.add_column(
        "vehicles_markers_hebrew",
        sa.Column("non_urban_intersection", sa.Integer(), nullable=True),
    )
    op.add_column(
        "vehicles_markers_hebrew",
        sa.Column("urban_intersection", sa.Integer(), nullable=True),
    )

    # involved_markers_hebrew (InvolvedMarkerView)
    op.add_column(
        "involved_markers_hebrew",
        sa.Column("non_urban_intersection_by_junction_number", sa.Text(), nullable=True),
    )
    op.add_column(
        "involved_markers_hebrew",
        sa.Column("non_urban_intersection_hebrew", sa.Text(), nullable=True),
    )
    op.add_column(
        "involved_markers_hebrew",
        sa.Column("non_urban_intersection", sa.Integer(), nullable=True),
    )
    op.add_column(
        "involved_markers_hebrew",
        sa.Column("urban_intersection", sa.Integer(), nullable=True),
    )

    # markers_hebrew (AccidentMarkerView)
    op.add_column(
        "markers_hebrew",
        sa.Column("non_urban_intersection_by_junction_number", sa.Text(), nullable=True),
    )
    op.add_column(
        "markers_hebrew",
        sa.Column("non_urban_intersection_hebrew", sa.Text(), nullable=True),
    )
    op.add_column(
        "markers_hebrew",
        sa.Column("non_urban_intersection", sa.Integer(), nullable=True),
    )
    op.add_column(
        "markers_hebrew",
        sa.Column("urban_intersection", sa.Integer(), nullable=True),
    )

    # markers (AccidentMarker)
    op.add_column(
        "markers",
        sa.Column("non_urban_intersection_by_junction_number", sa.Text(), nullable=True),
    )
    op.add_column(
        "markers",
        sa.Column("non_urban_intersection_hebrew", sa.Text(), nullable=True),
    )
    op.add_column(
        "markers",
        sa.Column("non_urban_intersection", sa.Integer(), nullable=True),
    )
    op.add_column(
        "markers",
        sa.Column("urban_intersection", sa.Integer(), nullable=True),
    )
