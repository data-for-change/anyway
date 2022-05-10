from typing import Dict, Union, Any

from flask_babel import _

from anyway.backend_constants import CrossCategory
from anyway.backend_constants import InjurySeverity
from anyway.models import InvolvedMarkerView
from anyway.request_params import RequestParams
from anyway.widgets.urban_widgets.urban_widget import UrbanWidget
from anyway.widgets.widget_utils import get_accidents_stats


# TODO: pretty sure there are errors in this widget, for example, is_included returns self.items
class UrbanCrosswalkWidget(UrbanWidget):
    name: str = "urban_accidents_by_cross_location"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 27

    def generate_items(self) -> None:
        self.items = UrbanCrosswalkWidget.get_crosswalk(
            self.request_params.location_info["yishuv_name"],
            self.request_params.location_info["street1_hebrew"],
            self.request_params.start_time,
            self.request_params.end_time,
        )

    @staticmethod
    def get_crosswalk(
        yishuv, street, start_time, end_time
    ) -> Dict[str, Any]:
        cross_output = {
            "with_crosswalk": get_accidents_stats(
                table_obj=InvolvedMarkerView,
                filters={
                    "injury_severity": [
                        InjurySeverity.KILLED.value,  # pylint: disable=no-member
                        InjurySeverity.SEVERE_INJURED.value,
                    ],
                    "cross_location": CrossCategory.CROSSWALK.get_codes(),
                    "involve_yishuv_name": yishuv,
                    "street1_hebrew": street,
                },
                group_by="street1_hebrew",
                count="street1_hebrew",
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
                    "involve_yishuv_name": yishuv,
                    "street1_hebrew": street,
                },
                group_by="street1_hebrew",
                count="street1_hebrew",
                start_time=start_time,
                end_time=end_time,
            ),
        }
        if not cross_output["with_crosswalk"]:
            cross_output["with_crosswalk"] = [{"street1_hebrew": street, "count": 0}]
        if not cross_output["without_crosswalk"]:
            cross_output["without_crosswalk"] = [{"street1_hebrew": street, "count": 0}]
        return cross_output

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": _("Pedestrian injury comparison on ")
            + request_params.location_info["street1_hebrew"]
        }
        return items

    def is_included(self) -> Union[dict, list, bool]:
        return self.items["with_crosswalk"][0]["count"] + self.items["without_crosswalk"][0]["count"] > 10
