"""user permissions management

Revision ID: bd67c88713b8
Revises: 10023013f155
Create Date: 2021-03-31 21:31:47.278834

"""

# revision identifiers, used by Alembic.
import datetime

from sqlalchemy import orm, text

from anyway.backend_constants import BackEndConstants

revision = "bd67c88713b8"
down_revision = "10023013f155"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

ADMIN_EMAIL = "anyway@anyway.co.il"


def upgrade():
    op.create_table(
        "roles2",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("name", sa.String(127), unique=True, index=True, nullable=False),
        sa.Column("description", sa.String(255)),
        sa.Column("create_date", sa.DateTime(), nullable=False, server_default=text('now()')),
    )

    op.create_table(
        "users_to_roles2",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column(
            "user_id", sa.BigInteger(), sa.ForeignKey("user_oauth.id"), index=True, nullable=False
        ),
        sa.Column("roles2_id", sa.Integer(), sa.ForeignKey("roles2.id"), index=True, nullable=False),
        sa.Column("create_date", sa.DateTime(), nullable=False, server_default=text('now()')),
    )

    from anyway.models import Roles2, UserOAuth, users_to_roles2

    bind = op.get_bind()
    session = orm.Session(bind=bind)

    role_admins = Roles2(
        name=BackEndConstants.Roles2Names.Admins,
        description="This is the default admin role.",
        create_date=datetime.datetime.now(),
    )
    session.add(role_admins)

    res = (
        session.query(UserOAuth)
        .with_entities(UserOAuth.email)
        .filter(UserOAuth.email == ADMIN_EMAIL)
        .first()
    )
    if res is None:
        user = UserOAuth(
            user_register_date=datetime.datetime.now(),
            user_last_login_date=datetime.datetime.now(),
            email=ADMIN_EMAIL,
            oauth_provider_user_name=ADMIN_EMAIL,
            is_active=True,
            oauth_provider="google",
            is_user_completed_registration=True,
            oauth_provider_user_id="unknown-manual-insert",
        )
        session.add(user)

    user_id = (
        session.query(UserOAuth)
        .with_entities(UserOAuth.id)
        .filter(UserOAuth.email == ADMIN_EMAIL)
        .first()
    )

    role_id = (
        session.query(Roles2).with_entities(Roles2.id).filter(Roles2.name == "admins").first()
    )

    insert_users_to_roles2 = users_to_roles2.insert().values(
        user_id=user_id.id,
        roles2_id=role_id.id,
        create_date=datetime.datetime.now(),
    )
    session.execute(insert_users_to_roles2)

    session.commit()


def downgrade():
    op.drop_table("users_to_roles2")
    op.drop_table("roles2")
