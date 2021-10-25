from anyway.RequestParams import RequestParams
from anyway.infographics_utils import register
from anyway.widgets.suburban_widgets.SubUrbanWidget import SubUrbanWidget


@register
class TopRoadSegmentsAccidentsWidget(SubUrbanWidget):
    name: str = "top_road_segments_accidents"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 22
        self.text = {"title": "5 המקטעים עם כמות התאונות הגדולה ביותר"}

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