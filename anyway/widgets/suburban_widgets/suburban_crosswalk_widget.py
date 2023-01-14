from typing import Dict, Any

from anyway.request_params import RequestParams
from anyway.backend_constants import InjurySeverity
from anyway.models import InvolvedMarkerView
from anyway.widgets.suburban_widgets.sub_urban_widget import SubUrbanWidget
from anyway.widgets.widget_utils import get_accidents_stats
from flask_babel import _

from anyway.backend_constants import CrossCategory


# TODO: pretty sure there are errors in this widget, for example, is_included returns self.items
class SuburbanCrosswalkWidget(SubUrbanWidget):
    name: str = "suburban_accidents_by_cross_location"
    files = [__file__]

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params)
        self.rank = 26

    def generate_items(self) -> None:
        self.items = SuburbanCrosswalkWidget.get_crosswalk(
            self.request_params.location_info["road_segment_name"],
            self.request_params.start_time,
            self.request_params.end_time,
        )

    @staticmethod
    def get_crosswalk(road, start_time, end_time) -> Dict[str, Any]:
        cross_output = {
            "with_crosswalk": get_accidents_stats(
                table_obj=InvolvedMarkerView,
                filters={
                    "injury_severity": [
                        InjurySeverity.KILLED.value,  # pylint: disable=no-member
                        InjurySeverity.SEVERE_INJURED.value,
                    ],
                    "cross_location": CrossCategory.CROSSWALK.get_codes(),
                    "road_segment_name": road,
                },
                group_by="road_segment_name",
                count="road_segment_name",
                start_time=start_time,
                end_time=end_time,
            ),
            "without_crosswalk": get_accidents_stats(
                table_obj=InvolvedMarkerView,
                filters={
                    "injury_severity": [
                        InjurySeverity.KILLED.value,  # pylint: disable=no-member
                        InjurySeverity.SEVERE_INJURED.value,
                    ],
                    "cross_location": CrossCategory.NONE.get_codes(),
                    "road_segment_name": road,
                },
                group_by="road_segment_name",
                count="road_segment_name",
                start_time=start_time,
                end_time=end_time,
            ),
        }
        if not cross_output["with_crosswalk"]:
            cross_output["with_crosswalk"] = [{"road_segment": road, "count": 0}]
        if not cross_output["without_crosswalk"]:
            cross_output["without_crosswalk"] = [{"road_segment": road, "count": 0}]
        return cross_output

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": _("Pedestrian injury comparison on ")
            + request_params.location_info["road_segment_name"]
        }
        return items

    def is_included(self) -> bool:
        return (
            self.items["with_crosswalk"][0]["count"] + self.items["without_crosswalk"][0]["count"]
        ) > 10
