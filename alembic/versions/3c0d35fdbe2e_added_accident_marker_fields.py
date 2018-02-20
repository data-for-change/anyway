"""Added accident marker fields

Revision ID: 3c0d35fdbe2e
Revises: 283bc6a2bcab
Create Date: 2018-02-20 10:51:20.643607

"""

# revision identifiers, used by Alembic.
revision = '3c0d35fdbe2e'
down_revision = '283bc6a2bcab'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('markers', sa.Column('day_in_week', sa.Integer(), nullable=True))
    op.add_column('markers', sa.Column('day_night', sa.Integer(), nullable=True))
    op.add_column('markers', sa.Column('district', sa.Integer(), nullable=True))
    op.add_column('markers', sa.Column('geo_area', sa.Integer(), nullable=True))
    op.add_column('markers', sa.Column('minizipali_status', sa.Integer(), nullable=True))
    op.add_column('markers', sa.Column('natural_area', sa.Integer(), nullable=True))
    op.add_column('markers', sa.Column('region', sa.Integer(), nullable=True))
    op.add_column('markers', sa.Column('traffic_light', sa.Integer(), nullable=True))
    op.add_column('markers', sa.Column('yishuv_shape', sa.Integer(), nullable=True))
    op.add_column('markers', sa.Column('yishuv_symbol', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('markers', 'yishuv_symbol')
    op.drop_column('markers', 'yishuv_shape')
    op.drop_column('markers', 'traffic_light')
    op.drop_column('markers', 'region')
    op.drop_column('markers', 'natural_area')
    op.drop_column('markers', 'minizipali_status')
    op.drop_column('markers', 'geo_area')
    op.drop_column('markers', 'district')
    op.drop_column('markers', 'day_night')
    op.drop_column('markers', 'day_in_week')
