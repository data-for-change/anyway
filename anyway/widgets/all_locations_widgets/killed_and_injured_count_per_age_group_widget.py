import logging
from typing import Dict

from flask_babel import _

from anyway.backend_constants import BE_CONST as BE
from anyway.request_params import RequestParams
from anyway.widgets.all_locations_widgets.killed_and_injured_count_per_age_group_widget_utils import (
    KilledAndInjuredCountPerAgeGroupWidgetUtils,
)
from anyway.widgets.all_locations_widgets import killed_and_injured_count_per_age_group_widget_utils
from anyway.widgets.all_locations_widgets.all_locations_widget import AllLocationsWidget
from anyway.widgets.widget import register
from anyway.widgets.widget_utils import get_location_text


@register
class KilledInjuredCountPerAgeGroupWidget(AllLocationsWidget):
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

    def is_included(self) -> bool:
        accidents_count = sum(item['value'] for item in self.items)
        return accidents_count > 0

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        if request_params.lang != "en":
            for item in items["data"]["items"]:
                try:
                    item["label_key"] = _(item["label_key"])
                except KeyError:
                    logging.exception(
                        f"KilledInjuredCountPerAgeGroupWidget.localize_items: Exception while translating {item}."
                    )

        location_text = get_location_text(request_params)
        items["data"]["text"] = {"title": _("Injury per age group"), "subtitle": _(location_text)}
        items["meta"]["information"] = _("Injured count per age group. The graph shows all injury severities: fatal, severe, and light.")
        return items
