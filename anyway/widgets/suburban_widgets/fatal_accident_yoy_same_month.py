from typing import Dict

from flask_babel import _

from anyway.request_params import RequestParams
from anyway.backend_constants import InjurySeverity, BackEndConstants
from anyway.models import InvolvedMarkerView, AccidentMarker
from anyway.widgets.widget import register
from anyway.widgets.suburban_widgets.sub_urban_widget import SubUrbanWidget
from anyway.widgets.widget_utils import get_accidents_stats


@register
class FatalAccidentYoYSameMonth(SubUrbanWidget):
    name: str = "fatal_accident_yoy_same_month"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 31

    def generate_items(self) -> None:
        latest_created_date = AccidentMarker.get_latest_marker_created_date()
        structured_data_list = []
        for year_stats in get_accidents_stats(
            table_obj=InvolvedMarkerView,
            filters={
                InvolvedMarkerView.accident_month.name: latest_created_date.month,
                InvolvedMarkerView.injury_severity.name: InjurySeverity.KILLED.value,
            },
            group_by=InvolvedMarkerView.accident_year.name,
            count=InvolvedMarkerView.injury_severity.name,
            start_time=self.request_params.start_time,
            end_time=self.request_params.end_time,
        ):
            structured_data_list.append(
                {
                    BackEndConstants.LKEY: year_stats[InvolvedMarkerView.accident_year.name],
                    BackEndConstants.VAL: year_stats["count"],
                }
            )
        self.items = structured_data_list

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": _("Monthly killed in accidents on year over compared for current month in previous years"),
        }
        return items
