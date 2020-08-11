"""create casualties_costs table

Revision ID: 6b5383680e26
Revises: 10b468849090
Create Date: 2020-08-03 12:20:36.184062

"""

# revision identifiers, used by Alembic.
revision = '6b5383680e26'
down_revision = '10b468849090'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('casualties_costs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('injured_type', sa.String(), nullable=False),
    sa.Column('injured_type_hebrew', sa.String(), nullable=False),
    sa.Column('injuries_cost_k', sa.Integer(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=False),
    sa.Column('data_source_hebrew', sa.String(), nullable=False),
    )


def downgrade():
    op.drop_table('casualties_costs')
