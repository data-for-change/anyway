"""Adding road_segment_id and yishuv_symbol to news_flash and cbs_locations tables, two_roads and street data cache tables

Revision ID: 618ad7e345b0
Revises: 30862849651c
Create Date: 2021-10-03 18:36:04.576348

"""

# revision identifiers, used by Alembic.
revision = '618ad7e345b0'
down_revision = '30862849651c'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


two_roads_table_name = 'infographics_two_roads_data_cache'
two_roads_table_name_temp = 'infographics_two_roads_data_cache_temp'
two_roads_index = 'infographics_two_roads_data_cache_id_years_idx'


def upgrade():
    create_new_fields()
    create_two_roads_cache()


def downgrade():
    drop_new_fields()
    drop_two_roads_cache()


def create_new_fields():
    op.add_column('news_flash', sa.Column('yishuv_symbol', sa.Integer(), nullable=True))
    op.add_column('news_flash', sa.Column('road_segment_id', sa.Integer(), nullable=True))
    op.add_column('news_flash', sa.Column('street1', sa.Integer(), nullable=True))
    op.add_column('news_flash', sa.Column('street2', sa.Integer(), nullable=True))
    op.add_column('news_flash', sa.Column('non_urban_intersection', sa.Integer(), nullable=True))
    op.add_column('cbs_locations', sa.Column('yishuv_symbol', sa.Integer(), nullable=True))
    op.add_column('cbs_locations', sa.Column('road_segment_id', sa.Integer(), nullable=True))
    op.add_column('cbs_locations', sa.Column('street1', sa.Integer(), nullable=True))
    op.add_column('cbs_locations', sa.Column('street2', sa.Integer(), nullable=True))
    op.add_column('cbs_locations', sa.Column('non_urban_intersection', sa.Integer(), nullable=True))


def drop_new_fields():
    op.drop_column('news_flash', 'yishuv_symbol')
    op.drop_column('news_flash', 'road_segment_id')
    op.drop_column('news_flash', 'street1')
    op.drop_column('news_flash', 'street2')
    op.drop_column('cbs_locations', 'yishuv_symbol')
    op.drop_column('cbs_locations', 'road_segment_id')
    op.drop_column('cbs_locations', 'street1')
    op.drop_column('cbs_locations', 'street2')

def create_two_roads_cache():
    op.create_table(two_roads_table_name,
                    sa.Column('road1', sa.Integer(), nullable=False),
                    sa.Column('road2', sa.Integer(), nullable=False),
                    sa.Column('years_ago', sa.Integer(), nullable=False),
                    sa.Column('data', sa.types.JSON(), nullable=False),
                    sa.PrimaryKeyConstraint('road1', 'road2', 'years_ago')
                    )
    op.create_index(two_roads_index, two_roads_table_name, ['news_flash_id', 'years_ago'], unique=True)

    op.create_table(two_roads_table_name_temp,
                    sa.Column('road1', sa.Integer(), nullable=False),
                    sa.Column('road2', sa.Integer(), nullable=False),
                    sa.Column('years_ago', sa.Integer(), nullable=False),
                    sa.Column('data', sa.types.JSON(), nullable=False),
                    sa.PrimaryKeyConstraint('road1', 'road2', 'years_ago')
                    )


def drop_two_roads_cache():
    op.drop_index(op.f(two_roads_index), table_name=two_roads_table_name)
    op.drop_table(two_roads_table_name)

    op.drop_table(two_roads_table_name_temp)

