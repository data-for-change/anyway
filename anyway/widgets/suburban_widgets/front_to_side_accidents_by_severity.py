from datetime import datetime
from typing import Dict, Optional, Any, List

import pandas as pd
from flask_babel import _
from sqlalchemy import case, func, distinct

from anyway.backend_constants import AccidentType, AccidentSeverity
from anyway.models import AccidentMarkerView
from anyway.request_params import RequestParams
from anyway.widgets.suburban_widgets.sub_urban_widget import SubUrbanWidget
from anyway.widgets.widget import register
from anyway.widgets.widget_utils import get_query

ROAD_SEGMENT_ACCIDENTS = "specific_road_segment_accidents"

# For query
PARAM_NAME = "provider_and_id"
OTHER_ACCIDENTS_LABEL = "other_accidents"
FRONT_SIDE_ACCIDENTS_LABEL = "front_side_accidents"

# For JSON output
SEVERITY = "severity"
DESC = "desc"
COUNT = "count"

# For translation
OTHERS_DESC = _("others")
FRONT_SIDE_DESC = _("front side")
SEVERITY_TEXT = "{} accidents"


@register
class FrondToSideAccidentsBySeverityWidget(SubUrbanWidget):
    name: str = "front_to_side_accidents_by_severity"
    files = [__file__]

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params)
        self.rank = 32
        self.road_segment_id: str = request_params.location_info["road_segment_id"]

    def generate_items(self) -> None:
        road_result = self._get_raw_front_to_side_accidents(
            road_segment_id=self.road_segment_id,
            start_date=self.request_params.start_time,
            end_date=self.request_params.end_time,
        )

        self.items = {ROAD_SEGMENT_ACCIDENTS: self._clac_percentage(result=road_result)}

    def _clac_percentage(self, result: List[Dict[str, Any]]) -> List[Dict]:
        ret = []
        for row in result:
            total = row[OTHER_ACCIDENTS_LABEL] + row[FRONT_SIDE_ACCIDENTS_LABEL]
            severity_name_text = AccidentSeverity(row["accident_severity"]).get_label()
            severity_text = SEVERITY_TEXT.format(severity_name_text)
            ret.extend(
                [
                    {
                        SEVERITY: severity_text,
                        DESC: FRONT_SIDE_DESC,
                        COUNT: round((row[FRONT_SIDE_ACCIDENTS_LABEL] / total) * 100),
                    },
                    {
                        SEVERITY: severity_text,
                        DESC: OTHERS_DESC,
                        COUNT: round((row[OTHER_ACCIDENTS_LABEL] / total) * 100),
                    },
                ]
            )

        return ret

    def _get_raw_front_to_side_accidents(
        self,
        road_segment_id: Optional[str],
        start_date: Optional[datetime.date],
        end_date: Optional[datetime.date],
    ) -> List[Dict[str, Any]]:

        other_accidents = case(
            [
                (
                    (
                        AccidentMarkerView.accident_type
                        != AccidentType.COLLISION_OF_FRONT_TO_SIDE.value
                    ),
                    AccidentMarkerView.provider_and_id,
                )
            ]
        )
        front_side_accidents = case(
            [
                (
                    (
                        AccidentMarkerView.accident_type
                        == AccidentType.COLLISION_OF_FRONT_TO_SIDE.value
                    ),
                    AccidentMarkerView.provider_and_id,
                )
            ]
        )
        query = get_query(
            table_obj=AccidentMarkerView,
            filters={},
            start_time=start_date,
            end_time=end_date
        )
        entities_query = query.with_entities(
            AccidentMarkerView.accident_severity,
            AccidentMarkerView.accident_severity_hebrew,
            func.count(distinct(other_accidents)).label(OTHER_ACCIDENTS_LABEL),
            func.count(distinct(front_side_accidents)).label(FRONT_SIDE_ACCIDENTS_LABEL),
        )

        if road_segment_id:
            entities_query = entities_query.filter(
                AccidentMarkerView.road_segment_id == road_segment_id
            )

        query_filtered = entities_query.filter(
            AccidentMarkerView.accident_severity.in_(
                [AccidentSeverity.FATAL.value, AccidentSeverity.SEVERE.value]
            )
        )
        query = query_filtered.group_by(
            AccidentMarkerView.accident_severity, AccidentMarkerView.accident_severity_hebrew
        )
        results = pd.read_sql_query(query.statement, query.session.bind).to_dict(orient="records")
        return results

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {"title": _("Front-side vs other accidents")}

        items["meta"]["information"] = _(
            "Fatal & severe accidents of type front-to-side in this road segment"
        )

        for item in items["data"]["items"][ROAD_SEGMENT_ACCIDENTS]:
            item[SEVERITY] = _(item[SEVERITY])
            item[DESC] = _(item[DESC])

        return items


_("fatal accidents")
_("severe accidents")
