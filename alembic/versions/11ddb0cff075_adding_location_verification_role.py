"""adding location verification role

Revision ID: 11ddb0cff075
Revises: fe08b885a23f
Create Date: 2024-04-21 06:18:03.777200

"""

# revision identifiers, used by Alembic.
revision = '11ddb0cff075'
down_revision = 'fe08b885a23f'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Use raw SQL to avoid schema mismatch with future 'app' column addition
    op.execute("""
        INSERT INTO roles (name, description, create_date)
        VALUES ('location_verification', 'Allows user to change and verify newsflash location.', now())
    """)


def downgrade():
    # Use raw SQL to avoid schema mismatch with future 'app' column addition
    op.execute("""
        DELETE FROM roles WHERE name = 'location_verification'
    """)
