from typing import Dict

import pandas as pd
import logging
from sqlalchemy import cast, func, Numeric, desc

# noinspection PyProtectedMember
from flask_babel import _
from anyway.request_params import RequestParams
from anyway.backend_constants import AccidentSeverity
from anyway.widgets.widget import register
from anyway.widgets.widget_utils import get_query
from anyway.models import AccidentMarkerView
from anyway.widgets.suburban_widgets.sub_urban_widget import SubUrbanWidget


@register
class TopRoadSegmentsAccidentsPerKmWidget(SubUrbanWidget):
    name: str = "top_road_segments_accidents_per_km"
    files = [__file__]

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params)
        self.rank = 13

    def generate_items(self) -> None:
        self.items = TopRoadSegmentsAccidentsPerKmWidget.get_top_road_segments_accidents_per_km(
            resolution=self.request_params.resolution,
            location_info=self.request_params.location_info,
            start_time=self.request_params.start_time,
            end_time=self.request_params.end_time,
        )

    @staticmethod
    def get_top_road_segments_accidents_per_km(
        resolution, location_info, start_time=None, end_time=None, limit=3
    ):
        query = get_query(
            table_obj=AccidentMarkerView,
            filters={"road1": location_info["road1"]},
            start_time=start_time,
            end_time=end_time,
        )

        try:
            query = (
                query.with_entities(
                    AccidentMarkerView.road_segment_name,
                    AccidentMarkerView.road_segment_length_km.label("segment_length"),
                    cast(
                        (
                            func.count(AccidentMarkerView.id)
                            / AccidentMarkerView.road_segment_length_km
                        ),
                        Numeric(10, 4),
                    ).label("accidents_per_km"),
                    func.count(AccidentMarkerView.id).label("total_accidents"),
                )
                .filter(AccidentMarkerView.road_segment_name.isnot(None))
                .filter(
                    AccidentMarkerView.accident_severity.in_(
                        [AccidentSeverity.FATAL.value, AccidentSeverity.SEVERE.value]
                    )
                )
                .group_by(
                    AccidentMarkerView.road_segment_name, AccidentMarkerView.road_segment_length_km
                )
                .order_by(desc("accidents_per_km"))
                .limit(limit)
            )

            result = pd.read_sql_query(query.statement, query.session.bind)
            return result.to_dict(orient="records")  # pylint: disable=no-member

        except Exception as exception:
            logging.exception(f"{TopRoadSegmentsAccidentsPerKmWidget.name}: {exception}")
            raise exception

    def is_included(self) -> bool:
        for item in self.items:
            if item["road_segment_name"] == self.request_params.location_info["road_segment_name"]:
                return True
        return False

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": _("Segments with most accidents per Km")
            + f" - {request_params.location_info['road1']}"
        }
        return items


_("Severe and fatal accidents per Km by section in road")
