from collections import defaultdict
from typing import Dict

import typing
from flask_babel import _

from anyway.backend_constants import AccidentSeverity
from anyway.infographics_dictionaries import segment_dictionary
from anyway.models import AccidentMarkerView
from anyway.request_params import RequestParams
from anyway.widgets.suburban_widgets.sub_urban_widget import SubUrbanWidget
from anyway.widgets.widget import register
from anyway.widgets.widget_utils import (
    get_accidents_stats,
    gen_entity_labels,
    format_2_level_items,
)


@register
class AccidentCountByAccidentYearWidget(SubUrbanWidget):
    name: str = "accident_count_by_accident_year"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 8
        self.text = {
            # "title" and "labels" will be set in localize_items()
        }
        self.information = "Fatal, severe and light accidents count in the specified years, split by accident severity"

    @staticmethod
    def sort_by_years_and_severity(data: defaultdict, years_range: typing.Iterable) -> Dict[int, dict]:
        res = {}
        for year in years_range:
            res[year] = {
                AccidentSeverity.FATAL.value: 0,
                AccidentSeverity.SEVERE.value: 0,
                AccidentSeverity.LIGHT.value: 0,
            }
            severity_in_year = data.get(year, {})
            for severity, count in severity_in_year.items():
                res[year][severity] += count

        return res

    def generate_items(self) -> None:

        res1 = get_accidents_stats(
            table_obj=AccidentMarkerView,
            filters=self.request_params.location_info,
            group_by=("accident_year", "accident_severity"),
            count="accident_severity",
            start_time=self.request_params.start_time,
            end_time=self.request_params.end_time,
        )

        years_range = range(
            self.request_params.start_time.year, self.request_params.end_time.year + 1
        )
        res2 = self.sort_by_years_and_severity(res1, years_range)

        self.items = format_2_level_items(res2, None, AccidentSeverity)

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": _("Number of accidents, by year, splitted by accident severity, in segment")
            + " "
            + segment_dictionary[request_params.location_info["road_segment_name"]],
            "labels_map": gen_entity_labels(AccidentSeverity),
        }
        return items


_("Fatal, severe and light accidents count in the specified years, split by accident severity")
