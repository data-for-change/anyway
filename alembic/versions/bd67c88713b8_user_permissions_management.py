"""user permissions management

Revision ID: bd67c88713b8
Revises: 10023013f155
Create Date: 2021-03-31 21:31:47.278834

"""

# revision identifiers, used by Alembic.
from sqlalchemy import text
from sqlalchemy.engine.reflection import Inspector


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

    # Use raw SQL to avoid schema mismatch with future 'app' column addition
    # Insert admin role
    op.execute("""
        INSERT INTO roles (name, description, create_date)
        VALUES ('admins', 'This is the default admin role.', now())
    """)

    # Insert admin user if not exists
    op.execute(f"""
        INSERT INTO users (user_register_date, user_last_login_date, email, oauth_provider_user_name,
                          is_active, oauth_provider, is_user_completed_registration, oauth_provider_user_id)
        SELECT now(), now(), '{ADMIN_EMAIL}', '{ADMIN_EMAIL}',
               true, 'google', true, 'unknown-manual-insert'
        WHERE NOT EXISTS (SELECT 1 FROM users WHERE email = '{ADMIN_EMAIL}')
    """)

    # Insert user-role association
    op.execute(f"""
        INSERT INTO users_to_roles (user_id, role_id, create_date)
        SELECT u.id, r.id, now()
        FROM users u, roles r
        WHERE u.email = '{ADMIN_EMAIL}' AND r.name = 'admins'
        AND NOT EXISTS (
            SELECT 1 FROM users_to_roles utr
            WHERE utr.user_id = u.id AND utr.role_id = r.id
        )
    """)


def downgrade():
    op.drop_table("users_to_roles")
    op.drop_table("roles")
    # Some of the changes are irreversible
