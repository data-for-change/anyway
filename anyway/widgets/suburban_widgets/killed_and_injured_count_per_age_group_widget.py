from typing import Dict

from flask_babel import _

from anyway.backend_constants import BE_CONST as BE
from anyway.request_params import RequestParams
from anyway.widgets.suburban_widgets.killed_and_injured_count_per_age_group_widget_utils import (
    KilledAndInjuredCountPerAgeGroupWidgetUtils
)
from anyway.widgets.suburban_widgets import killed_and_injured_count_per_age_group_widget_utils
from anyway.widgets.suburban_widgets.sub_urban_widget import SubUrbanWidget
from anyway.widgets.widget import register


@register
class KilledInjuredCountPerAgeGroupWidget(SubUrbanWidget):
    name: str = "killed_and_injured_count_per_age_group"
    files = [__file__, killed_and_injured_count_per_age_group_widget_utils.__file__]

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params)
        self.rank = 14

    def generate_items(self) -> None:
        raw_data = KilledAndInjuredCountPerAgeGroupWidgetUtils.filter_and_group_injured_count_per_age_group(
            self.request_params
        )
        structured_data_list = []
        for age_group, severity_dict in raw_data.items():
            count_total = 0
            for count in severity_dict.values():
                count_total += count

            structured_data_list.append({BE.LKEY: age_group, BE.VAL: count_total})

        self.items = structured_data_list

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": _("Injury per age group"),
            "subtitle": request_params.location_info["road_segment_name"],
        }
        return items
