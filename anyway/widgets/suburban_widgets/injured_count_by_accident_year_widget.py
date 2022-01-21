import typing
from collections import defaultdict
from typing import Dict

from flask_babel import _

from anyway.backend_constants import InjurySeverity
from anyway.infographics_dictionaries import segment_dictionary
from anyway.models import InvolvedMarkerView
from anyway.request_params import RequestParams
from anyway.widgets.suburban_widgets.sub_urban_widget import SubUrbanWidget
from anyway.widgets.widget import register
from anyway.widgets.widget_utils import (
    get_accidents_stats,
    gen_entity_labels,
    get_injured_filters,
    format_2_level_items,
)


@register
class InjuredCountByAccidentYearWidget(SubUrbanWidget):
    name: str = "injured_count_by_accident_year"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 9
        self.information = (
            "Fatal, severe and light injured count in the specified years, split by injury severity"
        )

    @staticmethod
    def sort_by_years_and_severity(
        data: defaultdict, years_range: typing.Iterable
    ) -> Dict[int, dict]:
        res = {}
        for year in years_range:
            res[year] = {
                InjurySeverity.KILLED.value: 0,
                InjurySeverity.SEVERE_INJURED.value: 0,
                InjurySeverity.LIGHT_INJURED.value: 0,
            }
            severity_in_year = data.get(year, {})
            for severity, count in severity_in_year.items():
                res[year][severity] += count

        return res

    def generate_items(self) -> None:
        res1 = get_accidents_stats(
            table_obj=InvolvedMarkerView,
            filters=get_injured_filters(self.request_params.location_info),
            group_by=("accident_year", "injury_severity"),
            count="injury_severity",
            start_time=self.request_params.start_time,
            end_time=self.request_params.end_time,
        )
        res2 = self.sort_by_years_and_severity(
            res1, range(self.request_params.start_time.year, self.request_params.end_time.year + 1)
        )
        self.items = format_2_level_items(res2, None, InjurySeverity)

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": _("Number of injured in accidents, per year, split by severity")
            + f" - {segment_dictionary[request_params.location_info['road_segment_name']]}",
            "labels_map": gen_entity_labels(InjurySeverity),
        }
        return items


_("Fatal, severe and light injured count in the specified years, split by injury severity")
