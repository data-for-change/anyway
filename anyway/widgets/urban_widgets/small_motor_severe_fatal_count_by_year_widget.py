from typing import Dict

from anyway.request_params import RequestParams
from anyway.backend_constants import InjurySeverity
from anyway.models import InvolvedMarkerView
from anyway.vehicle_type import VehicleCategory
from anyway.widgets.urban_widgets.urban_widget import UrbanWidget
from anyway.widgets.widget_utils import get_accidents_stats
from flask_babel import _


class SmallMotorSevereFatalCountByYearWidget(UrbanWidget):
    name: str = "severe_fatal_count_on_small_motor_by_accident_year"
    files = [__file__]
    # TODO: when accident vehicle becomes available in request params,
    # make it so widget shows only the vehicle in the newsflash (eg only e_bikes)

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params)
        self.rank = 15

    def generate_items(self) -> None:
        self.items = SmallMotorSevereFatalCountByYearWidget.get_motor_stats(
            self.request_params.location_info["yishuv_name"],
            self.request_params.start_time,
            self.request_params.end_time,
        )

    @staticmethod
    def get_motor_stats(location_info, start_time, end_time):
        count_by_year = get_accidents_stats(
            table_obj=InvolvedMarkerView,
            filters={
                "injury_severity": [
                    InjurySeverity.KILLED.value,
                    InjurySeverity.SEVERE_INJURED.value,
                ],
                "involve_vehicle_type": VehicleCategory.BICYCLE_AND_SMALL_MOTOR.get_codes(),
                "involve_yishuv_name": location_info,
            },
            group_by="accident_year",
            count="accident_year",
            start_time=start_time,
            end_time=end_time,
        )
        found_accidents = [d["accident_year"] for d in count_by_year if "accident_year" in d]
        start_year = start_time.year
        end_year = end_time.year
        for year in list(range(start_year, end_year + 1)):
            if year not in found_accidents:
                count_by_year.append({"accident_year": year, "count": 0})
        return count_by_year

    def is_included(self) -> bool:
        return self.items[-1]["count"] > 0 and self.items[-2]["count"] > 0

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": _("Severe or fatal accidents on bikes, e-bikes, or scooters"),
            "subtitle": request_params.location_info["yishuv_name"]
        }
        return items
