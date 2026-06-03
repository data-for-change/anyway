from sqlalchemy import desc, and_, sql, func, or_
from sqlalchemy.orm import load_only

from anyway.app_and_db import db
from anyway.backend_constants import BE_CONST, OneLane
from anyway.backend_constants import AccidentSeverity as BE_AccidentSeverity
from anyway.backend_constants import PlaceType
from anyway.models import MarkerResult, AccidentMarker, Vehicle, Involved

SHOW_ALL = 3
SHOW_ALL_ACCIDENT_TYPES = 1
SHOW_INTERSECTION = 2
SHOW_NOT_IN_INTERSECTION = 1
SHOW_URBAN = 2
SHOW_SUBURBAN = 1
SHOW_MULTI_LANE = 2
SHOW_ONE_LANE = 1
SHOW_ALL_DAYS = 7
SHOW_TIME = 24
SHOW_ALL_WEATHER = 0

def empty_markers_query():
    return db.session.query(AccidentMarker).filter(sql.false())

def empty_result() -> MarkerResult:
    return MarkerResult(
        accident_markers=empty_markers_query(),
        rsa_markers=empty_markers_query(),
        total_records=0,
    )

def construct_polygon_str(kwargs: dict) -> str:
    sw_lat = float(kwargs["sw_lat"])
    sw_lng = float(kwargs["sw_lng"])
    ne_lat = float(kwargs["ne_lat"])
    ne_lng = float(kwargs["ne_lng"])
    return "POLYGON(({0} {1},{0} {3},{2} {3},{2} {1},{0} {1}))".format(
        sw_lng, sw_lat, ne_lng, ne_lat
    )

def _get_marker_queries(
    polygon_str,
    start_date,
    end_date,
    query_entities=None,
):
    base_query = (
        db.session.query(AccidentMarker)
        .filter(AccidentMarker.geom.intersects(polygon_str))
        .filter(AccidentMarker.created >= start_date)
        .filter(AccidentMarker.created <= end_date)
    )

    if query_entities is not None:
        base_query = base_query.with_entities(*query_entities)

    markers = (
        base_query
        .filter(AccidentMarker.provider_code != BE_CONST.RSA_PROVIDER_CODE)
        .order_by(desc(AccidentMarker.created))
    )

    rsa_markers = (
        base_query
        .filter(AccidentMarker.provider_code == BE_CONST.RSA_PROVIDER_CODE)
        .order_by(desc(AccidentMarker.created))
    )

    return markers, rsa_markers

def handle_location_accuracy(markers, accurate, approx):
    if accurate and not approx:
        return markers.filter(AccidentMarker.location_accuracy == 1), False
    if approx and not accurate:
        return markers.filter(AccidentMarker.location_accuracy != 1), False
    return_early = not accurate and not approx
    return markers, return_early

def handle_accident_severity(markers, kwargs):
    if not kwargs.get("show_fatal", True):
        markers = markers.filter(AccidentMarker.accident_severity != BE_AccidentSeverity.FATAL.value)
    if not kwargs.get("show_severe", True):
        markers = markers.filter(AccidentMarker.accident_severity != BE_AccidentSeverity.SEVERE.value)
    if not kwargs.get("show_light", True):
        markers = markers.filter(AccidentMarker.accident_severity != BE_AccidentSeverity.LIGHT.value)
    return markers

def handle_urban_filter(markers, kwargs):
    urban_values = [PlaceType.URBAN_NOT_IN_JUNCTION.value, PlaceType.URBAN_IN_JUNCTION.value]
    suburban_values = [PlaceType.SUBURBAN_NOT_IN_JUNCTION.value, PlaceType.SUBURBAN_IN_JUNCTION.value]

    show_urban = kwargs.get("show_urban", SHOW_ALL)
    if show_urban == SHOW_ALL:
        return markers, False
    if show_urban == SHOW_URBAN:
        markers = markers.filter(AccidentMarker.road_type.in_(urban_values))
    elif show_urban == SHOW_SUBURBAN:
        markers = markers.filter(AccidentMarker.road_type.in_(suburban_values))
    else:
        return markers, True
    return markers, False

def handle_intersection_filter(markers, kwargs):
    in_junction_values = [PlaceType.URBAN_IN_JUNCTION.value, PlaceType.SUBURBAN_IN_JUNCTION.value]
    not_in_junction_values = [PlaceType.URBAN_NOT_IN_JUNCTION.value, PlaceType.SUBURBAN_NOT_IN_JUNCTION.value]

    show_intersection = kwargs.get("show_intersection", SHOW_ALL)
    if show_intersection == SHOW_ALL:
        return markers, False
    if show_intersection == SHOW_INTERSECTION:
        markers = markers.filter(AccidentMarker.road_type.in_(in_junction_values))
    elif show_intersection == SHOW_NOT_IN_INTERSECTION:
        markers = markers.filter(AccidentMarker.road_type.in_(not_in_junction_values))
    else:
        return markers, True
    return markers, False

def handle_lane_filter(markers, kwargs):
    multi_lane_values = [OneLane.MULTI_LANE_WITH_DIVIDER.value, OneLane.MULTI_LANE_WITHOUT_DIVIDER.value]

    show_lane = kwargs.get("show_lane", SHOW_ALL)
    if show_lane == SHOW_ALL:
        return markers, False
    if show_lane == SHOW_MULTI_LANE:
        markers = markers.filter(AccidentMarker.one_lane.in_(multi_lane_values))
    elif show_lane == SHOW_ONE_LANE:
        markers = markers.filter(AccidentMarker.one_lane == OneLane.ONE_LANE.value)
    else:
        return markers, True
    return markers, False

def handle_day_filter(markers, kwargs):
    if kwargs.get("show_day", SHOW_ALL_DAYS) != SHOW_ALL_DAYS:
        markers = markers.filter(
            func.extract("dow", AccidentMarker.created) == kwargs["show_day"]
        )
    return markers

def handle_holiday_filter(markers, kwargs):
    if kwargs.get("show_holiday", 0) != 0:
        markers = markers.filter(AccidentMarker.day_type == kwargs["show_holiday"])
    return markers

def handle_time_filter(markers, kwargs):
    show_time = kwargs.get("show_time", 24)
    if show_time != 24:
        if show_time == 25:  # Daylight (6-18)
            markers = markers.filter(
                func.extract("hour", AccidentMarker.created) >= 6
            ).filter(func.extract("hour", AccidentMarker.created) < 18)
        elif show_time == 26:  # Darktime (18-6)
            markers = markers.filter(
                (func.extract("hour", AccidentMarker.created) >= 18)
                | (func.extract("hour", AccidentMarker.created) < 6)
            )
        else:
            markers = markers.filter(
                func.extract("hour", AccidentMarker.created) >= show_time
            ).filter(func.extract("hour", AccidentMarker.created) < show_time + 6)
    elif kwargs["start_time"] != 25 and kwargs["end_time"] != 25:
        markers = markers.filter(
            func.extract("hour", AccidentMarker.created) >= kwargs["start_time"]
        ).filter(func.extract("hour", AccidentMarker.created) < kwargs["end_time"])
    return markers

def handle_weather_filter(markers, kwargs):
    if kwargs.get("weather", 0) != 0:
        markers = markers.filter(AccidentMarker.weather == kwargs["weather"])
    return markers

def handle_separation_filter(markers, kwargs):
    if kwargs.get("separation", 0) != 0:
        markers = markers.filter(AccidentMarker.multi_lane == kwargs["separation"])
    return markers

def handle_surface_filter(markers, kwargs):
    if kwargs.get("surface", 0) != 0:
        markers = markers.filter(AccidentMarker.road_surface == kwargs["surface"])
    return markers

def handle_accident_type_filter(markers, kwargs):
    accident_type = kwargs.get("acctype", SHOW_ALL_ACCIDENT_TYPES)
    if accident_type != SHOW_ALL_ACCIDENT_TYPES:
        markers = markers.filter(AccidentMarker.accident_type == accident_type)
    return markers

def handle_control_measure_filter(markers, kwargs):
    if kwargs.get("controlmeasure", 0) != 0:
        markers = markers.filter(
            AccidentMarker.road_control == kwargs["controlmeasure"]
        )
    return markers

def handle_case_type_filter(markers, kwargs):
    if kwargs.get("case_type", 0) != 0:
        markers = markers.filter(
            AccidentMarker.provider_code == kwargs["case_type"]
        )
    return markers

def handle_age_groups_filter(markers, kwargs):
    age_groups = kwargs.get("age_groups")
    if age_groups:
        age_groups_list = age_groups.split(",")
        if len(age_groups_list) < (BE_CONST.AGE_GROUPS_NUMBER + 1):
            markers = markers.filter(
                AccidentMarker.involved.any(Involved.age_group.in_(age_groups_list))
            )
    else:
        markers = empty_markers_query()
    return markers

#not currently used
def handle_light_transportation_filter(markers, kwargs):
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
    return markers

def handle_accidents_filter(markers, kwargs):
    if not kwargs["show_accidents"]:
        markers = markers.filter(
            and_(
                AccidentMarker.provider_code != BE_CONST.CBS_ACCIDENT_TYPE_1_CODE,
                AccidentMarker.provider_code != BE_CONST.CBS_ACCIDENT_TYPE_3_CODE,
                AccidentMarker.provider_code != BE_CONST.UNITED_HATZALA_CODE,
            )
        )
    return markers

def build_marker_result(markers, rsa_markers, involved_and_vehicles, kwargs):
    if not involved_and_vehicles:
        return MarkerResult(
            accident_markers=markers, rsa_markers=rsa_markers, total_records=None
        )

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
        vehicles = db.session.query(Vehicle).filter(
            Vehicle.accident_id.in_(markers_ids)
        )
    if fetch_involved:
        involved = db.session.query(Involved).filter(
            Involved.accident_id.in_(markers_ids)
        )
    result = (
        markers.all() if markers is not None else [],
        vehicles.all() if vehicles is not None else [],
        involved.all() if involved is not None else [],
    )
    return MarkerResult(
        accident_markers=result,
        rsa_markers=empty_markers_query(),
        total_records=len(result),
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

    polygon_str = construct_polygon_str(kwargs)
    markers, rsa_markers = _get_marker_queries(polygon_str, kwargs["start_date"], kwargs["end_date"], query_entities)

    if not kwargs["show_rsa"]:
        rsa_markers = empty_markers_query()
    markers = handle_accidents_filter(markers, kwargs)
    if yield_per:
        markers = markers.yield_per(yield_per)
    markers, return_early = handle_location_accuracy(markers, accurate, approx)
    if return_early:
        return empty_result()
    markers = handle_accident_severity(markers, kwargs)
    for filter_handler in (
        handle_urban_filter,
        handle_intersection_filter,
        handle_lane_filter,
    ):
        markers, return_early = filter_handler(markers, kwargs)
        if return_early:
            return MarkerResult(
                accident_markers=empty_markers_query(),
                rsa_markers=rsa_markers,
                total_records=None,
            )

    markers = handle_day_filter(markers, kwargs)
    markers = handle_holiday_filter(markers, kwargs)
    markers = handle_time_filter(markers, kwargs)
    markers = handle_weather_filter(markers, kwargs)
    markers = handle_separation_filter(markers, kwargs)
    markers = handle_surface_filter(markers, kwargs)
    markers = handle_accident_type_filter(markers, kwargs)
    markers = handle_control_measure_filter(markers, kwargs)
    markers = handle_case_type_filter(markers, kwargs)

    if is_thin:
        markers = markers.options(load_only("id", "longitude", "latitude"))

    markers = handle_age_groups_filter(markers, kwargs)

    #no button for this filter
    #markers = handle_light_transportation_filter(markers, kwargs)

    if page and per_page:
        markers = markers.offset((page - 1) * per_page).limit(per_page)

    return build_marker_result(markers, rsa_markers, involved_and_vehicles, kwargs)
