"""Adding streets table

Revision ID: b38237665bc9
Revises: 618ad7e345b0
Create Date: 2021-11-28 18:03:09.344492

"""

# revision identifiers, used by Alembic.
revision = 'b38237665bc9'
down_revision = '618ad7e345b0'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.create_table('streets',
                    sa.Column('yishuv_symbol', sa.Integer(), nullable=False),
                    sa.Column('street', sa.Integer(), nullable=False),
                    sa.Column('street_hebrew', sa.String(length=50), nullable=True),
                    sa.PrimaryKeyConstraint('yishuv_symbol', 'street')
                    )
    op.create_index('streets_yishuv_street_idx',
                    'streets',
                    ['yishuv_symbol', 'street'],
                    unique=True)
    op.create_index('streets_yishuv_street_hebrew_idx',
                    'streets',
                    ['yishuv_symbol', 'street_hebrew'],
                    unique=True)


def downgrade():
    op.drop_index(op.f('streets_yishuv_street_idx'), table_name='streets')
    op.drop_index(op.f('streets_yishuv_street_hebrew_idx'), table_name='streets')
    op.drop_table('streets')

