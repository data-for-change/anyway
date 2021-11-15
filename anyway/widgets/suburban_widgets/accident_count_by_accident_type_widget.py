from anyway.RequestParams import RequestParams
from anyway.widgets.widget_utils import get_accidents_stats
from anyway.models import AccidentMarkerView
from anyway.widgets.widget import register
from anyway.widgets.suburban_widgets.sub_urban_widget import SubUrbanWidget


@register
class AccidentCountByAccidentTypeWidget(SubUrbanWidget):
    name: str = "accident_count_by_accident_type"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 6

    def generate_items(self) -> None:
        self.items = AccidentCountByAccidentTypeWidget.get_accident_count_by_accident_type(
            location_info=self.request_params.location_info,
            start_time=self.request_params.start_time,
            end_time=self.request_params.end_time,
        )

    @staticmethod
    def get_accident_count_by_accident_type(location_info, start_time, end_time):
        all_accident_type_count = get_accidents_stats(
            table_obj=AccidentMarkerView,
            filters=location_info,
            group_by="accident_type_hebrew",
            count="accident_type_hebrew",
            start_time=start_time,
            end_time=end_time,
        )
        merged_accident_type_count = [{"accident_type": "התנגשות", "count": 0}]
        for item in all_accident_type_count:
            if "התנגשות" in item["accident_type"]:
                merged_accident_type_count[0]["count"] += item["count"]
            else:
                merged_accident_type_count.append(item)
        return merged_accident_type_count
