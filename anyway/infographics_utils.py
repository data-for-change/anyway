# -*- coding: utf-8 -*-
import logging
import datetime
import json
import os
from functools import lru_cache

import pandas as pd
from collections import defaultdict
from sqlalchemy import func
from sqlalchemy import cast, Numeric
from sqlalchemy import desc
from flask_babel import _
from anyway.backend_constants import BE_CONST
from anyway.models import NewsFlash, AccidentMarkerView, InvolvedMarkerView, RoadSegments
from anyway.parsers import resolution_dict
from anyway.app_and_db import db
from anyway.infographics_dictionaries import (
    driver_type_hebrew_dict,
    head_on_collisions_comparison_dict,
    english_accident_severity_dict,
)
from anyway.parsers import infographics_data_cache_updater
from anyway.constants import CONST

"""
    Widget structure:
    {
        'name': str,
        'data': {
                 'items': list (Array) | dictionary (Object),
                 'text': dictionary (Object) - can be empty
                 },
        'meta': {
                 'rank': int (Integer)
                 }
    }
"""


class Widget:
    def __init__(self, name, rank, items, text=None, meta=None):
        self.name = name
        self.rank = rank
        self.items = items
        self.text = text
        self.meta = meta

    def serialize(self):
        output = {}
        output["name"] = self.name
        output["data"] = {}
        output["data"]["items"] = self.items
        if self.text:
            output["data"]["text"] = self.text
        if self.meta:
            output["meta"] = self.meta
        else:
            output["meta"] = {}
        output["meta"]["rank"] = self.rank
        return output


def extract_news_flash_location(news_flash_id):
    news_flash_obj = db.session.query(NewsFlash).filter(NewsFlash.id == news_flash_id).first()
    if not news_flash_obj:
        logging.warning(f"could not find news flash id {str(news_flash_id)}")
        return None
    resolution = news_flash_obj.resolution if news_flash_obj.resolution else None
    if not news_flash_obj or not resolution or resolution not in resolution_dict:
        logging.warning(f"could not find valid resolution for news flash id {str(news_flash_id)}")
        return None
    data = {"resolution": resolution}
    for field in resolution_dict[resolution]:
        curr_field = getattr(news_flash_obj, field)
        if curr_field is not None:
            data[field] = curr_field
    gps = {}
    for field in ["lon", "lat"]:
        gps[field] = getattr(news_flash_obj, field)
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


def get_top_road_segments_accidents_per_km(
    resolution, location_info, start_time=None, end_time=None, limit=3
):
    if resolution != "כביש בינעירוני":  # relevent for non urban roads only
        return {}

    query = get_query(
        table_obj=AccidentMarkerView, filters=None, start_time=start_time, end_time=end_time
    )

    query = (
        query.with_entities(
            AccidentMarkerView.road_segment_name,
            func.count(AccidentMarkerView.road_segment_name).label("total_accidents"),
            (RoadSegments.to_km - RoadSegments.from_km).label("segment_length"),
            cast(
                (
                    func.count(AccidentMarkerView.road_segment_name)
                    / (RoadSegments.to_km - RoadSegments.from_km)
                ),
                Numeric(10, 4),
            ).label("accidents_per_km"),
        )
        .filter(AccidentMarkerView.road1 == RoadSegments.road)
        .filter(AccidentMarkerView.road_segment_number == RoadSegments.segment)
        .filter(AccidentMarkerView.road1 == location_info["road1"])
        .filter(AccidentMarkerView.road_segment_name is not None)
        .group_by(AccidentMarkerView.road_segment_name, RoadSegments.from_km, RoadSegments.to_km)
        .order_by(desc("accidents_per_km"))
        .limit(limit)
    )

    result = pd.read_sql_query(query.statement, query.session.bind)
    return result.to_dict(orient="records")  # pylint: disable=no-member


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
        query = query.group_by(group_by)
        query = query.with_entities(group_by, func.count(count))
    df = pd.read_sql_query(query.statement, query.session.bind)
    df.rename(columns={"count_1": "count"}, inplace=True)  # pylint: disable=no-member
    df.columns = [c.replace("_hebrew", "") for c in df.columns]
    return (  # pylint: disable=no-member
        df.to_dict(orient="records") if group_by or count else df.to_dict()
    )


def get_injured_filters(location_info):
    new_filters = {}
    for curr_filter, curr_values in location_info.items():
        if curr_filter in ["region_hebrew", "district_hebrew", "district_hebrew", "yishuv_name"]:
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
    query = get_query(table_obj, filters, start_time, end_time)
    query = query.with_entities(*entities)
    query = query.order_by(
        getattr(table_obj, "accident_severity"), getattr(table_obj, "accident_timestamp").desc()
    )
    query = query.limit(limit)
    df = pd.read_sql_query(query.statement, query.session.bind)
    df.columns = [c.replace("_hebrew", "") for c in df.columns]
    return df.to_dict(orient="records")  # pylint: disable=no-member


def get_most_severe_accidents(table_obj, filters, start_time, end_time, limit=10):
    entities = (
        "longitude",
        "latitude",
        "accident_severity_hebrew",
        "accident_timestamp",
        "accident_type_hebrew",
    )
    return get_most_severe_accidents_with_entities(
        table_obj, filters, entities, start_time, end_time, limit
    )


def get_accidents_heat_map(table_obj, filters, start_time, end_time):
    filters = filters or {}
    filters["provider_code"] = [
        BE_CONST.CBS_ACCIDENT_TYPE_1_CODE,
        BE_CONST.CBS_ACCIDENT_TYPE_3_CODE,
    ]
    query = get_query(table_obj, filters, start_time, end_time)
    query = query.with_entities("longitude", "latitude")
    df = pd.read_sql_query(query.statement, query.session.bind)
    return df.to_dict(orient="records")  # pylint: disable=no-member


def filter_and_group_injured_count_per_age_group(data_of_ages):
    import re

    range_dict = {0: 14, 15: 24, 25: 64, 65: 200}
    dict_by_required_age_group = defaultdict(int)

    for age_range_and_count in data_of_ages:
        age_range = age_range_and_count["age_group"]
        count = age_range_and_count["count"]

        # Parse the db age range
        match_parsing = re.match("([0-9]{2})\\-([0-9]{2})", age_range)
        if match_parsing:
            regex_age_matches = match_parsing.groups()
            if len(regex_age_matches) != 2:
                dict_by_required_age_group["unknown"] += count
                continue
            min_age_raw, max_age_raw = regex_age_matches
        else:
            match_parsing = re.match("([0-9]{2})\\+", age_range)  # e.g  85+
            if match_parsing:
                # We assume that no body live beyond age 200
                min_age_raw, max_age_raw = match_parsing.group(1), 200
            else:
                dict_by_required_age_group["unknown"] += count
                continue

        # Find to what "bucket" to aggregate the data
        min_age = int(min_age_raw)
        max_age = int(max_age_raw)
        for item in range_dict.items():
            item_min_range, item_max_range = item
            if (
                item_min_range <= min_age <= item_max_range
                and item_min_range <= max_age <= item_max_range
            ):
                string_age_range = f"{item_min_range:02}-{item_max_range:02}"
                dict_by_required_age_group[string_age_range] += count
                break

    # Rename the last key
    dict_by_required_age_group["65+"] = dict_by_required_age_group["65-200"]
    del dict_by_required_age_group["65-200"]

    # Modify return value to wanted format
    items = []
    for key in dict_by_required_age_group:
        items.append({"age_group": key, "count": dict_by_required_age_group[key]})

    return items


def get_most_severe_accidents_table_title(location_info):
    return "תאונות בסדר חומרה יורד במקטע " + location_info["road_segment_name"]


def get_heat_map_title(location_info):
    return "מוקדי תאונות קטלניות וקשות במקטע " + location_info["road_segment_name"]


def get_accident_count_by_severity(location_info, location_text, start_time, end_time):
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
    items["start_year"] = start_year
    items["end_year"] = end_year
    items["total_accidents_count"] = total_accidents_count
    return items


def get_most_severe_accidents_table(location_info, start_time, end_time):
    entities = (
        "id",
        "provider_code",
        "accident_timestamp",
        "accident_type_hebrew",
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
        accident["type"] = accident["accident_type"]
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
        accident["accident_severity"] = english_accident_severity_dict[
            accident["accident_severity"]
        ]
    return accidents


def count_accidents_by_driver_type(data):
    driver_types = defaultdict(int)
    for item in data:
        vehicle_type, count = item["involve_vehicle_type"], int(item["count"])
        if vehicle_type in BE_CONST.PROFESSIONAL_DRIVER_VEHICLE_TYPES:
            driver_types[driver_type_hebrew_dict["professional_driver"]] += count
        elif vehicle_type in BE_CONST.PRIVATE_DRIVER_VEHICLE_TYPES:
            driver_types[driver_type_hebrew_dict["private_vehicle_driver"]] += count
        elif (
            vehicle_type in BE_CONST.LIGHT_ELECTRIC_VEHICLE_TYPES
            or vehicle_type in BE_CONST.OTHER_VEHICLES_TYPES
        ):
            driver_types[driver_type_hebrew_dict["other_driver"]] += count
    output = []
    for driver_type, count in driver_types.items():
        output.append({"driver_type": driver_type, "count": count})
    return output


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
def get_news_flash_location_text(news_flash_id):
    news_flash_item = db.session.query(NewsFlash).filter(NewsFlash.id == news_flash_id).first()
    nf = news_flash_item.serialize()
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
        if key == head_on_collisions_comparison_dict["head_to_head_collision"]:
            data_list.append(
                {"desc": head_on_collisions_comparison_dict["head_to_head"], "count": value}
            )
        else:
            data_list.append({"desc": key, "count": value})

    return data_list


def get_head_to_head_stat(news_flash_id, start_time, end_time):
    news_flash_obj = extract_news_flash_obj(news_flash_id)
    road_data = {}
    filter_dict = {
        "road_type": BE_CONST.ROAD_TYPE_NOT_IN_CITY_NOT_IN_INTERSECTION,
        "accident_severity": BE_CONST.ACCIDENT_SEVERITY_DEADLY,
    }
    all_roads_data = get_accidents_stats(
        table_obj=AccidentMarkerView,
        filters=filter_dict,
        group_by="accident_type_hebrew",
        count="accident_type_hebrew",
        start_time=start_time,
        end_time=end_time,
    )

    if news_flash_obj.road1 and news_flash_obj.road_segment_name:
        filter_dict.update(
            {"road1": news_flash_obj.road1, "road_segment_name": news_flash_obj.road_segment_name}
        )
        road_data = get_accidents_stats(
            table_obj=AccidentMarkerView,
            filters=filter_dict,
            group_by="accident_type_hebrew",
            count="accident_type_hebrew",
            start_time=start_time,
            end_time=end_time,
        )

    road_data_dict = sum_road_accidents_by_specific_type(road_data, "התנגשות חזית בחזית")
    all_roads_data_dict = sum_road_accidents_by_specific_type(all_roads_data, "התנגשות חזית בחזית")

    return {
        "specific_road_segment_fatal_accidents": convert_roads_fatal_accidents_to_frontend_view(
            road_data_dict
        ),
        "all_roads_fatal_accidents": convert_roads_fatal_accidents_to_frontend_view(
            all_roads_data_dict
        ),
    }


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


def percentage_accidents_by_car_type(involved_by_vehicle_type_data):
    driver_types = defaultdict(float)
    total_count = 0
    for item in involved_by_vehicle_type_data:
        vehicle_type, count = item["involve_vehicle_type"], int(item["count"])
        total_count += count
        if vehicle_type in BE_CONST.CAR_VEHICLE_TYPES:
            driver_types["רכב פרטי"] += count
        elif vehicle_type in BE_CONST.LARGE_VEHICLE_TYPES:
            driver_types["מסחרי/משאית"] += count
        elif vehicle_type in BE_CONST.MOTORCYCLE_VEHICLE_TYPES:
            driver_types["אופנוע"] += count
        elif vehicle_type in BE_CONST.BICYCLE_AND_SMALL_MOTOR_VEHICLE_TYPES:
            driver_types["אופניים/קורקינט"] += count
        else:
            driver_types["אחר"] += count

    output = defaultdict(float)
    for k, v in driver_types.items():  # Calculate percentage
        output[k] = 100 * v / total_count

    return output


@lru_cache(maxsize=64)
def percentage_accidents_by_car_type_national_data_cache(start_time, end_time):
    involved_by_vehicle_type_data = get_accidents_stats(
        table_obj=InvolvedMarkerView,
        group_by="involve_vehicle_type",
        count="involve_vehicle_type",
        start_time=start_time,
        end_time=end_time,
    )
    return percentage_accidents_by_car_type(involved_by_vehicle_type_data)


def stats_accidents_by_car_type_with_national_data(
    involved_by_vehicle_type_data, start_time, end_time
):
    out = []
    data_by_segment = percentage_accidents_by_car_type(involved_by_vehicle_type_data)
    national_data = percentage_accidents_by_car_type_national_data_cache(start_time, end_time)

    for k, v in national_data.items():  # pylint: disable=W0612
        out.append(
            {
                "car_type": k,
                "percentage_segment": data_by_segment[k],
                "percentage_country": national_data[k],
            }
        )

    return out


def create_infographics_data(news_flash_id, number_of_years_ago):
    output = {}
    try:
        number_of_years_ago = int(number_of_years_ago)
    except ValueError:
        return {}
    if number_of_years_ago < 0 or number_of_years_ago > 100:
        return {}
    location_info = extract_news_flash_location(news_flash_id)
    if location_info is None:
        return {}
    logging.debug("location_info:{}".format(location_info))
    location_text = get_news_flash_location_text(news_flash_id)
    logging.debug("location_text:{}".format(location_text))
    gps = location_info["gps"]
    location_info = location_info["data"]
    output["meta"] = {"location_info": location_info.copy(), "location_text": location_text}
    output["widgets"] = []
    resolution = location_info.pop("resolution")
    if resolution is None:
        return {}

    if all(value is None for value in location_info.values()):
        return {}

    last_accident_date = get_latest_accident_date(table_obj=AccidentMarkerView, filters=None)
    # converting to datetime object to get the date
    end_time = last_accident_date.to_pydatetime().date()

    start_time = datetime.date(end_time.year + 1 - number_of_years_ago, 1, 1)

    output["meta"]["dates_comment"] = (
        str(start_time.year) + "-" + str(end_time.year) + ", עדכון אחרון: " + str(end_time)
    )

    # accident_severity count
    items = get_accident_count_by_severity(
        location_info=location_info,
        location_text=location_text,
        start_time=start_time,
        end_time=end_time,
    )

    accident_count_by_severity = Widget(name="accident_count_by_severity", rank=1, items=items)
    output["widgets"].append(accident_count_by_severity.serialize())

    # most severe accidents table
    most_severe_accidents_table = Widget(
        name="most_severe_accidents_table",
        rank=2,
        items=get_most_severe_accidents_table(location_info, start_time, end_time),
        text={"title": get_most_severe_accidents_table_title(location_info)},
    )
    output["widgets"].append(most_severe_accidents_table.serialize())

    # most severe accidents
    most_severe_accidents = Widget(
        name="most_severe_accidents",
        rank=3,
        items=get_most_severe_accidents(
            table_obj=AccidentMarkerView,
            filters=location_info,
            start_time=start_time,
            end_time=end_time,
        ),
    )
    output["widgets"].append(most_severe_accidents.serialize())

    # street view
    street_view = Widget(
        name="street_view", rank=4, items={"longitude": gps["lon"], "latitude": gps["lat"]}
    )
    output["widgets"].append(street_view.serialize())

    # head to head accidents
    head_on_collisions_comparison = Widget(
        name="head_on_collisions_comparison",
        rank=5,
        items=get_head_to_head_stat(
            news_flash_id=news_flash_id, start_time=start_time, end_time=end_time
        ),
        text={"title": "תאונות קטלניות ע״פ סוג"},
    )
    output["widgets"].append(head_on_collisions_comparison.serialize())

    # accident_type count
    accident_count_by_accident_type = Widget(
        name="accident_count_by_accident_type",
        rank=6,
        items=get_accident_count_by_accident_type(
            location_info=location_info, start_time=start_time, end_time=end_time
        ),
    )
    output["widgets"].append(accident_count_by_accident_type.serialize())

    # accidents heat map
    accidents_heat_map_filters = location_info.copy()
    accidents_heat_map_filters["accident_severity"] = [
        CONST.ACCIDENT_SEVERITY_DEADLY,
        CONST.ACCIDENT_SEVERITY_SEVERE,
    ]
    accidents_heat_map = Widget(
        name="accidents_heat_map",
        rank=7,
        items=get_accidents_heat_map(
            table_obj=AccidentMarkerView,
            filters=accidents_heat_map_filters,
            start_time=start_time,
            end_time=end_time,
        ),
        text={"title": get_heat_map_title(location_info)},
    )
    output["widgets"].append(accidents_heat_map.serialize())

    # accident count by accident year
    accident_count_by_accident_year = Widget(
        name="accident_count_by_accident_year",
        rank=8,
        items=get_accidents_stats(
            table_obj=AccidentMarkerView,
            filters=location_info,
            group_by="accident_year",
            count="accident_year",
            start_time=start_time,
            end_time=end_time,
        ),
        text={"title": "כמות התאונות לפי שנה במקטע " + location_info["road_segment_name"]},
    )
    output["widgets"].append(accident_count_by_accident_year.serialize())

    # injured count by accident year
    injured_count_by_accident_year = Widget(
        name="injured_count_by_accident_year",
        rank=9,
        items=get_accidents_stats(
            table_obj=InvolvedMarkerView,
            filters=get_injured_filters(location_info),
            group_by="accident_year",
            count="accident_year",
            start_time=start_time,
            end_time=end_time,
        ),
        text={"title": "נפגעים בתאונות במקטע " + location_info["road_segment_name"]},
    )
    output["widgets"].append(injured_count_by_accident_year.serialize())

    # accident count on day light
    accident_count_by_day_night = Widget(
        name="accident_count_by_day_night",
        rank=10,
        items=get_accidents_stats(
            table_obj=AccidentMarkerView,
            filters=location_info,
            group_by="day_night_hebrew",
            count="day_night_hebrew",
            start_time=start_time,
            end_time=end_time,
        ),
        text={"title": "כמות תאונות ביום ובלילה"},
    )
    output["widgets"].append(accident_count_by_day_night.serialize())

    # accidents distribution count by hour
    accidents_count_by_hour = Widget(
        name="accidents_count_by_hour",
        rank=11,
        items=get_accidents_stats(
            table_obj=AccidentMarkerView,
            filters=location_info,
            group_by="accident_hour",
            count="accident_hour",
            start_time=start_time,
            end_time=end_time,
        ),
        text={"title": "כמות תאונות לפי שעה"},
    )
    output["widgets"].append(accidents_count_by_hour.serialize())

    # accident count by road_segment
    top_road_segments_accidents_per_km = Widget(
        name="top_road_segments_accidents_per_km",
        rank=13,
        items=get_top_road_segments_accidents_per_km(
            resolution=resolution,
            location_info=location_info,
            start_time=start_time,
            end_time=end_time,
        ),
        text={"title": "תאונות לכל ק״מ כביש על פי מקטע בכביש " + str(int(location_info["road1"]))},
    )
    output["widgets"].append(top_road_segments_accidents_per_km.serialize())

    # injured count per age group
    data_of_injured_count_per_age_group_raw = get_accidents_stats(
        table_obj=InvolvedMarkerView,
        filters=get_injured_filters(location_info),
        group_by="age_group_hebrew",
        count="age_group_hebrew",
        start_time=start_time,
        end_time=end_time,
    )
    data_of_injured_count_per_age_group = filter_and_group_injured_count_per_age_group(
        data_of_injured_count_per_age_group_raw
    )
    injured_count_per_age_group = Widget(
        name="injured_count_per_age_group", rank=14, items=data_of_injured_count_per_age_group
    )
    output["widgets"].append(injured_count_per_age_group.serialize())

    # vision zero
    vision_zero = Widget(name="vision_zero", rank=15, items=["vision_zero_2_plus_1"])
    output["widgets"].append(vision_zero.serialize())

    # involved by driver type
    involved_by_vehicle_type_data = get_accidents_stats(
        table_obj=InvolvedMarkerView,
        filters=get_injured_filters(location_info),
        group_by="involve_vehicle_type",
        count="involve_vehicle_type",
        start_time=start_time,
        end_time=end_time,
    )
    accident_count_by_driver_type = Widget(
        name="accident_count_by_driver_type",
        rank=16,
        items=count_accidents_by_driver_type(involved_by_vehicle_type_data),
        text={"title": "מעורבות נהגים בתאונות לפי סוג במקטע " + location_info["road_segment_name"]},
    )
    output["widgets"].append(accident_count_by_driver_type.serialize())

    # involved by car type
    accident_count_by_car_type = Widget(
        name="accident_count_by_car_type",
        rank=17,
        items=stats_accidents_by_car_type_with_national_data(
            involved_by_vehicle_type_data, start_time, end_time
        ),
        text={
            "title": "השוואת אחוז הרכבים בתאונות במקטע "
            + location_info["road_segment_name"]
            + " לעומת ממוצע ארצי"
        },
    )
    output["widgets"].append(accident_count_by_car_type.serialize())

    def injured_accidents_with_pedestrians_mock_data():  # Temporary for Frontend
        return [
            {
                "year": 2009,
                "light_injury_severity_text": "פצוע קל",
                "light_injury_severity_count": 12,
                "severe_injury_severity_text": "פצוע קשה",
                "severe_injury_severity_count": 3,
                "killed_injury_severity_text": "הרוג",
                "killed_injury_severity_count": 0,
            },
            {
                "year": 2010,
                "light_injury_severity_text": "פצוע קל",
                "light_injury_severity_count": 24,
                "severe_injury_severity_text": "פצוע קשה",
                "severe_injury_severity_count": 0,
                "killed_injury_severity_text": "הרוג",
                "killed_injury_severity_count": 1,
            },
            {
                "year": 2011,
                "light_injury_severity_text": "פצוע קל",
                "light_injury_severity_count": 9,
                "severe_injury_severity_text": "פצוע קשה",
                "severe_injury_severity_count": 2,
                "killed_injury_severity_text": "הרוג",
                "killed_injury_severity_count": 1,
            },
            {
                "year": 2012,
                "light_injury_severity_text": "פצוע קל",
                "light_injury_severity_count": 21,
                "severe_injury_severity_text": "פצוע קשה",
                "severe_injury_severity_count": 2,
                "killed_injury_severity_text": "הרוג",
                "killed_injury_severity_count": 4,
            },
            {
                "year": 2013,
                "light_injury_severity_text": "פצוע קל",
                "light_injury_severity_count": 21,
                "severe_injury_severity_text": "פצוע קשה",
                "severe_injury_severity_count": 2,
                "killed_injury_severity_text": "הרוג",
                "killed_injury_severity_count": 4,
            },
            {
                "year": 2014,
                "light_injury_severity_text": "פצוע קל",
                "light_injury_severity_count": 10,
                "severe_injury_severity_text": "פצוע קשה",
                "severe_injury_severity_count": 0,
                "killed_injury_severity_text": "הרוג",
                "killed_injury_severity_count": 1,
            },
            {
                "year": 2015,
                "light_injury_severity_text": "פצוע קל",
                "light_injury_severity_count": 13,
                "severe_injury_severity_text": "פצוע קשה",
                "severe_injury_severity_count": 2,
                "killed_injury_severity_text": "הרוג",
                "killed_injury_severity_count": 0,
            },
        ]

    injured_accidents_with_pedestrians = Widget(
        name="injured_accidents_with_pedestrians",
        rank=18,
        items=injured_accidents_with_pedestrians_mock_data(),
        text={"title": "נפגעים הולכי רגל ברחוב ז׳בוטינסקי, פתח תקווה"},
    )
    output["widgets"].append(injured_accidents_with_pedestrians.serialize())

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

    injury_severity_by_cross_location = Widget(
        name="injury_severity_by_cross_location",
        rank=19,
        items=injury_severity_by_cross_location_mock_data(),
        text={"title": "הולכי רגל הרוגים ופצועים קשה ברחוב בן יהודה, תל אביב"},
    )
    output["widgets"].append(injury_severity_by_cross_location.serialize())

    def motorcycle_accidents_vs_all_accidents_mock_data():  # Temporary for Frontend
        return [
            {"location": "כביש 20", "vehicle": "אופנוע", "percentage": 0.50},
            {"location": "כביש 20", "vehicle": "אחר", "percentage": 0.50},
            {"location": "כל הארץ", "vehicle": "אחר", "percentage": 0.80},
            {"location": "כל הארץ", "vehicle": "אופנוע", "percentage": 0.20},
        ]

    motorcycle_accidents_vs_all_accidents = Widget(
        name="motorcycle_accidents_vs_all_accidents",
        rank=20,
        items=motorcycle_accidents_vs_all_accidents_mock_data(),
        text={"title": "תאונות אופנועים קשות וקטלניות בכביש 20 בהשוואה לכל הארץ"},
    )
    output["widgets"].append(motorcycle_accidents_vs_all_accidents.serialize())

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

    accidents_count_pedestrians_per_vehicle_street_vs_all = Widget(
        name="accidents_count_pedestrians_per_vehicle_street_vs_all",
        rank=21,
        items=accidents_count_pedestrians_per_vehicle_street_vs_all_mock_data(),
        text={
            "title": _(
                "Pedestrian Injuries on Ben Yehuda Street in Tel Aviv by Type of hitting Vehicle, Compared to Urban Accidents Across the country"
            )
        },
    )
    output["widgets"].append(accidents_count_pedestrians_per_vehicle_street_vs_all.serialize())

    def top_road_segments_accidents_mock_data():  # Temporary for Frontend
        return [
            {"segment name": "מחלף לה גרדיה - מחלף השלום", "count": 70},
            {"segment name": "מחלף השלום - מחלף הרכבת", "count": 48},
            {"segment name": "מחלף וולפסון - מחלף חולון", "count": 48},
            {"segment name": "מחלף קוממיות - מחלף יוספטל", "count": 34},
            {"segment name": "מחלף ההלכה - מחלף רוקח ", "count": 31},
        ]

    top_road_segments_accidents = Widget(
        name="top_road_segments_accidents",
        rank=22,
        items=top_road_segments_accidents_mock_data(),
        text={"title": "5 המקטעים עם כמות התאונות הגדולה ביותר"},
    )
    output["widgets"].append(top_road_segments_accidents.serialize())

    def pedestrian_injured_in_junctions_mock_data():  # Temporary for Frontend
        return [
            {"street name": "גורדון י ל", "count": 18},
            {"street name": "אידלסון אברהם", "count": 10},
            {"street name": "פרישמן", "count": 7},
        ]

    pedestrian_injured_in_junctions = Widget(
        name="pedestrian_injured_in_junctions",
        rank=23,
        items=pedestrian_injured_in_junctions_mock_data(),
        text={"title": "מספר נפגעים הולכי רגל בצמתים - רחוב בן יהודה, תל אביב"},
    )
    output["widgets"].append(pedestrian_injured_in_junctions.serialize())

    return json.dumps(output, default=str)


def get_infographics_data(news_flash_id, years_ago):
    if os.environ.get("FLASK_ENV") == "development":
        return create_infographics_data(news_flash_id, years_ago)
    else:
        try:
            res = infographics_data_cache_updater.get_infographics_data_from_cache(
                news_flash_id, years_ago
            )
        except Exception as e:
            logging.error(
                f"Exception while retrieving from infographics cache({news_flash_id},{years_ago})"
                f":cause:{e.__cause__}, class:{e.__class__}"
            )
            res = {}
        if not res:
            logging.error(f"infographics_data({news_flash_id}, {years_ago}) not found in cache")
        return res
