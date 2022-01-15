from collections import defaultdict, OrderedDict
from datetime import datetime
from typing import Dict, Tuple, Callable

from flask_sqlalchemy import BaseQuery
from sqlalchemy import func, asc

from anyway.app_and_db import db
from anyway.constants.backend_constants import BackEndConstants
from anyway.constants.injury_severity import InjurySeverity
from anyway.models import InvolvedMarkerView
from anyway.request_params import RequestParams
from anyway.utilities import parse_age_from_range

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
        road_number = request_params.location_info["road1"]
        road_segment = request_params.location_info["road_segment_name"]
        start_time = request_params.start_time
        end_time = request_params.end_time
        cache_key = (road_number, road_segment, start_time, end_time)
        if cache_dict.get(cache_key):
            return cache_dict.get(cache_key)

        query = KilledAndInjuredCountPerAgeGroupWidgetUtils.create_query_for_killed_and_injured_count_per_age_group(
            end_time, road_number, road_segment, start_time
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
        return dict_grouped, has_data

    @staticmethod
    def create_query_for_killed_and_injured_count_per_age_group(
        end_time: datetime.date, road_number: int, road_segment: str, start_time: datetime.date
    ) -> BaseQuery:
        query = (
            db.session.query(InvolvedMarkerView)
            .filter(InvolvedMarkerView.accident_timestamp >= start_time)
            .filter(InvolvedMarkerView.accident_timestamp <= end_time)
            .filter(
                InvolvedMarkerView.provider_code.in_(
                    [
                        BackEndConstants.CBS_ACCIDENT_TYPE_1_CODE,
                        BackEndConstants.CBS_ACCIDENT_TYPE_3_CODE,
                    ]
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
            .filter(
                (InvolvedMarkerView.road1 == road_number)
                | (InvolvedMarkerView.road2 == road_number)
            )
            .filter(InvolvedMarkerView.road_segment_name == road_segment)
            .group_by(InvolvedMarkerView.age_group, InvolvedMarkerView.injury_severity)
            .with_entities(
                InvolvedMarkerView.age_group,
                InvolvedMarkerView.injury_severity,
                func.count().label("count"),
            )
            .order_by(asc(InvolvedMarkerView.age_group))
        )
        return query
