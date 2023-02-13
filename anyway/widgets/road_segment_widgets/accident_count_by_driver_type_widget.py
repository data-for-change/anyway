import logging
from collections import defaultdict
from typing import Dict

from flask_babel import _
import anyway.backend_constants as consts
from anyway.request_params import RequestParams
from anyway.widgets.widget_utils import get_accidents_stats, get_injured_filters
from anyway.models import InvolvedMarkerView
from anyway.vehicle_type import VehicleCategory
from anyway.widgets.widget import register
from anyway.widgets.road_segment_widgets.road_segment_widget import RoadSegmentWidget


@register
class AccidentCountByDriverTypeWidget(RoadSegmentWidget):
    name: str = "accident_count_by_driver_type"
    files = [__file__]

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params)
        self.rank = 16
        self.information = "Driver involvement in accident by driver type: professional - trucks, taxi, bus, work, minibus, tractor, private - private car, motorcycle, light electric - electric scooter, mobility scooter, electric bike."

    def generate_items(self) -> None:
        self.items = AccidentCountByDriverTypeWidget.count_accidents_by_driver_type(
            self.request_params
        )

    @staticmethod
    def count_accidents_by_driver_type(request_params):
        filters = get_injured_filters(request_params.location_info)
        filters["involved_type"] = [
            consts.InvolvedType.DRIVER.value,
            consts.InvolvedType.INJURED_DRIVER.value,
        ]
        involved_by_vehicle_type_data = get_accidents_stats(
            table_obj=InvolvedMarkerView,
            filters=filters,
            group_by="involve_vehicle_type",
            count="provider_and_id",
            cnt_distinct=True,
            start_time=request_params.start_time,
            end_time=request_params.end_time,
        )
        driver_types = defaultdict(int)
        for item in involved_by_vehicle_type_data:
            vehicle_type, count = item["involve_vehicle_type"], int(item["count"])
            if vehicle_type in VehicleCategory.PROFESSIONAL_DRIVER.get_codes():
                driver_types[
                    # pylint: disable=no-member
                    consts.DriverType.PROFESSIONAL_DRIVER.get_label()
                ] += count
            elif vehicle_type in VehicleCategory.PRIVATE_DRIVER.get_codes():
                driver_types[
                    # pylint: disable=no-member
                    consts.DriverType.PRIVATE_VEHICLE_DRIVER.get_label()
                ] += count
            elif (
                vehicle_type in VehicleCategory.LIGHT_ELECTRIC.get_codes()
                or vehicle_type in VehicleCategory.OTHER.get_codes()
            ):
                # pylint: disable=no-member
                driver_types[consts.DriverType.OTHER_DRIVER.get_label()] += count
        output = [
            {"driver_type": driver_type, "count": count}
            for driver_type, count in driver_types.items()
        ]
        return output

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        for item in items["data"]["items"]:
            try:
                item["driver_type"] = _(item["driver_type"])
            except KeyError:
                logging.exception(
                    f"AccidentCountByDriverTypeWidget.localize_items: Exception while translating {item}."
                )
        items["data"]["text"] = {"title": _("Number of accidents by driver type")}
        return items


# adding calls to _() for pybabel extraction
_(
    "Driver involvement in accident by driver type: professional - trucks, taxi, bus, work, minibus, tractor, private - private car, motorcycle, light electric - electric scooter, mobility scooter, electric bike."
)
