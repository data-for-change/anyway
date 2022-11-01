from collections import Counter, OrderedDict
from datetime import datetime
from typing import Dict, Optional

from flask_sqlalchemy import BaseQuery
from sqlalchemy import func, asc

from anyway.app_and_db import db
from anyway.backend_constants import BE_CONST, InjurySeverity
from anyway.models import InvolvedMarkerView
from anyway.request_params import RequestParams
from anyway.utilities import parse_age_from_range

# RequestParams is not hashable, so we can't use functools.lru_cache
cache_dict = OrderedDict()

UNKNOWN = "unknown"
CACHE_MAX_SIZE = 10

AGE_RANGES = [0, 5, 15, 20, 25, 45, 65, 200]


class KilledAndInjuredCountPerAgeGroupWidgetUtils:
    @staticmethod
    def filter_and_group_injured_count_per_age_group(
        request_params: RequestParams,
    ) -> Dict[str, Counter]:
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

        dict_grouped = KilledAndInjuredCountPerAgeGroupWidgetUtils.parse_query_data(query)

        if dict_grouped is None:
            return {}

        while len(cache_dict) > CACHE_MAX_SIZE:
            cache_dict.popitem(last=False)

        cache_dict[cache_key] = dict_grouped
        return dict_grouped

    @staticmethod
    def parse_query_data(query: BaseQuery) -> Optional[Dict[str, Counter]]:
        dict_grouped = {k: Counter() for k in AGE_RANGES + [UNKNOWN]}
        has_data = False

        for row in query:
            group_name: str = UNKNOWN

            age_parsed = parse_age_from_range(row.age_group)
            if age_parsed:
                min_age, max_age = age_parsed
                # The age groups in the DB are not the same age groups in the widget, so we need to merge some groups.
                # Find the right bucket to aggregate the data:
                for item_min_range, item_max_range in zip(AGE_RANGES, AGE_RANGES[1:]):
                    if item_min_range <= min_age <= max_age <= item_max_range:
                        has_data = True
                        group_name = f"{item_min_range}-{item_max_range}" if item_max_range < 120 else f"{item_min_range}+"
                        break

            dict_grouped[group_name][row.injury_severity] += row.count
        if not has_data:
            return None
        return dict_grouped

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
