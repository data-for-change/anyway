import logging
from typing import Dict

from sqlalchemy import func, distinct

from anyway.backend_constants import InjurySeverity
from anyway.models import Involved
from anyway.request_params import RequestParams
from anyway.vehicle_type import VehicleType
from anyway.widgets.all_locations_widgets.all_locations_widget import AllLocationsWidget
from anyway.widgets.widget import register
from anyway.widgets.widget_utils import get_involved_counts

# noinspection PyProtectedMember

SERIOUSLY_INJURED_KILLED_IN_BICYCLES_SCOOTER_INFORMATION = \
    "מספר הנפגעים שנפצעו קשה או נהרגו בתאונות אופנים, אופנים חשמליים וקורקינט"

TITLE = "רוכבי אופניים וקורקינט שנפגעו קשה או נהרגו"

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
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {"title": TITLE}
        return items
