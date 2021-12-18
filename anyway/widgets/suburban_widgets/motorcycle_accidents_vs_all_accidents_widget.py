import datetime
from typing import List

import pandas as pd
from sqlalchemy import case, literal_column, func, distinct, desc

from anyway.request_params import RequestParams
from anyway.backend_constants import BE_CONST, AccidentSeverity
from anyway.widgets.widget_utils import get_query
from anyway.models import InvolvedMarkerView
from anyway.vehicle_type import VehicleCategory
from anyway.widgets.suburban_widgets.sub_urban_widget import SubUrbanWidget
from typing import Dict
from flask_babel import _

# TODO: register?
class MotorcycleAccidentsVsAllAccidentsWidget(SubUrbanWidget):
    name: str = "motorcycle_accidents_vs_all_accidents"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 20
        self.road_number: str = request_params.location_info["road1"]

    def generate_items(self) -> None:
        self.items = MotorcycleAccidentsVsAllAccidentsWidget.motorcycle_accidents_vs_all_accidents(
            self.request_params.start_time, self.request_params.end_time, self.road_number
        )

    @staticmethod
    def motorcycle_accidents_vs_all_accidents(
        start_time: datetime.date, end_time: datetime.date, road_number: str
    ) -> List:
        location_label = "location"
        location_other = "שאר הארץ"
        location_road = f"כביש {int(road_number)}"
        case_location = case(
            [
                (
                    (InvolvedMarkerView.road1 == road_number)
                    | (InvolvedMarkerView.road2 == road_number),
                    location_road,
                )
            ],
            else_=literal_column(f"'{location_other}'"),
        ).label(location_label)

        vehicle_label = "vehicle"
        vehicle_other = "אחר"
        vehicle_motorcycle = "אופנוע"
        case_vehicle = case(
            [
                (
                    InvolvedMarkerView.involve_vehicle_type.in_(
                        VehicleCategory.MOTORCYCLE.get_codes()
                    ),
                    literal_column(f"'{vehicle_motorcycle}'"),
                )
            ],
            else_=literal_column(f"'{vehicle_other}'"),
        ).label(vehicle_label)

        query = get_query(
            table_obj=InvolvedMarkerView, filters={}, start_time=start_time, end_time=end_time
        )

        num_accidents_label = "num_of_accidents"
        query = (
            query.with_entities(
                case_location,
                case_vehicle,
                func.count(distinct(InvolvedMarkerView.provider_and_id)).label(num_accidents_label),
            )
            .filter(InvolvedMarkerView.road_type.in_(BE_CONST.NON_CITY_ROAD_TYPES))
            .filter(
                InvolvedMarkerView.accident_severity.in_(
                    # pylint: disable=no-member
                    [AccidentSeverity.FATAL.value, AccidentSeverity.SEVERE.value]
                )
            )
            .group_by(location_label, vehicle_label)
            .order_by(desc(num_accidents_label))
        )
        # pylint: disable=no-member
        results = pd.read_sql_query(query.statement, query.session.bind).to_dict(
            orient="records"
        )  # pylint: disable=no-member

        counter_road_motorcycle = 0
        counter_other_motorcycle = 0
        counter_road_other = 0
        counter_other_other = 0
        for record in results:
            if record[location_label] == location_other:
                if record[vehicle_label] == vehicle_other:
                    counter_other_other = record[num_accidents_label]
                else:
                    counter_other_motorcycle = record[num_accidents_label]
            else:
                if record[vehicle_label] == vehicle_other:
                    counter_road_other = record[num_accidents_label]
                else:
                    counter_road_motorcycle = record[num_accidents_label]
        sum_road = counter_road_other + counter_road_motorcycle
        if sum_road == 0:
            sum_road = 1  # prevent division by zero
        sum_all = counter_other_other + counter_other_motorcycle + sum_road
        percentage_label = "percentage"
        location_all_label = "כל הארץ"

        return [
            {
                location_label: location_road,
                vehicle_label: vehicle_motorcycle,
                percentage_label: counter_road_motorcycle / sum_road,
            },
            {
                location_label: location_road,
                vehicle_label: vehicle_other,
                percentage_label: counter_road_other / sum_road,
            },
            {
                location_label: location_all_label,
                vehicle_label: vehicle_motorcycle,
                percentage_label: (counter_other_motorcycle + counter_road_motorcycle) / sum_all,
            },
            {
                location_label: location_all_label,
                vehicle_label: vehicle_other,
                percentage_label: (counter_other_other + counter_road_other) / sum_all,
            },
        ]

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": _('Number of fatal and severe motorcycle accidents') +f" - {request_params.location_info['road1']} " +_('compared to rest of country')
        }
        return items
