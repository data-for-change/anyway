from anyway.request_params import RequestParams
from anyway.widgets.suburban_widgets.sub_urban_widget import SubUrbanWidget
from typing import Dict
from flask_babel import _


class TopRoadSegmentsAccidentsWidget(SubUrbanWidget):
    name: str = "top_road_segments_accidents"
    files = [__file__]
    widget_digest = SubUrbanWidget.calc_widget_digest(files)

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 22

    def generate_items(self) -> None:
        self.items = TopRoadSegmentsAccidentsWidget.top_road_segments_accidents_mock_data()

    @staticmethod
    def top_road_segments_accidents_mock_data():  # Temporary for Frontend
        return [
            {"segment name": "מחלף לה גרדיה - מחלף השלום", "count": 70},
            {"segment name": "מחלף השלום - מחלף הרכבת", "count": 48},
            {"segment name": "מחלף וולפסון - מחלף חולון", "count": 48},
            {"segment name": "מחלף קוממיות - מחלף יוספטל", "count": 34},
            {"segment name": "מחלף ההלכה - מחלף רוקח ", "count": 31},
        ]

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {"title": _("Segments with most accidents")}
        return items
