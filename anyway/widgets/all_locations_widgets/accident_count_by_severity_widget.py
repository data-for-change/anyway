from anyway.backend_constants import AccidentSeverity
from anyway.widgets.widget_utils import get_accidents_stats
from anyway.request_params import RequestParams
from anyway.models import AccidentMarkerView
from anyway.widgets.widget import register
from anyway.backend_constants import BE_CONST
from anyway.widgets.all_locations_widgets.all_locations_widget import AllLocationsWidget
from flask_babel import _
from typing import Dict


@register
class AccidentCountBySeverityWidget(AllLocationsWidget):
    name: str = "accident_count_by_severity"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 1

    def generate_items(self) -> None:
        self.items = AccidentCountBySeverityWidget.get_accident_count_by_severity(
            self.request_params.location_info,
            self.request_params.start_time,
            self.request_params.end_time,
        )

    @staticmethod
    def get_accident_count_by_severity(location_info, start_time, end_time):
        count_by_severity = get_accidents_stats(
            table_obj=AccidentMarkerView,
            filters=location_info,
            group_by="accident_severity",
            count="accident_severity",
            start_time=start_time,
            end_time=end_time,
        )
        found_severities = [d["accident_severity"] for d in count_by_severity]
        items = {}
        total_accidents_count = 0
        start_year = start_time.year
        end_year = end_time.year
        for sev in AccidentSeverity:
            if sev.value not in found_severities:
                count_by_severity.append({"accident_severity": sev.value, "count": 0})
        for severity_and_count in count_by_severity:
            severity_english = AccidentSeverity.labels()[
                AccidentSeverity(severity_and_count["accident_severity"])
            ]
            severity_count_text = "severity_{}_count".format(severity_english)
            items[severity_count_text] = severity_and_count["count"]
            total_accidents_count += severity_and_count["count"]
        if total_accidents_count == 0:
            return {}
        items["start_year"] = start_year
        items["end_year"] = end_year
        items["total_accidents_count"] = total_accidents_count
        return items

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        if request_params.resolution == BE_CONST.ResolutionCategories.SUBURBAN_ROAD:
            items["data"]["text"] = {
                "title": _("Number of accidents by severity")
                + f" - {request_params.location_info['road_segment_name']}"
            }
            items["meta"]["information"] = "{}{} {}.".format(
                _("Fatal, severe and light accidents count in "), _("segment"),
                _("in the selected time")
            )
        elif request_params.resolution == BE_CONST.ResolutionCategories.STREET:
            # To have FE to treat it as a different widget
            num_accidents = items["data"]["items"]["total_accidents_count"]
            s = "{} {} - {} {} {}, {}, {} {} {}".format(
                _("in years"),
                request_params.start_time.year,
                request_params.end_time.year,
                _("on street"),
                request_params.location_info["street1_hebrew"],
                request_params.location_info["yishuv_name"],
                _("took place"),
                num_accidents,
                _("accidents"),
            )
            items["data"]["text"] = {"title": s}
            items["meta"]["information"] = "{}{} {}.".format(
                _("Fatal, severe and light accidents count in "),
                _("street"),
                _("in the selected time")
            )
        return items


_("Fatal, severe and light accidents count in the specified location.")
