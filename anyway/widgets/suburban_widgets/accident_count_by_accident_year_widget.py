import logging
from typing import Dict

from flask_babel import _

from anyway.RequestParams import RequestParams
from anyway.backend_constants import AccidentSeverity
from anyway.infographics_dictionaries import segment_dictionary
from anyway.models import AccidentMarkerView
from anyway.widgets.widget import register
from anyway.widgets.suburban_widgets.sub_urban_widget import SubUrbanWidget
from anyway.widgets.widget_utils import (
    get_accidents_stats,
    add_empty_keys_to_gen_two_level_dict,
    gen_entity_labels,
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

        res = get_accidents_stats(
            table_obj=AccidentMarkerView,
            filters=self.request_params.location_info,
            group_by=("accident_severity", "accident_year"),
            count="accident_year",
            start_time=self.request_params.start_time,
            end_time=self.request_params.end_time,
        )
        try:
            self.items = add_empty_keys_to_gen_two_level_dict(
                res,
                AccidentSeverity.codes(),
                list(
                    range(
                        self.request_params.start_time.year, self.request_params.end_time.year + 1
                    )
                ),
            )
        except Exception as e:
            logging.exception(f"failed to add empty keys to {res}", e)

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": _("Number of accidents, by year, splitted by accident severity, in segment")
            + " "
            + segment_dictionary[request_params.location_info["road_segment_name"]],
            "labels": gen_entity_labels(AccidentSeverity),
        }
        return items


_("Fatal, severe and light accidents count in the specified years, split by accident severity")
