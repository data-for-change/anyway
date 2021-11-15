import datetime
from typing import Optional, Dict

from anyway.RequestParams import RequestParams
from anyway.backend_constants import BE_CONST, AccidentType
from anyway.widgets.widget_utils import get_accidents_stats
from anyway.models import AccidentMarkerView
from anyway.widgets.widget import register
from anyway.widgets.suburban_widgets.sub_urban_widget import SubUrbanWidget


@register
class Road2Plus1Widget(SubUrbanWidget):
    name: str = "vision_zero_2_plus_1"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.information = "Road 2 plus 1 solution to prevent fatal accidents."
        self.rank = 24

    def generate_items(self) -> None:
        self.items = {"image_src": "vision_zero_2_plus_1"}

    def get_frontal_accidents_in_past_year(self) -> Optional[int]:
        location_info = self.request_params.location_info
        road_data = {}
        filter_dict = {"road_type": BE_CONST.ROAD_TYPE_NOT_IN_CITY_NOT_IN_INTERSECTION}

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
                start_time=self.request_params.end_time - datetime.timedelta(days=365),
                end_time=self.request_params.end_time,
            )

            road_sums = self.sum_count_of_accident_type(
                # pylint: disable=no-member
                road_data,
                AccidentType.HEAD_ON_FRONTAL_COLLISION.value,
            )

            return road_sums

    @staticmethod
    def sum_count_of_accident_type(data: Dict, acc_type: int) -> int:
        given = sum([d["count"] for d in data if d["accident_type"] == acc_type])
        return given

    # noinspection PyUnboundLocalVariable
    def is_included(self) -> bool:
        frontal_accidents_past_year = self.get_frontal_accidents_in_past_year()
        if frontal_accidents_past_year is not None:
            return frontal_accidents_past_year >= 2
        return False
