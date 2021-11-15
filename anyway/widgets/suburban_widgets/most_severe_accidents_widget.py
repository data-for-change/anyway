import logging
from typing import Dict

from flask_babel import _

from anyway.RequestParams import RequestParams
from anyway.backend_constants import AccidentSeverity, AccidentType
from anyway.widgets.suburban_widgets.most_severe_accidents_table_widget import (
    get_most_severe_accidents_with_entities,
)
from anyway.models import AccidentMarkerView
from anyway.widgets.widget import register
from anyway.widgets.suburban_widgets.sub_urban_widget import SubUrbanWidget


@register
class MostSevereAccidentsWidget(SubUrbanWidget):
    name: str = "most_severe_accidents"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 3
        self.information = "Most recent fatal and severe accidents displayed on a map. Up to 10 accidents are presented."

    def generate_items(self) -> None:
        self.items = MostSevereAccidentsWidget.get_most_severe_accidents(
            AccidentMarkerView,
            self.request_params.location_info,
            self.request_params.start_time,
            self.request_params.end_time,
        )

    @staticmethod
    def get_most_severe_accidents(table_obj, filters, start_time, end_time, limit=10):
        entities = (
            "longitude",
            "latitude",
            "accident_severity",
            "accident_timestamp",
            "accident_type",
        )

        items = get_most_severe_accidents_with_entities(
            table_obj, filters, entities, start_time, end_time, limit
        )
        for item in items:
            item["accident_severity"] = _(AccidentSeverity(item["accident_severity"]).get_label())
        return items

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        for item in items["data"]["items"]:
            try:
                item["accident_type"] = _(AccidentType(item["accident_type"]).get_label())
            except KeyError:
                logging.exception(
                    f"MostSevereAccidentsWidget.localize_items: Exception while translating {item}."
                )
        return items


# adding calls to _() for pybabel extraction
_("Most recent fatal and severe accidents displayed on a map. Up to 10 accidents are presented.")
