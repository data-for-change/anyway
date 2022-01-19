from typing import Dict

from flask_babel import _

from anyway.request_params import RequestParams
from anyway.backend_constants import AccidentSeverity
from anyway.models import AccidentMarkerView
from anyway.widgets.widget import register
from anyway.widgets.suburban_widgets.sub_urban_widget import SubUrbanWidget
from anyway.widgets.widget_utils import (
    get_accidents_stats,
)


@register
class FatalAccidentYoYSameMonth(SubUrbanWidget):
    name: str = "fatal_accident_yoy_same_month"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 8

    def generate_items(self) -> None:
        self.items = get_accidents_stats(
            table_obj=AccidentMarkerView,
            filters={"accident_month": 9, "accident_severity": AccidentSeverity.FATAL},
            group_by=("accident_year"),
            count="accident_severity",
            start_time=self.request_params.start_time,
            end_time=self.request_params.end_time,
        )

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": _("Killed in accidents on September compared to September in previous years"),
        }
        return items


_("Killed in accidents on September compared to September in previous years")
