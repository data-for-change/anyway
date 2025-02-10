import json
import logging
from typing import Iterable, Dict, Any, List
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import and_
from flask import request, Response
from anyway.models import (
    Involved,
    SDAccident,
    SDInvolved,
    AccidentMarkerView,
    Involved,
)
from anyway.app_and_db import db
from anyway.utilities import chunked_generator


def load_data():
    conn = db.get_engine().connect()
    trans = conn.begin()
    sess = sessionmaker()(bind=conn)
    try:
        sess.query(SDInvolved).delete()
        sess.query(SDAccident).delete()
        sd_load_accident(sess)
        sd_load_involved(sess)
        trans.commit()
        return Response(json.dumps("Tables loaded", default=str), mimetype="application/json")
    except Exception as e:
        trans.rollback()
        logging.exception("Error loading data: %s", e)
    finally:
        sess.close()
        conn.close()


def sd_load_involved(sess: Session):
    for chunk in chunked_generator(get_involved_data(sess), 4069):
        sess.execute(SDInvolved.__table__.insert(), chunk)


def get_involved_data(sess: Session):
    for d in (
        sess.query(Involved, SDAccident)
        .join(
            SDAccident,
            and_(
                SDAccident.provider_code == Involved.provider_code,
                SDAccident.accident_id == Involved.accident_id,
                SDAccident.accident_year == Involved.accident_year,
            ),
        )
        .with_entities(
            Involved.id,
            Involved.accident_id,
            Involved.accident_year,
            Involved.provider_code,
            Involved.age_group,
            Involved.injured_type,
            Involved.injury_severity,
            Involved.population_type,
            Involved.sex,
            Involved.vehicle_type,
        )
    ):
        yield {
            "_id": d.id,
            "accident_id": d.accident_id,
            "accident_year": d.accident_year,
            "provider_code": d.provider_code,
            "age_group": d.age_group,
            "injured_type": d.injured_type,
            "injury_severity": d.injury_severity,
            "population_type": d.population_type,
            "sex": d.sex,
            "vehicle_type": d.vehicle_type,
        }


def sd_load_accident(sess: Session):
    sd_load_accident_main(sess)
    set_vehicles_in_sd_acc_table(sess)


def sd_load_accident_main(sess: Session):
    for chunk in chunked_generator(sd_get_accident_data(sess), 1024):
        sess.execute(SDAccident.__table__.insert(), chunk)


def sd_get_accident_data(sess: Session) -> Iterable[Dict[str, Any]]:
    return (
        {
            "accident_id": d.id,
            "accident_year": d.accident_year,
            "provider_code": d.provider_code,
            "accident_month": d.accident_month,
            "accident_timestamp": d.accident_timestamp,
            "accident_type": d.accident_type,
            "accident_yishuv_symbol": d.yishuv_symbol,
            "day_in_week": d.day_in_week,
            "day_night": d.day_night,
            "location_accuracy": d.location_accuracy,
            "multi_lane": d.multi_lane,
            "one_lane": d.one_lane,
            "road1": d.road1,
            "road2": d.road2,
            "road_segment_number": d.road_segment_number,
            "road_type": d.road_type,
            "road_width": d.road_width,
            "speed_limit": d.speed_limit,
            "street1": d.street1,
            "street2": d.street2,
            "latitude": d.latitude,
            "longitude": d.longitude,
        }
        for d in sess.query(AccidentMarkerView).with_entities(
            AccidentMarkerView.id,
            AccidentMarkerView.accident_year,
            AccidentMarkerView.provider_code,
            AccidentMarkerView.accident_month,
            AccidentMarkerView.accident_timestamp,
            AccidentMarkerView.accident_type,
            AccidentMarkerView.yishuv_symbol,
            AccidentMarkerView.day_in_week,
            AccidentMarkerView.day_night,
            AccidentMarkerView.location_accuracy,
            AccidentMarkerView.multi_lane,
            AccidentMarkerView.one_lane,
            AccidentMarkerView.road1,
            AccidentMarkerView.road2,
            AccidentMarkerView.road_segment_number,
            AccidentMarkerView.road_type,
            AccidentMarkerView.road_width,
            AccidentMarkerView.speed_limit,
            AccidentMarkerView.street1,
            AccidentMarkerView.street2,
            AccidentMarkerView.latitude,
            AccidentMarkerView.longitude,
        )
    )


def set_vehicles_in_sd_acc_table(sess: Session):
    """
    vehicles is a bitmap of vehicle types involved in the accident
    """
    sess.execute(
        """
        UPDATE safety_data_accident
        SET vehicles=subquery.vt_bitmap
        FROM
          (SELECT accident_id,
                  provider_code,
                  accident_year,
                  bit_or(vt_power2) AS vt_bitmap
           FROM
             (SELECT DISTINCT vehicles.accident_id,
                              vehicles.provider_code,
                              vehicles.accident_year,
                              1 << vehicle_type AS vt_power2
              FROM vehicles
              LEFT JOIN vehicle_type ON vehicles.vehicle_type = vehicle_type.id
              AND vehicles.accident_year = vehicle_type.year
              AND vehicles.provider_code = vehicle_type.provider_code) IVT
           GROUP BY accident_id,
                    provider_code,
                    accident_year) AS subquery
        WHERE safety_data_accident.accident_id=subquery.accident_id
          AND safety_data_accident.accident_year=subquery.accident_year
          AND safety_data_accident.provider_code=subquery.provider_code
        """
    )


def get_params() -> dict:
    def f(v: List[str]) -> List[str]:
        res = []
        [res.extend(x.split(",")) for x in v]
        return res

    params = request.values
    vals = {k: f(params.getlist(key=k)) for k in params.keys()}
    return vals
