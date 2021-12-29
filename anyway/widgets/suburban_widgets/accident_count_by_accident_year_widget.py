from typing import Dict

from flask_babel import _

from anyway.backend_constants import AccidentSeverity as AS
from anyway.infographics_dictionaries import segment_dictionary
from anyway.models import AccidentMarkerView
from anyway.request_params import RequestParams
from anyway.widgets.suburban_widgets.sub_urban_widget import SubUrbanWidget
from anyway.widgets.widget import register
from anyway.widgets.widget_utils import (
    get_accidents_stats,
    add_empty_keys_to_gen_two_level_dict,
    gen_entity_labels,
    format_2_level_items,
    order_severity_in_stack_bar_widget,
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
        res2 = add_empty_keys_to_gen_two_level_dict(
            res1,
            list(range(self.request_params.start_time.year, self.request_params.end_time.year + 1)),
            AS.codes(),
        )

        two_level_format = format_2_level_items(res2, None, AS)
        self.items = order_severity_in_stack_bar_widget(
            two_level_format, [AS.LIGHT.get_label(), AS.SEVERE.get_label(), AS.FATAL.get_label()]
        )

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": _("Number of accidents, by year, splitted by accident severity, in segment")
            + " "
            + segment_dictionary[request_params.location_info["road_segment_name"]],
            "labels_map": gen_entity_labels(AS),
        }
        return items


_("Fatal, severe and light accidents count in the specified years, split by accident severity")
