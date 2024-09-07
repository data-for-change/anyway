"""add numeric indexes

Revision ID: 97740b33407d
Revises: 53d0b00fb750
Create Date: 2024-08-24 11:19:33.674396

"""

# revision identifiers, used by Alembic.
revision = '97740b33407d'
down_revision = '53d0b00fb750'
branch_labels = None
depends_on = None

from alembic import op
# import sqlalchemy as sa


# pylint: disable=E1101
def upgrade():
    for table in ['markers', 'markers_hebrew']:
        for field in ['yishuv_symbol', 'street1', 'street2']:
            op.create_index(f'ix_{table}_{field}', table, [field], unique=False)
    for table in ['markers_hebrew']:
        for field in ['yishuv_name', 'street1_hebrew', 'street2_hebrew']:
            op.drop_index(f'ix_{table}_{field}', table_name=table)


# pylint: disable=E1101
def downgrade():
    for table in ['markers', 'markers_hebrew']:
        for field in ['yishuv_symbol', 'street1', 'street2']:
            op.drop_index(f'ix_{table}_{field}', table_name=table)
    for table in ['markers_hebrew']:
        for field in ['yishuv_name', 'street1_hebrew', 'street2_hebrew']:
            op.create_index(f'ix_{table}_{field}', table, [field], unique=False)
