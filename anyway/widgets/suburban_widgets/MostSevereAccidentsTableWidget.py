import logging
from enum import __call__
from typing import Dict

from flask_babel import _

from anyway.RequestParams import RequestParams
from anyway.infographics_utils import register, get_most_severe_accidents_with_entities, \
    get_casualties_count_in_accident, get_most_severe_accidents_table_title
from anyway.models import AccidentMarkerView
from anyway.widgets.suburban_widgets.SubUrbanWidget import SubUrbanWidget


@register
class MostSevereAccidentsTableWidget(SubUrbanWidget):
    name: str = "most_severe_accidents_table"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 2
        self.information = "Most recent fatal and severe accidents in location, ordered by date. Up to 10 accidents are presented."

    def generate_items(self) -> None:
        self.items = MostSevereAccidentsTableWidget.prepare_table(
            self.request_params.location_info,
            self.request_params.start_time,
            self.request_params.end_time,
        )

    @staticmethod
    def prepare_table(location_info, start_time, end_time):
        entities = (
            "id",
            "provider_code",
            "accident_timestamp",
            "accident_type",
            "accident_year",
            "accident_severity",
        )
        accidents = get_most_severe_accidents_with_entities(
            table_obj=AccidentMarkerView,
            filters=location_info,
            entities=entities,
            start_time=start_time,
            end_time=end_time,
        )
        # Add casualties
        for accident in accidents:
            accident["type"] = AccidentType(accident["accident_type"]).get_label()
            dt = accident["accident_timestamp"].to_pydatetime()
            accident["date"] = dt.strftime("%d/%m/%y")
            accident["hour"] = dt.strftime("%H:%M")
            accident["killed_count"] = get_casualties_count_in_accident(
                accident["id"], accident["provider_code"], 1, accident["accident_year"]
            )
            accident["severe_injured_count"] = get_casualties_count_in_accident(
                accident["id"], accident["provider_code"], 2, accident["accident_year"]
            )
            accident["light_injured_count"] = get_casualties_count_in_accident(
                accident["id"], accident["provider_code"], 3, accident["accident_year"]
            )
            # TODO: remove injured_count after FE adaptation to light and severe counts
            accident["injured_count"] = (
                    accident["severe_injured_count"] + accident["light_injured_count"]
            )
            del (
                accident["accident_timestamp"],
                accident["accident_type"],
                accident["id"],
                accident["provider_code"],
            )
            accident["accident_severity"] = AccidentSeverity(
                accident["accident_severity"]
            ).get_label()
        return accidents

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        if request_params.lang != "en":
            for item in items["data"]["items"]:
                try:
                    item["accident_severity"] = _(item["accident_severity"])
                    item["type"] = _(item["type"])
                except KeyError:
                    logging.exception(
                        f"MostSevereAccidentsTableWidget.localize_items: Exception while translating {item}."
                    )
        items["data"]["text"] = {
            "title": get_most_severe_accidents_table_title(request_params.location_info)
        }
        return items