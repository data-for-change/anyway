import copy
from collections import defaultdict, OrderedDict
from typing import Dict, Tuple, Callable

from flask_sqlalchemy import BaseQuery
from sqlalchemy import func, asc
from flask_babel import _

from anyway.app_and_db import db
from anyway.backend_constants import BE_CONST, InjurySeverity
from anyway.models import InvolvedMarkerView
from anyway.request_params import RequestParams
from anyway.utilities import parse_age_from_range
from anyway.widgets.widget_utils import (
    get_expression_for_fields,
    add_resolution_location_accuracy_filter,
)

# RequestParams is not hashable, so we can't use functools.lru_cache
cache_dict = OrderedDict()

SIXTY_FIVE_PLUS = "65+"
SIXTY_TWOHUNDRED = "65-200"
UNKNOWN = "unknown"
CACHE_MAX_SIZE = 10

AGE_RANGE_DICT = {0: 4, 5: 14, 15: 19, 20: 24, 25: 44, 45: 64, 65: 200}


class KilledAndInjuredCountPerAgeGroupWidgetUtils:
    @staticmethod
    def filter_and_group_injured_count_per_age_group(
        request_params: RequestParams,
    ) -> Dict[str, Dict[int, int]]:
        start_time = request_params.start_time
        end_time = request_params.end_time
        if request_params.resolution == BE_CONST.ResolutionCategories.STREET:
            involve_yishuv_name = request_params.location_info["yishuv_name"]
            street1_hebrew = request_params.location_info["street1_hebrew"]
            cache_key = (involve_yishuv_name, street1_hebrew, start_time, end_time)

        elif request_params.resolution == BE_CONST.ResolutionCategories.SUBURBAN_ROAD:
            road_number = request_params.location_info["road1"]
            road_segment_id = request_params.location_info["road_segment_id"]
            cache_key = (road_number, road_segment_id, start_time, end_time)

        if cache_dict.get(cache_key):
            return cache_dict.get(cache_key)

        query = KilledAndInjuredCountPerAgeGroupWidgetUtils.create_query_for_killed_and_injured_count_per_age_group(
            end_time, start_time, request_params.location_info, request_params.resolution
        )

        dict_grouped, has_data = KilledAndInjuredCountPerAgeGroupWidgetUtils.parse_query_data(query)

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
        # initialize the dict for fixed order of the ranges
        for item_min_range, item_max_range in AGE_RANGE_DICT.items():
            for injury_id in InjurySeverity.codes():
                string_age_range = f"{item_min_range:02}-{item_max_range:02}"
                dict_grouped[string_age_range][injury_id] = 0

        has_data = False
        for row in query:
            has_data = True
            age_range = row.age_group
            injury_id = row.injury_severity
            count = row.count

            # The age groups in the DB are not the same age groups in the Widget - so we need to merge some groups
            age_parse = parse_age_from_range(age_range)
            if not age_parse:
                dict_grouped[UNKNOWN][injury_id] += count
            else:
                min_age, max_age = age_parse
                found_age_range = False
                # Find to what "bucket" to aggregate the data
                for item_min_range, item_max_range in AGE_RANGE_DICT.items():
                    if item_min_range <= min_age <= max_age <= item_max_range:
                        string_age_range = f"{item_min_range:02}-{item_max_range:02}"
                        dict_grouped[string_age_range][injury_id] += count
                        found_age_range = True
                        break

                if not found_age_range:
                    dict_grouped[UNKNOWN][injury_id] += count
        # Rename the last key
        dict_grouped[SIXTY_FIVE_PLUS] = dict_grouped[SIXTY_TWOHUNDRED]
        del dict_grouped[SIXTY_TWOHUNDRED]
        if UNKNOWN in dict_grouped:
            dict_grouped[_("unknown")] = dict_grouped.pop(UNKNOWN)
        return dict_grouped, has_data

    @staticmethod
    def create_query_for_killed_and_injured_count_per_age_group(
        end_time, start_time, location_info, resolution
    ) -> BaseQuery:
        loc_filter = adapt_location_fields_to_involve_table(location_info)
        loc_filter = add_resolution_location_accuracy_filter(loc_filter,
                                                             resolution)
        loc_ex = get_expression_for_fields(loc_filter, InvolvedMarkerView)

        query = (
            db.session.query(InvolvedMarkerView)
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
                        InjurySeverity.KILLED.value,  # pylint: disable=no-member
                        InjurySeverity.SEVERE_INJURED.value,  # pylint: disable=no-member
                        InjurySeverity.LIGHT_INJURED.value,  # pylint: disable=no-member
                    ]
                )
            )
            .filter(loc_ex)
            .group_by(InvolvedMarkerView.age_group, InvolvedMarkerView.injury_severity)
            .with_entities(
                InvolvedMarkerView.age_group,
                InvolvedMarkerView.injury_severity,
                func.count().label("count"),
            )
            .order_by(asc(InvolvedMarkerView.age_group))
        )
        return query


def adapt_location_fields_to_involve_table(filter: dict) -> dict:
    res = copy.copy(filter)
    for field in ["yishuv_name", "yishuv_symbol"]:
        if field in res:
            res[f"involve_{field}"] = res.pop(field)
    return res
