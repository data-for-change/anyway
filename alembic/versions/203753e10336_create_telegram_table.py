"""create telegram table

Revision ID: 203753e10336
Revises: ccc480c5d0a2
Create Date: 2023-02-09 20:00:06.800714

"""

# revision identifiers, used by Alembic.
revision = '203753e10336'
down_revision = 'ccc480c5d0a2'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

table_names = ["telegram_groups", "telegram_groups_test"]
def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    for table_name in table_names:
        op.create_table(table_name,
                        sa.Column('id', sa.Integer(), nullable=False),
                        sa.Column('filter', JSON(), nullable=False, server_default="{}"),
                        sa.PrimaryKeyConstraint('id')
                        )

def downgrade():
    for table_name in table_names:
        op.drop_table(table_name)