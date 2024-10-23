from typing import Dict

import pandas as pd
from flask_babel import _

from anyway.request_params import RequestParams
from anyway.backend_constants import BE_CONST
from anyway.widgets.widget_utils import (
    get_query, get_location_text, add_resolution_location_accuracy_filter
)
from anyway.models import AccidentMarkerView
from anyway.widgets.widget import register
from anyway.widgets.all_locations_widgets.all_locations_widget import AllLocationsWidget


@register
class AccidentsHeatMapWidget(AllLocationsWidget):
    name: str = "accidents_heat_map"
    files = [__file__]

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params)
        self.rank = 7

    def generate_items(self) -> None:
        accidents_heat_map_filters = add_resolution_location_accuracy_filter(
            self.request_params.location_info.copy(),
            self.request_params.resolution
        )
        self.items = self.get_accidents_heat_map(
            filters=accidents_heat_map_filters,
            start_time=self.request_params.start_time,
            end_time=self.request_params.end_time,
        )

    @staticmethod
    def get_accidents_heat_map(filters, start_time, end_time):
        filters = filters or {}
        filters["provider_code"] = [
            BE_CONST.CBS_ACCIDENT_TYPE_1_CODE,
            BE_CONST.CBS_ACCIDENT_TYPE_3_CODE,
        ]
        query = get_query(AccidentMarkerView, filters, start_time, end_time)
        query = query.with_entities("longitude", "latitude")
        df = pd.read_sql_query(query.statement, query.session.bind)
        return df.to_dict(orient="records")  # pylint: disable=no-member

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        location_text = get_location_text(request_params)
        items["data"]["text"] = {
            "title": _("All accidents heat map"),
            "subtitle": _(location_text),
        }
        items["meta"]["information"] = _("All accidents heat map (fatal, severe, light) in location")
        return items
