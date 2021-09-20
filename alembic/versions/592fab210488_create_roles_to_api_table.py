"""create roles_to_api table

Revision ID: 592fab210488
Revises: bc10fd684e42
Create Date: 2021-09-18 15:45:56.555520

"""

# revision identifiers, used by Alembic.
import datetime

from sqlalchemy import text, orm

revision = "592fab210488"
down_revision = "bc10fd684e42"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        "roles_to_api",
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id"), index=True, nullable=False),
        sa.Column("api_name", sa.String(511), index=True, nullable=False),
        sa.Column("create_date", sa.DateTime(), index=True, nullable=False, server_default=text("now()")),
        sa.PrimaryKeyConstraint("role_id", "api_name"),
    )

    bind = op.get_bind()
    session = orm.Session(bind=bind)
    init_table_with_default_roles(session)
    session.commit()


def init_table_with_default_roles(session: orm.Session):
    from anyway.models import Roles
    role_id = session.query(Roles).with_entities(Roles.id).filter(Roles.name == "admins").first()

    session.add(get_new_row_for_RolesToAPI(role_id=role_id, api_name="/admin/get_all_users_info"))
    session.add(get_new_row_for_RolesToAPI(role_id=role_id, api_name="/user/add_role"))
    session.add(get_new_row_for_RolesToAPI(role_id=role_id, api_name="/admin/update_user"))
    session.add(get_new_row_for_RolesToAPI(role_id=role_id, api_name="/user/add_to_role"))
    session.add(get_new_row_for_RolesToAPI(role_id=role_id, api_name="/user/remove_from_role"))
    session.add(get_new_row_for_RolesToAPI(role_id=role_id, api_name="/user/change_user_active_mode"))
    session.add(get_new_row_for_RolesToAPI(role_id=role_id, api_name="/admin/get_roles_to_api"))
    session.add(get_new_row_for_RolesToAPI(role_id=role_id, api_name="/user/get_roles_list"))


def get_new_row_for_RolesToAPI(role_id: int, api_name: str):
    from anyway.models import RolesToAPI
    return RolesToAPI(
        role_id=role_id,
        api_name=api_name,
        create_date=datetime.datetime.now(),
    )


def downgrade():
    op.drop_table("roles_to_api")
