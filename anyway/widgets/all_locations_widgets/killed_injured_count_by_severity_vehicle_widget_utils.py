import copy
from collections import defaultdict, OrderedDict
from typing import Dict, Tuple, Callable

from flask_sqlalchemy import BaseQuery
from sqlalchemy import func, asc

# noinspection PyProtectedMember
from flask_babel import _

from anyway.app_and_db import db
from anyway.vehicle_type import VehicleType, UNKNOWN_VEHICLE_TYPE
from anyway.backend_constants import BE_CONST, InjurySeverity
from anyway.models import InvolvedMarkerView
from anyway.request_params import RequestParams
from anyway.widgets.widget_utils import (
    get_expression_for_fields,
    add_resolution_location_accuracy_filter,
    remove_loc_text_fields_from_filter,
)

# RequestParams is not hashable, so we can't use functools.lru_cache
cache_dict = OrderedDict()
CACHE_MAX_SIZE = 10


class KilledInjuredCountPerSeverityVehicleWidgetUtils:
    @staticmethod
    def filter_and_group_injured_count_per_severity_vehicle(
        request_params: RequestParams,
    ) -> Dict[str, Dict[int, int]]:
        start_time = request_params.start_time
        end_time = request_params.end_time
        cache_key = tuple(request_params.location_info.values()) + (start_time, end_time)

        if cache_key in cache_dict:
            return cache_dict.get(cache_key)

        query = KilledInjuredCountPerSeverityVehicleWidgetUtils.create_query_for_killed_injured_count_per_severity_vehicle(
            end_time, start_time, request_params.location_info, request_params.resolution
        )

        dict_grouped, has_data = KilledInjuredCountPerSeverityVehicleWidgetUtils.parse_query_data(
            query
        )

        if not has_data:
            return {}

        while len(cache_dict) > CACHE_MAX_SIZE:
            cache_dict.popitem(last=False)

        cache_dict[cache_key] = dict_grouped
        return dict_grouped

    @staticmethod
    def parse_query_data(query: BaseQuery) -> Tuple[Dict[str, Dict[int, int]], bool]:
        def defaultdict_int_factory() -> Callable:
            return lambda: defaultdict(int)

        dict_grouped = defaultdict(defaultdict_int_factory())
        # initialize the dict for fixed order of the vehicle types
        for vehicle_type in [UNKNOWN_VEHICLE_TYPE] + VehicleType.codes():
            for injury_id in InjurySeverity.codes():
                dict_grouped[vehicle_type][injury_id] = 0

        has_data = False
        for row in query:
            has_data = True
            vehicle_type = row.involve_vehicle_type
            injury_id = row.injury_severity
            count = row.count
            # Defensive: only increment if vehicle_type is a valid VehicleType
            try:
                dict_grouped[vehicle_type][injury_id] += count
            except Exception:
                raise Exception(f"Unknown vehicle type {vehicle_type} in InvolvedMarkerView")
        return dict_grouped, has_data

    @staticmethod
    def create_query_for_killed_injured_count_per_severity_vehicle(
        end_time, start_time, location_info, resolution
    ) -> BaseQuery:
        loc_filter = adapt_location_fields_to_involve_table(location_info)
        loc_filter = add_resolution_location_accuracy_filter(loc_filter, resolution)
        loc_filter = remove_loc_text_fields_from_filter(loc_filter)
        loc_ex = get_expression_for_fields(loc_filter, InvolvedMarkerView)

        query = (
            db.session.query(
                func.coalesce(InvolvedMarkerView.involve_vehicle_type, UNKNOWN_VEHICLE_TYPE).label(
                    "involve_vehicle_type"
                ),
                InvolvedMarkerView.injury_severity,
                func.count().label("count"),
            )
            .filter(InvolvedMarkerView.accident_timestamp >= start_time)
            .filter(InvolvedMarkerView.accident_timestamp <= end_time)
            .filter(
                InvolvedMarkerView.provider_code.in_(
                    [BE_CONST.CBS_ACCIDENT_TYPE_1_CODE, BE_CONST.CBS_ACCIDENT_TYPE_3_CODE]
                )
            )
            .filter(
                InvolvedMarkerView.injury_severity.in_(
                    [
                        InjurySeverity.KILLED.value,
                        InjurySeverity.SEVERE_INJURED.value,
                        InjurySeverity.LIGHT_INJURED.value,
                    ]
                )
            )
            .filter(loc_ex)
            .group_by("involve_vehicle_type", InvolvedMarkerView.injury_severity)
        )
        return query


def adapt_location_fields_to_involve_table(filter: dict) -> dict:
    res = copy.copy(filter)
    for field in ["yishuv_name", "yishuv_symbol"]:
        if field in res:
            res[f"accident_{field}"] = res.pop(field)
    return res
