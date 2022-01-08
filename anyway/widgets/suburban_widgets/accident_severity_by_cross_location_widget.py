from anyway.request_params import RequestParams
from anyway.widgets.widget import register
from anyway.widgets.suburban_widgets.sub_urban_widget import SubUrbanWidget
from typing import Dict

@register
class AccidentSeverityByCrossLocationWidget(SubUrbanWidget):
    name: str = "accident_severity_by_cross_location"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 19

    @staticmethod
    def is_in_cache() -> bool:
        return False

    def generate_items(self) -> None:
        # TODO: add real data
        self.items = (
            AccidentSeverityByCrossLocationWidget.injury_severity_by_cross_location_mock_data()
        )

    @staticmethod
    def injury_severity_by_cross_location_mock_data():  # Temporary for Frontend
        return [
            {
                "cross_location_text": "במעבר חצייה",
                "light_injury_severity_text": "פצוע קל",
                "light_injury_severity_count": 37,
                "severe_injury_severity_text": "פצוע קשה",
                "severe_injury_severity_count": 6,
                "killed_injury_severity_text": "הרוג",
                "killed_injury_severity_count": 0,
            },
            {
                "cross_location_text": "לא במעבר חצייה",
                "light_injury_severity_text": "פצוע קל",
                "light_injury_severity_count": 11,
                "severe_injury_severity_text": "פצוע קשה",
                "severe_injury_severity_count": 10,
                "killed_injury_severity_text": "הרוג",
                "killed_injury_severity_count": 0,
            },
        ]

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": "Number of pedestrian accidents on Ben Yehuda street in Tel Aviv by crossing location"
        }
        return items