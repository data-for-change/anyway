from typing import Dict, Any

from flask_babel import _

from anyway.backend_constants import CrossCategory
from anyway.backend_constants import InjurySeverity
from anyway.models import InvolvedMarkerView
from anyway.request_params import RequestParams
from anyway.widgets.urban_widgets.urban_widget import UrbanWidget
from anyway.widgets.widget_utils import get_accidents_stats


class UrbanCrosswalkWidget(UrbanWidget):
    name: str = "urban_accidents_by_cross_location"
    files = [__file__]

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params)
        self.rank = 27

    def generate_items(self) -> None:
        self.items = UrbanCrosswalkWidget.get_crosswalk(
            self.request_params.location_info,
            self.request_params.start_time,
            self.request_params.end_time,
            self.request_params.resolution,
        )

    @staticmethod
    def get_crosswalk(location_info: dict, start_time, end_time, resolution) -> Dict[str, Any]:
        cross_output = {
            "with_crosswalk": get_accidents_stats(
                table_obj=InvolvedMarkerView,
                filters={
                    "injury_severity": [
                        InjurySeverity.KILLED.value,  # pylint: disable=no-member
                        InjurySeverity.SEVERE_INJURED.value,
                    ],
                    "cross_location": CrossCategory.CROSSWALK.get_codes(),
                    "accident_yishuv_symbol": location_info["yishuv_symbol"],
                    "street1": location_info["street"],
                },
                group_by="street1",
                count="street1",
                start_time=start_time,
                end_time=end_time,
                resolution=resolution,
            ),
            "without_crosswalk": get_accidents_stats(
                table_obj=InvolvedMarkerView,
                filters={
                    "injury_severity": [
                        InjurySeverity.KILLED.value,  # pylint: disable=no-member
                        InjurySeverity.SEVERE_INJURED.value,
                    ],
                    "cross_location": CrossCategory.NONE.get_codes(),
                    "accident_yishuv_symbol": location_info["yishuv_symbol"],
                    "street1": location_info["street"],
                },
                group_by="street1",
                count="street1",
                start_time=start_time,
                end_time=end_time,
                resolution=resolution,
            ),
        }
        if not cross_output["with_crosswalk"]:
            cross_output["with_crosswalk"] = [{"street1_hebrew": location_info["_hebrew"],
                                               "count": 0}]
        if not cross_output["without_crosswalk"]:
            cross_output["without_crosswalk"] = [{"street1_hebrew": location_info["street_hebrew"],
                                                   "count": 0}]
        return cross_output

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": _("Pedestrian injury comparison"),
            "subtitle": _(request_params.location_info["street1_hebrew"])
        }
        return items

    def is_included(self) -> bool:
        return (
            self.items["with_crosswalk"][0]["count"] + self.items["without_crosswalk"][0]["count"]
            > 10
        )
