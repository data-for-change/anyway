from anyway.request_params import RequestParams
from anyway.widgets.widget_utils import get_accidents_stats
from anyway.models import AccidentMarkerView
from anyway.widgets.widget import register
from anyway.widgets.suburban_widgets.sub_urban_widget import SubUrbanWidget
from typing import Dict

# noinspection PyProtectedMember
from flask_babel import _
from anyway.backend_constants import AccidentType


@register
class AccidentCountByAccidentTypeWidget(SubUrbanWidget):
    name: str = "accident_count_by_accident_type"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 6
        self.information = (
            "Distribution of accidents by type in the selected segment and time period. "
            "Three most common accident types are displayed"
        )

    def generate_items(self) -> None:
        # noinspection PyUnresolvedReferences
        self.items = AccidentCountByAccidentTypeWidget.get_accident_count_by_accident_type(
            location_info=self.request_params.location_info,
            start_time=self.request_params.start_time,
            end_time=self.request_params.end_time,
        )

    @staticmethod
    def get_accident_count_by_accident_type(location_info, start_time, end_time):
        all_accident_type_count = get_accidents_stats(
            table_obj=AccidentMarkerView,
            filters=location_info,
            group_by="accident_type",
            count="accident_type",
            start_time=start_time,
            end_time=end_time,
        )
        merged_accident_type_count = [{"accident_type": "Collision", "count": 0}]
        for item in all_accident_type_count:
            at: AccidentType = AccidentType(item["accident_type"])
            if at.is_collision():
                merged_accident_type_count[0]["count"] += item["count"]
            else:
                item["accident_type"] = at.get_label()
                merged_accident_type_count.append(item)
        res = sorted(merged_accident_type_count, key=lambda x: x["count"], reverse=True)
        return res[: min(3, len(res))]

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {"title": _("Number of accidents by accident type")}
        for item in items["data"]["items"]:
            to_translate = item["accident_type"]
            item["accident_type"] = _(to_translate)
        return items


_("Collision")
_(
    "Distribution of accidents by type in the selected segment and time period. Three most common accident types are displayed"
)
