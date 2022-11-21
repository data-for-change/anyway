from typing import Dict

from flask_babel import _
from anyway.backend_constants import InjurySeverity, BackEndConstants as Constants
from anyway.request_params import RequestParams
from anyway.utilities import half_rounded_up
from anyway.vehicle_type import VehicleType
from anyway.widgets.all_locations_widgets.all_locations_widget import AllLocationsWidget
from anyway.widgets.widget import register
from anyway.widgets.widget_utils import get_involved_counts

# noinspection PyProtectedMember
TITLE = _("Number of severely injured or killed in bike, e-bike, or scooter accidents")


@register
class SeriouslyInjuredKilledInBicyclesScooterWidget(AllLocationsWidget):
    name: str = "seriously_injured_killed_in_bicycles_scooter"
    files = [__file__]
    severities = (InjurySeverity.KILLED, InjurySeverity.SEVERE_INJURED)
    vehicle_types = (VehicleType.BIKE, VehicleType.ELECTRIC_BIKE, VehicleType.ELECTRIC_SCOOTER)

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params)
        self.rank = 32
        self.information = _("Severely injured or killed in bike, e-bike, or scooter accidents")

    def generate_items(self) -> None:
        # noinspection PyUnresolvedReferences
        self.items = SeriouslyInjuredKilledInBicyclesScooterWidget.get_seriously_injured_killed_in_bicycles_scooter(
            self.request_params.start_time.year,
            self.request_params.end_time.year,
            self.request_params.location_info,
        )

    @staticmethod
    def get_seriously_injured_killed_in_bicycles_scooter(
            start_year,
            end_year,
            location_info
    ):

        res = get_involved_counts(start_year, end_year,
                                  SeriouslyInjuredKilledInBicyclesScooterWidget.severities,
                                  SeriouslyInjuredKilledInBicyclesScooterWidget.vehicle_types,
                                  location_info)
        return res

    @staticmethod
    def create_location_description(location_info, location_text) -> str:
        return _("in ") + location_info[Constants.YISHUV_NAME] \
            if Constants.YISHUV_NAME in location_info \
            else location_text

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        subtitle = SeriouslyInjuredKilledInBicyclesScooterWidget.create_location_description(
            request_params.location_info,
            request_params.location_text)
        items["data"]["text"] = {"title": TITLE,
                                 "subtitle": subtitle}
        return items

    def is_included(self) -> bool:
        num_of_years_in_query = len(self.items)
        years_with_accidents = [item["label_key"] for item in self.items if item["value"] > 0]
        num_of_years_with_accidents = len(years_with_accidents)
        return num_of_years_with_accidents >= half_rounded_up(num_of_years_in_query)