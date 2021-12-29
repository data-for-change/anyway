from typing import Dict

from flask_babel import _

from anyway.request_params import RequestParams
from anyway.backend_constants import BE_CONST, AccidentSeverity, AccidentType
from anyway.widgets.widget_utils import get_accidents_stats
from anyway.models import AccidentMarkerView
from anyway.widgets.widget import register
from anyway.widgets.suburban_widgets.sub_urban_widget import SubUrbanWidget


@register
class HeadOnCollisionsComparisonWidget(SubUrbanWidget):
    name: str = "head_on_collisions_comparison"
    SPECIFIC_ROAD_SUBTITLE = "specific_road_segment_fatal_accidents"
    ALL_ROADS_SUBTITLE = "all_roads_fatal_accidents"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 5
        self.information = (
            "Fatal accidents distribution by accident type - head on collisions vs other accidents."
        )

    def generate_items(self) -> None:
        self.items = self.get_head_to_head_stat()

    def get_head_to_head_stat(self) -> Dict:
        location_info = self.request_params.location_info
        road_data = {}

        filter_dict = {
            "road_type": BE_CONST.ROAD_TYPE_NOT_IN_CITY_NOT_IN_INTERSECTION,
            "accident_severity": AccidentSeverity.FATAL.value,  # pylint: disable=no-member
        }
        all_roads_data = get_accidents_stats(
            table_obj=AccidentMarkerView,
            filters=filter_dict,
            group_by="accident_type",
            count="accident_type",
            start_time=self.request_params.start_time,
            end_time=self.request_params.end_time,
        )

        if location_info["road1"] and location_info["road_segment_name"]:
            filter_dict.update(
                {
                    "road1": location_info["road1"],
                    "road_segment_name": location_info["road_segment_name"],
                }
            )
            road_data = get_accidents_stats(
                table_obj=AccidentMarkerView,
                filters=filter_dict,
                group_by="accident_type",
                count="accident_type",
                start_time=self.request_params.start_time,
                end_time=self.request_params.end_time,
            )

        road_sums = self.sum_count_of_accident_type(
            # pylint: disable=no-member
            road_data,
            AccidentType.HEAD_ON_FRONTAL_COLLISION.value,
        )
        all_roads_sums = self.sum_count_of_accident_type(
            # pylint: disable=no-member
            all_roads_data,
            AccidentType.HEAD_ON_FRONTAL_COLLISION.value,
        )

        res = {
            self.SPECIFIC_ROAD_SUBTITLE: [
                {"desc": "frontal", "count": road_sums["given"]},
                {"desc": "others", "count": road_sums["others"]},
            ],
            self.ALL_ROADS_SUBTITLE: [
                {"desc": "frontal", "count": all_roads_sums["given"]},
                {"desc": "others", "count": all_roads_sums["others"]},
            ],
        }
        return res

    @staticmethod
    def sum_count_of_accident_type(data: Dict, acc_type: int) -> Dict:
        given = sum([d["count"] for d in data if d["accident_type"] == acc_type])
        others = sum([d["count"] for d in data if d["accident_type"] != acc_type])
        return {"given": given, "others": others}

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        i = items["data"]["items"]
        items["data"]["text"] = {
            "title": _("Fatal head on collisions vs other accidents")
        }
        for val in i.values():
            for e in val:
                e["desc"] = _(e["desc"])
        return items

    # noinspection PyUnboundLocalVariable
    def is_included(self) -> bool:
        segment_items = self.items[self.SPECIFIC_ROAD_SUBTITLE]
        for item in segment_items:
            if item["desc"] == "frontal":
                segment_h2h = item["count"]
            elif item["desc"] == "others":
                segment_others = item["count"]
            else:
                raise ValueError
        segment_total = segment_h2h + segment_others
        all_items = self.items[self.ALL_ROADS_SUBTITLE]
        for item in all_items:
            if item["desc"] == "frontal":
                all_h2h = item["count"]
            elif item["desc"] == "others":
                all_others = item["count"]
            else:
                raise ValueError
        all_total = all_h2h + all_others
        return segment_h2h > 0 and (segment_h2h / segment_total) > all_h2h / all_total


# adding calls to _() for pybabel extraction
_("others")
_("frontal")
_("Fatal accidents distribution by accident type - head on collisions vs other accidents.")
