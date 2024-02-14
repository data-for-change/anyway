from anyway.request_params import RequestParams
from anyway.widgets.widget_utils import get_accidents_stats, get_location_text
from anyway.models import AccidentMarkerView
from anyway.widgets.widget import register
from anyway.widgets.all_locations_widgets.all_locations_widget import AllLocationsWidget
from typing import Dict
from flask_babel import _


@register
class AccidentCountByDayNightWidget(AllLocationsWidget):
    name: str = "accident_count_by_day_night"
    files = [__file__]

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params)
        self.rank = 10
        self.information = (
            "Distribution of accidents by day/night. "
            "Day/night are determined by sunrise and sunset at each day of the year."
        )

    def generate_items(self) -> None:
        self.items = get_accidents_stats(
            table_obj=AccidentMarkerView,
            filters=self.request_params.location_info,
            group_by="day_night_hebrew",
            count="day_night_hebrew",
            start_time=self.request_params.start_time,
            end_time=self.request_params.end_time,
        )

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        location_text = get_location_text(request_params)
        items["data"]["text"] = {"title": _("Accidents by time"), "subtitle": _(location_text)}
        return items


_(
    "Distribution of accidents by day/night. "
    "Day/night are determined by sunrise and sunset at each day of the year."
)
