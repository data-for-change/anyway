"""create cities vehicles registered table

Revision ID: 6708baa8438
Revises: 333c6c0afa8f
Create Date: 2017-11-05 20:58:42.080047

"""

# revision identifiers, used by Alembic.
revision = '6708baa8438'
down_revision = '333c6c0afa8f'
branch_labels = None
depends_on = None

import sqlalchemy as sa
from alembic import op

_table_name = "cities_vehicles_registered"


def downgrade():
    op.drop(_table_name)


def upgrade():
    op.create_table(
        _table_name,
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('city_id', sa.Integer(), nullable=True),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('name_eng', sa.String(length=100), nullable=True),
        sa.Column('motorcycle', sa.Integer(), nullable=False),
        sa.Column('special', sa.Integer(), nullable=False),
        sa.Column('taxi', sa.Integer(), nullable=False),
        sa.Column('bus', sa.Integer(), nullable=False),
        sa.Column('minibus', sa.Integer(), nullable=False),
        sa.Column('truck_over3500', sa.Integer(), nullable=False),
        sa.Column('truck_upto3500', sa.Integer(), nullable=False),
        sa.Column('private', sa.Integer(), nullable=False),
        sa.Column('population_year', sa.Integer(), nullable=False),
        sa.Column('population', sa.Integer(), nullable=False),
        sa.Column('total', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name','year','population_year')
    )
