"""add suburban junction table

Revision ID: 7ea883c8a245
Revises: d9cb98c752d4
Create Date: 2023-06-04 17:43:13.170728

"""

# revision identifiers, used by Alembic.
revision = '7ea883c8a245'
down_revision = 'd9cb98c752d4'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


# noinspection PyUnresolvedReferences
def upgrade():
    op.create_table("road_junction_km",
                    sa.Column('road', sa.BigInteger(), nullable=False),
                    sa.Column('non_urban_intersection', sa.Integer(), nullable=False),
                    sa.Column('km', sa.Float(), nullable=False),
                    sa.PrimaryKeyConstraint('road', 'non_urban_intersection')
                    )
    op.create_index('road_junction_km_idx',
                    "road_junction_km",
                    ['road', 'non_urban_intersection'],
                    unique=True)


# noinspection PyUnresolvedReferences
def downgrade():
    op.drop_index(op.f('road_junction_km_idx'), table_name="road_junction_km")
    op.drop_table("road_junction_km")
