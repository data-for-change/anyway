"""convert-two-streets-cache-to-single

Revision ID: d365c792c756
Revises: b38237665bc9
Create Date: 2021-12-30 16:57:22.196091

"""

# revision identifiers, used by Alembic.
revision = 'd365c792c756'
down_revision = 'b38237665bc9'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from typing import Optional


two_streets_table_name = 'infographics_two_streets_data_cache'
two_streets_table_name_temp = 'infographics_two_streets_data_cache_temp'
two_streets_index = 'infographics_two_streets_data_cache_id_years_idx'


def upgrade():
    op.create_table('infographics_street_data_cache',
                    sa.Column('yishuv_symbol', sa.Integer(), nullable=False),
                    sa.Column('street', sa.Integer(), nullable=False),
                    sa.Column('years_ago', sa.Integer(), nullable=False),
                    sa.Column('data', sa.JSON(), nullable=True),
                    sa.PrimaryKeyConstraint('yishuv_symbol', 'street', 'years_ago')
                    )
    op.create_index('infographics_street_data_cache_id_years_idx',
                    'infographics_street_data_cache',
                    ['yishuv_symbol', 'street', 'years_ago'], unique=True
                    )
    op.create_table('infographics_street_data_cache_temp',
                    sa.Column('yishuv_symbol', sa.Integer(), nullable=False),
                    sa.Column('street', sa.Integer(), nullable=False),
                    sa.Column('years_ago', sa.Integer(), nullable=False),
                    sa.Column('data', sa.JSON(), nullable=True),
                    sa.PrimaryKeyConstraint('yishuv_symbol', 'street', 'years_ago')
                    )
    drop_two_streets_cache()


def downgrade():
    op.drop_table('infographics_street_data_cache_temp')
    op.drop_index('infographics_street_data_cache_id_years_idx', table_name='infographics_street_data_cache')
    op.drop_table('infographics_street_data_cache')

    create_two_streets_cache()


def drop_two_streets_cache():
    op.drop_index(op.f(two_streets_index), table_name=two_streets_table_name)
    op.drop_table(two_streets_table_name)

    op.drop_table(two_streets_table_name_temp)


def create_two_streets_table(table: str, index: Optional[str]):
    op.create_table(table,
                    sa.Column('street1', sa.Integer(), nullable=False),
                    sa.Column('street2', sa.Integer(), nullable=True),
                    sa.Column('yishuv_symbol', sa.Integer(), nullable=False),
                    sa.Column('years_ago', sa.Integer(), nullable=False),
                    sa.Column('data', sa.types.JSON(), nullable=False),
                    sa.PrimaryKeyConstraint('street1', 'street2', 'years_ago')
                    )
    if index:
        op.create_index(index, table,
                        ['street1', 'street2', 'yishuv_symbol', 'years_ago'],
                        unique=True)


def create_two_streets_cache():
    create_two_streets_table(two_streets_table_name, two_streets_index)
    create_two_streets_table(two_streets_table_name_temp, None)

