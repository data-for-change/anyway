import datetime
import logging
from typing import List, Dict

from flask_babel import _
from sqlalchemy import func, distinct, desc

from anyway.request_params import RequestParams
from anyway.app_and_db import db
from anyway.widgets.widget_utils import get_query, run_query
from anyway.models import VehicleMarkerView, AccidentType
from anyway.vehicle_type import VehicleCategory
from anyway.widgets.suburban_widgets.sub_urban_widget import SubUrbanWidget


# TODO: register?
class AccidentTypeVehicleTypeRoadComparisonWidget(SubUrbanWidget):
    name: str = "vehicle_accident_vs_all_accidents"  # WIP: change by vehicle type
    files = [__file__]
    widget_digest = SubUrbanWidget.calc_widget_digest(files)
    MAX_ACCIDENT_TYPES_TO_RETURN: int = 5

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.road_number: str = request_params.location_info["road1"]
        # WIP: change rank, text by vehicle type
        self.rank = 25

    def generate_items(self) -> None:
        self.items = AccidentTypeVehicleTypeRoadComparisonWidget.accident_type_road_vs_all_count(
            self.request_params.start_time, self.request_params.end_time, self.road_number
        )

    @staticmethod
    def accident_type_road_vs_all_count(
        start_time: datetime.date, end_time: datetime.date, road_number: str
    ) -> List:
        num_accidents_label = "num_of_accidents"
        location_all = "כל הארץ"
        location_road = f"כביש {int(road_number)}"

        vehicle_types = VehicleCategory.MOTORCYCLE.get_codes()  # WIP: change by vehicle type

        all_roads_query = AccidentTypeVehicleTypeRoadComparisonWidget.get_accident_count_by_vehicle_type_query(
            start_time, end_time, num_accidents_label, vehicle_types
        )
        all_roads_query_result = run_query(all_roads_query)
        all_roads_sum_accidents = 0
        all_roads_map = {}
        for record in all_roads_query_result:
            all_roads_sum_accidents += record[num_accidents_label]
            all_roads_map[record[VehicleMarkerView.accident_type.name]] = record[
                num_accidents_label
            ]

        road_query = all_roads_query.filter(
            (VehicleMarkerView.road1 == road_number) | (VehicleMarkerView.road2 == road_number)
        )
        road_query_result = run_query(road_query)
        road_sum_accidents = 0
        types_to_report = []
        for record in road_query_result:
            road_sum_accidents += record[num_accidents_label]

        for record in road_query_result:
            if (
                len(types_to_report)
                == AccidentTypeVehicleTypeRoadComparisonWidget.MAX_ACCIDENT_TYPES_TO_RETURN
            ):
                break
            accident_type = record[VehicleMarkerView.accident_type.name]
            types_to_report.append(
                {
                    VehicleMarkerView.accident_type.name: accident_type,
                    location_road: record[num_accidents_label] / road_sum_accidents,
                    location_all: all_roads_map[accident_type] / all_roads_sum_accidents,
                }
            )
        return types_to_report

    @staticmethod
    def get_accident_count_by_vehicle_type_query(
        start_time: datetime.date,
        end_time: datetime.date,
        num_accidents_label: str,
        vehicle_types: List[int],
    ) -> db.session.query:
        return (
            get_query(
                table_obj=VehicleMarkerView,
                start_time=start_time,
                end_time=end_time,
                filters={VehicleMarkerView.vehicle_type.name: vehicle_types},
            )
            .with_entities(
                VehicleMarkerView.accident_type,
                func.count(distinct(VehicleMarkerView.provider_and_id)).label(num_accidents_label),
            )
            .group_by(VehicleMarkerView.accident_type)
            .order_by(desc(num_accidents_label))
        )

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        for item in items["data"]["items"]:
            try:
                item[VehicleMarkerView.accident_type.name] = _(
                    AccidentType(item["accident_type"]).get_label()
                )
            except KeyError:
                logging.exception(
                    f"AccidentTypeVehicleTypeRoadComparisonWidget.localize_items: Exception while translating {item}."
                )
        items["data"]["text"] = {
            # TODO: after registering decide on title
            "title": "Number of accidents by vehicle type by severity"
        }
        return items
