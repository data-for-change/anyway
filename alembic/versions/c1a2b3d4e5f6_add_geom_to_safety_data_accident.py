"""add geom column to safety_data_accident

Revision ID: c1a2b3d4e5f6
Revises: e55bdf34f0f0
Create Date: 2026-07-02 18:48:00.000000

"""

# revision identifiers, used by Alembic.
revision = 'c1a2b3d4e5f6'
down_revision = 'e55bdf34f0f0'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    conn = op.get_bind()
    conn.execute(
        "SELECT AddGeometryColumn('public','safety_data_accident','geom',4326,'POINT',2);"
    )
    conn.execute(
        "UPDATE safety_data_accident "
        "SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326) "
        "WHERE longitude IS NOT NULL AND latitude IS NOT NULL;"
    )
    conn.execute(
        "CREATE INDEX idx_safety_data_accident_geom "
        "ON safety_data_accident USING GIST(geom);"
    )


def downgrade():
    conn = op.get_bind()
    conn.execute('DROP INDEX IF EXISTS idx_safety_data_accident_geom;')
    op.drop_column('safety_data_accident', 'geom')
