"""add infographics data cache table

Revision ID: d8f0c029862a
Revises: c7722630e010
Create Date: 2020-06-08 16:24:30.153844

"""

# revision identifiers, used by Alembic.
revision = 'd8f0c029862a'
down_revision = 'c7722630e010'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

table_name = 'infographics_data_cache'
table_name_temp = 'infographics_data_cache_temp'

def upgrade():
    op.create_table(table_name,
                    sa.Column('news_flash_id', sa.BigInteger(), nullable=False),
                    sa.Column('years_ago', sa.Integer(), nullable=False),
                    sa.Column('data', sa.types.JSON(), nullable=False),
                    sa.PrimaryKeyConstraint('news_flash_id', 'years_ago')
                    )
    op.create_index('infographics_data_cache_id_years_idx', table_name, ['news_flash_id', 'years_ago'], unique=True)

    op.create_table(table_name_temp,
                    sa.Column('news_flash_id', sa.BigInteger(), nullable=False),
                    sa.Column('years_ago', sa.Integer(), nullable=False),
                    sa.Column('data', sa.types.JSON(), nullable=False),
                    sa.PrimaryKeyConstraint('news_flash_id', 'years_ago')
                    )


def downgrade():
    op.drop_index(op.f('infographics_data_cache_id_years_idx'), table_name=table_name)
    op.drop_table(table_name)

    op.drop_table(table_name_temp)

