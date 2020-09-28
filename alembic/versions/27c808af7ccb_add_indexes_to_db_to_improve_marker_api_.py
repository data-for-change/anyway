"""Add indexes to db to improve marker api performance

Revision ID: 27c808af7ccb
Revises: 16c2d576e01e
Create Date: 2020-09-18 12:07:11.965776

"""

# revision identifiers, used by Alembic.
revision = '27c808af7ccb'
down_revision = '16c2d576e01e'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.create_index(op.f('ix_latitude'), 'discussions', ['latitude'], unique=False)
    op.create_index(op.f('ix_longitude'), 'discussions', ['longitude'], unique=False)
    op.create_index(op.f('ix_created'), 'discussions', ['created'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_latitude'), table_name='discussions')
    op.drop_index(op.f('ix_longitude'), table_name='discussions')
    op.drop_index(op.f('ix_created'), table_name='discussions')

