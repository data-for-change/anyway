"""create traffic volume table

Revision ID: 7174ff899832
Revises: 3070e32fe18
Create Date: 2019-03-09 17:22:52.517242

"""

# revision identifiers, used by Alembic.
revision = '7174ff899832'
down_revision = '02a8fabf9e53'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('traffic_volume',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('year', sa.Integer(), nullable=True),
                    sa.Column('road', sa.Integer(), nullable=True),
                    sa.Column('section', sa.Integer(), nullable=True),
                    sa.Column('lane', sa.Integer(), nullable=True),
                    sa.Column('month', sa.Integer(), nullable=True),
                    sa.Column('day', sa.Integer(), nullable=True),
                    sa.Column('day_of_week', sa.Integer(), nullable=True),
                    sa.Column('hour', sa.Integer(), nullable=True),
                    sa.Column('volume', sa.Integer(), nullable=False),
                    sa.Column('status', sa.Integer(), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('year', 'road', 'section', 'lane', 'month',
                                            'day', 'day_of_week', 'hour')
                    )


def downgrade():
    op.drop_table('traffic_volume')
