import logging
from collections import defaultdict
from functools import lru_cache
from typing import Dict
from flask_babel import _
from anyway.backend_constants import BE_CONST
from anyway.infographics_dictionaries import segment_dictionary
from anyway.models import InvolvedMarkerView
from anyway.vehicle_type import VehicleCategory
from anyway.widgets.Widget import register
from anyway.widgets.suburban_widgets.SubUrbanWidget import SubUrbanWidget
from anyway.RequestParams import RequestParams
from anyway.widgets.widget_utils import get_accidents_stats, get_injured_filters


@register
class AccidentCountByCarTypeWidget(SubUrbanWidget):
    name: str = "accident_count_by_car_type"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 17

    def generate_items(self) -> None:
        self.items = AccidentCountByCarTypeWidget.get_stats_accidents_by_car_type_with_national_data(
            self.request_params
        )

    @staticmethod
    def get_stats_accidents_by_car_type_with_national_data(
        request_params: RequestParams, involved_by_vehicle_type_data=None
    ):
        out = []
        if involved_by_vehicle_type_data is None:
            involved_by_vehicle_type_data = get_accidents_stats(
                table_obj=InvolvedMarkerView,
                filters=get_injured_filters(request_params.location_info),
                group_by="involve_vehicle_type",
                count="involve_vehicle_type",
                start_time=request_params.start_time,
                end_time=request_params.end_time,
            )

        start_time = request_params.start_time
        end_time = request_params.end_time
        data_by_segment = AccidentCountByCarTypeWidget.percentage_accidents_by_car_type(
            involved_by_vehicle_type_data
        )
        national_data = AccidentCountByCarTypeWidget.percentage_accidents_by_car_type_national_data_cache(
            start_time, end_time
        )

        for k, v in national_data.items():  # pylint: disable=W0612
            out.append(
                {
                    "car_type": k,
                    "percentage_segment": data_by_segment[k],
                    "percentage_country": national_data[k],
                }
            )
        return out

    @staticmethod
    def percentage_accidents_by_car_type(involved_by_vehicle_type_data):
        driver_types = defaultdict(float)
        total_count = 0
        for item in involved_by_vehicle_type_data:
            vehicle_type, count = item["involve_vehicle_type"], int(item["count"])
            total_count += count
            if vehicle_type in VehicleCategory.CAR.get_codes():
                driver_types[VehicleCategory.CAR.value] += count
            elif vehicle_type in VehicleCategory.LARGE.get_codes():
                driver_types[VehicleCategory.LARGE.value] += count
            elif vehicle_type in VehicleCategory.MOTORCYCLE.get_codes():
                driver_types[VehicleCategory.MOTORCYCLE.value] += count
            elif vehicle_type in VehicleCategory.BICYCLE_AND_SMALL_MOTOR.get_codes():
                driver_types[VehicleCategory.BICYCLE_AND_SMALL_MOTOR.value] += count
            else:
                driver_types[VehicleCategory.OTHER.value] += count

        output = defaultdict(float)
        for k, v in driver_types.items():  # Calculate percentage
            output[k] = 100 * v / total_count

        return output

    @staticmethod
    @lru_cache(maxsize=64)
    def percentage_accidents_by_car_type_national_data_cache(start_time, end_time):
        involved_by_vehicle_type_data = get_accidents_stats(
            table_obj=InvolvedMarkerView,
            filters={
                "road_type": [
                    BE_CONST.ROAD_TYPE_NOT_IN_CITY_NOT_IN_INTERSECTION,
                    BE_CONST.ROAD_TYPE_NOT_IN_CITY_IN_INTERSECTION,
                ]
            },
            group_by="involve_vehicle_type",
            count="involve_vehicle_type",
            start_time=start_time,
            end_time=end_time,
        )
        return AccidentCountByCarTypeWidget.percentage_accidents_by_car_type(
            involved_by_vehicle_type_data
        )

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        for item in items["data"]["items"]:
            try:
                item["car_type"] = _(VehicleCategory(item["car_type"]).get_english_display_name())
            except ValueError:
                logging.exception(f"AccidentCountByCarType.localize_items: item:{item}")
        base_title = _(
            "comparing vehicle type percentage in accidents in {} relative to national average"
        )
        items["data"]["text"] = {
            "title": base_title.format(
                segment_dictionary[request_params.location_info["road_segment_name"]]
            )
        }
        return items
