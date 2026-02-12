"""removing vehicle status columns

Revision ID: ef951922e4ef
Revises: 46475f6cbe70
Create Date: 2026-02-12 20:31:53.001999
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "ef951922e4ef"
down_revision = "46475f6cbe70"
branch_labels = None
depends_on = None


def upgrade():
    # Drop vehicle_status dimension table
    op.drop_index("ix_vehicle_status_id", table_name="vehicle_status")
    op.drop_index("ix_vehicle_status_provider_code", table_name="vehicle_status")
    op.drop_index("ix_vehicle_status_year", table_name="vehicle_status")
    op.drop_table("vehicle_status")

    # Remove vehicle_status columns from related tables/views
    op.drop_column("involved_markers_hebrew", "vehicle_status")
    op.drop_column("involved_markers_hebrew", "vehicle_status_hebrew")

    op.drop_column("vehicles", "vehicle_status")

    op.drop_column("vehicles_hebrew", "vehicle_status")
    op.drop_column("vehicles_hebrew", "vehicle_status_hebrew")

    op.drop_column("vehicles_markers_hebrew", "vehicle_status")
    op.drop_column("vehicles_markers_hebrew", "vehicle_status_hebrew")


def downgrade():
    # Recreate vehicle_status dimension table
    op.create_table(
        "vehicle_status",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("provider_code", sa.Integer(), nullable=False),
        sa.Column("vehicle_status_hebrew", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", "year", "provider_code", name="vehicle_status_pkey"),
    )
    op.create_index("ix_vehicle_status_year", "vehicle_status", ["year"], unique=False)
    op.create_index("ix_vehicle_status_provider_code", "vehicle_status", ["provider_code"], unique=False)
    op.create_index("ix_vehicle_status_id", "vehicle_status", ["id"], unique=False)

    # Add vehicle_status columns back to related tables/views
    op.add_column("involved_markers_hebrew", sa.Column("vehicle_status", sa.Integer(), nullable=True))
    op.add_column("involved_markers_hebrew", sa.Column("vehicle_status_hebrew", sa.Text(), nullable=True))

    op.add_column("vehicles", sa.Column("vehicle_status", sa.Integer(), nullable=True))

    op.add_column("vehicles_hebrew", sa.Column("vehicle_status", sa.Integer(), nullable=True))
    op.add_column("vehicles_hebrew", sa.Column("vehicle_status_hebrew", sa.Text(), nullable=True))

    op.add_column("vehicles_markers_hebrew", sa.Column("vehicle_status", sa.Integer(), nullable=True))
    op.add_column("vehicles_markers_hebrew", sa.Column("vehicle_status_hebrew", sa.Text(), nullable=True))
