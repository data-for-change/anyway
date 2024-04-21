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
from sqlalchemy import orm
import datetime


def upgrade():
    from anyway.models import Roles

    bind = op.get_bind()
    session = orm.Session(bind=bind)

    role_location_verification = Roles(
        name="location_verification",
        description="Allows user to change and verify newsflash location.",
        create_date=datetime.datetime.now(),
    )
    session.add(role_location_verification)
    session.commit()


def downgrade():
    from anyway.models import Roles

    bind = op.get_bind()
    session = orm.Session(bind=bind)

    # Delete the role added in the upgrade
    session.query(Roles).filter(Roles.name == "location_verification").delete()

    session.commit()
