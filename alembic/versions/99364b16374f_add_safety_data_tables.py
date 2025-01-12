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
    create_safety_data_accident_table()
    create_safety_data_involved_table()

def create_safety_data_accident_table():
    op.create_table( # pylint: disable=no-member
        sd_accident_table,
        sa.Column('accident_id', sa.BigInteger(), primary_key=True, autoincrement=False, nullable=False),
        sa.Column('accident_year', sa.Integer(), primary_key=True, autoincrement=False, nullable=False),
        sa.Column('provider_code', sa.Integer(), primary_key=True, autoincrement=False, nullable=False),
        sa.Column('accident_month', sa.Integer()),
        sa.Column('accident_timestamp', sa.TIMESTAMP()),
        sa.Column('accident_type', sa.Integer(), nullable=True),
        sa.Column('accident_yishuv_symbol', sa.Integer(), nullable=True),
        sa.Column('day_in_week', sa.Integer(), nullable=True),
        sa.Column('day_night', sa.Integer(), nullable=True),
        sa.Column('location_accuracy', sa.Integer(), nullable=True),
        sa.Column('multi_lane', sa.Integer(), nullable=True),
        sa.Column('one_lane', sa.Integer(), nullable=True),
        sa.Column('road1', sa.Integer(), nullable=True),
        sa.Column('road2', sa.Integer(), nullable=True),
        sa.Column('road_segment_number', sa.Integer(), nullable=True),
        sa.Column('road_type', sa.Integer(), nullable=True),
        sa.Column('road_width', sa.Integer(), nullable=True),
        sa.Column('speed_limit', sa.Integer(), nullable=True),
        sa.Column('street1', sa.Integer(), nullable=True),
        sa.Column('street2', sa.Integer(), nullable=True),
        sa.Column('vehicles', sa.Integer(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
    )
    for field in ['accident_year', 'accident_month', 'accident_timestamp',
                  'accident_type', 'accident_yishuv_symbol',
                  'day_night', 'multi_lane', 'one_lane',
                  'road1', 'road2', 'road_segment_number', 'road_type', 'road_width',
                  'speed_limit',
                  'street1', 'street2',
                  'latitude', 'longitude',
                  ]:
         # pylint: disable=no-member
        op.create_index(op.f(f'ix_{sd_accident_table}_{field}'), sd_accident_table, [field], unique=False)

def create_safety_data_involved_table():
    op.create_table( # pylint: disable=no-member
        sd_involved_table,
        sa.Column('_id', sa.Integer(), primary_key=True, autoincrement=False, nullable=False),
        sa.Column('accident_id', sa.BigInteger(), nullable=False),
        sa.Column('accident_year', sa.Integer(), nullable=False),
        sa.Column('provider_code', sa.Integer(), nullable=False),
        sa.Column('age_group', sa.Integer(), nullable=True),
        sa.Column('injured_type', sa.Integer(), nullable=True),
        sa.Column('injury_severity', sa.Integer(), nullable=True),
        sa.Column('population_type', sa.Integer(), nullable=True),
        sa.Column('sex', sa.Integer(), nullable=True),
        sa.Column('vehicle_type', sa.Integer(), nullable=True),
    )
    op.create_foreign_key(f'{sd_involved_table}_accident_id_fkey', # pylint: disable=no-member
                          sd_involved_table, sd_accident_table,
                          ['accident_id', 'provider_code', 'accident_year'],
                          ['accident_id', 'provider_code', 'accident_year'],
                          ondelete='CASCADE')
    op.create_index(op.f(f'ix_{sd_involved_table}_inv_acc'), sd_involved_table, # pylint: disable=no-member
                    ['accident_id', 'accident_year', 'provider_code'], unique=False)
    for field in ['injury_severity', 'injured_type',
                  'age_group', 'sex', 'population_type', 'vehicle_type']:
         # pylint: disable=no-member
        op.create_index(op.f(f'ix_{sd_involved_table}_{field}'), sd_involved_table, [field], unique=False)

