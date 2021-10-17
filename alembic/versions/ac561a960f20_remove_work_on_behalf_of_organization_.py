"""Remove work_on_behalf_of_organization from Users table

Revision ID: ac561a960f20
Revises: 2dcc57ee1757
Create Date: 2021-10-13 00:07:12.033996

"""

# revision identifiers, used by Alembic.
revision = 'ac561a960f20'
down_revision = '2dcc57ee1757'
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

