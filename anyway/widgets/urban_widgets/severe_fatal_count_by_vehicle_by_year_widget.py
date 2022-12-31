from typing import Dict, Any

from anyway.request_params import RequestParams
from anyway.backend_constants import InjurySeverity
from anyway.models import InvolvedMarkerView
from anyway.vehicle_type import VehicleType
from anyway.widgets.urban_widgets.urban_widget import UrbanWidget
from anyway.widgets.widget_utils import get_accidents_stats
from flask_babel import _


# TODO: pretty sure there are errors in this widget, for example, is_included returns self.items
class SevereFatalCountByVehicleByYearWidget(UrbanWidget):
    name: str = "accidents_on_small_motor_by_vehicle_by_year"
    files = [__file__]
    # TODO: when accident vehicle becomes available in request params,
    # make it so widget is only included on newsflashes that have a relevant vehicle

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params)
        self.rank = 28

    def generate_items(self) -> None:
        self.items = SevereFatalCountByVehicleByYearWidget.separate_data(
            self.request_params.location_info["yishuv_name"],
            self.request_params.start_time,
            self.request_params.end_time,
        )

    @staticmethod
    def separate_data(yishuv, start_time, end_time) -> Dict[str, Any]:
        output = {
            "e_bikes": get_accidents_stats(
                table_obj=InvolvedMarkerView,
                filters={
                    "injury_severity": [
                        InjurySeverity.KILLED.value,
                        InjurySeverity.SEVERE_INJURED.value,
                    ],
                    "involve_vehicle_type": VehicleType.ELECTRIC_BIKE.value,
                    "involve_yishuv_name": yishuv,
                },
                group_by="accident_year",
                count="accident_year",
                start_time=start_time,
                end_time=end_time,
            ),
            "bikes": get_accidents_stats(
                table_obj=InvolvedMarkerView,
                filters={
                    "injury_severity": [
                        InjurySeverity.KILLED.value,
                        InjurySeverity.SEVERE_INJURED.value,
                    ],
                    "involve_vehicle_type": VehicleType.BIKE.value,
                    "involve_yishuv_name": yishuv,
                },
                group_by="accident_year",
                count="accident_year",
                start_time=start_time,
                end_time=end_time,
            ),
            "e_scooters": get_accidents_stats(
                table_obj=InvolvedMarkerView,
                filters={
                    "injury_severity": [
                        InjurySeverity.KILLED.value,
                        InjurySeverity.SEVERE_INJURED.value,
                    ],
                    "involve_vehicle_type": VehicleType.ELECTRIC_SCOOTER.value,
                    "involve_yishuv_name": yishuv,
                },
                group_by="accident_year",
                count="accident_year",
                start_time=start_time,
                end_time=end_time,
            ),
        }
        bike_accidents = [d["accident_year"] for d in output["bikes"] if "accident_year" in d]
        ebike_accidents = [d["accident_year"] for d in output["e_bikes"] if "accident_year" in d]
        scooter_accidents = [
            d["accident_year"] for d in output["e_scooters"] if "accident_year" in d
        ]
        start_year = start_time.year
        end_year = end_time.year
        for year in list(range(start_year, end_year + 1)):
            if year not in bike_accidents:
                output["bikes"].append({"accident_year": year, "count": 0})
            if year not in ebike_accidents:
                output["e_bikes"].append({"accident_year": year, "count": 0})
            if year not in scooter_accidents:
                output["e_scooters"].append({"accident_year": year, "count": 0})
        return output

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": _("Severe or fatal accidents on bikes, e-bikes, or scooters"),
            "subtitle": request_params.location_info["yishuv_name"]
        }
        return items

    def is_included(self) -> bool:
        count = (
            self.items["bikes"][-1]["count"]
            + self.items["e_bikes"][-1]["count"]
            + self.items["e_scooters"][-1]["count"]
        )
        return count > 1
