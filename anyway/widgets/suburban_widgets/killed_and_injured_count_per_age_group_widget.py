from collections import defaultdict
from datetime import datetime
from typing import Callable, Dict, Tuple, List

from flask_babel import _
from flask_sqlalchemy import BaseQuery
from sqlalchemy import func, asc

from anyway.app_and_db import db
from anyway.backend_constants import BE_CONST, InjurySeverity as IS
from anyway.models import InvolvedMarkerView
from anyway.request_params import RequestParams
from anyway.utilities import parse_age_from_range
from anyway.widgets.suburban_widgets.sub_urban_widget import SubUrbanWidget
from anyway.widgets.widget import register
from anyway.widgets.widget_utils import (
    order_severity_in_stack_bar_widget,
    gen_entity_labels,
    add_empty_keys_to_gen_two_level_dict,
)

# RequestParams is not hashable, so we can't use functools.lru_cache
cache_dict = {}
AGE_RANGE_DICT = {0: 4, 5: 14, 15: 19, 20: 24, 25: 44, 45: 64, 65: 200}


@register
class KilledInjuredCountPerAgeGroupStackedWidget(SubUrbanWidget):
    name: str = "killed_and_injured_count_per_age_group_stacked"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 30

    def generate_items(self) -> None:
        raw_data = filter_and_group_injured_count_per_age_group(self.request_params)

        partial_processed = add_empty_keys_to_gen_two_level_dict(
            raw_data,
            get_age_range_list(),
            IS.codes(),
        )

        structured_data_list = []
        for age_group, severity_dict in partial_processed.items():
            series_severity = [
                {"label_key": IS(severity_value).get_label(), "value": count}
                for severity_value, count in severity_dict.items()
            ]
            structured_data_list.append({"label_key": age_group, "series": series_severity})

        self.items = order_severity_in_stack_bar_widget(
            structured_data_list,
            [
                IS.KILLED.get_label(),
                IS.SEVERE_INJURED.get_label(),
                IS.LIGHT_INJURED.get_label(),
            ],
        )

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": _("Killed and injury stacked per age group in ")
            + request_params.location_info["road_segment_name"],
            "labels_map": gen_entity_labels(IS),
        }
        return items


@register
class KilledInjuredCountPerAgeGroupWidget(SubUrbanWidget):
    name: str = "killed_and_injured_count_per_age_group"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 14

    def generate_items(self) -> None:
        raw_data = filter_and_group_injured_count_per_age_group(self.request_params)
        structured_data_list = []
        for age_group, severity_dict in raw_data.items():
            count_total = 0
            for count in severity_dict.values():
                count_total += count

            structured_data_list.append({"label_key": age_group, "value": count_total})

        self.items = structured_data_list

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": _("Killed and injury per age group in ")
            + request_params.location_info["road_segment_name"]
        }
        return items


def filter_and_group_injured_count_per_age_group(request_params: RequestParams) -> Dict:
    road_number = request_params.location_info["road1"]
    road_segment = request_params.location_info["road_segment_name"]
    start_time = request_params.start_time
    end_time = request_params.end_time
    cache_key = (road_number, road_segment, start_time, end_time)
    if cache_dict.get(cache_key):
        return cache_dict.get(cache_key)

    query = create_query_for_killed_and_injured_count_per_age_group(
        end_time, road_number, road_segment, start_time
    )

    dict_grouped, has_data = parse_query_data(query)

    if not has_data:
        return {}

    while len(cache_dict) > 10:
        cache_dict.popitem()

    cache_dict[cache_key] = dict_grouped
    return dict_grouped


def get_age_range_list() -> List[str]:
    age_list = []
    for item_min_range, item_max_range in AGE_RANGE_DICT.items():
        if 200 == item_max_range:
            age_list.append("65+")
        else:
            age_list.append(f"{item_min_range:02}-{item_max_range:02}")

    return age_list


def parse_query_data(query: BaseQuery) -> Tuple[Dict, bool]:
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
            dict_grouped["unknown"][injury_id] += count
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
                dict_grouped["unknown"][injury_id] += count

    # Rename the last key
    dict_grouped["65+"] = dict_grouped["65-200"]
    del dict_grouped["65-200"]
    return dict_grouped, has_data


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
                    IS.KILLED.value,  # pylint: disable=no-member
                    IS.SEVERE_INJURED.value,  # pylint: disable=no-member
                    IS.LIGHT_INJURED.value,  # pylint: disable=no-member
                ]
            )
        )
        .filter(
            (InvolvedMarkerView.road1 == road_number) | (InvolvedMarkerView.road2 == road_number)
        )
        .filter(InvolvedMarkerView.road_segment_name == road_segment)
        .group_by(InvolvedMarkerView.age_group, InvolvedMarkerView.injury_severity)
        .with_entities(InvolvedMarkerView.age_group, InvolvedMarkerView.injury_severity, func.count().label("count"))
        .order_by(asc(InvolvedMarkerView.age_group))
    )
    return query
