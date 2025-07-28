"""add id column to telegram_forwarded_messages

Revision ID: 41af3263a5a3
Revises: 78d8c5f870e2
Create Date: 2025-07-28 15:35:56.773801

"""
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '41af3263a5a3'
down_revision = '78d8c5f870e2'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.drop_constraint('telegram_forwarded_messages_pkey', 'telegram_forwarded_messages', type_='primary')
    op.add_column('telegram_forwarded_messages', sa.Column('id', sa.Integer(), primary_key=True))
    op.create_primary_key('id', 'telegram_forwarded_messages', ['id'])
    op.add_column('telegram_forwarded_messages',
                  sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=text("now()")))

def downgrade():
    op.drop_constraint('id', 'telegram_forwarded_messages', type_='primary')
    op.drop_column('telegram_forwarded_messages', 'id')
    op.create_primary_key('message_id', 'telegram_forwarded_messages', ['message_id'])
    op.drop_column('telegram_forwarded_messages', 'timestamp')

