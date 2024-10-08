"""Removed waze uuid unique constraints and foreign key from newsflash

Revision ID: ef627578319a
Revises: bd67c88713b8
Create Date: 2021-09-01 09:58:22.269256

"""

# revision identifiers, used by Alembic.
revision = 'ef627578319a'
down_revision = 'bd67c88713b8'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('news_flash_waze_alert_fkey', 'news_flash', type_='foreignkey')
    op.drop_column('news_flash', 'waze_alert')
    op.drop_index('ix_waze_alerts_uuid', table_name='waze_alerts')
    op.create_index(op.f('ix_waze_alerts_uuid'), 'waze_alerts', ['uuid'], unique=False)
    op.drop_index('ix_waze_traffic_jams_uuid', table_name='waze_traffic_jams')
    op.create_index(op.f('ix_waze_traffic_jams_uuid'), 'waze_traffic_jams', ['uuid'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_waze_traffic_jams_uuid'), table_name='waze_traffic_jams')
    op.create_index('ix_waze_traffic_jams_uuid', 'waze_traffic_jams', ['uuid'], unique=True)
    op.drop_index(op.f('ix_waze_alerts_uuid'), table_name='waze_alerts')
    op.create_index('ix_waze_alerts_uuid', 'waze_alerts', ['uuid'], unique=True)
    op.add_column('news_flash', sa.Column('waze_alert', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key('news_flash_waze_alert_fkey', 'news_flash', 'waze_alerts', ['waze_alert'], ['id'])
    # ### end Alembic commands ###
