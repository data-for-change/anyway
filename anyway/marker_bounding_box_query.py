from sqlalchemy import desc, and_, sql, func, or_
from sqlalchemy.orm import load_only

from anyway.app_and_db import db
from anyway.backend_constants import BE_CONST
from anyway.models import MarkerResult, AccidentMarker, Vehicle, Involved
from anyway.vehicle_type import VehicleType as BE_VehicleType


def empty_result() -> MarkerResult:
    return MarkerResult(
        accident_markers=db.session.query(AccidentMarker).filter(sql.false()),
        rsa_markers=db.session.query(AccidentMarker).filter(sql.false()),
        total_records=0,
    )

def marker_bounding_box_query(
    is_thin=False, yield_per=None, involved_and_vehicles=False, query_entities=None, **kwargs
) -> MarkerResult:
    approx = kwargs.get("approx", True)
    accurate = kwargs.get("accurate", True)
    page = kwargs.get("page")
    per_page = kwargs.get("per_page")

    if not kwargs.get("show_markers", True):
        return empty_result()

    sw_lat = float(kwargs["sw_lat"])
    sw_lng = float(kwargs["sw_lng"])
    ne_lat = float(kwargs["ne_lat"])
    ne_lng = float(kwargs["ne_lng"])
    polygon_str = "POLYGON(({0} {1},{0} {3},{2} {3},{2} {1},{0} {1}))".format(
        sw_lng, sw_lat, ne_lng, ne_lat
    )

    if query_entities is not None:
        markers = (
            db.session.query(AccidentMarker)
            .with_entities(*query_entities)
            .filter(AccidentMarker.geom.intersects(polygon_str))
            .filter(AccidentMarker.created >= kwargs["start_date"])
            .filter(AccidentMarker.created <= kwargs["end_date"])
            .filter(AccidentMarker.provider_code != BE_CONST.RSA_PROVIDER_CODE)
            .order_by(desc(AccidentMarker.created))
        )

        rsa_markers = (
            db.session.query(AccidentMarker)
            .with_entities(*query_entities)
            .filter(AccidentMarker.geom.intersects(polygon_str))
            .filter(AccidentMarker.created >= kwargs["start_date"])
            .filter(AccidentMarker.created <= kwargs["end_date"])
            .filter(AccidentMarker.provider_code == BE_CONST.RSA_PROVIDER_CODE)
            .order_by(desc(AccidentMarker.created))
        )
    else:
        markers = (
            db.session.query(AccidentMarker)
            .filter(AccidentMarker.geom.intersects(polygon_str))
            .filter(AccidentMarker.created >= kwargs["start_date"])
            .filter(AccidentMarker.created <= kwargs["end_date"])
            .filter(AccidentMarker.provider_code != BE_CONST.RSA_PROVIDER_CODE)
            .order_by(desc(AccidentMarker.created))
        )

        rsa_markers = (
            db.session.query(AccidentMarker)
            .filter(AccidentMarker.geom.intersects(polygon_str))
            .filter(AccidentMarker.created >= kwargs["start_date"])
            .filter(AccidentMarker.created <= kwargs["end_date"])
            .filter(AccidentMarker.provider_code == BE_CONST.RSA_PROVIDER_CODE)
            .order_by(desc(AccidentMarker.created))
        )

    if not kwargs["show_rsa"]:
        rsa_markers = db.session.query(AccidentMarker).filter(sql.false())
    if not kwargs["show_accidents"]:
        markers = markers.filter(
            and_(
                AccidentMarker.provider_code != BE_CONST.CBS_ACCIDENT_TYPE_1_CODE,
                AccidentMarker.provider_code != BE_CONST.CBS_ACCIDENT_TYPE_3_CODE,
                AccidentMarker.provider_code != BE_CONST.UNITED_HATZALA_CODE,
            )
        )
    if yield_per:
        markers = markers.yield_per(yield_per)
    if accurate and not approx:
        markers = markers.filter(AccidentMarker.location_accuracy == 1)
    elif approx and not accurate:
        markers = markers.filter(AccidentMarker.location_accuracy != 1)
    elif not accurate and not approx:
        return empty_result()
    if not kwargs.get("show_fatal", True):
        markers = markers.filter(AccidentMarker.accident_severity != 1)
    if not kwargs.get("show_severe", True):
        markers = markers.filter(AccidentMarker.accident_severity != 2)
    if not kwargs.get("show_light", True):
        markers = markers.filter(AccidentMarker.accident_severity != 3)
    if kwargs.get("show_urban", 3) != 3:
        if kwargs["show_urban"] == 2:
            markers = markers.filter(AccidentMarker.road_type >= 1).filter(
                AccidentMarker.road_type <= 2
            )
        elif kwargs["show_urban"] == 1:
            markers = markers.filter(AccidentMarker.road_type >= 3).filter(
                AccidentMarker.road_type <= 4
            )
        else:
            return MarkerResult(
                accident_markers=db.session.query(AccidentMarker).filter(sql.false()),
                rsa_markers=rsa_markers,
                total_records=None,
            )
    if kwargs.get("show_intersection", 3) != 3:
        if kwargs["show_intersection"] == 2:
            markers = markers.filter(AccidentMarker.road_type != 2).filter(
                AccidentMarker.road_type != 4
            )
        elif kwargs["show_intersection"] == 1:
            markers = markers.filter(AccidentMarker.road_type != 1).filter(
                AccidentMarker.road_type != 3
            )
        else:
            return MarkerResult(
                accident_markers=db.session.query(AccidentMarker).filter(sql.false()),
                rsa_markers=rsa_markers,
                total_records=None,
            )
    if kwargs.get("show_lane", 3) != 3:
        if kwargs["show_lane"] == 2:
            markers = markers.filter(AccidentMarker.one_lane >= 2).filter(
                AccidentMarker.one_lane <= 3
            )
        elif kwargs["show_lane"] == 1:
            markers = markers.filter(AccidentMarker.one_lane == 1)
        else:
            return MarkerResult(
                accident_markers=db.session.query(AccidentMarker).filter(sql.false()),
                rsa_markers=rsa_markers,
                total_records=None,
            )

    if kwargs.get("show_day", 7) != 7:
        markers = markers.filter(
            func.extract("dow", AccidentMarker.created) == kwargs["show_day"]
        )
    if kwargs.get("show_holiday", 0) != 0:
        markers = markers.filter(AccidentMarker.day_type == kwargs["show_holiday"])

    if kwargs.get("show_time", 24) != 24:
        if kwargs["show_time"] == 25:  # Daylight (6-18)
            markers = markers.filter(func.extract("hour", AccidentMarker.created) >= 6).filter(
                func.extract("hour", AccidentMarker.created) < 18
            )
        elif kwargs["show_time"] == 26:  # Darktime (18-6)
            markers = markers.filter(
                (func.extract("hour", AccidentMarker.created) >= 18)
                | (func.extract("hour", AccidentMarker.created) < 6)
            )
        else:
            markers = markers.filter(
                func.extract("hour", AccidentMarker.created) >= kwargs["show_time"]
            ).filter(func.extract("hour", AccidentMarker.created) < kwargs["show_time"] + 6)
    elif kwargs["start_time"] != 25 and kwargs["end_time"] != 25:
        markers = markers.filter(
            func.extract("hour", AccidentMarker.created) >= kwargs["start_time"]
        ).filter(func.extract("hour", AccidentMarker.created) < kwargs["end_time"])
    if kwargs.get("weather", 0) != 0:
        markers = markers.filter(AccidentMarker.weather == kwargs["weather"])
    if kwargs.get("separation", 0) != 0:
        markers = markers.filter(AccidentMarker.multi_lane == kwargs["separation"])
    if kwargs.get("surface", 0) != 0:
        markers = markers.filter(AccidentMarker.road_surface == kwargs["surface"])
    if kwargs.get("acctype", 0) != 0:
        if kwargs["acctype"] <= 20:
            markers = markers.filter(AccidentMarker.accident_type == kwargs["acctype"])
        elif kwargs["acctype"] == BE_CONST.BIKE_ACCIDENTS:
            markers = markers.filter(
                AccidentMarker.vehicles.any(Vehicle.vehicle_type == BE_VehicleType.BIKE.value)
            )
    if kwargs.get("controlmeasure", 0) != 0:
        markers = markers.filter(AccidentMarker.road_control == kwargs["controlmeasure"])

    if kwargs.get("case_type", 0) != 0:
        markers = markers.filter(AccidentMarker.provider_code == kwargs["case_type"])

    if is_thin:
        markers = markers.options(load_only("id", "longitude", "latitude"))

    if kwargs.get("age_groups"):
        age_groups_list = kwargs.get("age_groups").split(",")
        if len(age_groups_list) < (BE_CONST.AGE_GROUPS_NUMBER + 1):
            markers = markers.filter(
                AccidentMarker.involved.any(Involved.age_group.in_(age_groups_list))
            )
    else:
        markers = db.session.query(AccidentMarker).filter(sql.false())

    if kwargs.get("light_transportation", False):
        age_groups_list = kwargs.get("age_groups").split(",")
        LOCATION_ACCURACY_PRECISE_LIST = [1, 3, 4]
        markers = markers.filter(
            AccidentMarker.location_accuracy.in_(LOCATION_ACCURACY_PRECISE_LIST)
        )
        INJURED_TYPES = [1, 6, 7]
        markers = markers.filter(
            or_(
                AccidentMarker.involved.any(
                    and_(
                        Involved.injured_type.in_(INJURED_TYPES),
                        Involved.injury_severity >= 1,
                        Involved.injury_severity <= 3,
                        Involved.age_group.in_(age_groups_list),
                    )
                ),
                AccidentMarker.involved.any(
                    and_(
                        Involved.vehicle_type == 15,
                        Involved.injury_severity >= 1,
                        Involved.injury_severity <= 3,
                        Involved.age_group.in_(age_groups_list),
                    )
                ),
                AccidentMarker.involved.any(
                    and_(
                        Involved.vehicle_type == 21,
                        Involved.injury_severity >= 1,
                        Involved.injury_severity <= 3,
                        Involved.age_group.in_(age_groups_list),
                    )
                ),
                AccidentMarker.involved.any(
                    and_(
                        Involved.vehicle_type == 23,
                        Involved.injury_severity >= 1,
                        Involved.injury_severity <= 3,
                        Involved.age_group.in_(age_groups_list),
                    )
                ),
            )
        )

    if page and per_page:
        markers = markers.offset((page - 1) * per_page).limit(per_page)

    if involved_and_vehicles:
        fetch_markers = kwargs.get("fetch_markers", True)
        fetch_vehicles = kwargs.get("fetch_vehicles", True)
        fetch_involved = kwargs.get("fetch_involved", True)
        markers_ids = [marker.id for marker in markers]
        markers = None
        vehicles = None
        involved = None
        if fetch_markers:
            markers = db.session.query(AccidentMarker).filter(
                AccidentMarker.id.in_(markers_ids)
            )
        if fetch_vehicles:
            vehicles = db.session.query(Vehicle).filter(Vehicle.accident_id.in_(markers_ids))
        if fetch_involved:
            involved = db.session.query(Involved).filter(Involved.accident_id.in_(markers_ids))
        result = (
            markers.all() if markers is not None else [],
            vehicles.all() if vehicles is not None else [],
            involved.all() if involved is not None else [],
        )
        return MarkerResult(
            accident_markers=result,
            rsa_markers=db.session.query(AccidentMarker).filter(sql.false()),
            total_records=len(result),
        )
    else:
        return MarkerResult(
            accident_markers=markers, rsa_markers=rsa_markers, total_records=None
        )
