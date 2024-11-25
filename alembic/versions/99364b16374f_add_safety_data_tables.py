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

_table_name = "safety_data_involved"


def downgrade():
    op.drop_table(_table_name)


def upgrade():
    op.create_table(
        _table_name,
        sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('accident_year', sa.Integer()),
        sa.Column('accident_timestamp', sa.TIMESTAMP()),
        sa.Column('injury_severity', sa.Integer(), nullable=True),
        sa.Column('age_group', sa.Integer(), nullable=True),
        sa.Column('sex', sa.Integer(), nullable=True),
        sa.Column('accident_yishuv_symbol', sa.Integer(), nullable=True),
        sa.Column('street1', sa.Integer(), nullable=True),
        sa.Column('street2', sa.Integer(), nullable=True),
        sa.Column('road_type', sa.Integer(), nullable=True),
        sa.Column('road_light', sa.Integer(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
    )
    for field in ['accident_year', 'accident_timestamp', 'injury_severity',
                  'age_group', 'sex', 'accident_yishuv_symbol', 'street1',
                  'street2', 'road_type', 'road_light']:
        op.create_index(op.f(f'ix_accident_hour_raw_{field}'), _table_name, [field], unique=False)
