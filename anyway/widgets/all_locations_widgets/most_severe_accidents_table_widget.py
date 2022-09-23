import logging
from typing import Dict

import pandas as pd
from flask_babel import _
from anyway.request_params import RequestParams
from anyway.backend_constants import BE_CONST, AccidentSeverity, AccidentType, InjurySeverity
from anyway.infographics_dictionaries import segment_dictionary
from anyway.widgets.widget_utils import get_query, get_accidents_stats
from anyway.models import AccidentMarkerView, InvolvedMarkerView
from anyway.widgets.all_locations_widgets.all_locations_widget import AllLocationsWidget
from anyway.widgets.widget import register


def get_most_severe_accidents_with_entities(
    table_obj,
    filters,
    entities,
    start_time,
    end_time,
    resolution: BE_CONST.ResolutionCategories,
    limit=10,
):
    filters = filters or {}
    filters["provider_code"] = [
        BE_CONST.CBS_ACCIDENT_TYPE_1_CODE,
        BE_CONST.CBS_ACCIDENT_TYPE_3_CODE,
    ]
    # pylint: disable=no-member
    filters["accident_severity"] = [AccidentSeverity.FATAL.value, AccidentSeverity.SEVERE.value]
    query = get_query(table_obj, filters, start_time, end_time)
    query = query.with_entities(*entities)
    query = query.order_by(
        getattr(table_obj, "accident_timestamp").desc(),
        getattr(table_obj, "accident_severity").asc(),
    )
    query = query.limit(limit)
    df = pd.read_sql_query(query.statement, query.session.bind)
    df.columns = [c.replace("_hebrew", "") for c in df.columns]
    return df.to_dict(orient="records")  # pylint: disable=no-member


def get_most_severe_accidents_table_title(
    location_info: dict, resolution: BE_CONST.ResolutionCategories
):
    if resolution == BE_CONST.ResolutionCategories.SUBURBAN_ROAD:
        return (
            _("Most severe accidents in segment")
            + " "
            + segment_dictionary[location_info["road_segment_name"]]
        )
    elif resolution == BE_CONST.ResolutionCategories.STREET:
        return (
            _("Severe accidents in street")
            + f" {location_info['street1_hebrew']} "
            + _("in ")
            + f"{location_info['yishuv_name']}"
        )


# count of dead and severely injured
def get_casualties_count_in_accident(accident_id, provider_code, injury_severity, accident_year):
    filters = {
        "accident_id": accident_id,
        "provider_code": provider_code,
        "injury_severity": injury_severity,
        "accident_year": accident_year,
    }
    casualties = get_accidents_stats(
        table_obj=InvolvedMarkerView,
        filters=filters,
        group_by="injury_severity",
        count="injury_severity",
    )
    res = 0
    for ca in casualties:
        res += ca["count"]
    return res


@register
class MostSevereAccidentsTableWidget(AllLocationsWidget):
    name: str = "most_severe_accidents_table"
    files = [__file__]
    widget_digest = AllLocationsWidget.calc_widget_digest(files)

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params)
        self.rank = 2
        self.information = "Most recent fatal and severe accidents, ordered by date. Up to 10 accidents are presented."

    def generate_items(self) -> None:
        # noinspection PyUnresolvedReferences
        self.items = MostSevereAccidentsTableWidget.prepare_table(
            self.request_params.location_info,
            self.request_params.start_time,
            self.request_params.end_time,
            self.request_params.resolution,
        )

    @staticmethod
    def prepare_table(
        location_info, start_time, end_time, resolution: BE_CONST.ResolutionCategories
    ):
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
            resolution=resolution,
        )
        # Add casualties
        for accident in accidents:
            accident["type"] = AccidentType(accident["accident_type"]).get_label()
            dt = accident["accident_timestamp"].to_pydatetime()
            accident["date"] = dt.strftime("%d/%m/%y")
            accident["hour"] = dt.strftime("%H:%M")
            accident["killed_count"] = get_casualties_count_in_accident(
                accident["id"],
                accident["provider_code"],
                InjurySeverity.KILLED.value,
                accident["accident_year"],
            )
            accident["severe_injured_count"] = get_casualties_count_in_accident(
                accident["id"],
                accident["provider_code"],
                InjurySeverity.SEVERE_INJURED.value,
                accident["accident_year"],
            )
            accident["light_injured_count"] = get_casualties_count_in_accident(
                accident["id"],
                accident["provider_code"],
                InjurySeverity.LIGHT_INJURED.value,
                accident["accident_year"],
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
            "title": get_most_severe_accidents_table_title(
                request_params.location_info, request_params.resolution
            )
        }
        return items


# adding calls to _() for pybabel extraction
_("Most recent fatal and severe accidents, ordered by date. Up to 10 accidents are presented.")
