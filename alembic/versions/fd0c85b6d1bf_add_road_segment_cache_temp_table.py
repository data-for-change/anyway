"""Add road segment cache temp table

Revision ID: fd0c85b6d1bf
Revises: d365c792c756
Create Date: 2022-03-05 13:48:20.997434

"""

# revision identifiers, used by Alembic.
revision = "fd0c85b6d1bf"
down_revision = "d365c792c756"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.create_table(
        "infographics_road_segments_data_cache_temp",
        sa.Column("road_segment_id", sa.BigInteger(), nullable=False),
        sa.Column("years_ago", sa.Integer(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("road_segment_id", "years_ago"),
    )


def downgrade():
    op.drop_table("infographics_road_segments_data_cache_temp")
