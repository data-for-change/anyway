from typing import Dict

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
)


@register
class TotalAccidentCountByAccidentYearWidget(SubUrbanWidget):
    name: str = "total_accident_count_by_accident_year_stacked_bar"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 21
        self.text = {
            # "title" and "labels" will be set in localize_items()
        }
        self.information = _("Accidents count in the specified years")

    def generate_items(self) -> None:
        res1 = get_accidents_stats(
            table_obj=AccidentMarkerView,
            filters=self.request_params.location_info,
            group_by="accident_year",
            count="accident_year",
            start_time=self.request_params.start_time,
            end_time=self.request_params.end_time,
        )
        self.items = []
        for year_result in res1:
            self.items.append(
                {"label_key": year_result["accident_year"], "value": year_result["count"]}
            )

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": _("Number of accidents, by year in segment")
            + " "
            + segment_dictionary[request_params.location_info["road_segment_name"]],
            "labels_map": gen_entity_labels(AccidentSeverity),
        }
        return items

