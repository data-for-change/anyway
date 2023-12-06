"""add suburban junction table

Revision ID: 13dcbe0a3a64
Revises: 203753e10336
Create Date: 2023-01-16 12:39:03.026479

"""

# revision identifiers, used by Alembic.
revision = '13dcbe0a3a64'
down_revision = '203753e10336'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.create_table(
        'suburban_junction',
        sa.Column('non_urban_intersection', sa.Integer(), primary_key=True, nullable=False, default=None),
        sa.Column('non_urban_intersection_hebrew', sa.VARCHAR(length=100)),
        sa.Column('roads', postgresql.ARRAY(sa.Integer(), dimensions=1), nullable=False),
    )
    op.create_index('suburban_junction_non_urban_intersection_idx',
                    'suburban_junction',
                    ['non_urban_intersection'], unique=True
                    )


def downgrade():
    op.drop_index('suburban_junction_non_urban_intersection_idx',
                  table_name='suburban_junction'
                  )
    op.drop_table('suburban_junction')
