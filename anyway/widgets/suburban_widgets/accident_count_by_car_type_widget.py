import logging
from collections import defaultdict
from functools import lru_cache
from math import floor
from typing import Dict

from flask_babel import _

import anyway.widgets.widget_utils as widget_utils
from anyway.backend_constants import BE_CONST
from anyway.infographics_dictionaries import segment_dictionary
from anyway.models import VehicleMarkerView
from anyway.request_params import RequestParams
from anyway.vehicle_type import VehicleCategory
from anyway.widgets.suburban_widgets.sub_urban_widget import SubUrbanWidget
from anyway.widgets.widget import register

MAX_NUMBER_OF_ITEMS = 2


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
        request_params: RequestParams, vehicle_grouped_by_type_count_unique=None
    ):
        out = []
        if vehicle_grouped_by_type_count_unique is None:
            vehicle_grouped_by_type_count_unique = widget_utils.get_accidents_stats(
                table_obj=VehicleMarkerView,
                filters=request_params.location_info,
                group_by="vehicle_type",
                count="provider_and_id",
                start_time=request_params.start_time,
                end_time=request_params.end_time,
            )

        start_time = request_params.start_time
        end_time = request_params.end_time
        data_by_segment = AccidentCountByCarTypeWidget.percentage_accidents_by_car_type(
            vehicle_grouped_by_type_count_unique
        )
        national_data = AccidentCountByCarTypeWidget.percentage_accidents_by_car_type_national_data_cache(
            start_time, end_time
        )

        for car_type in data_by_segment:
            out.append(
                {
                    "label_key": car_type,
                    "series": [
                        {"label_key": "percentage_segment", "value": data_by_segment[car_type]},
                        {"label_key": "percentage_country", "value": national_data[car_type]},
                    ],
                }
            )
        return out

    @staticmethod
    def percentage_accidents_by_car_type(vehicle_grouped_by_type_count_unique) -> Dict[str, int]:
        vehicle_type_dict = defaultdict(int)
        total_count = 0
        for item in vehicle_grouped_by_type_count_unique:
            vehicle_type, count = item["vehicle_type"], int(item["count"])
            total_count += count
            if vehicle_type in VehicleCategory.CAR.get_codes():
                vehicle_type_dict[VehicleCategory.CAR.value] += count
            elif vehicle_type in VehicleCategory.LARGE.get_codes():
                vehicle_type_dict[VehicleCategory.LARGE.value] += count
            elif vehicle_type in VehicleCategory.MOTORCYCLE.get_codes():
                vehicle_type_dict[VehicleCategory.MOTORCYCLE.value] += count
            elif vehicle_type in VehicleCategory.BICYCLE_AND_SMALL_MOTOR.get_codes():
                vehicle_type_dict[VehicleCategory.BICYCLE_AND_SMALL_MOTOR.value] += count
            else:
                vehicle_type_dict[VehicleCategory.OTHER.value] += count

        # Order the vehicle_type_dict dict by value which is the count of the vehicle_type
        vehicle_type_dict = dict(
            sorted(vehicle_type_dict.items(), key=lambda item: item[1], reverse=True)
        )

        output = {}
        sum_all = 0
        # Calculate percentage of MAX_NUMBER_OF_ITEMS
        for i, (key, value) in enumerate(vehicle_type_dict.items()):
            output[key] = floor(100 * value / total_count)
            sum_all += output[key]
            if i >= MAX_NUMBER_OF_ITEMS:
                break

        # Round up to 100
        if len(vehicle_type_dict) <= 3 and sum_all < 100:
            # Add 1 to the first element
            for key, value in output.items():
                output[key] += 1
                break

        # Use defaultdict to return 0 where there is no key, so when there is no data for this type of vehicle the
        # result will be zero
        return defaultdict(int, output)

    @staticmethod
    @lru_cache(maxsize=64)
    def percentage_accidents_by_car_type_national_data_cache(start_time, end_time) -> Dict[str, int]:
        vehicle_grouped_by_type_count_unique = widget_utils.get_accidents_stats(
            table_obj=VehicleMarkerView,
            filters={
                "road_type": [
                    BE_CONST.ROAD_TYPE_NOT_IN_CITY_NOT_IN_INTERSECTION,
                    BE_CONST.ROAD_TYPE_NOT_IN_CITY_IN_INTERSECTION,
                ]
            },
            group_by="vehicle_type",
            count="provider_and_id",
            start_time=start_time,
            end_time=end_time,
        )
        return AccidentCountByCarTypeWidget.percentage_accidents_by_car_type(
            vehicle_grouped_by_type_count_unique
        )

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        for item in items["data"]["items"]:
            try:
                item["label_key"] = _(VehicleCategory(item["label_key"]).get_english_display_name())
            except ValueError:
                logging.exception(f"AccidentCountByCarType.localize_items: item:{item}")
        base_title = _(
            "Comparing vehicle type in accidents in {} relative to national average"
        )
        items["data"]["text"] = {
            "title": base_title.format(
                segment_dictionary[request_params.location_info["road_segment_name"]]
            )
        }
        items["meta"]["information"] = _("Vehicle accidents by type in specific segment, sorted by segment, compared to the national average")
        return items
