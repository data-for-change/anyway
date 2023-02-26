"""add critical in newsflash

Revision ID: 26c3c9c4eb53
Revises: 13dcbe0a3a64
Create Date: 2023-01-18 20:58:05.032521

"""

# revision identifiers, used by Alembic.
revision = '26c3c9c4eb53'
down_revision = '13dcbe0a3a64'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('news_flash', sa.Column('critical', sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column('news_flash', 'critical')
