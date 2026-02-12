"""removing road sign columns

Revision ID: 46475f6cbe70
Revises: 42609a9cb467
Create Date: 2026-02-12 15:33:11.709885
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "46475f6cbe70"
down_revision = "42609a9cb467"
branch_labels = None
depends_on = None


def upgrade():
    # Drop road_sign dimension table
    op.drop_index("ix_road_sign_id", table_name="road_sign")
    op.drop_index("ix_road_sign_provider_code", table_name="road_sign")
    op.drop_index("ix_road_sign_year", table_name="road_sign")
    op.drop_table("road_sign")

    # Remove road_sign columns from related tables/views
    op.drop_column("injured_around_school_all_data", "markers_road_sign")

    op.drop_column("involved_markers_hebrew", "road_sign")
    op.drop_column("involved_markers_hebrew", "road_sign_hebrew")

    op.drop_column("markers", "road_sign")

    op.drop_column("markers_hebrew", "road_sign")
    op.drop_column("markers_hebrew", "road_sign_hebrew")

    op.drop_column("vehicles_markers_hebrew", "road_sign")
    op.drop_column("vehicles_markers_hebrew", "road_sign_hebrew")


def downgrade():
    # Recreate road_sign dimension table
    op.create_table(
        "road_sign",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("provider_code", sa.Integer(), nullable=False),
        sa.Column("road_sign_hebrew", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", "year", "provider_code", name="road_sign_pkey"),
    )
    op.create_index("ix_road_sign_year", "road_sign", ["year"], unique=False)
    op.create_index("ix_road_sign_provider_code", "road_sign", ["provider_code"], unique=False)
    op.create_index("ix_road_sign_id", "road_sign", ["id"], unique=False)

    # Add road_sign columns back to related tables/views
    op.add_column("injured_around_school_all_data", sa.Column("markers_road_sign", sa.Float(), nullable=True))

    op.add_column("involved_markers_hebrew", sa.Column("road_sign", sa.Integer(), nullable=True))
    op.add_column("involved_markers_hebrew", sa.Column("road_sign_hebrew", sa.Text(), nullable=True))

    op.add_column("markers", sa.Column("road_sign", sa.Integer(), nullable=True))

    op.add_column("markers_hebrew", sa.Column("road_sign", sa.Integer(), nullable=True))
    op.add_column("markers_hebrew", sa.Column("road_sign_hebrew", sa.Text(), nullable=True))

    op.add_column("vehicles_markers_hebrew", sa.Column("road_sign", sa.Integer(), nullable=True))
    op.add_column("vehicles_markers_hebrew", sa.Column("road_sign_hebrew", sa.Text(), nullable=True))
