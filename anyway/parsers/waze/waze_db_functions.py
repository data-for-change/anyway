from anyway.models import WazeAlert, WazeTrafficJams
from anyway.app_and_db import app, db


def insert_waze_alerts(waze_alerts):
    """
    insert new waze alerts to db
    :param waze_alerts_df: DataFrame contains waze alerts
    """

    return _upsert_waze_objects_by_uuid(WazeAlert, waze_alerts)


def insert_waze_traffic_jams(waze_traffic_jams):
    """
    insert new waze traffic jams to db
    :param waze_traffic_jams_df: DataFrame contains waze traffic jams
    """

    return _upsert_waze_objects_by_uuid(WazeTrafficJams, waze_traffic_jams)


def enrich_waze_alerts_ended_at_timestamp(timestamp, latest_waze_objects, back_filled):
    return _enrich_ended_at_timestamp(WazeAlert, timestamp, latest_waze_objects, back_filled)


def enrich_waze_traffic_jams_ended_at_timestamp(timestamp, latest_waze_objects, back_filled):
    return _enrich_ended_at_timestamp(WazeTrafficJams, timestamp, latest_waze_objects, back_filled)


def _upsert_waze_objects_by_uuid(model, waze_objects):
    new_records = 0
    with db.session.no_autoflush:
        for waze_object in waze_objects:
            db.session.flush()
            existing_objects = db.session.query(model).filter(
                model.uuid == str(waze_object["uuid"])
            )
            object_count = existing_objects.count()
            if object_count == 0:
                new_object = model(**waze_object)
                db.session.add(new_object)
                new_records += 1
            elif object_count > 1:

                # sanity: as the uuid field is unique - this should never happen
                raise RuntimeError("Too many waze objects with the same uuid")
            else:

                # update the existing alert
                existing_object = existing_objects[0]
                for key, val in waze_object.items():
                    setattr(existing_object, key, val)

        db.session.commit()
    return new_records


def _enrich_ended_at_timestamp(model, timestamp, latest_waze_objects, back_filled):
    latest_waze_objects_uuids = [waze_object["uuid"] for waze_object in latest_waze_objects]
    query = db.session.query(model).filter(
        model.ended_at_estimate.is_(None),
        model.uuid.in_(latest_waze_objects_uuids),
        model.back_filled.is_(back_filled),
    )
    for waze_object in query:
        waze_object.ended_at_estimate = timestamp
    db.session.commit()
