"""removing police unit columns

Revision ID: b460c29c20b7
Revises: 548f002e20d6
Create Date: 2026-02-12 14:36:22.639664
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b460c29c20b7"
down_revision = "548f002e20d6"
branch_labels = None
depends_on = None


def upgrade():
    # Drop police_unit dimension table
    op.drop_index("ix_police_unit_id", table_name="police_unit")
    op.drop_index("ix_police_unit_provider_code", table_name="police_unit")
    op.drop_index("ix_police_unit_year", table_name="police_unit")
    op.drop_table("police_unit")

    # Remove police_unit columns from related tables/views
    op.drop_column("injured_around_school_all_data", "markers_police_unit")

    op.drop_column("involved_markers_hebrew", "police_unit")
    op.drop_column("involved_markers_hebrew", "police_unit_hebrew")

    op.drop_column("markers", "police_unit")

    op.drop_column("markers_hebrew", "police_unit")
    op.drop_column("markers_hebrew", "police_unit_hebrew")

    op.drop_column("vehicles_markers_hebrew", "police_unit")
    op.drop_column("vehicles_markers_hebrew", "police_unit_hebrew")


def downgrade():
    # Recreate police_unit dimension table
    op.create_table(
        "police_unit",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("provider_code", sa.Integer(), nullable=False),
        sa.Column("police_unit_hebrew", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", "year", "provider_code", name="police_unit_pkey"),
    )
    op.create_index("ix_police_unit_year", "police_unit", ["year"], unique=False)
    op.create_index("ix_police_unit_provider_code", "police_unit", ["provider_code"], unique=False)
    op.create_index("ix_police_unit_id", "police_unit", ["id"], unique=False)

    # Add police_unit columns back to related tables/views
    op.add_column(
        "injured_around_school_all_data",
        sa.Column("markers_police_unit", sa.Float(), nullable=True),
    )

    op.add_column("involved_markers_hebrew", sa.Column("police_unit", sa.Integer(), nullable=True))
    op.add_column("involved_markers_hebrew", sa.Column("police_unit_hebrew", sa.Text(), nullable=True))

    op.add_column("markers", sa.Column("police_unit", sa.Integer(), nullable=True))

    op.add_column("markers_hebrew", sa.Column("police_unit", sa.Integer(), nullable=True))
    op.add_column("markers_hebrew", sa.Column("police_unit_hebrew", sa.Text(), nullable=True))

    op.add_column("vehicles_markers_hebrew", sa.Column("police_unit", sa.Integer(), nullable=True))
    op.add_column("vehicles_markers_hebrew", sa.Column("police_unit_hebrew", sa.Text(), nullable=True))