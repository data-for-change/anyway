"""removing road shape columns

Revision ID: 42609a9cb467
Revises: b460c29c20b7
Create Date: 2026-02-12 15:09:04.110756
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "42609a9cb467"
down_revision = "b460c29c20b7"
branch_labels = None
depends_on = None


def upgrade():
    # drop road_shape columns from tables/views
    op.drop_column("injured_around_school_all_data", "markers_road_shape")

    op.drop_column("involved_markers_hebrew", "road_shape")
    op.drop_column("involved_markers_hebrew", "road_shape_hebrew")

    op.drop_column("markers", "road_shape")

    op.drop_column("markers_hebrew", "road_shape")
    op.drop_column("markers_hebrew", "road_shape_hebrew")

    op.drop_column("vehicles_markers_hebrew", "road_shape")
    op.drop_column("vehicles_markers_hebrew", "road_shape_hebrew")

    # drop the dimension table itself (only if it was removed from models)
    op.drop_table("road_shape")


def downgrade():
    # recreate road_shape table (as it was in the autogen)
    op.create_table(
        "road_shape",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("provider_code", sa.Integer(), nullable=False),
        sa.Column("road_shape_hebrew", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", "year", "provider_code", name="road_shape_pkey"),
    )

    # add columns back
    op.add_column(
        "vehicles_markers_hebrew",
        sa.Column("road_shape_hebrew", sa.Text(), nullable=True),
    )
    op.add_column(
        "vehicles_markers_hebrew",
        sa.Column("road_shape", sa.Integer(), nullable=True),
    )

    op.add_column(
        "markers_hebrew",
        sa.Column("road_shape_hebrew", sa.Text(), nullable=True),
    )
    op.add_column(
        "markers_hebrew",
        sa.Column("road_shape", sa.Integer(), nullable=True),
    )

    op.add_column(
        "markers",
        sa.Column("road_shape", sa.Integer(), nullable=True),
    )

    op.add_column(
        "involved_markers_hebrew",
        sa.Column("road_shape_hebrew", sa.Text(), nullable=True),
    )
    op.add_column(
        "involved_markers_hebrew",
        sa.Column("road_shape", sa.Integer(), nullable=True),
    )

    op.add_column(
        "injured_around_school_all_data",
        sa.Column("markers_road_shape", sa.Float(), nullable=True),
    )