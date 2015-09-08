"""create fk from vehicles and involved to markers on id and provider_code

Revision ID: 1569548127f0
Revises: 
Create Date: 2015-09-07 21:27:30.336635

"""

# revision identifiers, used by Alembic.
revision = '1569548127f0'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_foreign_key(
            'fk_vehicles_markers_pk',
            'vehicles', 'markers',
            ['accident_id', 'provider_code'],
            ['id', 'provider_code'],
            )
    op.create_foreign_key(
            'fk_involved_markers_pk',
            'involved', 'markers',
            ['accident_id', 'provider_code'],
            ['id', 'provider_code'],
            )


def downgrade():
    op.drop_constraint('fk_vehicles_markers_pk', 'vehicles')
    op.drop_constraint('fk_involved_markers_pk', 'involved')
