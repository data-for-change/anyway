# -*- coding: utf-8 -*-
import time
import logging
import datetime
import json
import os
import copy
from functools import lru_cache
from collections import defaultdict
from typing import Optional, Dict, List, Union, Any, Type, Callable

# noinspection PyUnresolvedReferences
from dataclasses import dataclass
import traceback

import pandas as pd
from collections import defaultdict

from sqlalchemy import func, distinct, literal_column, case
from sqlalchemy import cast, Numeric
from sqlalchemy import desc
from sqlalchemy import or_
from sqlalchemy.sql.elements import and_


# noinspection PyProtectedMember
from flask_babel import _
from anyway.backend_constants import (
    BE_CONST,
    InjuredType,
    LabeledCode,
    InjurySeverity,
    AccidentSeverity,
    DriverType,
    AccidentType,
)
from anyway.models import NewsFlash, AccidentMarkerView, InvolvedMarkerView, VehicleMarkerView
from anyway.parsers import resolution_dict
from anyway.app_and_db import db
from anyway.infographics_dictionaries import (
    head_on_collisions_comparison_dict,
    segment_dictionary,
)
from anyway.parsers import infographics_data_cache_updater
from anyway.utilities import parse_age_from_range
from anyway.vehicle_type import VehicleCategory


@dataclass
class RequestParams:
    """
    Input for infographics data generation, per api call
    """

    news_flash_obj: NewsFlash
    years_ago: int
    location_text: str
    location_info: Dict[str, Any]
    resolution: Dict
    gps: Dict
    start_time: datetime.date
    end_time: datetime.date
    lang: str

    def __str__(self):
        return f"RequestParams(location_text:{self.location_text}, start_time:{self.start_time}, end_time:{self.end_time}, lang:{self.lang})"


class Widget:
    """
    Base class for widgets. Each widget will be a class that is derived from Widget, and instantiated
    with RequestParams and its name.
    The Serialize() method returns the data that the API returns, and has structure that is specified below.
    To add a new widget sub-class:
    - Make is subclass of Widget
    - Set attribute rank
    - Implement method generate_items()
    - Optionally set additional attributes if needed, and alter the returned values of `is_in_cache()` and
      `is_included()` when needed.
    Returned Widget structure:
    `{
        'name': str,
        'data': {
                 'items': list (Array) | dictionary (Object),
                 'text': dictionary (Object) - can be empty
                 },
        'meta': {
                 'rank': int (Integer)
                 }
    }`
    """

    request_params: RequestParams
    name: str
    rank: int
    items: Union[Dict, List]
    text: Dict
    meta: Optional[Dict]

    def __init__(self, request_params: RequestParams, name: str):
        self.request_params = copy.deepcopy(request_params)
        self.name = name
        self.rank = -1
        self.items = {}
        self.text = {}
        self.meta = None
        self.information = ""

    def get_name(self) -> str:
        return self.name

    def get_rank(self) -> int:
        return self.rank

    @staticmethod
    def is_in_cache() -> bool:
        """Whether this widget is stored in the cache"""
        return True

    # noinspection PyMethodMayBeStatic
    def is_included(self) -> bool:
        """Whether this widget is included in the response"""
        return bool(self.items)

    def generate_items(self) -> None:
        """ Generates the data of the widget and set it to self.items"""
        pass

    @staticmethod
    def is_relevant(request_params: RequestParams) -> bool:
        return True

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        if "name" in items:
            logging.debug(
                f"Widget.localize_items: widget {items['name']} should implement localize_items method"
            )
        else:
            logging.error(f"Widget.localize_items: bad input (missing 'name' key):{items}")
        return items

    def serialize(self):
        if not self.items:
            self.generate_items()
        output = {"name": self.name, "data": {}}
        output["data"]["items"] = self.items
        if self.text:
            output["data"]["text"] = self.text
        if self.meta:
            output["meta"] = self.meta
        else:
            output["meta"] = {}
        output["meta"]["rank"] = self.rank
        output["meta"]["information"] = self.information
        return output


widgets_dict: Dict[str, Type[Widget]] = {}


class SubUrbanWidget(Widget):
    def __init__(self, request_params: RequestParams, name: str):
        if not is_sub_urban(request_params):
            logging.error(
                f"SubUrbanWidget initialized with missing location fields:{request_params}"
            )
            raise ValueError("SubUrban fields missing")
        super().__init__(request_params, name)

    @staticmethod
    def is_relevant(request_params: RequestParams) -> bool:
        return is_sub_urban(request_params)


class UrbanWidget(Widget):
    def __init__(self, request_params: RequestParams, name: str):
        if not is_urban(request_params):
            logging.error(f"UrbanWidget initialized with missing location fields:{request_params}")
            raise ValueError("Urban fields missing")
        super().__init__(request_params, name)

    @staticmethod
    def is_relevant(request_params: RequestParams) -> bool:
        return is_urban(request_params)


def get_widget_factories() -> List[Callable[[RequestParams], Widget]]:
    """Returns list of callables that generate all widget instances"""
    return list(widgets_dict.values())


def get_widget_class_by_name(name: str) -> Type[Widget]:
    return widgets_dict[name]


def register(widget_class: Type[Widget]) -> Type[Widget]:
    if widgets_dict.get(widget_class.name) is not None:
        logging.error(f"Double register:{widget_class.name}:{widget_class}\n")
    widgets_dict[widget_class.name] = widget_class
    logging.debug(f"register:{widget_class.name}:{widget_class}\n")
    return widget_class


@register
class AccidentCountBySeverityWidget(SubUrbanWidget):
    name: str = "accident_count_by_severity"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 1
        self.information = "Fatal, severe and light accidents count in the specified location."

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
            group_by="accident_severity_hebrew",
            count="accident_severity_hebrew",
            start_time=start_time,
            end_time=end_time,
        )
        severity_dict = {"קטלנית": "fatal", "קשה": "severe", "קלה": "light"}
        items = {}
        total_accidents_count = 0
        start_year = start_time.year
        end_year = end_time.year
        for severity_and_count in count_by_severity:
            accident_severity_hebrew = severity_and_count["accident_severity"]
            severity_english = severity_dict[accident_severity_hebrew]
            severity_count_text = "severity_{}_count".format(severity_english)
            items[severity_count_text] = severity_and_count["count"]
            total_accidents_count += severity_and_count["count"]
        if total_accidents_count == 0:
            return {}
        items["start_year"] = start_year
        items["end_year"] = end_year
        items["total_accidents_count"] = total_accidents_count
        return items


# adding calls to _() for pybabel extraction
_("Fatal, severe and light accidents count in the specified location.")
_("Fatal, severe and light injured count in the specified years, split by injury severity")
_("Fatal, severe and light accidents count in the specified years, split by accident severity")


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


# adding calls to _() for pybabel extraction
_(
    "Most recent fatal and severe accidents in location, ordered by date. Up to 10 accidents are presented."
)


@register
class MostSevereAccidentsWidget(SubUrbanWidget):
    name: str = "most_severe_accidents"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 3
        self.information = "Most recent fatal and severe accidents displayed on a map. Up to 10 accidents are presented."

    def generate_items(self) -> None:
        self.items = MostSevereAccidentsWidget.get_most_severe_accidents(
            AccidentMarkerView,
            self.request_params.location_info,
            self.request_params.start_time,
            self.request_params.end_time,
        )

    @staticmethod
    def get_most_severe_accidents(table_obj, filters, start_time, end_time, limit=10):
        entities = (
            "longitude",
            "latitude",
            "accident_severity",
            "accident_timestamp",
            "accident_type",
        )

        items = get_most_severe_accidents_with_entities(
            table_obj, filters, entities, start_time, end_time, limit
        )
        for item in items:
            item["accident_severity"] = _(AccidentSeverity(item["accident_severity"]).get_label())
        return items

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        for item in items["data"]["items"]:
            try:
                item["accident_type"] = _(AccidentType(item["accident_type"]).get_label())
            except KeyError:
                logging.exception(
                    f"MostSevereAccidentsWidget.localize_items: Exception while translating {item}."
                )
        return items


# adding calls to _() for pybabel extraction
_("Most recent fatal and severe accidents displayed on a map. Up to 10 accidents are presented.")


@register
class StreetViewWidget(SubUrbanWidget):
    name: str = "street_view"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 4

    def generate_items(self) -> None:
        self.items = {
            "longitude": self.request_params.gps["lon"],
            "latitude": self.request_params.gps["lat"],
        }


@register
class HeadOnCollisionsComparisonWidget(SubUrbanWidget):
    name: str = "head_on_collisions_comparison"
    SPECIFIC_ROAD_SUBTITLE = "specific_road_segment_fatal_accidents"
    ALL_ROADS_SUBTITLE = "all_roads_fatal_accidents"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 5
        self.information = (
            "Fatal accidents distribution by accident type - head on collisions vs other accidents."
        )

    def generate_items(self) -> None:
        self.items = self.get_head_to_head_stat()

    def get_head_to_head_stat(self) -> Dict:
        news_flash = self.request_params.news_flash_obj
        road_data = {}

        filter_dict = {
            "road_type": BE_CONST.ROAD_TYPE_NOT_IN_CITY_NOT_IN_INTERSECTION,
            "accident_severity": AccidentSeverity.FATAL.value,  # pylint: disable=no-member
        }
        all_roads_data = get_accidents_stats(
            table_obj=AccidentMarkerView,
            filters=filter_dict,
            group_by="accident_type",
            count="accident_type",
            start_time=self.request_params.start_time,
            end_time=self.request_params.end_time,
        )

        if news_flash.road1 and news_flash.road_segment_name:
            filter_dict.update(
                {
                    "road1": news_flash.road1,
                    "road_segment_name": news_flash.road_segment_name,
                }
            )
            road_data = get_accidents_stats(
                table_obj=AccidentMarkerView,
                filters=filter_dict,
                group_by="accident_type",
                count="accident_type",
                start_time=self.request_params.start_time,
                end_time=self.request_params.end_time,
            )

        road_sums = self.sum_count_of_accident_type(
            # pylint: disable=no-member
            road_data,
            AccidentType.HEAD_ON_FRONTAL_COLLISION.value,
        )
        all_roads_sums = self.sum_count_of_accident_type(
            # pylint: disable=no-member
            all_roads_data,
            AccidentType.HEAD_ON_FRONTAL_COLLISION.value,
        )

        res = {
            self.SPECIFIC_ROAD_SUBTITLE: [
                {"desc": "frontal", "count": road_sums["given"]},
                {"desc": "others", "count": road_sums["others"]},
            ],
            self.ALL_ROADS_SUBTITLE: [
                {"desc": "frontal", "count": all_roads_sums["given"]},
                {"desc": "others", "count": all_roads_sums["others"]},
            ],
        }
        return res

    @staticmethod
    def sum_count_of_accident_type(data: Dict, acc_type: int) -> Dict:
        given = sum([d["count"] for d in data if d["accident_type"] == acc_type])
        others = sum([d["count"] for d in data if d["accident_type"] != acc_type])
        return {"given": given, "others": others}

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        i = items["data"]["items"]
        items["data"]["text"] = {"title": _("fatal accidents by type")}
        for val in i.values():
            for e in val:
                e["desc"] = _(e["desc"])
        return items

    # noinspection PyUnboundLocalVariable
    def is_included(self) -> bool:
        segment_items = self.items[self.SPECIFIC_ROAD_SUBTITLE]
        for item in segment_items:
            if item["desc"] == "frontal":
                segment_h2h = item["count"]
            elif item["desc"] == "others":
                segment_others = item["count"]
            else:
                raise ValueError
        segment_total = segment_h2h + segment_others
        all_items = self.items[self.ALL_ROADS_SUBTITLE]
        for item in all_items:
            if item["desc"] == "frontal":
                all_h2h = item["count"]
            elif item["desc"] == "others":
                all_others = item["count"]
            else:
                raise ValueError
        all_total = all_h2h + all_others
        return segment_h2h > 0 and (segment_h2h / segment_total) > all_h2h / all_total


# adding calls to _() for pybabel extraction
_("others")
_("frontal")
_("Fatal accidents distribution by accident type - head on collisions vs other accidents.")


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


@register
class AccidentsHeatMapWidget(SubUrbanWidget):
    name: str = "accidents_heat_map"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 7

    def generate_items(self) -> None:
        accidents_heat_map_filters = self.request_params.location_info.copy()
        accidents_heat_map_filters["accident_severity"] = [
            # pylint: disable=no-member
            AccidentSeverity.FATAL.value,
            # pylint: disable=no-member
            AccidentSeverity.SEVERE.value,
        ]
        self.items = AccidentsHeatMapWidget.get_accidents_heat_map(
            filters=accidents_heat_map_filters,
            start_time=self.request_params.start_time,
            end_time=self.request_params.end_time,
        )

    @staticmethod
    def get_accidents_heat_map(filters, start_time, end_time):
        filters = filters or {}
        filters["provider_code"] = [
            BE_CONST.CBS_ACCIDENT_TYPE_1_CODE,
            BE_CONST.CBS_ACCIDENT_TYPE_3_CODE,
        ]
        query = get_query(AccidentMarkerView, filters, start_time, end_time)
        query = query.with_entities("longitude", "latitude")
        df = pd.read_sql_query(query.statement, query.session.bind)
        return df.to_dict(orient="records")  # pylint: disable=no-member

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": _("Fatal and severe accidents heat map")
            + " "
            + segment_dictionary[request_params.location_info["road_segment_name"]]
        }
        return items


@register
class AccidentCountByAccidentYearWidget(SubUrbanWidget):
    name: str = "accident_count_by_accident_year"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 8
        self.text = {
            # "title" and "labels" will be set in localize_items()
        }
        self.information = "Fatal, severe and light accidents count in the specified years, split by accident severity"

    def generate_items(self) -> None:

        res = get_accidents_stats(
            table_obj=AccidentMarkerView,
            filters=self.request_params.location_info,
            group_by=("accident_severity", "accident_year"),
            count="accident_year",
            start_time=self.request_params.start_time,
            end_time=self.request_params.end_time,
        )
        try:
            self.items = add_empty_keys_to_gen_two_level_dict(
                res,
                AccidentSeverity.codes(),
                list(
                    range(
                        self.request_params.start_time.year, self.request_params.end_time.year + 1
                    )
                ),
            )
        except Exception as e:
            logging.exception(f"failed to add empty keys to {res}", e)

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": _("Number of accidents, by year, splitted by accident severity, in segment")
            + " "
            + segment_dictionary[request_params.location_info["road_segment_name"]],
            "labels": gen_entity_labels(AccidentSeverity),
        }
        return items


@register
class InjuredCountByAccidentYearWidget(SubUrbanWidget):
    name: str = "injured_count_by_accident_year"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 9
        self.text = {
            # "title" and "labels" will be set in localize_items()
        }
        self.information = (
            "Fatal, severe and light injured count in the specified years, split by injury severity"
        )

    def generate_items(self) -> None:
        res = get_accidents_stats(
            table_obj=InvolvedMarkerView,
            filters=get_injured_filters(self.request_params.location_info),
            group_by=("injury_severity", "accident_year"),
            count="accident_year",
            start_time=self.request_params.start_time,
            end_time=self.request_params.end_time,
        )
        try:
            self.items = add_empty_keys_to_gen_two_level_dict(
                res,
                InjurySeverity.codes(),
                list(
                    range(
                        self.request_params.start_time.year, self.request_params.end_time.year + 1
                    )
                ),
            )
        except Exception as e:
            logging.exception(f"failed to add empty keys to {res}", e)

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": _("Number of injured in accidents, per year, splitted by severity, in segment")
            + " "
            + segment_dictionary[request_params.location_info["road_segment_name"]],
            "labels": gen_entity_labels(InjurySeverity),
        }
        return items


@register
class AccidentCountByDayNightWidget(SubUrbanWidget):
    name: str = "accident_count_by_day_night"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 10
        self.text = {"title": "כמות תאונות ביום ובלילה"}

    def generate_items(self) -> None:
        self.items = get_accidents_stats(
            table_obj=AccidentMarkerView,
            filters=self.request_params.location_info,
            group_by="day_night_hebrew",
            count="day_night_hebrew",
            start_time=self.request_params.start_time,
            end_time=self.request_params.end_time,
        )


@register
class AccidentCountByHourWidget(SubUrbanWidget):
    name: str = "accident_count_by_hour"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 11
        self.text = {"title": "כמות תאונות לפי שעה"}

    def generate_items(self) -> None:
        self.items = get_accidents_stats(
            table_obj=AccidentMarkerView,
            filters=self.request_params.location_info,
            group_by="accident_hour",
            count="accident_hour",
            start_time=self.request_params.start_time,
            end_time=self.request_params.end_time,
        )


@register
class AccidentCountByRoadLightWidget(SubUrbanWidget):
    name: str = "accident_count_by_road_light"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 12
        self.text = {"title": "כמות תאונות לפי תאורה"}

    def generate_items(self) -> None:
        self.items = get_accidents_stats(
            table_obj=AccidentMarkerView,
            filters=self.request_params.location_info,
            group_by="road_light_hebrew",
            count="road_light_hebrew",
            start_time=self.request_params.start_time,
            end_time=self.request_params.end_time,
        )


class TopRoadSegmentsAccidentsPerKmWidget(SubUrbanWidget):
    name: str = "top_road_segments_accidents_per_km"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 13
        self.text = {
            "title": "תאונות לכל ק״מ כביש על פי מקטע בכביש "
            + str(int(self.request_params.location_info["road1"]))
        }

    def generate_items(self) -> None:
        self.items = TopRoadSegmentsAccidentsPerKmWidget.get_top_road_segments_accidents_per_km(
            resolution=self.request_params.resolution,
            location_info=self.request_params.location_info,
            start_time=self.request_params.start_time,
            end_time=self.request_params.end_time,
        )

    @staticmethod
    def get_top_road_segments_accidents_per_km(
        resolution, location_info, start_time=None, end_time=None, limit=3
    ):
        if resolution != "כביש בינעירוני":  # relevent for non urban roads only
            return {}
        filters = {}
        filters["road1"] = location_info["road1"]
        query = get_query(
            table_obj=AccidentMarkerView, filters=filters, start_time=start_time, end_time=end_time
        )

        query = (
            query.with_entities(
                AccidentMarkerView.road_segment_name,
                AccidentMarkerView.road_segment_length_km.label("segment_length"),
                cast(
                    (func.count(AccidentMarkerView.id) / AccidentMarkerView.road_segment_length_km),
                    Numeric(10, 4),
                ).label("accidents_per_km"),
                func.count(AccidentMarkerView.id).label("total_accidents"),
            )
            .filter(AccidentMarkerView.road_segment_name.isnot(None))
            .group_by(
                AccidentMarkerView.road_segment_name, AccidentMarkerView.road_segment_length_km
            )
            .order_by(desc("accidents_per_km"))
            .limit(limit)
        )

        result = pd.read_sql_query(query.statement, query.session.bind)
        return result.to_dict(orient="records")  # pylint: disable=no-member


class InjuredCountPerAgeGroupWidget(SubUrbanWidget):
    name: str = "injured_count_per_age_group"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 14

    def generate_items(self) -> None:
        self.items = InjuredCountPerAgeGroupWidget.filter_and_group_injured_count_per_age_group(
            self.request_params
        )

    @staticmethod
    def filter_and_group_injured_count_per_age_group(request_params: RequestParams):
        road_number = request_params.location_info["road1"]

        query = (
            db.session.query(InvolvedMarkerView)
            .filter(InvolvedMarkerView.accident_timestamp >= request_params.start_time)
            .filter(InvolvedMarkerView.accident_timestamp <= request_params.end_time)
            .filter(
                InvolvedMarkerView.provider_code.in_(
                    [
                        BE_CONST.CBS_ACCIDENT_TYPE_1_CODE,
                        BE_CONST.CBS_ACCIDENT_TYPE_3_CODE,
                    ]
                )
            )
            .filter(
                InvolvedMarkerView.injury_severity.in_(
                    [
                        InjurySeverity.KILLED.value,  # pylint: disable=no-member
                        InjurySeverity.SEVERE_INJURED.value,  # pylint: disable=no-member
                    ]
                )
            )
            .filter(
                (InvolvedMarkerView.road1 == road_number)
                | (InvolvedMarkerView.road2 == road_number)
            )
            .group_by("age_group", "injury_severity")
            .with_entities("age_group", "injury_severity", func.count().label("count"))
        )

        # if there's no data - return empty dict
        if query.count() == 0:
            return {}

        range_dict = {0: 4, 5: 9, 10: 14, 15: 19, 20: 24, 25: 34, 35: 44, 45: 54, 55: 64, 65: 200}

        def defaultdict_int_factory() -> Callable:
            return lambda: defaultdict(int)

        dict_grouped = defaultdict(defaultdict_int_factory())

        for row in query:
            age_range = row.age_group
            injury_name = InjurySeverity(row.injury_severity).get_label()
            count = row.count

            # The age groups in the DB are not the same age groups in the Widget - so we need to merge some of the groups
            age_parse = parse_age_from_range(age_range)
            if not age_parse:
                dict_grouped["unknown"][injury_name] += count
            else:
                min_age, max_age = age_parse
                found_age_range = False
                # Find to what "bucket" to aggregate the data
                for item_min_range, item_max_range in range_dict.items():
                    if item_min_range <= min_age <= max_age <= item_max_range:
                        string_age_range = f"{item_min_range:02}-{item_max_range:02}"
                        dict_grouped[string_age_range][injury_name] += count
                        found_age_range = True
                        break

                if not found_age_range:
                    dict_grouped["unknown"][injury_name] += count

        # Rename the last key
        dict_grouped["65+"] = dict_grouped["65-200"]
        del dict_grouped["65-200"]

        return dict_grouped

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": _("Injury severity per age group in ")
            + request_params.location_info["road_segment_name"]
        }
        return items


@register
class Road2Plus1Widget(SubUrbanWidget):
    name: str = "vision_zero_2_plus_1"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.information = "Road 2 plus 1 solution to prevent fatal accidents."
        self.rank = 24

    def generate_items(self) -> None:
        self.items = {"image_src": "vision_zero_2_plus_1"}

    def get_frontal_accidents_in_past_year(self) -> Optional[int]:
        news_flash = self.request_params.news_flash_obj
        road_data = {}
        filter_dict = {
            "road_type": BE_CONST.ROAD_TYPE_NOT_IN_CITY_NOT_IN_INTERSECTION,
        }

        if news_flash.road1 and news_flash.road_segment_name:
            filter_dict.update(
                {"road1": news_flash.road1, "road_segment_name": news_flash.road_segment_name}
            )
            road_data = get_accidents_stats(
                table_obj=AccidentMarkerView,
                filters=filter_dict,
                group_by="accident_type",
                count="accident_type",
                start_time=self.request_params.end_time - datetime.timedelta(days=365),
                end_time=self.request_params.end_time,
            )

            road_sums = self.sum_count_of_accident_type(
                # pylint: disable=no-member
                road_data,
                AccidentType.HEAD_ON_FRONTAL_COLLISION.value,
            )

            return road_sums

    @staticmethod
    def sum_count_of_accident_type(data: Dict, acc_type: int) -> int:
        given = sum([d["count"] for d in data if d["accident_type"] == acc_type])
        return given

    # noinspection PyUnboundLocalVariable
    def is_included(self) -> bool:
        frontal_accidents_past_year = self.get_frontal_accidents_in_past_year()
        if frontal_accidents_past_year is not None:
            return frontal_accidents_past_year >= 2
        return False


@register
class AccidentCountByDriverTypeWidget(SubUrbanWidget):
    name: str = "accident_count_by_driver_type"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 16
        self.information = "Driver involvement in accident by driver type: professional - trucks, taxi, bus, work, minibus, tractor, private - private car, motorcycle, light electric - electric scooter, mobility scooter, electric bike."

    def generate_items(self) -> None:
        self.items = AccidentCountByDriverTypeWidget.count_accidents_by_driver_type(
            self.request_params
        )

    @staticmethod
    def count_accidents_by_driver_type(request_params):
        involved_by_vehicle_type_data = get_accidents_stats(
            table_obj=InvolvedMarkerView,
            filters=get_injured_filters(request_params.location_info),
            group_by="involve_vehicle_type",
            count="involve_vehicle_type",
            start_time=request_params.start_time,
            end_time=request_params.end_time,
        )
        driver_types = defaultdict(int)
        for item in involved_by_vehicle_type_data:
            vehicle_type, count = item["involve_vehicle_type"], int(item["count"])
            if vehicle_type in VehicleCategory.PROFESSIONAL_DRIVER.get_codes():
                driver_types[
                    # pylint: disable=no-member
                    DriverType.PROFESSIONAL_DRIVER.get_label()
                ] += count
            elif vehicle_type in VehicleCategory.PRIVATE_DRIVER.get_codes():
                driver_types[
                    # pylint: disable=no-member
                    DriverType.PRIVATE_VEHICLE_DRIVER.get_label()
                ] += count
            elif (
                vehicle_type in VehicleCategory.LIGHT_ELECTRIC.get_codes()
                or vehicle_type in VehicleCategory.OTHER.get_codes()
            ):
                # pylint: disable=no-member
                driver_types[DriverType.OTHER_DRIVER.get_label()] += count
        output = [
            {"driver_type": driver_type, "count": count}
            for driver_type, count in driver_types.items()
        ]
        return output

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        for item in items["data"]["items"]:
            try:
                item["driver_type"] = _(item["driver_type"])
            except KeyError:
                logging.exception(
                    f"AccidentCountByDriverTypeWidget.localize_items: Exception while translating {item}."
                )
        items["data"]["text"] = {
            "title": _("accident count by driver type ")
            + request_params.location_info["road_segment_name"]
        }
        return items


# adding calls to _() for pybabel extraction
_(
    "Driver involvement in accident by driver type: professional - trucks, taxi, bus, work, minibus, tractor, private - private car, motorcycle, light electric - electric scooter, mobility scooter, electric bike."
)


@register
class AccidentCountByCarTypeWidget(SubUrbanWidget):
    name: str = "accident_count_by_car_type"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 17

    def generate_items(self) -> None:
        self.items = (
            AccidentCountByCarTypeWidget.get_stats_accidents_by_car_type_with_national_data(
                self.request_params
            )
        )

    @staticmethod
    def get_stats_accidents_by_car_type_with_national_data(
        request_params: RequestParams, involved_by_vehicle_type_data=None
    ):
        out = []
        if involved_by_vehicle_type_data is None:
            involved_by_vehicle_type_data = get_accidents_stats(
                table_obj=InvolvedMarkerView,
                filters=get_injured_filters(request_params.location_info),
                group_by="involve_vehicle_type",
                count="involve_vehicle_type",
                start_time=request_params.start_time,
                end_time=request_params.end_time,
            )

        start_time = request_params.start_time
        end_time = request_params.end_time
        data_by_segment = AccidentCountByCarTypeWidget.percentage_accidents_by_car_type(
            involved_by_vehicle_type_data
        )
        national_data = (
            AccidentCountByCarTypeWidget.percentage_accidents_by_car_type_national_data_cache(
                start_time, end_time
            )
        )

        for k, v in national_data.items():  # pylint: disable=W0612
            out.append(
                {
                    "car_type": k,
                    "percentage_segment": data_by_segment[k],
                    "percentage_country": national_data[k],
                }
            )

        return out

    @staticmethod
    def percentage_accidents_by_car_type(involved_by_vehicle_type_data):
        driver_types = defaultdict(float)
        total_count = 0
        for item in involved_by_vehicle_type_data:
            vehicle_type, count = item["involve_vehicle_type"], int(item["count"])
            total_count += count
            if vehicle_type in VehicleCategory.CAR.get_codes():
                driver_types[VehicleCategory.CAR.value] += count
            elif vehicle_type in VehicleCategory.LARGE.get_codes():
                driver_types[VehicleCategory.LARGE.value] += count
            elif vehicle_type in VehicleCategory.MOTORCYCLE.get_codes():
                driver_types[VehicleCategory.MOTORCYCLE.value] += count
            elif vehicle_type in VehicleCategory.BICYCLE_AND_SMALL_MOTOR.get_codes():
                driver_types[VehicleCategory.BICYCLE_AND_SMALL_MOTOR.value] += count
            else:
                driver_types[VehicleCategory.OTHER.value] += count

        output = defaultdict(float)
        for k, v in driver_types.items():  # Calculate percentage
            output[k] = 100 * v / total_count

        return output

    @staticmethod
    @lru_cache(maxsize=64)
    def percentage_accidents_by_car_type_national_data_cache(start_time, end_time):
        involved_by_vehicle_type_data = get_accidents_stats(
            table_obj=InvolvedMarkerView,
            filters={
                "road_type": [
                    BE_CONST.ROAD_TYPE_NOT_IN_CITY_NOT_IN_INTERSECTION,
                    BE_CONST.ROAD_TYPE_NOT_IN_CITY_IN_INTERSECTION,
                ]
            },
            group_by="involve_vehicle_type",
            count="involve_vehicle_type",
            start_time=start_time,
            end_time=end_time,
        )
        return AccidentCountByCarTypeWidget.percentage_accidents_by_car_type(
            involved_by_vehicle_type_data
        )

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        for item in items["data"]["items"]:
            try:
                item["car_type"] = _(VehicleCategory(item["car_type"]).get_english_display_name())
            except ValueError:
                logging.exception(f"AccidentCountByCarType.localize_items: item:{item}")
        base_title = _(
            "comparing vehicle type percentage in accidents in"
            " {} "
            "relative to national average"
        )
        items["data"]["text"] = {
            "title": base_title.format(
                segment_dictionary[request_params.location_info["road_segment_name"]]
            )
        }
        return items


@register
class InjuredAccidentsWithPedestriansWidget(UrbanWidget):
    name: str = "injured_accidents_with_pedestrians"

    def validate_parameters(self, yishuv_name, street1_hebrew):
        # TODO: validate each parameter and display message accordingly
        return (
            yishuv_name is not None
            and street1_hebrew is not None
            and self.request_params.years_ago is not None
        )

    def convert_to_dict(self, query_results):
        res = {}

        for query_result in query_results:
            if query_result.injury_severity not in res:
                res[query_result.injury_severity] = {}
            if query_result.accident_year not in res[query_result.injury_severity]:
                res[query_result.injury_severity][query_result.accident_year] = 0

            res[query_result.injury_severity][query_result.accident_year] += query_result.count

        return res

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 18

    def generate_items(self) -> None:
        try:
            yishuv_name = self.request_params.location_info.get("yishuv_name")
            street1_hebrew = self.request_params.location_info.get("street1_hebrew")

            if not self.validate_parameters(yishuv_name, street1_hebrew):
                logging.exception(
                    f"Could not validate parameters for {NewsFlash} : {self.request_params.news_flash_obj.id}"
                )
                return None

            query = (
                db.session.query(InvolvedMarkerView)
                .with_entities(
                    InvolvedMarkerView.accident_year,
                    InvolvedMarkerView.injury_severity,
                    func.count().label("count"),
                )
                .filter(InvolvedMarkerView.accident_yishuv_name == yishuv_name)
                .filter(
                    InvolvedMarkerView.injury_severity.in_(
                        [
                            InjurySeverity.KILLED.value,
                            InjurySeverity.SEVERE_INJURED.value,
                            InjurySeverity.LIGHT_INJURED.value,
                        ]
                    )
                )
                .filter(InvolvedMarkerView.injured_type == InjuredType.PEDESTRIAN.value)
                .filter(
                    or_(
                        InvolvedMarkerView.street1_hebrew == street1_hebrew,
                        InvolvedMarkerView.street2_hebrew == street1_hebrew,
                    )
                )
                .filter(
                    and_(
                        InvolvedMarkerView.accident_timestamp >= self.request_params.start_time,
                        InvolvedMarkerView.accident_timestamp <= self.request_params.end_time,
                    )
                )
                .group_by(InvolvedMarkerView.accident_year, InvolvedMarkerView.injury_severity)
            )

            self.items = add_empty_keys_to_gen_two_level_dict(
                self.convert_to_dict(query.all()),
                InjurySeverity.codes(),
                list(
                    range(
                        self.request_params.start_time.year, self.request_params.end_time.year + 1
                    )
                ),
            )

        except Exception as e:
            logging.error(f"InjuredAccidentsWithPedestriansWidget.generate_items(): {e}")
            raise Exception(e)

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        items["data"]["text"] = {
            "title": f"נפגעים הולכי רגל ב- {get_news_flash_location_text(request_params.news_flash_obj)}",
            "labels": gen_entity_labels(InjurySeverity),
        }
        return items


@register
class AccidentSeverityByCrossLocationWidget(SubUrbanWidget):
    name: str = "accident_severity_by_cross_location"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 19
        self.text = {"title": "הולכי רגל הרוגים ופצועים קשה ברחוב בן יהודה, תל אביב"}

    @staticmethod
    def is_in_cache() -> bool:
        return False

    def generate_items(self) -> None:
        self.items = (
            AccidentSeverityByCrossLocationWidget.injury_severity_by_cross_location_mock_data()
        )

    @staticmethod
    def injury_severity_by_cross_location_mock_data():  # Temporary for Frontend
        return [
            {
                "cross_location_text": "במעבר חצייה",
                "light_injury_severity_text": "פצוע קל",
                "light_injury_severity_count": 37,
                "severe_injury_severity_text": "פצוע קשה",
                "severe_injury_severity_count": 6,
                "killed_injury_severity_text": "הרוג",
                "killed_injury_severity_count": 0,
            },
            {
                "cross_location_text": "לא במעבר חצייה",
                "light_injury_severity_text": "פצוע קל",
                "light_injury_severity_count": 11,
                "severe_injury_severity_text": "פצוע קשה",
                "severe_injury_severity_count": 10,
                "killed_injury_severity_text": "הרוג",
                "killed_injury_severity_count": 0,
            },
        ]


class MotorcycleAccidentsVsAllAccidentsWidget(SubUrbanWidget):
    name: str = "motorcycle_accidents_vs_all_accidents"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 20
        self.road_number: str = request_params.location_info["road1"]
        self.text = {
            "title": f"תאונות אופנועים קשות וקטלניות בכביש {int(self.road_number)} בהשוואה לכל הארץ"
        }

    def generate_items(self) -> None:
        self.items = MotorcycleAccidentsVsAllAccidentsWidget.motorcycle_accidents_vs_all_accidents(
            self.request_params.start_time, self.request_params.end_time, self.road_number
        )

    @staticmethod
    def motorcycle_accidents_vs_all_accidents(
        start_time: datetime.date, end_time: datetime.date, road_number: str
    ) -> List:
        location_label = "location"
        location_other = "שאר הארץ"
        location_road = f"כביש {int(road_number)}"
        case_location = case(
            [
                (
                    (InvolvedMarkerView.road1 == road_number)
                    | (InvolvedMarkerView.road2 == road_number),
                    location_road,
                )
            ],
            else_=literal_column(f"'{location_other}'"),
        ).label(location_label)

        vehicle_label = "vehicle"
        vehicle_other = "אחר"
        vehicle_motorcycle = "אופנוע"
        case_vehicle = case(
            [
                (
                    InvolvedMarkerView.involve_vehicle_type.in_(
                        VehicleCategory.MOTORCYCLE.get_codes()
                    ),
                    literal_column(f"'{vehicle_motorcycle}'"),
                )
            ],
            else_=literal_column(f"'{vehicle_other}'"),
        ).label(vehicle_label)

        query = get_query(
            table_obj=InvolvedMarkerView, filters={}, start_time=start_time, end_time=end_time
        )

        num_accidents_label = "num_of_accidents"
        query = (
            query.with_entities(
                case_location,
                case_vehicle,
                func.count(distinct(InvolvedMarkerView.provider_and_id)).label(num_accidents_label),
            )
            .filter(InvolvedMarkerView.road_type.in_(BE_CONST.NON_CITY_ROAD_TYPES))
            .filter(
                InvolvedMarkerView.accident_severity.in_(
                    # pylint: disable=no-member
                    [AccidentSeverity.FATAL.value, AccidentSeverity.SEVERE.value]
                )
            )
            .group_by(location_label, vehicle_label)
            .order_by(desc(num_accidents_label))
        )
        # pylint: disable=no-member
        results = pd.read_sql_query(query.statement, query.session.bind).to_dict(
            orient="records"
        )  # pylint: disable=no-member

        counter_road_motorcycle = 0
        counter_other_motorcycle = 0
        counter_road_other = 0
        counter_other_other = 0
        for record in results:
            if record[location_label] == location_other:
                if record[vehicle_label] == vehicle_other:
                    counter_other_other = record[num_accidents_label]
                else:
                    counter_other_motorcycle = record[num_accidents_label]
            else:
                if record[vehicle_label] == vehicle_other:
                    counter_road_other = record[num_accidents_label]
                else:
                    counter_road_motorcycle = record[num_accidents_label]
        sum_road = counter_road_other + counter_road_motorcycle
        if sum_road == 0:
            sum_road = 1  # prevent division by zero
        sum_all = counter_other_other + counter_other_motorcycle + sum_road
        percentage_label = "percentage"
        location_all_label = "כל הארץ"

        return [
            {
                location_label: location_road,
                vehicle_label: vehicle_motorcycle,
                percentage_label: counter_road_motorcycle / sum_road,
            },
            {
                location_label: location_road,
                vehicle_label: vehicle_other,
                percentage_label: counter_road_other / sum_road,
            },
            {
                location_label: location_all_label,
                vehicle_label: vehicle_motorcycle,
                percentage_label: (counter_other_motorcycle + counter_road_motorcycle) / sum_all,
            },
            {
                location_label: location_all_label,
                vehicle_label: vehicle_other,
                percentage_label: (counter_other_other + counter_road_other) / sum_all,
            },
        ]


class AccidentCountPedestriansPerVehicleStreetVsAllWidget(SubUrbanWidget):
    name: str = "accident_count_pedestrians_per_vehicle_street_vs_all"

    def __init__(self, request_params: RequestParams):
        Widget.__init__(self, request_params, type(self).name)
        self.rank = 21
        self.text = {
            "title": _(
                "Pedestrian Injuries on Ben Yehuda Street in Tel Aviv by Type of hitting Vehicle, Compared to Urban Accidents Across the country"
            )
        }

    @staticmethod
    def is_in_cache() -> bool:
        return False

    def generate_items(self) -> None:
        self.items = (
            AccidentCountPedestriansPerVehicleStreetVsAllWidget.accidents_count_pedestrians_per_vehicle_street_vs_all_mock_data()
        )

    @staticmethod
    def accidents_count_pedestrians_per_vehicle_street_vs_all_mock_data():  # Temporary for Frontend
        return [
            {"location": "כל הארץ", "vehicle": "מכונית", "num_of_accidents": 61307},
            {"location": "כל הארץ", "vehicle": "רכב כבד", "num_of_accidents": 15801},
            {"location": "כל הארץ", "vehicle": "אופנוע", "num_of_accidents": 3884},
            {"location": "כל הארץ", "vehicle": "אופניים וקורקינט ממונע", "num_of_accidents": 1867},
            {"location": "כל הארץ", "vehicle": "אחר", "num_of_accidents": 229},
            {"location": "בן יהודה", "vehicle": "מכונית", "num_of_accidents": 64},
            {"location": "בן יהודה", "vehicle": "אופנוע", "num_of_accidents": 40},
            {"location": "בן יהודה", "vehicle": "רכב כבד", "num_of_accidents": 22},
            {"location": "בן יהודה", "vehicle": "אופניים וקורקינט ממונע", "num_of_accidents": 9},
        ]


@register
class TopRoadSegmentsAccidentsWidget(SubUrbanWidget):
    name: str = "top_road_segments_accidents"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 22
        self.text = {"title": "5 המקטעים עם כמות התאונות הגדולה ביותר"}

    def generate_items(self) -> None:
        self.items = TopRoadSegmentsAccidentsWidget.top_road_segments_accidents_mock_data()

    @staticmethod
    def top_road_segments_accidents_mock_data():  # Temporary for Frontend
        return [
            {"segment name": "מחלף לה גרדיה - מחלף השלום", "count": 70},
            {"segment name": "מחלף השלום - מחלף הרכבת", "count": 48},
            {"segment name": "מחלף וולפסון - מחלף חולון", "count": 48},
            {"segment name": "מחלף קוממיות - מחלף יוספטל", "count": 34},
            {"segment name": "מחלף ההלכה - מחלף רוקח ", "count": 31},
        ]


@register
class PedestrianInjuredInJunctionsWidget(SubUrbanWidget):
    name: str = "pedestrian_injured_in_junctions"

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.rank = 23
        self.text = {"title": "מספר נפגעים הולכי רגל בצמתים - רחוב בן יהודה, תל אביב"}

    def generate_items(self) -> None:
        self.items = PedestrianInjuredInJunctionsWidget.pedestrian_injured_in_junctions_mock_data()

    @staticmethod
    def pedestrian_injured_in_junctions_mock_data():  # Temporary for Frontend
        return [
            {"street name": "גורדון י ל", "count": 18},
            {"street name": "אידלסון אברהם", "count": 10},
            {"street name": "פרישמן", "count": 7},
        ]


class AccidentTypeVehicleTypeRoadComparisonWidget(SubUrbanWidget):
    name: str = "vehicle_accident_vs_all_accidents"  # WIP: change by vehicle type
    MAX_ACCIDENT_TYPES_TO_RETURN: int = 5

    def __init__(self, request_params: RequestParams):
        super().__init__(request_params, type(self).name)
        self.road_number: str = request_params.location_info["road1"]
        # WIP: change rank, text by vehicle type
        self.rank = 25
        self.text = {
            "title": f"סוגי תאונות אופנועים בכביש {int(self.road_number)} בהשוואה לכל הארץ"
        }

    def generate_items(self) -> None:
        self.items = AccidentTypeVehicleTypeRoadComparisonWidget.accident_type_road_vs_all_count(
            self.request_params.start_time, self.request_params.end_time, self.road_number
        )

    @staticmethod
    def accident_type_road_vs_all_count(
        start_time: datetime.date, end_time: datetime.date, road_number: str
    ) -> List:
        num_accidents_label = "num_of_accidents"
        location_all = "כל הארץ"
        location_road = f"כביש {int(road_number)}"

        vehicle_types = VehicleCategory.MOTORCYCLE.get_codes()  # WIP: change by vehicle type

        all_roads_query = (
            AccidentTypeVehicleTypeRoadComparisonWidget.get_accident_count_by_vehicle_type_query(
                start_time, end_time, num_accidents_label, vehicle_types
            )
        )
        all_roads_query_result = run_query(all_roads_query)
        all_roads_sum_accidents = 0
        all_roads_map = {}
        for record in all_roads_query_result:
            all_roads_sum_accidents += record[num_accidents_label]
            all_roads_map[record[VehicleMarkerView.accident_type.name]] = record[
                num_accidents_label
            ]

        road_query = all_roads_query.filter(
            (VehicleMarkerView.road1 == road_number) | (VehicleMarkerView.road2 == road_number)
        )
        road_query_result = run_query(road_query)
        road_sum_accidents = 0
        types_to_report = []
        for record in road_query_result:
            road_sum_accidents += record[num_accidents_label]

        for record in road_query_result:
            if (
                len(types_to_report)
                == AccidentTypeVehicleTypeRoadComparisonWidget.MAX_ACCIDENT_TYPES_TO_RETURN
            ):
                break
            accident_type = record[VehicleMarkerView.accident_type.name]
            types_to_report.append(
                {
                    VehicleMarkerView.accident_type.name: accident_type,
                    location_road: record[num_accidents_label] / road_sum_accidents,
                    location_all: all_roads_map[accident_type] / all_roads_sum_accidents,
                }
            )
        return types_to_report

    @staticmethod
    def get_accident_count_by_vehicle_type_query(
        start_time: datetime.date,
        end_time: datetime.date,
        num_accidents_label: str,
        vehicle_types: List[int],
    ) -> db.session.query:
        return (
            get_query(
                table_obj=VehicleMarkerView,
                start_time=start_time,
                end_time=end_time,
                filters={VehicleMarkerView.vehicle_type.name: vehicle_types},
            )
            .with_entities(
                VehicleMarkerView.accident_type,
                func.count(distinct(VehicleMarkerView.provider_and_id)).label(num_accidents_label),
            )
            .group_by(VehicleMarkerView.accident_type)
            .order_by(desc(num_accidents_label))
        )

    @staticmethod
    def localize_items(request_params: RequestParams, items: Dict) -> Dict:
        for item in items["data"]["items"]:
            try:
                item[VehicleMarkerView.accident_type.name] = _(
                    AccidentType(item["accident_type"]).get_label()
                )
            except KeyError:
                logging.exception(
                    f"AccidentTypeVehicleTypeRoadComparisonWidget.localize_items: Exception while translating {item}."
                )
        return items


def run_query(query: db.session.query) -> Dict:
    # pylint: disable=no-member
    return pd.read_sql_query(query.statement, query.session.bind).to_dict(orient="records")


def extract_news_flash_location(news_flash_obj):
    resolution = news_flash_obj.resolution or None
    if not news_flash_obj or not resolution or resolution not in resolution_dict:
        logging.warning(
            f"could not find valid resolution for news flash id {str(news_flash_obj.id)}"
        )
        return None
    data = {"resolution": resolution}
    for field in resolution_dict[resolution]:
        curr_field = getattr(news_flash_obj, field)
        if curr_field is not None:
            data[field] = curr_field
    gps = {"lat": news_flash_obj.lat, "lon": news_flash_obj.lon}
    return {"name": "location", "data": data, "gps": gps}


def get_query(table_obj, filters, start_time, end_time):
    query = db.session.query(table_obj)
    if start_time:
        query = query.filter(getattr(table_obj, "accident_timestamp") >= start_time)
    if end_time:
        query = query.filter(getattr(table_obj, "accident_timestamp") <= end_time)
    if filters:
        for field_name, value in filters.items():
            if isinstance(value, list):
                values = value
            else:
                values = [value]
            query = query.filter((getattr(table_obj, field_name)).in_(values))
    return query


def get_accidents_stats(
    table_obj, filters=None, group_by=None, count=None, start_time=None, end_time=None
):
    filters = filters or {}
    filters["provider_code"] = [
        BE_CONST.CBS_ACCIDENT_TYPE_1_CODE,
        BE_CONST.CBS_ACCIDENT_TYPE_3_CODE,
    ]
    # get stats
    query = get_query(table_obj, filters, start_time, end_time)
    if group_by:
        if isinstance(group_by, tuple):
            if len(group_by) == 2:
                query = query.group_by(*group_by)
                query = query.with_entities(*group_by, func.count(count))
                dd = query.all()
                res = retro_dictify(dd)
                return res
            else:
                err_msg = f"get_accidents_stats: {group_by}: Only a string or a tuple of two are valid for group_by"
                logging.error(err_msg)
                raise Exception(err_msg)
        else:
            query = query.group_by(group_by)
            query = query.with_entities(group_by, func.count(count))
    df = pd.read_sql_query(query.statement, query.session.bind)
    df.rename(columns={"count_1": "count"}, inplace=True)  # pylint: disable=no-member
    df.columns = [c.replace("_hebrew", "") for c in df.columns]
    return (  # pylint: disable=no-member
        df.to_dict(orient="records") if group_by or count else df.to_dict()
    )


def add_empty_keys_to_gen_two_level_dict(
    d, level_1_values: List[Any], level_2_values: List[Any], default_level_3_value: int = 0
) -> Dict[Any, Dict[Any, int]]:
    for v1 in level_1_values:
        if v1 not in d:
            d[v1] = {}
        for v2 in level_2_values:
            if v2 not in d[v1]:
                d[v1][v2] = default_level_3_value
    return d


# noinspection Mypy
def retro_dictify(indexable) -> Dict[Any, Dict[Any, Any]]:
    d = defaultdict(dict)
    for row in indexable:
        here = d
        for elem in row[:-2]:
            if elem not in here:
                here[elem] = defaultdict(lambda: 0)
            here = here[elem]
        here[row[-2]] = row[-1]
    return d


def get_injured_filters(location_info):
    new_filters = {}
    for curr_filter, curr_values in location_info.items():
        if curr_filter in ["region_hebrew", "district_hebrew", "yishuv_name"]:
            new_filter_name = "accident_" + curr_filter
            new_filters[new_filter_name] = curr_values
        else:
            new_filters[curr_filter] = curr_values
    new_filters["injury_severity"] = [1, 2, 3, 4, 5]
    return new_filters


def get_most_severe_accidents_with_entities(
    table_obj, filters, entities, start_time, end_time, limit=10
):
    filters = filters or {}
    filters["provider_code"] = [
        BE_CONST.CBS_ACCIDENT_TYPE_1_CODE,
        BE_CONST.CBS_ACCIDENT_TYPE_3_CODE,
    ]
    # pylint: disable=no-member
    filters["accident_severity"] = [
        AccidentSeverity.FATAL.value,
        AccidentSeverity.SEVERE.value,
    ]
    query = get_query(table_obj, filters, start_time, end_time)
    query = query.with_entities(*entities)
    query = query.order_by(getattr(table_obj, "accident_timestamp").desc())
    query = query.limit(limit)
    df = pd.read_sql_query(query.statement, query.session.bind)
    df.columns = [c.replace("_hebrew", "") for c in df.columns]
    return df.to_dict(orient="records")  # pylint: disable=no-member


def get_most_severe_accidents_table_title(location_info):
    return (
        _("Most severe accidents in segment")
        + " "
        + segment_dictionary[location_info["road_segment_name"]]
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


# generate text describing location or road segment of news flash
# to be used by most severe accidents additional info widget
def get_news_flash_location_text(news_flash_obj: NewsFlash):
    nf = news_flash_obj.serialize()
    resolution = nf["resolution"] if nf["resolution"] else ""
    yishuv_name = nf["yishuv_name"] if nf["yishuv_name"] else ""
    road1 = str(int(nf["road1"])) if nf["road1"] else ""
    road2 = str(int(nf["road2"])) if nf["road2"] else ""
    street1_hebrew = nf["street1_hebrew"] if nf["street1_hebrew"] else ""
    road_segment_name = nf["road_segment_name"] if nf["road_segment_name"] else ""
    if resolution == "כביש בינעירוני" and road1 and road_segment_name:
        res = "כביש " + road1 + " במקטע " + road_segment_name
    elif resolution == "עיר" and not yishuv_name:
        res = nf["location"]
    elif resolution == "עיר" and yishuv_name:
        res = nf["yishuv_name"]
    elif resolution == "צומת בינעירוני" and road1 and road2:
        res = "צומת כביש " + road1 + " עם כביש " + road2
    elif resolution == "צומת בינעירוני" and road1 and road_segment_name:
        res = "כביש " + road1 + " במקטע " + road_segment_name
    elif resolution == "רחוב" and yishuv_name and street1_hebrew:
        res = " רחוב " + street1_hebrew + " ב" + yishuv_name
    else:
        logging.warning(
            "Did not found quality resolution. Using location field. News Flash id:{}".format(
                nf["id"]
            )
        )
        res = nf["location"]
    return res


def extract_news_flash_obj(news_flash_id):
    news_flash_obj = db.session.query(NewsFlash).filter(NewsFlash.id == news_flash_id).first()

    if not news_flash_obj:
        logging.warning("Could not find news flash id {}".format(news_flash_id))
        return None

    return news_flash_obj


def sum_road_accidents_by_specific_type(road_data, field_name):
    dict_merge = defaultdict(int)
    dict_merge[field_name] = 0
    dict_merge[head_on_collisions_comparison_dict["others"]] = 0

    for accident_data in road_data:
        if accident_data["accident_type"] == field_name:
            dict_merge[field_name] += accident_data["count"]
        else:
            dict_merge[head_on_collisions_comparison_dict["others"]] += accident_data["count"]
    return dict_merge


def convert_roads_fatal_accidents_to_frontend_view(data_dict):
    data_list = []
    for key, value in data_dict.items():
        # pylint: disable=no-member
        if key == AccidentType.HEAD_ON_FRONTAL_COLLISION.value:
            data_list.append(
                {"desc": head_on_collisions_comparison_dict["head_to_head"], "count": value}
            )
        else:
            data_list.append({"desc": key, "count": value})

    return data_list


# gets the latest date an accident has occured
def get_latest_accident_date(table_obj, filters):
    filters = filters or {}
    filters["provider_code"] = [
        BE_CONST.CBS_ACCIDENT_TYPE_1_CODE,
        BE_CONST.CBS_ACCIDENT_TYPE_3_CODE,
    ]
    query = db.session.query(func.max(table_obj.accident_timestamp))
    df = pd.read_sql_query(query.statement, query.session.bind)
    return (df.to_dict(orient="records"))[0].get("max_1")  # pylint: disable=no-member


def gen_entity_labels(entity: Type[LabeledCode]) -> dict:
    res = {}
    for e in entity:
        label = e.get_label()
        res[e.value] = {"name": label, "localized_name": _(label)}
    return res


# noinspection PyArgumentList
def generate_widgets(request_params: RequestParams, to_cache: bool = True) -> List[Widget]:
    widgets = []
    # noinspection PyArgumentList
    for w in widgets_dict.values():
        if w.is_relevant(request_params) and w.is_in_cache() == to_cache:
            widget: Widget = w(request_params)
            widgets.append(widget)
            logging.debug(f"name:{widget.name}, class:{get_widget_class_by_name(widget.name)}")
    for w in widgets:
        w.generate_items()
    filtered_widgets = []
    for w in widgets:
        if w.is_included():
            filtered_widgets.append(w)
    return filtered_widgets


def get_request_params(
    news_flash_id: int, number_of_years_ago: int, lang: str
) -> Optional[RequestParams]:
    try:
        number_of_years_ago = int(number_of_years_ago)
    except ValueError:
        return None
    if number_of_years_ago < 0 or number_of_years_ago > 100:
        return None
    news_flash_obj: Optional[NewsFlash] = extract_news_flash_obj(news_flash_id)
    if news_flash_obj is None:
        return None
    location_info = extract_news_flash_location(news_flash_obj)
    if location_info is None:
        return None
    logging.debug("location_info:{}".format(location_info))
    location_text = get_news_flash_location_text(news_flash_obj)
    logging.debug("location_text:{}".format(location_text))
    gps = location_info["gps"]
    location_info = location_info["data"]
    resolution = location_info.pop("resolution")
    if resolution is None:
        return None

    if all(value is None for value in location_info.values()):
        return None

    last_accident_date = get_latest_accident_date(table_obj=AccidentMarkerView, filters=None)
    # converting to datetime object to get the date
    end_time = last_accident_date.to_pydatetime().date()

    start_time = datetime.date(end_time.year + 1 - number_of_years_ago, 1, 1)

    request_params = RequestParams(
        news_flash_obj=news_flash_obj,
        years_ago=number_of_years_ago,
        location_text=location_text,
        location_info=location_info,
        resolution=resolution,
        gps=gps,
        start_time=start_time,
        end_time=end_time,
        lang=lang,
    )
    logging.debug(f"Ending get_request_params. params: {request_params}")
    return request_params


def create_infographics_data(news_flash_id, number_of_years_ago, lang: str) -> str:
    request_params = get_request_params(news_flash_id, number_of_years_ago, lang)
    output = create_infographics_items(request_params)
    return json.dumps(output, default=str)


def create_infographics_items(request_params: RequestParams) -> Dict:
    def get_dates_comment():
        return {
            "date_range": [request_params.start_time.year, request_params.end_time.year],
            "last_update": time.mktime(request_params.end_time.timetuple())
        }

    try:
        if request_params is None:
            return {}

        output = {}
        try:
            number_of_years_ago = int(request_params.years_ago)
        except ValueError:
            return {}
        if number_of_years_ago < 0 or number_of_years_ago > 100:
            return {}
        logging.debug("location_info:{}".format(request_params.location_info))
        logging.debug("location_text:{}".format(request_params.location_text))
        output["meta"] = {
            "location_info": request_params.location_info.copy(),
            "location_text": request_params.location_text,
            "dates_comment": get_dates_comment()
        }
        output["widgets"] = []
        widgets: List[Widget] = generate_widgets(request_params=request_params, to_cache=True)
        widgets.extend(generate_widgets(request_params=request_params, to_cache=False))
        output["widgets"].extend(list(map(lambda w: w.serialize(), widgets)))

    except Exception as e:
        logging.error(f"exception in create_infographics_data:{e}:{traceback.format_exc()}")
        output = {}
    return output


def get_infographics_data(news_flash_id, years_ago, lang: str) -> Dict:
    request_params = get_request_params(news_flash_id, years_ago, lang)
    if os.environ.get("FLASK_ENV") == "development":
        output = create_infographics_items(request_params)
    else:
        try:
            output = infographics_data_cache_updater.get_infographics_data_from_cache(
                news_flash_id, years_ago
            )
        except Exception as e:
            logging.error(
                f"Exception while retrieving from infographics cache({news_flash_id},{years_ago})"
                f":cause:{e.__cause__}, class:{e.__class__}"
            )
            output = {}
    if not output:
        logging.error(f"infographics_data({news_flash_id}, {years_ago}) not found in cache")
    elif "widgets" not in output:
        logging.error(f"get_infographics_data: 'widgets' key missing from output:{output}")
    else:
        output["widgets"] = localize_after_cache(request_params, output["widgets"])
    return output


def localize_after_cache(request_params: RequestParams, items_list: List[Dict]) -> List[Dict]:
    res = []
    for items in items_list:
        if "name" in items:
            res.append(
                get_widget_class_by_name(items["name"]).localize_items(request_params, items)
            )
        else:
            logging.error(f"localize_after_cache: bad input (missing 'name' key):{items}")
        items["meta"]["information"] = _(items.get("meta", {}).get("information", ""))
    return res


def is_urban(request_params: RequestParams) -> bool:
    return (
        request_params is not None
        and "yishuv_name" in request_params.location_info
        and "street1_hebrew" in request_params.location_info
    )


def is_sub_urban(request_params: RequestParams) -> bool:
    return (
        request_params is not None
        and "road1" in request_params.location_info
        and "road_segment_name" in request_params.location_info
    )


def is_news_flash_resolution_supported(news_flash_obj: NewsFlash) -> bool:
    location_data = extract_news_flash_location(news_flash_obj)
    if location_data is None or location_data["data"]["resolution"] is None:
        return False
    location = location_data["data"]
    for cat in BE_CONST.SUPPORTED_RESOLUTIONS:
        if cat.value in resolution_dict and set(resolution_dict[cat.value]) <= location.keys():
            return True
    return False


def get_infographics_mock_data():
    mock_data = {"meta": None, "widgets": []}
    widgets_path = os.path.join("static", "data", "widgets")
    meta_path = os.path.join("static", "data", "widgets_meta")

    assert len(os.listdir(meta_path)) == 1

    meta_file = os.listdir(meta_path)[0]
    with open(os.path.join(meta_path, meta_file)) as f:
        mock_data["meta"] = json.loads(f.read())

    for file in os.listdir(widgets_path):
        with open(os.path.join(widgets_path, file)) as f:
            widget = json.loads(f.read())
            mock_data["widgets"].append(widget)
    mock_data["widgets"] = sorted(mock_data["widgets"], key=lambda widget: widget["meta"]["rank"])
    return mock_data
