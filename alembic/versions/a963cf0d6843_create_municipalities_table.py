"""create municipalities table

Revision ID: a963cf0d6843
Revises: 4f1a251e37d1
Create Date: 2019-12-12 12:09:25.112460

"""

# revision identifiers, used by Alembic.
import geoalchemy2

revision = 'a963cf0d6843'
down_revision = '4f1a251e37d1'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

table_name = 'municipalities'


def upgrade():
    op.create_table(table_name,
                    sa.Column('id', sa.BigInteger, primary_key=True),
                    sa.Column('heb_name', sa.String(100), nullable=False),
                    sa.Column('eng_name', sa.String(100), nullable=True),
                    sa.Column('polygon', geoalchemy2.types.Geometry(geometry_type='POLYGON'), nullable=False),
                    sa.Column('symbol', sa.Integer, nullable=True),
                    sa.Column('osm_id', sa.Integer, nullable=True),
                    sa.Column('file_name', sa.String(100), nullable=False)
                    )
    op.create_index(op.f('idx_' + table_name + '_id'), table_name, ['id'], unique=True)


def downgrade():
    op.drop_table(table_name)
