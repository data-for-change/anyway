"""adding cross columns to involved

Revision ID: 237ab8f171d0
Revises: ef951922e4ef
Create Date: 2026-02-12 20:56:58.410115
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "237ab8f171d0"
down_revision = "ef951922e4ef"
branch_labels = None
depends_on = None


def upgrade():
    # involved (raw)
    op.add_column("involved", sa.Column("cross_direction", sa.Integer(), nullable=True))
    op.add_column("involved", sa.Column("cross_location", sa.Integer(), nullable=True))
    op.add_column("involved", sa.Column("cross_mode", sa.Integer(), nullable=True))
    op.add_column("involved", sa.Column("didnt_cross", sa.Integer(), nullable=True))

    # involved_hebrew (decorated)
    op.add_column("involved_hebrew", sa.Column("cross_direction", sa.Integer(), nullable=True))
    op.add_column("involved_hebrew", sa.Column("cross_direction_hebrew", sa.Text(), nullable=True))

    op.add_column("involved_hebrew", sa.Column("cross_location", sa.Integer(), nullable=True))
    op.add_column("involved_hebrew", sa.Column("cross_location_hebrew", sa.Text(), nullable=True))

    op.add_column("involved_hebrew", sa.Column("cross_mode", sa.Integer(), nullable=True))
    op.add_column("involved_hebrew", sa.Column("cross_mode_hebrew", sa.Text(), nullable=True))

    op.add_column("involved_hebrew", sa.Column("didnt_cross", sa.Integer(), nullable=True))
    op.add_column("involved_hebrew", sa.Column("didnt_cross_hebrew", sa.Text(), nullable=True))


def downgrade():
    # involved_hebrew
    op.drop_column("involved_hebrew", "didnt_cross_hebrew")
    op.drop_column("involved_hebrew", "didnt_cross")
    op.drop_column("involved_hebrew", "cross_mode_hebrew")
    op.drop_column("involved_hebrew", "cross_mode")
    op.drop_column("involved_hebrew", "cross_location_hebrew")
    op.drop_column("involved_hebrew", "cross_location")
    op.drop_column("involved_hebrew", "cross_direction_hebrew")
    op.drop_column("involved_hebrew", "cross_direction")

    # involved
    op.drop_column("involved", "didnt_cross")
    op.drop_column("involved", "cross_mode")
    op.drop_column("involved", "cross_location")
    op.drop_column("involved", "cross_direction")