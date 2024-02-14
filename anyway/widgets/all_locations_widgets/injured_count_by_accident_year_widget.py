from typing import Dict

from flask_babel import _

from anyway.backend_constants import InjurySeverity
from anyway.models import InvolvedMarkerView
from anyway.request_params import RequestParams
from anyway.widgets.all_locations_widgets.all_locations_widget import AllLocationsWidget
from anyway.widgets.widget import register
from anyway.widgets.widget_utils import (
    get_accidents_stats,
    gen_entity_labels,
    get_injured_filters,
    format_2_level_items,
    sort_and_fill_gaps_for_stacked_bar,
    get_location_text,
)


@register
class InjuredCountByAccidentYearWidget(AllLocationsWidget):
    name: str = "injured_count_by_accident_year"
    files = [__file__]

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params)
        self.rank = 9
        self.information = (
            "Fatal, severe and light injured count in the specified years, split by injury severity"
        )

    def generate_items(self) -> None:
        res1 = get_accidents_stats(
            table_obj=InvolvedMarkerView,
            filters=get_injured_filters(self.request_params),
            group_by=("accident_year", "injury_severity"),
            count="injury_severity",
            start_time=self.request_params.start_time,
            end_time=self.request_params.end_time,
        )
        res2 = sort_and_fill_gaps_for_stacked_bar(
            res1,
            range(self.request_params.start_time.year, self.request_params.end_time.year + 1),
            {
                InjurySeverity.KILLED.value: 0,
                InjurySeverity.SEVERE_INJURED.value: 0,
                InjurySeverity.LIGHT_INJURED.value: 0,
            },
        )
        self.items = format_2_level_items(res2, None, InjurySeverity)

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        location_text = get_location_text(request_params)
        items["data"]["text"] = {
            "title": _("Number of injured in accidents, per year, split by severity"),
            "subtitle": _(location_text),
            "labels_map": gen_entity_labels(InjurySeverity),
        }
        return items


_("Fatal, severe and light injured count in the specified years, split by injury severity")
