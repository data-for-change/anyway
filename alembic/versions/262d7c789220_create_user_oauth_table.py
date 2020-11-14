"""Create user_oauth table

Revision ID: 262d7c789220
Revises: 9687ef04f99d
Create Date: 2020-11-14 17:43:42.489837

"""

# revision identifiers, used by Alembic.
revision = '262d7c789220'
down_revision = '9687ef04f99d'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    """I am separating the user specific data and the provider user specific data by name, for example:
        I assume that the user email address should be the same no matter what service it is,
        but the user profile url is specific to that provider -
        the user will have the same email on facebook & google but a different user profile url on google and facebook"""

    op.create_table('user_oauth',
                    sa.Column('id', sa.BigInteger, autoincrement=True, nullable=False, primary_key=True, index=True),
                    sa.Column('user_register_date', sa.DateTime, nullable=False),
                    sa.Column('user_last_login_date', sa.DateTime, nullable=False),
                    sa.Column('email', sa.String(255), nullable=True, index=True),
                    sa.Column('name', sa.String(255), nullable=True),
                    sa.Column('is_active', sa.Boolean, nullable=True),
                    sa.Column('oauth_provider', sa.String(64), nullable=False, index=True),
                    sa.Column('oauth_provider_user_id', sa.String, nullable=False, index=True),
                    sa.Column('oauth_provider_user_domain', sa.String, nullable=True),
                    sa.Column('oauth_provider_user_picture_url', sa.String, nullable=True),
                    sa.Column('oauth_provider_user_locale', sa.String(64), nullable=True),
                    sa.Column('oauth_provider_user_profile_url', sa.String, nullable=True),
                    sa.Column('work_on_behalf_of_organization', sa.String(128), nullable=True),
                    )


def downgrade():
    op.drop_table('user_oauth')