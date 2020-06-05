"""change_accident_field_to_non_nullable

Revision ID: c7722630e010
Revises: ce386162d9f4
Create Date: 2020-06-04 10:47:17.074670

"""

# revision identifiers, used by Alembic.
revision = 'c7722630e010'
down_revision = 'ce386162d9f4'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    os.execute('UPDATE news_flash SET accident = false WHERE accident is null');
    op.alter_column('news_flash', 'accident',
               existing_type=sa.BOOLEAN(),
               nullable=False)

def downgrade():
    op.alter_column('news_flash', 'accident',
               existing_type=sa.BOOLEAN(),
               nullable=True)
