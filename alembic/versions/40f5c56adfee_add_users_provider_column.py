"""added provider column to users table

Revision ID: 40f5c56adfee
Revises: 407f7f23156f
Create Date: 2016-02-02 22:19:49.329707

"""

# revision identifiers, used by Alembic.
revision = '40f5c56adfee'
down_revision = '407f7f23156f'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('users', sa.Column('provider', sa.String(64), nullable=True))


def downgrade():
    op.drop_column('users', 'provider')
