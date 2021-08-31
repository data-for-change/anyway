"""remove work_on_behalf_of_organization from Users table

Revision ID: bc10fd684e42
Revises: bd67c88713b8
Create Date: 2021-08-31 19:24:43.751675

"""

# revision identifiers, used by Alembic.
revision = "bc10fd684e42"
down_revision = "bd67c88713b8"
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
