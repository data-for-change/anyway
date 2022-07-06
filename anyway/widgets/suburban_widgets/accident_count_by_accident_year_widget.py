from typing import Dict

from flask_babel import _

from anyway.backend_constants import AccidentSeverity, BE_CONST
from anyway.infographics_dictionaries import segment_dictionary
from anyway.models import AccidentMarkerView
from anyway.request_params import RequestParams
from anyway.widgets.suburban_widgets.sub_urban_widget import SubUrbanWidget
from anyway.widgets.widget import register
from anyway.widgets.widget_utils import (
    get_accidents_stats,
    gen_entity_labels,
    format_2_level_items,
    sort_and_fill_gaps_for_stacked_bar,
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

    def generate_items(self) -> None:
        res1 = get_accidents_stats(
            table_obj=AccidentMarkerView,
            filters=self.request_params.location_info,
            group_by=("accident_year", "accident_severity"),
            count="accident_severity",
            start_time=self.request_params.start_time,
            end_time=self.request_params.end_time,
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
        self.items = format_2_level_items(res2, None, AccidentSeverity, total=True)

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": _("Accidents in segment")
            + " "
            + segment_dictionary[request_params.location_info["road_segment_name"]],
            "labels_map": {**gen_entity_labels(AccidentSeverity),
             **{BE_CONST.TOTAL : _("total_accidents")}}
        }
        return items


_("Fatal, severe and light accidents count in the specified years, split by accident severity")
