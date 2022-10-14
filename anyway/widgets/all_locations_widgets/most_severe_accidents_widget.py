import logging
from typing import Dict

# noinspection PyProtectedMember
from flask_babel import _

from anyway.request_params import RequestParams
from anyway.backend_constants import AccidentSeverity, AccidentType, BE_CONST
from anyway.widgets.all_locations_widgets.most_severe_accidents_table_widget import (
    get_most_severe_accidents_with_entities,
    get_most_severe_accidents_table_title,
)
from anyway.models import AccidentMarkerView
from anyway.widgets.widget import register
from anyway.widgets.all_locations_widgets.all_locations_widget import AllLocationsWidget


@register
class MostSevereAccidentsWidget(AllLocationsWidget):
    name: str = "most_severe_accidents"
    files = [__file__]
    widget_digest = AllLocationsWidget.calc_widget_digest(files)

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params)
        self.rank = 3
        self.information = "Most recent fatal and severe accidents displayed on a map. Up to 10 accidents are presented."

    def generate_items(self) -> None:
        # noinspection PyUnresolvedReferences
        self.items = MostSevereAccidentsWidget.get_most_severe_accidents(
            AccidentMarkerView,
            self.request_params.location_info,
            self.request_params.start_time,
            self.request_params.end_time,
            self.request_params.resolution,
        )

    @staticmethod
    def get_most_severe_accidents(
        table_obj,
        filters,
        start_time,
        end_time,
        resolution: BE_CONST.ResolutionCategories,
        limit=10,
    ):
        entities = (
            "longitude",
            "latitude",
            "accident_severity",
            "accident_timestamp",
            "accident_type",
        )

        items = get_most_severe_accidents_with_entities(
            table_obj, filters, entities, start_time, end_time, resolution, limit
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
        items["data"]["text"] = {
            "title": get_most_severe_accidents_table_title(
                request_params.location_info, request_params.resolution
            )
        }
        return items


# adding calls to _() for pybabel extraction
_("Most recent fatal and severe accidents displayed on a map. Up to 10 accidents are presented.")
