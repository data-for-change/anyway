"""comment schema

Revision ID: 4351468c3446
Revises: d9cb98c752d4
Create Date: 2023-08-16 13:52:26.245990

"""

# revision identifiers, used by Alembic.
revision = '4351468c3446'
down_revision = 'd9cb98c752d4'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.create_table('comments',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('author', sa.Integer(), nullable=False),
    sa.Column('parent', sa.Integer(), nullable=True),
    sa.Column('created_time', sa.DateTime(), nullable=True),
    sa.Column('street', sa.Text(), nullable=True),
    sa.Column('city', sa.Text(), nullable=True),
    sa.Column('road_segment_id', sa.Integer(), nullable=True),
    sa.Column('type', sa.Enum('REGION', 'DISTRICT', 'CITY', 'STREET', 'URBAN_JUNCTION', 'SUBURBAN_ROAD', 'SUBURBAN_JUNCTION', 'OTHER', name='resolutioncategories'), nullable=False),
    sa.ForeignKeyConstraint(['author'], ['users.id'], ),
    sa.ForeignKeyConstraint(['parent'], ['comments.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_comments_city'), 'comments', ['city'], unique=False)
    op.create_index(op.f('ix_comments_created_time'), 'comments', ['created_time'], unique=False)
    op.create_index(op.f('ix_comments_id'), 'comments', ['id'], unique=False)
    op.create_index(op.f('ix_comments_road_segment_id'), 'comments', ['road_segment_id'], unique=False)
    op.create_index(op.f('ix_comments_street'), 'comments', ['street'], unique=False)
    op.create_index(op.f('ix_comments_type'), 'comments', ['type'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_comments_type'), table_name='comments')
    op.drop_index(op.f('ix_comments_street'), table_name='comments')
    op.drop_index(op.f('ix_comments_road_segment_id'), table_name='comments')
    op.drop_index(op.f('ix_comments_id'), table_name='comments')
    op.drop_index(op.f('ix_comments_created_time'), table_name='comments')
    op.drop_index(op.f('ix_comments_city'), table_name='comments')
    op.drop_table('comments')
    # ### end Alembic commands ###
