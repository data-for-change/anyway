"""waze_rotation_triggers

Revision ID: e3b76e3753d6
Revises: 3e59d406d707
Create Date: 2020-10-20 13:41:47.521190

"""

# revision identifiers, used by Alembic.
revision = 'e3b76e3753d6'
down_revision = '3e59d406d707'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.execute("""
CREATE FUNCTION rotate_waze_alerts() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  DELETE FROM waze_alerts WHERE created_at < NOW() - INTERVAL '6 months';
  RETURN NULL;
END;
$$;

CREATE TRIGGER rotate_waze_alerts_trigger
    AFTER INSERT ON waze_alerts
    EXECUTE PROCEDURE rotate_waze_alerts();

CREATE FUNCTION rotate_waze_traffic_jams() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  DELETE FROM waze_traffic_jams WHERE created_at < NOW() - INTERVAL '6 months';
  RETURN NULL;
END;
$$;

CREATE TRIGGER rotate_waze_traffic_jams_trigger
    AFTER INSERT ON waze_traffic_jams
    EXECUTE PROCEDURE rotate_waze_traffic_jams();

""")


def downgrade():
    op.execute("""
DROP TRIGGER rotate_waze_alerts_trigger ON waze_alerts;
DROP FUNCTION rotate_waze_alerts;
DROP TRIGGER rotate_waze_traffic_jams_trigger ON waze_traffic_jams;
DROP FUNCTION rotate_waze_traffic_jams;
""")
