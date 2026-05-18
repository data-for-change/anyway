"""adding junction and junction_arm tables

Revision ID: 39966aa5db4d
Revises: c5d5e94fb059
Create Date: 2026-02-10 16:45:35.963690

"""

# revision identifiers, used by Alembic.
revision = '39966aa5db4d'
down_revision = 'c5d5e94fb059'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'junction',
        sa.Column('junction', sa.Integer(), nullable=False),
        sa.Column('junction_hebrew', sa.String(length=100), nullable=True),
        sa.Column('x', sa.Float(), nullable=True),
        sa.Column('y', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('junction'),
    )
    op.create_table(
        'junction_arm',
        sa.Column('arm_symbol', sa.Integer(), nullable=False),
        sa.Column('junction_symbol', sa.Integer(), nullable=True),
        sa.Column('is_suburban', sa.Boolean(), nullable=True),
        sa.Column('road_symbol', sa.Integer(), nullable=True),
        sa.Column('km', sa.Float(), nullable=True),
        sa.Column('yishuv_symbol', sa.Integer(), nullable=True),
        sa.Column('street_symbol', sa.Integer(), nullable=True),
        sa.Column('arm_name', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('arm_symbol'),
    )
    op.create_index(op.f('ix_junction_arm_arm_symbol'), 'junction_arm', ['arm_symbol'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_junction_arm_arm_symbol'), table_name='junction_arm')
    op.drop_table('junction_arm')
    op.drop_table('junction')
    # ### end Alembic commands ###
