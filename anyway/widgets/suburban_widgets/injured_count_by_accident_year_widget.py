from typing import Dict

from flask_babel import _

from anyway.request_params import RequestParams
from anyway.constants.injury_severity import InjurySeverity
from anyway.infographics_dictionaries import segment_dictionary
from anyway.widgets.widget_utils import (
    get_accidents_stats,
    add_empty_keys_to_gen_two_level_dict,
    gen_entity_labels,
    get_injured_filters,
    format_2_level_items,
)
from anyway.models import InvolvedMarkerView
from anyway.widgets.widget import register
from anyway.widgets.suburban_widgets.sub_urban_widget import SubUrbanWidget


@register
class InjuredCountByAccidentYearWidget(SubUrbanWidget):
    name: str = "injured_count_by_accident_year"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 9
        self.information = (
            "Fatal, severe and light injured count in the specified years, split by injury severity"
        )

    def generate_items(self) -> None:
        res1 = get_accidents_stats(
            table_obj=InvolvedMarkerView,
            filters=get_injured_filters(self.request_params.location_info),
            group_by=("accident_year", "injury_severity"),
            count="injury_severity",
            start_time=self.request_params.start_time,
            end_time=self.request_params.end_time,
        )
        res2 = add_empty_keys_to_gen_two_level_dict(
            res1,
            list(range(self.request_params.start_time.year, self.request_params.end_time.year + 1)),
            InjurySeverity.codes(),
        )
        self.items = format_2_level_items(res2, None, InjurySeverity)

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": _('Number of injured in accidents, per year, split by severity') +f" - {segment_dictionary[request_params.location_info['road_segment_name']]}",
            "labels_map": gen_entity_labels(InjurySeverity),
        }
        return items


_("Fatal, severe and light injured count in the specified years, split by injury severity")
