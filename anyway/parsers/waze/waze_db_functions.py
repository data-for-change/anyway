from flask_sqlalchemy import SQLAlchemy
from anyway.utilities import init_flask
from anyway.models import WazeAlert, WazeTrafficJams

def insert_waze_alerts(waze_alerts):
    """
    insert new waze alerts to db
    :param waze_alerts_df: DataFrame contains waze alerts
    """

    app = init_flask()
    db = SQLAlchemy(app)

    db.session.bulk_insert_mappings(WazeAlert, waze_alerts)
    db.session.commit()


def insert_waze_traffic_jams(waze_traffic_jams):
    """
    insert new waze traffic jams to db
    :param waze_traffic_jams_df: DataFrame contains waze traffic jams
    """

    app = init_flask()
    db = SQLAlchemy(app)

    db.session.bulk_insert_mappings(WazeTrafficJams, waze_traffic_jams)
    db.session.commit()