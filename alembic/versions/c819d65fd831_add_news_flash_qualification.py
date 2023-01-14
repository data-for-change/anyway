"""add news flash qualification

Revision ID: c819d65fd831
Revises: fe6dcd0178f7
Create Date: 2022-08-05 21:03:00.853536

"""

# revision identifiers, used by Alembic.
revision = "c819d65fd831"
down_revision = "fe6dcd0178f7"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    from anyway.backend_constants import NewsflashLocationQualification
    op.add_column(
        "news_flash",
        sa.Column(
            "newsflash_location_qualification",
            sa.Integer(),
            server_default=sa.text(f"{NewsflashLocationQualification.NOT_VERIFIED.value}"),
        ),
    )
    op.add_column(
        "news_flash", sa.Column("location_qualifying_user", sa.BigInteger(), nullable=True)
    )


def downgrade():
    op.drop_column("news_flash", "newsflash_location_qualification")
    op.drop_column("news_flash", "location_qualifying_user")
