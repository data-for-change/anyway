from anyway.backend_constants import AccidentSeverity
from anyway.widgets.widget_utils import get_accidents_stats, join_strings
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
    def get_transcription(request_params: RequestParams, items: Dict):
        total_accidents_count = items.get("total_accidents_count")
        if total_accidents_count == 0:
            return ""
        severity_light_count = items.get("severity_light_count")
        if severity_light_count == 0:
            severity_light_count_text = ""
        elif severity_light_count == 1:
            severity_light_count_text = _("one light")
        else:
            severity_light_count_text = f"{severity_light_count} " + _("light plural")
        severity_severe_count = items.get("severity_severe_count")
        if severity_severe_count == 0:
            severity_severe_count_text = ""
        elif severity_severe_count == 1:
            severity_severe_count_text = _("one severe")
        else:
            severity_severe_count_text = f"{severity_severe_count} " + _("severe plural")
        severity_fatal_count = items.get("severity_fatal_count")
        if severity_fatal_count == 0:
            severity_fatal_count_text = ""
        elif severity_fatal_count == 1:
            severity_fatal_count_text = _("one fatal")
        else:
            severity_fatal_count_text = f"{severity_fatal_count} " + _("fatal plural")
        if request_params.resolution == BE_CONST.ResolutionCategories.STREET:
            text = "{in_yishuv_keyword} {yishuv_name} {in_street_keyword} {street_name} ".format(
                in_yishuv_keyword=_("in yishuv"),
                yishuv_name=_(request_params.location_info.get("yishuv_name")),
                in_street_keyword=_("in street"),
                street_name=_(request_params.location_info.get("street1_hebrew")),
            )
        elif request_params.resolution == BE_CONST.ResolutionCategories.SUBURBAN_ROAD:
            text = "{in_road_keyword} {road_num} {in_segment_keyword} {segment_name} ".format(
                in_road_keyword=_("in road"),
                road_num=request_params.location_info.get("road1"),
                in_segment_keyword=_("in segment"),
                segment_name=_(request_params.location_info.get("road_segment_name")),
            )
        else:
            raise Exception(f"cannot convert to hebrew for resolution : {request_params.resolution.value}")
        text += "{between_years_keyword} {start_year} - {end_year}, {separator_keyword} {incidents_num} {incident_keyword}, {out_of_them_keywoard} ".format(
            between_years_keyword=_("between the years"),
            start_year=request_params.start_time.year,
            end_year=request_params.end_time.year,
            separator_keyword=_("took place"),
            incidents_num=total_accidents_count,
            incident_keyword=_("accidents"),
            out_of_them_keywoard=_("out of them"),
        )
        text += join_strings(
            [severity_fatal_count_text, severity_severe_count_text, severity_light_count_text],
            sep_a=" ,",
            sep_b=_(" and "),
        )
        return text

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        if request_params.resolution in (
            BE_CONST.ResolutionCategories.SUBURBAN_ROAD,
            BE_CONST.ResolutionCategories.SUBURBAN_JUNCTION,
        ):
            is_segment = request_params.resolution == BE_CONST.ResolutionCategories.SUBURBAN_ROAD
            items["data"]["text"] = {
                "title": _("Number of accidents by severity"),
                "subtitle": _(request_params.location_info["road_segment_name"])
                if is_segment
                else _(request_params.location_info["non_urban_intersection_hebrew"]),
                "transcription": AccidentCountBySeverityWidget.get_transcription(
                    request_params=request_params, items=items["data"]["items"]
                ),
            }
            items["meta"][
                "information"
            ] = "{incident_description}{incident_location} {incident_time}.".format(
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
            subtitle = _(
                "{street_name}, {yishuv_name}".format(
                    street_name=request_params.location_info["street1_hebrew"],
                    yishuv_name=request_params.location_info["yishuv_name"],
                )
            )
            items["data"]["text"] = {
                "title": s,
                "subtitle": subtitle,
                "transcription": AccidentCountBySeverityWidget.get_transcription(
                    request_params=request_params, items=items["data"]["items"]
                ),
            }
            items["meta"][
                "information"
            ] = "{incident_description}{incident_location} {incident_time}.".format(
                incident_description=_("Fatal, severe and light accidents count in "),
                incident_location=_("street"),
                incident_time=_("in the selected time"),
            )
        return items


_("Fatal, severe and light accidents count in the specified location.")
_("junction")
_("one light")
_("light plural")
_("one severe")
_("severe plural")
_("one fatal")
_("fatal plural")
_("in segment")
_("in street")
_("in road")
_("in segment")
_("between the years")
_("took place")
_("out of them")
_("accidents")
_(" and ")
_("in the selected time")
