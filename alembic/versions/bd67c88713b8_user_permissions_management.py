"""user permissions management

Revision ID: bd67c88713b8
Revises: 10023013f155
Create Date: 2021-03-31 21:31:47.278834

"""

# revision identifiers, used by Alembic.
import datetime

from sqlalchemy import orm, text
from sqlalchemy.engine.reflection import Inspector

from anyway.backend_constants import BackEndConstants

revision = "bd67c88713b8"
down_revision = "10023013f155"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

ADMIN_EMAIL = "anyway@anyway.co.il"


def get_tables_names() -> [str]:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()
    return tables


def upgrade():
    # In cases of downgrade and upgrade those tables will no longer exits - and so the transaction will fail
    tables_names = get_tables_names()
    for table_name in [
        "roles_users",
        "roles",
        "report_preferences",
        "general_preferences",
    ]:
        if table_name in tables_names:
            op.drop_table(table_name)

    if "user_oauth" in tables_names:
        if "users" in tables_names:
            op.drop_table("users")
        op.rename_table("user_oauth", "users")

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("name", sa.String(127), unique=True, index=True, nullable=False),
        sa.Column("description", sa.String(255)),
        sa.Column("create_date", sa.DateTime(), nullable=False, server_default=text("now()")),
    )

    op.create_table(
        "users_to_roles",
        sa.Column(
            "user_id", sa.BigInteger(), sa.ForeignKey("users.id"), index=True, nullable=False
        ),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id"), index=True, nullable=False),
        sa.Column("create_date", sa.DateTime(), nullable=False, server_default=text("now()")),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
    )

    from anyway.models import Roles, Users, users_to_roles

    bind = op.get_bind()
    session = orm.Session(bind=bind)

    role_admins = Roles(
        name=BackEndConstants.Roles2Names.Admins.value,
        description="This is the default admin role.",
        create_date=datetime.datetime.now(),
    )
    session.add(role_admins)

    res = session.query(Users).with_entities(Users.email).filter(Users.email == ADMIN_EMAIL).first()
    if res is None:
        user = Users(
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
        session.query(Users).with_entities(Users.id).filter(Users.email == ADMIN_EMAIL).first()
    )

    role_id = session.query(Roles).with_entities(Roles.id).filter(Roles.name == "admins").first()

    insert_users_to_roles = users_to_roles.insert().values(
        user_id=user_id.id,
        role_id=role_id.id,
        create_date=datetime.datetime.now(),
    )
    session.execute(insert_users_to_roles)

    session.commit()


def downgrade():
    op.drop_table("users_to_roles")
    op.drop_table("roles")
    # Some of the changes are irreversible
