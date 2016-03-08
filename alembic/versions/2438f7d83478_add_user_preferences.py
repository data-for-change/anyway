"""add user preferences

Revision ID: 2438f7d83478
Revises: 40f5c56adfee
Create Date: 2016-03-08 21:20:42.234353

"""

# revision identifiers, used by Alembic.
revision = '2438f7d83478'
down_revision = '40f5c56adfee'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'general_preferences',
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), primary_key=True),
        sa.Column('minimum_displayed_severity', sa.Integer, nullable=True),
        sa.Column('resource_type', sa.String(64), nullable=True),
    )	

    op.create_table(
        'report_preferences',
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), primary_key=True),
        sa.Column('line_number', sa.Integer, primary_key=True),
        sa.Column('historical_report', sa.Boolean, default=False),
        sa.Column('how_many_months_back', sa.Integer, nullable=True),
        sa.Column('latitude', sa.Float),
        sa.Column('longitude', sa.Float),
        sa.Column('radius', sa.Float),
        sa.Column('minimum_severity', sa.Integer),
    )

	
def downgrade():
    op.drop_table('report_preferences')
    op.drop_table('general_preferences')
	
