import logging
from typing import Dict

from sqlalchemy import func, distinct

from anyway.backend_constants import InjurySeverity, BackEndConstants as Constants
from anyway.models import Involved
from anyway.request_params import RequestParams
from anyway.utilities import half_rounded_up
from anyway.vehicle_type import VehicleType
from anyway.widgets.all_locations_widgets.all_locations_widget import AllLocationsWidget
from anyway.widgets.widget import register
from anyway.widgets.widget_utils import get_involved_counts
from flask_babel import _

# noinspection PyProtectedMember

SERIOUSLY_INJURED_KILLED_IN_BICYCLES_SCOOTER_INFORMATION = \
    "מספר הנפגעים שנפצעו קשה או נהרגו בתאונות אופנים, אופנים חשמליים וקורקינט"

TITLE = _("Severe or fatal accidents on bikes, e-bikes, or scooters")


@register
class SeriouslyInjuredKilledInBicyclesScooterWidget(AllLocationsWidget):
    name: str = "seriously_injured_killed_in_bicycles_scooter"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 32
        self.information = SERIOUSLY_INJURED_KILLED_IN_BICYCLES_SCOOTER_INFORMATION
        logging.debug(request_params.location_info)

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
        selected_columns = (
            Involved.accident_year.label("label_key"),
            func.count(distinct(Involved.id)).label("value")
        )

        severities = (InjurySeverity.KILLED, InjurySeverity.SEVERE_INJURED)
        vehicle_types = (VehicleType.BIKE, VehicleType.ELECTRIC_BIKE, VehicleType.ELECTRIC_SCOOTER)
        return get_involved_counts(selected_columns, start_year, end_year, severities, vehicle_types, location_info)

    @staticmethod
    def create_location_description(location_info, location_text) -> str:
        return location_info[Constants.YISHUV_NAME] \
            if Constants.YISHUV_NAME in location_info \
            else location_text

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        subtitle = SeriouslyInjuredKilledInBicyclesScooterWidget.create_location_description(
            request_params.location_info,
            request_params.location_text)
        items["data"]["text"] = {"title": TITLE,
                                 "subtitle": subtitle}
        #logging.debug(request_params.location_info, request_params.location_text)
        return items

    def is_included(self) -> bool:
        logging.debug(self.items)
        num_of_years_in_query = len(self.items)
        years_with_accidents = [item["label_key"] for item in self.items if item["value"] > 0]
        num_of_years_with_accidents = len(years_with_accidents)
        return num_of_years_with_accidents >= half_rounded_up(num_of_years_in_query)