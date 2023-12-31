from typing import Dict
from anyway.request_params import RequestParams
from anyway.backend_constants import InjurySeverity
from anyway.models import InvolvedMarkerView
from anyway.widgets.all_locations_widgets.all_locations_widget import AllLocationsWidget
from anyway.widgets.widget import register
from anyway.widgets.widget_utils import get_accidents_stats, join_strings, get_location_text
from anyway.backend_constants import BE_CONST
from flask_babel import _


@register
class InjuredCountBySeverityWidget(AllLocationsWidget):
    name: str = "injured_count_by_severity"
    files = [__file__]

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params)
        self.rank = 29
        self.information = "Fatal, severe and light injuries count in the specified location."

    def generate_items(self) -> None:
        self.items = InjuredCountBySeverityWidget.get_injured_count_by_severity(
            self.request_params.resolution,
            self.request_params.location_info,
            self.request_params.start_time,
            self.request_params.end_time,
        )

    @staticmethod
    def get_injured_count_by_severity(resolution, location_info, start_time, end_time):
        filters = {}
        filters["injury_severity"] = [
            InjurySeverity.KILLED.value,
            InjurySeverity.SEVERE_INJURED.value,
            InjurySeverity.LIGHT_INJURED.value,
        ]

        if resolution == BE_CONST.ResolutionCategories.STREET:
            filters["involve_yishuv_name"] = location_info.get("yishuv_name")
            filters["street1_hebrew"] = location_info.get("street1_hebrew")
        elif resolution == BE_CONST.ResolutionCategories.SUBURBAN_ROAD:
            filters["road1"] = location_info.get("road1")
            filters["road_segment_name"] = location_info.get("road_segment_name")

        count_by_severity = get_accidents_stats(
            table_obj=InvolvedMarkerView,
            filters=filters,
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
            severity_count_text = f"{severity_english}_count".replace(" ", "_")
            items[severity_count_text] = severity_and_count["count"]
            total_injured_count += severity_and_count["count"]
        if total_injured_count == 0:
            return {}
        items["start_year"] = start_year
        items["end_year"] = end_year
        items["total_injured_count"] = total_injured_count
        return items

    @staticmethod
    def get_transcription(request_params: RequestParams, items: Dict):
        total_injured_count = items.get("total_injured_count")
        if total_injured_count == 0:
            return ""
        severity_light_count = items.get("light_injured_count")
        if severity_light_count == 0:
            severity_light_count_text = ""
        elif severity_light_count == 1:
            severity_light_count_text = _("one light injured")
        else:
            severity_light_count_text = f"{severity_light_count} " + _("light injured plural")
        severity_severe_count = items.get("severe_injured_count")
        if severity_severe_count == 0:
            severity_severe_count_text = ""
        elif severity_severe_count == 1:
            severity_severe_count_text = _("one severe injured")
        else:
            severity_severe_count_text = f"{severity_severe_count} " + _("severe injured plural")
        killed_count = items.get("killed_count")
        if killed_count == 0:
            killed_count_text = ""
        elif killed_count == 1:
            killed_count_text = _("one killed")
        else:
            killed_count_text = f"{killed_count} " + _("killed plural")
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
            raise Exception(
                f"cannot convert to hebrew for resolution : {request_params.resolution.get('resolution')}"
            )
        text += "{between_years_keyword} {start_year} - {end_year}, {injured_killed_keyword} {injured_num} {people_phrase}, {out_of_them_keywoard} ".format(
            between_years_keyword=_("between the years"),
            start_year=request_params.start_time.year,
            end_year=request_params.end_time.year,
            injured_killed_keyword=_("injured/killed"),
            injured_num=total_injured_count,
            people_phrase=_("people from car accidents"),
            out_of_them_keywoard=_("out of them"),
        )
        text += join_strings(
            [killed_count_text, severity_severe_count_text, severity_light_count_text],
            sep_a=" ,",
            sep_b=_(" and "),
        )
        return text

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        subtitle = get_location_text(request_params)
        items["data"]["text"] = {
            "title": _("Number of Injuries in accidents by severity"),
            "subtitle": _(subtitle),
            "transcription": InjuredCountBySeverityWidget.get_transcription(
                request_params=request_params, items=items["data"]["items"]
            ),
        }
        return items


_("injured/killed")
_("people from car accidents")
_("one killed")
_("killed plural")
_("one severe injured")
_("severe injured plural")
_("one light injured")
_("light injured plural")
