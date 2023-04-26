from anyway.backend_constants import AccidentSeverity
from anyway.widgets.widget_utils import get_accidents_stats
from anyway.request_params import RequestParams
from anyway.models import AccidentMarkerView
from anyway.widgets.widget import register
from anyway.backend_constants import BE_CONST
from anyway.widgets.all_locations_widgets.all_locations_widget import AllLocationsWidget
from flask_babel import _
from typing import Dict, List


@register
class AccidentCountBySeverityWidget(AllLocationsWidget):
    name: str = "accident_count_by_severity"
    files: List[str] = [__file__]

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params)
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
            severity_count_text = f"severity_{severity_english}_count"
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
        if request_params.resolution in (BE_CONST.ResolutionCategories.SUBURBAN_ROAD,
                                         BE_CONST.ResolutionCategories.SUBURBAN_JUNCTION):
            is_segment = request_params.resolution == BE_CONST.ResolutionCategories.SUBURBAN_ROAD
            items["data"]["text"] = {
                "title": _("Number of accidents by severity"),
                "subtitle": _(request_params.location_info['road_segment_name'] if is_segment else
                              request_params.location_info['non_urban_intersection_hebrew']),
            }
            items["meta"]["information"] = "{incident_description}{incident_location} {incident_time}.".format(
                incident_description=_("Fatal, severe and light accidents count in "),
                incident_location=_("segment") if is_segment else _("junction"),
                incident_time=_("in the selected time"),
            )
        elif request_params.resolution == BE_CONST.ResolutionCategories.STREET:
            # To have FE to treat it as a different widget
            num_accidents = items["data"]["items"]["total_accidents_count"]
            s = "{range_keyword} {start_year} - {end_year}, {separator_keyword} {incidents_num} {incident_keyword}".format(
                range_keyword=_("in years"),
                start_year=request_params.start_time.year,
                end_year=request_params.end_time.year,
                separator_keyword=_("took place"),
                incidents_num=num_accidents,
                incident_keyword=_("accidents"),
            )
            subtitle = _("{street_name}, {yishuv_name}".format(street_name=request_params.location_info["street1_hebrew"],
                                                               yishuv_name=request_params.location_info["yishuv_name"]))
            items["data"]["text"] = {"title": s, "subtitle": subtitle}
            items["meta"]["information"] = "{incident_description}{incident_location} {incident_time}.".format(
                incident_description=_("Fatal, severe and light accidents count in "),
                incident_location=_("street"),
                incident_time=_("in the selected time"),
            )
        return items


_("Fatal, severe and light accidents count in the specified location.")
_("junction")
