"""Add organization tables

Revision ID: 30862849651c
Revises: ac561a960f20
Create Date: 2021-10-23 16:52:43.391156

"""

# revision identifiers, used by Alembic.
from sqlalchemy import text

revision = '30862849651c'
down_revision = 'ac561a960f20'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table("organization",
                    sa.Column('name', sa.String(255), primary_key=True, unique=True, nullable=False, index=True),
                    sa.Column("create_date", sa.DateTime(), nullable=False, server_default=text("now()")),
                    )
    op.create_table(
        "users_to_organizations",
        sa.Column(
            "user_id", sa.BigInteger(), sa.ForeignKey("users.id"), index=True, nullable=False
        ),
        sa.Column("organization_name", sa.String(255), sa.ForeignKey("organization.name"), index=True, nullable=False),
        sa.Column("create_date", sa.DateTime(), nullable=False, server_default=text("now()")),
        sa.PrimaryKeyConstraint("user_id", "organization_name"),
    )


def downgrade():
    op.drop_table("users_to_organizations")
    op.drop_table("organization")
