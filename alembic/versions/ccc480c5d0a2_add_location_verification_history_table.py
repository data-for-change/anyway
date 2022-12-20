"""add_location_verification_history_table

Revision ID: ccc480c5d0a2
Revises: c819d65fd831
Create Date: 2022-09-17 12:27:27.378408

"""

# revision identifiers, used by Alembic.
revision = "ccc480c5d0a2"
down_revision = "c819d65fd831"
branch_labels = None
depends_on = None

from alembic import op
from sqlalchemy import ForeignKey, text
import sqlalchemy as sa


def upgrade():
    op.create_table(
        "location_verification_history",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), ForeignKey("users.id"), nullable=False),
        sa.Column("news_flash_id", sa.BigInteger(), ForeignKey("news_flash.id"), nullable=False),
        sa.Column("location_verification_before_change", sa.Integer(), nullable=False),
        sa.Column("location_before_change", sa.Text(), nullable=False),
        sa.Column("location_verification_after_change", sa.Integer(), nullable=False),
        sa.Column("location_after_change", sa.Text(), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=False,  default=text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("location_verification_history")
