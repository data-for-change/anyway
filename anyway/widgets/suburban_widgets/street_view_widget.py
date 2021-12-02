from anyway.request_params import RequestParams
from anyway.widgets.widget import register
from anyway.widgets.suburban_widgets.sub_urban_widget import SubUrbanWidget


@register
class StreetViewWidget(SubUrbanWidget):
    name: str = "street_view"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 4

    def generate_items(self) -> None:
        self.items = {
            "longitude": self.request_params.gps["lon"],
            "latitude": self.request_params.gps["lat"],
        }
