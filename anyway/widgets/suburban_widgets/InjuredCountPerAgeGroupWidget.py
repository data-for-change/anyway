from collections import defaultdict
from typing import Callable, Dict

from flask_babel import _
from sqlalchemy import func

from anyway.RequestParams import RequestParams
from anyway.app_and_db import db
from anyway.backend_constants import BE_CONST, InjurySeverity
from anyway.models import InvolvedMarkerView
from anyway.utilities import parse_age_from_range
from anyway.widgets.suburban_widgets.SubUrbanWidget import SubUrbanWidget


class InjuredCountPerAgeGroupWidget(SubUrbanWidget):
    name: str = "injured_count_per_age_group"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 14

    def generate_items(self) -> None:
        self.items = InjuredCountPerAgeGroupWidget.filter_and_group_injured_count_per_age_group(
            self.request_params
        )

    @staticmethod
    def filter_and_group_injured_count_per_age_group(request_params: RequestParams):
        road_number = request_params.location_info["road1"]
        road_segment = request_params.location_info["road_segment_name"]

        query = (
            db.session.query(InvolvedMarkerView)
            .filter(InvolvedMarkerView.accident_timestamp >= request_params.start_time)
            .filter(InvolvedMarkerView.accident_timestamp <= request_params.end_time)
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
                    ]
                )
            )
            .filter(
                (InvolvedMarkerView.road1 == road_number)
                | (InvolvedMarkerView.road2 == road_number)
            )
            .filter(InvolvedMarkerView.road_segment_name == road_segment)
            .group_by("age_group", "injury_severity")
            .with_entities("age_group", "injury_severity", func.count().label("count"))
        )

        # if there's no data - return empty dict
        if query.count() == 0:
            return {}

        range_dict = {0: 4, 5: 9, 10: 14, 15: 19, 20: 24, 25: 34, 35: 44, 45: 54, 55: 64, 65: 200}

        def defaultdict_int_factory() -> Callable:
            return lambda: defaultdict(int)

        dict_grouped = defaultdict(defaultdict_int_factory())

        for row in query:
            age_range = row.age_group
            injury_name = InjurySeverity(row.injury_severity).get_label()
            count = row.count

            # The age groups in the DB are not the same age groups in the Widget - so we need to merge some of the groups
            age_parse = parse_age_from_range(age_range)
            if not age_parse:
                dict_grouped["unknown"][injury_name] += count
            else:
                min_age, max_age = age_parse
                found_age_range = False
                # Find to what "bucket" to aggregate the data
                for item_min_range, item_max_range in range_dict.items():
                    if item_min_range <= min_age <= max_age <= item_max_range:
                        string_age_range = f"{item_min_range:02}-{item_max_range:02}"
                        dict_grouped[string_age_range][injury_name] += count
                        found_age_range = True
                        break

                if not found_age_range:
                    dict_grouped["unknown"][injury_name] += count

        # Rename the last key
        dict_grouped["65+"] = dict_grouped["65-200"]
        del dict_grouped["65-200"]

        return dict_grouped

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": _("Injury severity per age group in ")
            + request_params.location_info["road_segment_name"]
        }
        return items
