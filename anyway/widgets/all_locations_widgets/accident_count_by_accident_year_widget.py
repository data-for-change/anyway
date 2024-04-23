from typing import Dict

from flask_babel import _

from anyway.backend_constants import AccidentSeverity
from anyway.models import AccidentMarkerView
from anyway.request_params import RequestParams
from anyway.widgets.all_locations_widgets.all_locations_widget import AllLocationsWidget
from anyway.widgets.widget import register
from anyway.widgets.widget_utils import (
    gen_entity_labels,
    format_2_level_items,
    sort_and_fill_gaps_for_stacked_bar,
    get_location_text,
)


@register
class AccidentCountByAccidentYearWidget(AllLocationsWidget):
    name: str = "accident_count_by_accident_year"
    files = [__file__]

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params)
        self.rank = 8
        self.text = {
            # "title" and "labels" will be set in localize_items()
        }
        self.information = "Fatal, severe and light accidents count in the specified years, split by accident severity"

    def generate_items(self) -> None:
        res1 = self.widget_accidents_stats(
            table_obj=AccidentMarkerView,
            filters=self.request_params.location_info,
            group_by=("accident_year", "accident_severity"),
            count="accident_severity",
            start_time=self.request_params.start_time,
            end_time=self.request_params.end_time,
            resolution=self.request_params.resolution
        )
        res2 = sort_and_fill_gaps_for_stacked_bar(
            res1,
            range(self.request_params.start_time.year, self.request_params.end_time.year + 1),
            {
                AccidentSeverity.FATAL.value: 0,
                AccidentSeverity.SEVERE.value: 0,
                AccidentSeverity.LIGHT.value: 0,
            },
        )
        self.items = format_2_level_items(res2, None, AccidentSeverity)

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        location_text = get_location_text(request_params)
        items["data"]["text"] = {
            "title": _("Number of accidents, per year, split by severity"),
            "subtitle": _(location_text),
            "labels_map": gen_entity_labels(AccidentSeverity),
        }
        return items


_("Fatal, severe and light accidents count in the specified years, split by accident severity")
