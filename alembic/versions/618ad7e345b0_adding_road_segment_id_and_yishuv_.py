"""Adding road_segment_id and yishuv_symbol to news_flash and cbs_locations tables

Revision ID: 618ad7e345b0
Revises: 4f98b6b083b7
Create Date: 2021-10-03 18:36:04.576348

"""

# revision identifiers, used by Alembic.
revision = '618ad7e345b0'
down_revision = '4f98b6b083b7'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('news_flash', sa.Column('yishuv_symbol', sa.Integer(), nullable=True))
    op.add_column('news_flash', sa.Column('road_segment_id', sa.Integer(), nullable=True))
    op.add_column('news_flash', sa.Column('street1', sa.Integer(), nullable=True))
    op.add_column('news_flash', sa.Column('street2', sa.Integer(), nullable=True))
    op.add_column('cbs_locations', sa.Column('yishuv_symbol', sa.Integer(), nullable=True))
    op.add_column('cbs_locations', sa.Column('road_segment_id', sa.Integer(), nullable=True))
    op.add_column('cbs_locations', sa.Column('street1', sa.Integer(), nullable=True))
    op.add_column('cbs_locations', sa.Column('street2', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('news_flash', 'yishuv_symbol')
    op.drop_column('news_flash', 'road_segment_id')
    op.drop_column('news_flash', 'street1')
    op.drop_column('news_flash', 'street2')
    op.drop_column('cbs_locations', 'yishuv_symbol')
    op.drop_column('cbs_locations', 'road_segment_id')
    op.drop_column('cbs_locations', 'street1')
    op.drop_column('cbs_locations', 'street2')
