"""added columns for social accounts

Revision ID: 407f7f23156f
Revises:
Create Date: 2016-01-18 22:29:30.336635

"""

# revision identifiers, used by Alembic.
revision = '407f7f23156f'
down_revision = '1569548127f0'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('users', sa.Column('social_id', sa.String(64), nullable=True, unique=True))
    op.add_column('users', sa.Column('nickname', sa.String(64), nullable=True))
    op.add_column('users', sa.Column('provider', sa.String(64), nullable=True))


def downgrade():
    op.drop_column('users', 'social_id')
    op.drop_column('users', 'nickname')
    op.drop_column('users', 'provider')
