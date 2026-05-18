"""changing safety data vehicles to bigint

Revision ID: e55bdf34f0f0
Revises: dbaf0b04c390
Create Date: 2026-02-24 19:26:14.864680

"""

# revision identifiers, used by Alembic.
revision = 'e55bdf34f0f0'
down_revision = 'dbaf0b04c390'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.alter_column('safety_data_accident', 'vehicles', type_=sa.BigInteger(), existing_type=sa.Integer())
    # ### end Alembic commands ###


def downgrade():
    op.alter_column('safety_data_accident', 'vehicles', type_=sa.Integer(), existing_type=sa.BigInteger())
    # ### end Alembic commands ###
