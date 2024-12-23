import json
from sqlalchemy.orm import aliased
from sqlalchemy import and_
from flask import request, Response
from anyway.models import (
    InvolvedMarkerView, SDAccident, SDInvolved, AccidentMarkerView,
    City, InjurySeverity, Streets, Sex, RoadLight, RoadType, AgeGroup,
    Involved,
)
from anyway.app_and_db import app, db


def load_data():
    load_data = request.values.get("load-data")
    if load_data:
        return sd_load_data()


def get_data():
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
    sd_load_accident()
    sd_load_involved()
    return Response(json.dumps("Tables loaded", default=str), mimetype="application/json")

def sd_load_involved():
    db.session.query(SDInvolved).delete()
    db.session.commit()
    db.get_engine().execute(
        SDInvolved.__table__.insert(),
          [d for d in get_involved_data()]
          )
    db.session.commit()

def get_involved_data():
    for d in db.session.query(InvolvedMarkerView, SDAccident)\
        .join(SDAccident,
            and_(SDAccident.provider_code == InvolvedMarkerView.provider_code,
                 SDAccident.accident_id == InvolvedMarkerView.accident_id,
                 SDAccident.accident_year == InvolvedMarkerView.accident_year))\
        .with_entities(InvolvedMarkerView.involve_id,
                        InvolvedMarkerView.accident_id,
                        InvolvedMarkerView.accident_year,
                        InvolvedMarkerView.provider_code,
                        InvolvedMarkerView.injury_severity,
                        InvolvedMarkerView.injured_type,
                        InvolvedMarkerView.age_group,
                        InvolvedMarkerView.sex,
                        InvolvedMarkerView.population_type,
                        )\
        .limit(1000):
        yield{
                "involve_id": d.involve_id,
                "accident_id": d.accident_id,
                "accident_year": d.accident_year,
                "provider_code": d.provider_code,
                "injury_severity": d.injury_severity,
                "injured_type": d.injured_type,
                "age_group": d.age_group,
                "sex": d.sex,
                "population_type": d.population_type,
            }

def sd_load_accident():
    from anyway.models import SDAccident, AccidentMarkerView, SDInvolved
    db.session.query(SDAccident).delete()
    db.session.commit()
    db.get_engine().execute(
        SDAccident.__table__.insert(),
        [
            {
                "accident_id": d.id,
                "accident_year": d.accident_year,
                "provider_code": d.provider_code,
                "accident_month": d.accident_month,
                "accident_timestamp": d.accident_timestamp,
                "road_type": d.road_type,
                "road_width": d.road_width,
                "day_night": d.day_night,
                "one_lane_type": d.one_lane,
                "multi_lane_type": d.multi_lane,
                "speed_limit_type": d.speed_limit,
                "yishuv_symbol": d.yishuv_symbol,
                "street1": d.street1,
                "street2": d.street2,
                "road": d.road1,
                "road_segment": d.road_segment_number,
                "lat": d.latitude,
                "lon": d.longitude,
            }
            for d in db.session.query(AccidentMarkerView)
            .with_entities(AccidentMarkerView.id,
                           AccidentMarkerView.accident_year,
                           AccidentMarkerView.provider_code,
                           AccidentMarkerView.accident_year,
                           AccidentMarkerView.accident_month,
                           AccidentMarkerView.accident_timestamp,
                           AccidentMarkerView.road_type,
                           AccidentMarkerView.road_width,
                           AccidentMarkerView.day_night,
                           AccidentMarkerView.one_lane,
                           AccidentMarkerView.multi_lane,
                           AccidentMarkerView.speed_limit,
                           AccidentMarkerView.yishuv_symbol,
                           AccidentMarkerView.street1,
                           AccidentMarkerView.street2,
                           AccidentMarkerView.road1,
                           AccidentMarkerView.road_segment_number,
                           AccidentMarkerView.latitude,
                           AccidentMarkerView.longitude,
                           )
                           .limit(1000)
        ]
    )
    db.session.commit()


