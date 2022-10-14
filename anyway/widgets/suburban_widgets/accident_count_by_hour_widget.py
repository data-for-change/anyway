from anyway.request_params import RequestParams
from anyway.widgets.widget_utils import get_accidents_stats
from anyway.models import AccidentMarkerView
from anyway.widgets.suburban_widgets.sub_urban_widget import SubUrbanWidget
from typing import Dict
from flask_babel import _


class AccidentCountByHourWidget(SubUrbanWidget):
    name: str = "accident_count_by_hour"
    files = [__file__]
    widget_digest = SubUrbanWidget.calc_widget_digest(files)

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
        )

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": _("Number of accidents by hour")
            + f" - {request_params.location_info['road_segment_name']}"
        }
        return items
