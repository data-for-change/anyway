"""remove work_on_behalf_of_organization from Users table

Revision ID: 0b877ab8221c
Revises: d2dfd0ce5a7e
Create Date: 2021-09-22 13:50:55.411517

"""

# revision identifiers, used by Alembic.
revision = '0b877ab8221c'
down_revision = 'd2dfd0ce5a7e'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column("users", "work_on_behalf_of_organization")


def downgrade():
    op.add_column(
        "users", sa.Column("work_on_behalf_of_organization", sa.String(128), nullable=True)
    )
