"""Rename road segment column in safety_data_accident

Revision ID: 78d8c5f870e2
Revises: 99364b16374f
Create Date: 2025-02-20 08:18:38.381337

"""

# revision identifiers, used by Alembic.
revision = '78d8c5f870e2'
down_revision = '99364b16374f'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


sd_accident_table = "safety_data_accident"


def upgrade():
    op.alter_column(sd_accident_table, 'road_segment_number', new_column_name='road_segment_id', existing_type=sa.Integer(), nullable=True)


def downgrade():
    op.alter_column(sd_accident_table, 'road_segment_id', new_column_name='road_segment_number', existing_type=sa.Integer(), nullable=True)
