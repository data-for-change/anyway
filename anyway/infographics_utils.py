# -*- coding: utf-8 -*-
import time
import logging
import datetime
import json
import os
from typing import Optional, Dict, List, Callable
import traceback

import pandas as pd
from collections import defaultdict

from sqlalchemy import func

# noinspection PyProtectedMember
from flask_babel import _

from anyway.RequestParams import RequestParams
from anyway.backend_constants import BE_CONST, AccidentType
from anyway.models import NewsFlash, AccidentMarkerView
from anyway.parsers import resolution_dict
from anyway.app_and_db import db
from anyway.infographics_dictionaries import head_on_collisions_comparison_dict
from anyway.parsers import infographics_data_cache_updater
from anyway.parsers.location_extraction import get_road_segment_name_and_number
from anyway.widgets import Widget

# We need to import the modules, which in turn imports all the widgets, and registers them, even if they are not explicitly used here
# pylint: disable=unused-import
import anyway.widgets.urban_widgets
import anyway.widgets.suburban_widgets
# pylint: enable=unused-import

def get_widget_factories() -> List[Callable[[RequestParams], type(Widget)]]:
    """Returns list of callables that generate all widget instances"""
    return list(Widget.widgets_dict.values())


def get_widget_class_by_name(name: str) -> type(Widget):
    return Widget.widgets_dict[name]


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
            if isinstance(curr_field, float):
                curr_field = int(curr_field)
            data[field] = curr_field
    gps = {"lat": news_flash_obj.lat, "lon": news_flash_obj.lon}
    return {"name": "location", "data": data, "gps": gps}


def extract_road_segment_location(road_segment_id):
    data = {"resolution": "interurban_road_segment"}
    road1, road_segment_name = get_road_segment_name_and_number(road_segment_id)
    data["road1"] = int(road1)
    data["road_segment_name"] = road_segment_name
    # fake gps - todo: fix
    gps = {"lat": 32.825610, "lon": 35.165395}
    return {"name": "location", "data": data, "gps": gps}


# count of dead and severely injured


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


# generate text describing location or road segment of news flash
# to be used by most severe accidents additional info widget
def get_road_segment_location_text(road1, road_segment_name):
    res = "כביש " + str(road1) + " במקטע " + road_segment_name
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


# noinspection PyArgumentList
def generate_widgets(request_params: RequestParams, to_cache: bool = True) -> List[type(Widget)]:
    widgets = []
    # noinspection PyArgumentList
    for w in Widget.widgets_dict.values():
        if w.is_relevant(request_params) and w.is_in_cache() == to_cache:
            widget: Widget = w(request_params)
            widgets.append(widget)
            logging.debug(f"name:{widget.name}, class:{get_widget_class_by_name(widget.name)}")
    for w in widgets:
        print(w.name)
        try:
            w.generate_items()
        except Exception as e:
            print(e)
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


def get_request_params_for_road_segment(
    road_segment_id: int, number_of_years_ago: int, lang: str
) -> Optional[RequestParams]:
    try:
        number_of_years_ago = int(number_of_years_ago)
    except ValueError:
        return None
    if number_of_years_ago < 0 or number_of_years_ago > 100:
        return None
    location_info = extract_road_segment_location(road_segment_id)
    if location_info is None:
        return None
    logging.debug("location_info:{}".format(location_info))
    location_text = get_road_segment_location_text(
        location_info["data"]["road1"], location_info["data"]["road_segment_name"]
    )
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
        news_flash_obj=None,
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


def create_infographics_data_for_road_segment(
    road_segment_id, number_of_years_ago, lang: str
) -> str:
    request_params = get_request_params_for_road_segment(road_segment_id, number_of_years_ago, lang)
    output = create_infographics_items(request_params)
    return json.dumps(output, default=str)


def create_infographics_items(request_params: RequestParams) -> Dict:
    def get_dates_comment():
        return {
            "date_range": [request_params.start_time.year, request_params.end_time.year],
            "last_update": time.mktime(request_params.end_time.timetuple()),
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
            "dates_comment": get_dates_comment(),
        }
        output["widgets"] = []
        widgets: List[type(Widget)] = generate_widgets(request_params=request_params, to_cache=True)
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


def get_infographics_data_for_road_segment(road_segment_id, years_ago, lang: str) -> Dict:
    request_params = get_request_params_for_road_segment(road_segment_id, years_ago, lang)
    if os.environ.get("FLASK_ENV") == "development":
        output = create_infographics_items(request_params)
    else:
        try:
            output = infographics_data_cache_updater.get_infographics_data_from_cache_by_road_segment(
                road_segment_id, years_ago
            )
        except Exception as e:
            logging.error(
                f"Exception while retrieving from infographics cache({road_segment_id},{years_ago})"
                f":cause:{e.__cause__}, class:{e.__class__}"
            )
            output = {}
    if not output:
        logging.error(f"infographics_data({road_segment_id}, {years_ago}) not found in cache")
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
