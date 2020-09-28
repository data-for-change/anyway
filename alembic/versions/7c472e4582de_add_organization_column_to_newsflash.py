"""Add organization column to newsflash

Revision ID: 7c472e4582de
Revises: 2c54437f4ee4
Create Date: 2020-08-21 02:08:31.654024

"""

# revision identifiers, used by Alembic.
revision = '7c472e4582de'
down_revision = '2c54437f4ee4'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('news_flash', sa.Column('organization', sa.Text(), nullable=True))



def downgrade():
    op.drop_column('news_flash', 'organization')
