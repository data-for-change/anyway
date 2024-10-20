"""add street numeric indexes to involved heberw

Revision ID: e962054e4422
Revises: mn9px8cacn24
Create Date: 2024-10-20 08:24:08.746964

"""

# revision identifiers, used by Alembic.
revision = 'e962054e4422'
down_revision = 'mn9px8cacn24'
branch_labels = None
depends_on = None

from alembic import op
# import sqlalchemy as sa


def upgrade():
    op.create_index('ix_involved_markers_hebrew_street1',
                    'involved_markers_hebrew', ['street1'], unique=False)
    op.create_index('ix_involved_markers_hebrew_street2',
                    'involved_markers_hebrew', ['street2'], unique=False)


def downgrade():
    op.drop_index('ix_involved_markers_hebrew_street1', 'involved_markers_hebrew')
    op.drop_index('ix_involved_markers_hebrew_street2', 'involved_markers_hebrew')
