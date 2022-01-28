import datetime
from typing import List

import pandas as pd
from sqlalchemy import case, literal_column, func, distinct, desc

from anyway.widgets.widget import register
from anyway.request_params import RequestParams
from anyway.backend_constants import BE_CONST, AccidentSeverity
from anyway.widgets.widget_utils import get_query
from anyway.models import InvolvedMarkerView
from anyway.vehicle_type import VehicleCategory
from anyway.widgets.suburban_widgets.sub_urban_widget import SubUrbanWidget
from typing import Dict
from flask_babel import _


location_other = "location other"
location_road = "location road"
location_all_label = "all roads"
_("all roads")


@register
class MotorcycleAccidentsVsAllAccidentsWidget(SubUrbanWidget):
    name: str = "motorcycle_accidents_vs_all_accidents"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 20
        self.road_number: str = request_params.location_info["road1"]

    def generate_items(self) -> None:
        # noinspection PyUnresolvedReferences
        self.items = MotorcycleAccidentsVsAllAccidentsWidget.motorcycle_accidents_vs_all_accidents(
            self.request_params.start_time, self.request_params.end_time, self.road_number
        )

    @staticmethod
    def motorcycle_accidents_vs_all_accidents(
        start_time: datetime.date, end_time: datetime.date, road_number: str
    ) -> List:
        location_label = "location"
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
        vehicle_other = VehicleCategory.OTHER.get_english_display_name()
        vehicle_motorcycle = VehicleCategory.MOTORCYCLE.get_english_display_name()
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

        return [
            {
                "label_key": location_road,
                "series": [
                    {"label_key": vehicle_motorcycle, "value": counter_road_motorcycle / sum_road},
                    {"label_key": vehicle_other, "value": counter_road_other / sum_road},
                ],
            },
            {
                "label_key": location_all_label,
                "series": [
                    {
                        "label_key": vehicle_motorcycle,
                        "value": (counter_other_motorcycle + counter_road_motorcycle) / sum_all,
                    },
                    {
                        "label_key": vehicle_other,
                        "value": (counter_other_other + counter_road_other) / sum_all,
                    },
                ],
            },
        ]

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        road_num = request_params.location_info["road1"]
        moto = VehicleCategory.MOTORCYCLE.get_english_display_name()
        other = VehicleCategory.OTHER.get_english_display_name()
        road_label = f"road {road_num}"
        road_label_display_name = f"{_('road')} {road_num}"
        for item in items["data"]["items"]:
            if item["label_key"] == location_road:
                item["label_key"] = road_label_display_name
            else:
                item["label_key"] = _(item["label_key"])
            for e in item["series"]:
                e["label_key"] = _(e["label_key"])
        items["data"]["text"] = {
            "title": _("Fatal and severe motorcycle accidents on road")
            + f" {road_num} "
            + _("compared to rest of country"),
            "labels_map": {
                moto: _(moto),
                other: _(other),
                location_all_label: _(location_all_label),
                road_label: road_label_display_name,
            },
        }
        return items


_("road")
