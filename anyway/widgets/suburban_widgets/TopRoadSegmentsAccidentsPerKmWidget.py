import pandas as pd
from sqlalchemy import cast, func, Numeric, desc

from anyway.RequestParams import RequestParams
from anyway.infographics_utils import get_query
from anyway.models import AccidentMarkerView


class TopRoadSegmentsAccidentsPerKmWidget(SubUrbanWidget):
    name: str = "top_road_segments_accidents_per_km"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 13
        self.text = {
            "title": "תאונות לכל ק״מ כביש על פי מקטע בכביש "
                     + str(int(self.request_params.location_info["road1"]))
        }

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
        if resolution != "כביש בינעירוני":  # relevent for non urban roads only
            return {}
        filters = {}
        filters["road1"] = location_info["road1"]
        query = get_query(
            table_obj=AccidentMarkerView, filters=filters, start_time=start_time, end_time=end_time
        )

        query = (
            query.with_entities(
                AccidentMarkerView.road_segment_name,
                AccidentMarkerView.road_segment_length_km.label("segment_length"),
                cast(
                    (func.count(AccidentMarkerView.id) / AccidentMarkerView.road_segment_length_km),
                    Numeric(10, 4),
                ).label("accidents_per_km"),
                func.count(AccidentMarkerView.id).label("total_accidents"),
            )
                .filter(AccidentMarkerView.road_segment_name.isnot(None))
                .group_by(
                AccidentMarkerView.road_segment_name, AccidentMarkerView.road_segment_length_km
            )
                .order_by(desc("accidents_per_km"))
                .limit(limit)
        )

        result = pd.read_sql_query(query.statement, query.session.bind)
        return result.to_dict(orient="records")  # pylint: disable=no-member