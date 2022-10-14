from typing import Dict

from anyway.request_params import RequestParams
from anyway.backend_constants import InjurySeverity
from anyway.models import InvolvedMarkerView
from anyway.widgets.widget import register
from anyway.widgets.suburban_widgets.sub_urban_widget import SubUrbanWidget
from anyway.widgets.widget_utils import get_accidents_stats
from flask_babel import _


@register
class InjuredCountBySeverityWidget(SubUrbanWidget):
    name: str = "injured_count_by_severity"
    files = [__file__]
    widget_digest = SubUrbanWidget.calc_widget_digest(files)

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params)
        self.rank = 29
        self.information = "Fatal, severe and light injuries count in the specified location."

    def generate_items(self) -> None:
        self.items = InjuredCountBySeverityWidget.get_injured_count_by_severity(
            self.request_params.location_info["road1"],
            self.request_params.location_info["road_segment_name"],
            self.request_params.start_time,
            self.request_params.end_time,
        )

    @staticmethod
    def get_injured_count_by_severity(road, segment, start_time, end_time):
        count_by_severity = get_accidents_stats(
            table_obj=InvolvedMarkerView,
            filters={
                "injury_severity": [
                    InjurySeverity.KILLED.value,
                    InjurySeverity.SEVERE_INJURED.value,
                    InjurySeverity.LIGHT_INJURED.value,
                ],
                "road1": road,
                "road_segment_name": segment,
            },
            group_by="injury_severity",
            count="injury_severity",
            start_time=start_time,
            end_time=end_time,
        )
        found_severities = [d["injury_severity"] for d in count_by_severity]
        items = {}
        total_injured_count = 0
        start_year = start_time.year
        end_year = end_time.year
        for sev in InjurySeverity:
            if sev.value not in found_severities:
                count_by_severity.append({"injury_severity": sev.value, "count": 0})
        for severity_and_count in count_by_severity:
            severity_english = InjurySeverity.labels()[
                InjurySeverity(severity_and_count["injury_severity"])
            ]
            severity_count_text = "{}_count".format(severity_english).replace(" ", "_")
            items[severity_count_text] = severity_and_count["count"]
            total_injured_count += severity_and_count["count"]
        if total_injured_count == 0:
            return {}
        items["start_year"] = start_year
        items["end_year"] = end_year
        items["total_injured_count"] = total_injured_count
        return items

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": _("Number of Injuries in accidents by severity")
            + f" - {request_params.location_info['road_segment_name']}"
        }
        return items
