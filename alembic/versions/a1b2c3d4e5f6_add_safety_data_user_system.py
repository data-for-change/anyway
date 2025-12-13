"""Add safety data user system

Revision ID: a1b2c3d4e5f6
Revises: 41af3263a5a3
Create Date: 2025-11-24 12:00:00.000000

"""
import datetime
from sqlalchemy import orm, text
from sqlalchemy.engine.reflection import Inspector
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '41af3263a5a3'
branch_labels = None
depends_on = None
existing_tables = ['users', 'roles', 'organization', 'users_to_roles', 'users_to_organizations']
ANYWAY_APP_ID_STR = '0'
SAFETY_DATA_APP_ID = 1

def upgrade():
    # Drop non-PK constraints and non-primary indexes on users (PostgreSQL)
    for table in existing_tables:
        op.execute(f"""
    DO $$
    DECLARE r RECORD;
    BEGIN
      -- Drop constraints except primary keys
      FOR r IN
        SELECT c.conname, n.nspname, t.relname
        FROM pg_constraint c
        JOIN pg_class t ON c.conrelid = t.oid
        JOIN pg_namespace n ON t.relnamespace = n.oid
        WHERE t.relname = '{table}' AND n.nspname = 'public' AND c.contype <> 'p'
      LOOP
        EXECUTE format('ALTER TABLE %I.%I DROP CONSTRAINT IF EXISTS %I CASCADE', r.nspname, r.relname, r.conname);
      END LOOP;

      -- Drop indexes that are not primary indexes
      FOR r IN
        SELECT n.nspname, i.relname as indexname
        FROM pg_index idx
        JOIN pg_class i ON i.oid = idx.indexrelid
        JOIN pg_class t ON t.oid = idx.indrelid
        JOIN pg_namespace n ON i.relnamespace = n.oid
        WHERE t.relname = '{table}' AND n.nspname = 'public' AND NOT idx.indisprimary
      LOOP
        EXECUTE format('DROP INDEX IF EXISTS %I.%I', r.nspname, r.indexname);
      END LOOP;
    END$$;
        """)
    # Add app column to users table (0 = ANYWAY, 1 = SAFETY_DATA)
    op.add_column('users', sa.Column('app', sa.Integer(), nullable=False, server_default=ANYWAY_APP_ID_STR))
    op.alter_column('users', 'app', server_default=None)
    op.create_index(op.f('ix_users_email_app'), 'users', ['email', 'app'], unique=True)

    # Add app column to roles table (0 = ANYWAY, 1 = SAFETY_DATA)
    op.add_column('roles', sa.Column('app', sa.Integer(), nullable=False, server_default=ANYWAY_APP_ID_STR))
    op.alter_column('roles', 'app', server_default=None)
    op.create_index(op.f('ix_roles_name_app'), 'roles', ['name', 'app'], unique=True)

    # Add app column to organization table (0 = ANYWAY, 1 = SAFETY_DATA)
    op.add_column('organization', sa.Column('app', sa.Integer(), nullable=False, server_default=ANYWAY_APP_ID_STR))
    op.alter_column('organization', 'app', server_default=None)
    op.create_index(op.f('ix_organization_name_app'), 'organization', ['name', 'app'], unique=True)

    # Add app column to users_to_roles table
    op.add_column('users_to_roles', sa.Column('app', sa.Integer(), nullable=False, server_default=ANYWAY_APP_ID_STR))
    op.alter_column('users_to_roles', 'app', server_default=None)
    # op.drop_constraint('users_to_roles_pkey', 'users_to_roles', type_='primary')
    op.create_index('ix_users_to_roles_user_role_app', 'users_to_roles', ['user_id', 'role_id', 'app'],
                     unique=True)

    # Add app column to users_to_organizations table
    op.add_column('users_to_organizations', sa.Column('app', sa.Integer(), nullable=False,
                                                       server_default=ANYWAY_APP_ID_STR))
    op.alter_column('users_to_organizations', 'app', server_default=None)
    op.create_index('ix_users_to_organizations_user_org_app', 'users_to_organizations',
                    ['user_id', 'organization_id', 'app'], unique=True)

    # Create grants table
    op.create_table('grants',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('app', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('create_date', sa.DateTime(), server_default=text('now()'), nullable=False),
    )
    op.create_index(op.f('ix_grants_name_app'), 'grants', ['name', 'app'], unique=True)

    # Create users_to_grants table
    op.create_table('users_to_grants',
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('grant_id', sa.Integer(), nullable=False),
        sa.Column('app', sa.Integer(), nullable=False),
        sa.Column('create_date', sa.DateTime(), server_default=text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['grant_id'], ['grants.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    )
    op.create_index(op.f('ix_users_to_grants_user_id'), 'users_to_grants', ['user_id'], unique=False)
    op.create_index('ix_users_to_grants_user_grant_app', 'users_to_grants', ['user_id', 'grant_id', 'app'], unique=True)

    # Insert default roles for safety_data (app = 1)
    op.execute(f"""INSERT INTO roles (name, description, app, create_date)
                   VALUES ('anonymous', 'Anonymous user', {SAFETY_DATA_APP_ID}, now())""")
    op.execute(f"""INSERT INTO roles (name, description, app, create_date)
                   VALUES ('authenticated', 'Basic authenticated user', {SAFETY_DATA_APP_ID}, now())""")
    op.execute(f"""INSERT INTO roles (name, description, app, create_date)
                   VALUES ('admins', 'Safety-Data administrator', {SAFETY_DATA_APP_ID}, now())""")

    add_builtin_safety_data_admin()


def downgrade():
    # Remove default roles (app = 1 for safety_data)
    for table in existing_tables:
        op.execute(f"DELETE FROM {table} WHERE app = 1")

    # Revert users_to_grants table
    op.drop_table('users_to_grants')
    op.drop_table('grants')

    # users_to_organizations
    op.drop_index('ix_users_to_organizations_user_org_app', table_name='users_to_organizations')
    op.create_index('ix_users_to_organizations_user_org', 'users_to_organizations', ['user_id', 'organization_id'], unique=True)
    op.drop_column('users_to_organizations', 'app')

    # Revert users_to_roles table
    op.drop_index('ix_users_to_roles_user_role_app', table_name='users_to_roles')
    op.create_index('ix_users_to_roles_user_role', 'users_to_roles', ['user_id', 'role_id'], unique=True)
    op.drop_column('users_to_roles', 'app')

    # Revert organization table
    op.drop_index(op.f('ix_organization_name_app'), table_name='organization')
    op.create_index('ix_organization_name', 'organization', ['name'], unique=True)
    # op.create_unique_constraint('organization_name_key', 'organization', ['name']) # Implicitly created by unique index?
    op.drop_column('organization', 'app')

    # Revert roles table
    op.drop_index(op.f('ix_roles_name_app'), table_name='roles')
    op.create_index('ix_roles_name', 'roles', ['name'], unique=True)
    # op.create_unique_constraint('roles_name_key', 'roles', ['name'])
    op.drop_column('roles', 'app')

    # Revert users table
    op.drop_index(op.f('ix_users_email_app'), table_name='users')
    op.drop_column('users', 'app')

def add_builtin_safety_data_admin():
    from anyway.models import Roles, Users, users_to_roles

    ADMIN_EMAIL = "anyway@anyway.co.il"
    bind = op.get_bind()
    session = orm.Session(bind=bind)

    res = session.query(Users).with_entities(Users.email) \
            .filter(Users.email == ADMIN_EMAIL, Users.app == SAFETY_DATA_APP_ID).first()
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
            app=SAFETY_DATA_APP_ID,
        )
        session.add(user)

    user_id = (
        session.query(Users).with_entities(Users.id).filter(
            Users.email == ADMIN_EMAIL, Users.app == SAFETY_DATA_APP_ID
        ).first()
    )

    role_id = session.query(Roles).with_entities(Roles.id).filter(
        Roles.name == "admins", Roles.app == SAFETY_DATA_APP_ID
    ).first()

    insert_users_to_roles = users_to_roles.insert().values(
        user_id=user_id.id,
        role_id=role_id.id,
        app=SAFETY_DATA_APP_ID,
        create_date=datetime.datetime.now(),
    )
    session.execute(insert_users_to_roles)

    session.commit()
