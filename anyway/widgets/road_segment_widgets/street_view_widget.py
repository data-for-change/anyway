from anyway.request_params import RequestParams
from anyway.widgets.widget import register
from anyway.widgets.road_segment_widgets.road_segment_widget import RoadSegmentWidget
from typing import Dict
from flask_babel import _


@register
class StreetViewWidget(RoadSegmentWidget):
    name: str = "street_view"
    files = [__file__]

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params)
        self.rank = 4

    def generate_items(self) -> None:
        self.items = {
            "longitude": self.request_params.gps.get("lon"),
            "latitude": self.request_params.gps.get("lat"),
        }

    def is_included(self):
        return self.request_params.gps and self.request_params.gps.get("lon") and self.request_params.gps.get("lat")


    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {"title": _("Street view widget")}
        return items
