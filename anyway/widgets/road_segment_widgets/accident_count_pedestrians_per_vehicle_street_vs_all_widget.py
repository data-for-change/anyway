from anyway.request_params import RequestParams
from anyway.widgets.widget import Widget
from anyway.widgets.road_segment_widgets.road_segment_widget import RoadSegmentWidget
from typing import Dict


# TODO: register?
class AccidentCountPedestriansPerVehicleStreetVsAllWidget(RoadSegmentWidget):
    name: str = "accident_count_pedestrians_per_vehicle_street_vs_all"
    files = [__file__]

    def __init__(self, request_params: RequestParams):
        Widget.__init__(self, request_params)
        self.rank = 21

    @staticmethod
    def is_in_cache() -> bool:
        return False

    def generate_items(self) -> None:
        # TODO: add real data
        self.items = (
            AccidentCountPedestriansPerVehicleStreetVsAllWidget.accidents_count_pedestrians_per_vehicle_street_vs_all_mock_data()
        )

    @staticmethod
    def accidents_count_pedestrians_per_vehicle_street_vs_all_mock_data():  # Temporary for Frontend
        return [
            {"location": "כל הארץ", "vehicle": "מכונית", "num_of_accidents": 61307},
            {"location": "כל הארץ", "vehicle": "רכב כבד", "num_of_accidents": 15801},
            {"location": "כל הארץ", "vehicle": "אופנוע", "num_of_accidents": 3884},
            {"location": "כל הארץ", "vehicle": "אופניים וקורקינט ממונע", "num_of_accidents": 1867},
            {"location": "כל הארץ", "vehicle": "אחר", "num_of_accidents": 229},
            {"location": "בן יהודה", "vehicle": "מכונית", "num_of_accidents": 64},
            {"location": "בן יהודה", "vehicle": "אופנוע", "num_of_accidents": 40},
            {"location": "בן יהודה", "vehicle": "רכב כבד", "num_of_accidents": 22},
            {"location": "בן יהודה", "vehicle": "אופניים וקורקינט ממונע", "num_of_accidents": 9},
        ]

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": "Number of pedestrian accidents by type of hitting vehicle compared to urban accidents across the country",
            "subtitle": "Ben Yehuda street in Tel Aviv"
        }
        return items
