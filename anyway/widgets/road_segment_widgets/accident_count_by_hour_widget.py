from anyway.request_params import RequestParams
from anyway.widgets.widget_utils import get_accidents_stats
from anyway.models import AccidentMarkerView
from anyway.widgets.road_segment_widgets.road_segment_widget import RoadSegmentWidget
from typing import Dict
from flask_babel import _


class AccidentCountByHourWidget(RoadSegmentWidget):
    name: str = "accident_count_by_hour"
    files = [__file__]

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params)
        self.rank = 11

    def generate_items(self) -> None:
        self.items = get_accidents_stats(
            table_obj=AccidentMarkerView,
            filters=self.request_params.location_info,
            group_by="accident_hour",
            count="accident_hour",
            start_time=self.request_params.start_time,
            end_time=self.request_params.end_time,
            resolution=self.request_params.resolution,
        )

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": _("Number of accidents by hour"),
            "subtitle": _(request_params.location_info['road_segment_name'])
        }
        return items
