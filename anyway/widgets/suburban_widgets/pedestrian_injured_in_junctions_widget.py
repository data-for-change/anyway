from anyway.request_params import RequestParams
from anyway.widgets.widget import register
from anyway.widgets.suburban_widgets.sub_urban_widget import SubUrbanWidget
from typing import Dict

# TODO: unregister? this widget produces only mock data
@register
class PedestrianInjuredInJunctionsWidget(SubUrbanWidget):
    name: str = "pedestrian_injured_in_junctions"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 23

    # TODO: add real data
    def generate_items(self) -> None:
        self.items = PedestrianInjuredInJunctionsWidget.pedestrian_injured_in_junctions_mock_data()

    @staticmethod
    def pedestrian_injured_in_junctions_mock_data():  # Temporary for Frontend
        return [
            {"street name": "גורדון י ל", "count": 18},
            {"street name": "אידלסון אברהם", "count": 10},
            {"street name": "פרישמן", "count": 7},
        ]

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": "Number of pedestrian accidents on junctions in Ben Yehuda street in Tel Aviv"
        }
        return items
