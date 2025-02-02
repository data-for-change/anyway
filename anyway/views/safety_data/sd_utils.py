import json
import logging
from typing import Optional, Iterable, Dict, Any
from sqlalchemy.orm import aliased, sessionmaker, Session
from sqlalchemy import and_
from flask import request, Response
from anyway.models import (
    Involved, SDAccident, SDInvolved, AccidentMarkerView,
    City, InjurySeverity, Streets, Sex, RoadLight, RoadType, AgeGroup,
    Involved,
)
from anyway.app_and_db import app, db
from anyway.views.safety_data.involved_query import InvolvedQuery
from anyway.utilities import chunked_generator


def load_data():
    load_data = request.values.get("load-data")
    if load_data:
        return sd_load_data()


def sd_involved_query_from_anyway_tables():
    S1: Streets = aliased(Streets)
    S2: Streets = aliased(Streets)
    res = (
        db.session.query(Involved,
                         AccidentMarkerView,
                         City,
                         InjurySeverity,
                         Streets,
                         Sex,
                         RoadLight,
                         RoadType,
                         AgeGroup,
                         )
        .join(AccidentMarkerView,
              and_(Involved.provider_code == AccidentMarkerView.provider_code,
                   Involved.accident_id == AccidentMarkerView.id,
                   Involved.accident_year == AccidentMarkerView.accident_year))
        .join(City, AccidentMarkerView.yishuv_symbol == City.yishuv_symbol)
        .join(InjurySeverity, and_(Involved.injury_severity == InjurySeverity.id,
                                   Involved.accident_year == InjurySeverity.year,
                                   Involved.provider_code == InjurySeverity.provider_code))
        .join(S1, and_(AccidentMarkerView.street1 == S1.street,
                       AccidentMarkerView.yishuv_symbol == S1.yishuv_symbol))
        .join(S2, and_(AccidentMarkerView.street2 == S2.street,
                       AccidentMarkerView.yishuv_symbol == S2.yishuv_symbol))
        .join(Sex, and_(Involved.sex == Sex.id,
                        Involved.accident_year == Sex.year,
                        Involved.provider_code == Sex.provider_code))
        .join(RoadLight, and_(AccidentMarkerView.road_light == RoadLight.id,
                        AccidentMarkerView.accident_year == RoadLight.year,
                        AccidentMarkerView.provider_code == RoadLight.provider_code))
        .join(RoadType, and_(AccidentMarkerView.road_type == RoadType.id,
                        AccidentMarkerView.accident_year == RoadType.year,
                        AccidentMarkerView.provider_code == RoadType.provider_code))
        .join(AgeGroup, and_(Involved.age_group == AgeGroup.id,
                        Involved.accident_year == AgeGroup.year,
                        Involved.provider_code == AgeGroup.provider_code))
        # .filter(AccidentMarkerView.yishuv_symbol == 5000)
        # .filter(Involved.id == 26833652)
        .with_entities(
            Involved.id,
            AccidentMarkerView.accident_year,
            AccidentMarkerView.accident_timestamp,
            City.heb_name,
            S1.street_hebrew,
            S2.street_hebrew,
            RoadLight.road_light_hebrew,
            RoadType.road_type_hebrew,
            AccidentMarkerView.latitude,
            AccidentMarkerView.longitude,
            InjurySeverity.injury_severity_hebrew,
            Sex.sex_hebrew,
            AgeGroup.age_group_hebrew,
        )
        .limit(50).all()
    )
    return Response(json.dumps(res, default=str), mimetype="application/json")

def sd_load_data():
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
    for d in sess.query(Involved, SDAccident)\
        .join(SDAccident,
            and_(SDAccident.provider_code == Involved.provider_code,
                 SDAccident.accident_id == Involved.accident_id,
                 SDAccident.accident_year == Involved.accident_year))\
        .with_entities(Involved.id,
                        Involved.accident_id,
                        Involved.accident_year,
                        Involved.provider_code,
                        Involved.age_group,
                        Involved.injured_type,
                        Involved.injury_severity,
                        Involved.population_type,
                        Involved.sex,
                        Involved.vehicle_type,
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
            for d in sess.query(AccidentMarkerView)
            .with_entities(AccidentMarkerView.id,
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
    sess.execute("""
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
