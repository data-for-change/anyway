"""added indices to involved markers

Revision ID: d9cb98c752d4
Revises: 26c3c9c4eb53
Create Date: 2023-04-07 15:16:09.370327

"""

# revision identifiers, used by Alembic.
revision = 'd9cb98c752d4'
down_revision = '26c3c9c4eb53'
branch_labels = None
depends_on = None

from alembic import op

def upgrade():
    op.create_index('inv_markers_accident_yishuv_symbol_idx', 'involved_markers_hebrew', ['accident_yishuv_symbol'], unique=False)
    op.create_index('inv_markers_injury_severity_idx', 'involved_markers_hebrew', ['injury_severity'], unique=False)
    op.create_index('inv_markers_involve_vehicle_type_idx', 'involved_markers_hebrew', ['involve_vehicle_type'], unique=False)


def downgrade():
    op.drop_index('inv_markers_involve_vehicle_type_idx', table_name='involved_markers_hebrew')
    op.drop_index('inv_markers_injury_severity_idx', table_name='involved_markers_hebrew')
    op.drop_index('inv_markers_accident_yishuv_symbol_idx', table_name='involved_markers_hebrew')