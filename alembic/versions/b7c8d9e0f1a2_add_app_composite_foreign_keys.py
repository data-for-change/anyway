"""Add app-aware composite foreign keys to user association tables

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-01-02 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b7c8d9e0f1a2'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add composite foreign key constraints to ensure app-level data integrity.
    This ensures that:
    - users_to_roles references only users and roles from the same app
    - users_to_organizations references only users and organizations from the same app
    - users_to_grants references only users and grants from the same app
    """

    # First, add unique constraints on (id, app) for the referenced tables
    # These are needed for composite foreign keys
    op.create_index('ix_users_id_app', 'users', ['id', 'app'], unique=True)
    op.create_index('ix_roles_id_app', 'roles', ['id', 'app'], unique=True)
    op.create_index('ix_organization_id_app', 'organization', ['id', 'app'], unique=True)
    op.create_index('ix_grants_id_app', 'grants', ['id', 'app'], unique=True)

    # Add composite foreign key constraint to users_to_roles
    # This ensures user_id and role_id both exist and have matching app values
    op.create_foreign_key(
        'fk_users_to_roles_user_app',
        'users_to_roles', 'users',
        ['user_id', 'app'], ['id', 'app'],
        ondelete='CASCADE'
    )

    op.create_foreign_key(
        'fk_users_to_roles_role_app',
        'users_to_roles', 'roles',
        ['role_id', 'app'], ['id', 'app'],
        ondelete='CASCADE'
    )

    # Add composite foreign key constraint to users_to_organizations
    # This ensures user_id and organization_id both exist and have matching app values
    op.create_foreign_key(
        'fk_users_to_organizations_user_app',
        'users_to_organizations', 'users',
        ['user_id', 'app'], ['id', 'app'],
        ondelete='CASCADE'
    )

    op.create_foreign_key(
        'fk_users_to_organizations_org_app',
        'users_to_organizations', 'organization',
        ['organization_id', 'app'], ['id', 'app'],
        ondelete='CASCADE'
    )

    # Add composite foreign key constraint to users_to_grants
    # This ensures user_id and grant_id both exist and have matching app values
    op.create_foreign_key(
        'fk_users_to_grants_user_app',
        'users_to_grants', 'users',
        ['user_id', 'app'], ['id', 'app'],
        ondelete='CASCADE'
    )

    op.create_foreign_key(
        'fk_users_to_grants_grant_app',
        'users_to_grants', 'grants',
        ['grant_id', 'app'], ['id', 'app'],
        ondelete='CASCADE'
    )


def downgrade():
    """
    Remove composite foreign key constraints and unique indexes.
    """

    # Drop foreign key constraints
    op.drop_constraint('fk_users_to_grants_grant_app', 'users_to_grants', type_='foreignkey')
    op.drop_constraint('fk_users_to_grants_user_app', 'users_to_grants', type_='foreignkey')
    op.drop_constraint('fk_users_to_organizations_org_app', 'users_to_organizations', type_='foreignkey')
    op.drop_constraint('fk_users_to_organizations_user_app', 'users_to_organizations', type_='foreignkey')
    op.drop_constraint('fk_users_to_roles_role_app', 'users_to_roles', type_='foreignkey')
    op.drop_constraint('fk_users_to_roles_user_app', 'users_to_roles', type_='foreignkey')

    # Drop unique indexes
    op.drop_index('ix_grants_id_app', table_name='grants')
    op.drop_index('ix_organization_id_app', table_name='organization')
    op.drop_index('ix_roles_id_app', table_name='roles')
    op.drop_index('ix_users_id_app', table_name='users')
