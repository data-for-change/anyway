"""Add safety-data tables

Revision ID: 99364b16374f
Revises: e962054e4422
Create Date: 2024-11-15 11:03:26.435210

"""

# revision identifiers, used by Alembic.
revision = '99364b16374f'
down_revision = 'e962054e4422'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

sd_involved_table = "safety_data_involved"
sd_accident_table = "safety_data_accident"


def downgrade():
    op.drop_table(sd_involved_table) # pylint: disable=no-member
    op.drop_table(sd_accident_table) # pylint: disable=no-member


def upgrade():
    op.create_table( # pylint: disable=no-member
        sd_involved_table,
        sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('accident_id', sa.Integer()),
        sa.Column('injury_severity', sa.Integer(), nullable=True),
        sa.Column('injured_type', sa.Integer(), nullable=True),
        sa.Column('age_group', sa.Integer(), nullable=True),
        sa.Column('sex', sa.Integer(), nullable=True),
        sa.Column('population_type', sa.Integer(), nullable=True),
    )
    for field in ['accident_id', 'injury_severity', 'injured_type', 'age_group', 'sex', 'population_type']:
         # pylint: disable=no-member
        op.create_index(op.f(f'ix_{sd_involved_table}_{field}'), sd_involved_table, [field], unique=False)

    op.create_table( # pylint: disable=no-member
        sd_accident_table,
        sa.Column('acc_id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('acc_year', sa.Integer()),
        sa.Column('acc_month', sa.Integer()),
        sa.Column('acc_timestamp', sa.TIMESTAMP()),
        sa.Column('road_type', sa.Integer(), nullable=True),
        sa.Column('road_width', sa.Integer(), nullable=True),
        sa.Column('day_night', sa.Integer(), nullable=True),
        sa.Column('one_lane_type', sa.Integer(), nullable=True),
        sa.Column('multi_lane_type', sa.Integer(), nullable=True),
        sa.Column('speed_limit_type', sa.Integer(), nullable=True),
        sa.Column('yishuv_symbol', sa.Integer(), nullable=True),
        sa.Column('street1', sa.Integer(), nullable=True),
        sa.Column('street2', sa.Integer(), nullable=True),
        sa.Column('road', sa.Integer(), nullable=True),
        sa.Column('road_segment', sa.Integer(), nullable=True),
        sa.Column('vehicle_types', sa.Integer(), nullable=True), # bit map
        sa.Column('lat', sa.Float(), nullable=True),
        sa.Column('lon', sa.Float(), nullable=True),
    )
    for field in ['acc_id', 'acc_year', 'acc_month', 'acc_timestamp',
                  'road_type', 'road_width', 'day_night',
                  'one_lane_type', 'multi_lane_type', 'speed_limit_type',
                  'yishuv_symbol', 'street1', 'street2', 'road', 'road_segment', 'vehicle_types',
                  'lat', 'lon',
                  ]:
         # pylint: disable=no-member
        op.create_index(op.f(f'ix_{sd_accident_table}_{field}'), sd_accident_table, [field], unique=False)
