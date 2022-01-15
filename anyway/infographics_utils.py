# -*- coding: utf-8 -*-
import logging
import datetime
import json
import os
import traceback

from typing import Optional, Dict, List, Callable, Type
from collections import defaultdict

# noinspection PyProtectedMember
from flask_babel import _

from anyway.request_params import (
    RequestParams,
    get_news_flash_location_text,
    get_road_segment_location_text,
    extract_road_segment_location,
    extract_news_flash_obj,
    get_latest_accident_date,
    extract_news_flash_location,
    get_request_params_from_request_values,
)
from anyway.constants.backend_constants import BackEndConstants
from anyway.constants.accident_type import AccidentType
from anyway.models import NewsFlash, AccidentMarkerView
from anyway.parsers import resolution_dict
from anyway.infographics_dictionaries import head_on_collisions_comparison_dict
from anyway.parsers import infographics_data_cache_updater
from anyway.widgets.widget import Widget, widgets_dict

logger = logging.getLogger("infographics_utils")

# We need to import the modules, which in turn imports all the widgets, and registers them, even if they are not
# explicitly used here
# pylint: disable=unused-import
import anyway.widgets.urban_widgets
import anyway.widgets.suburban_widgets


# pylint: enable=unused-import


def get_widget_factories() -> List[Callable[[RequestParams], Type[Widget]]]:
    """Returns list of callables that generate all widget instances"""
    return list(widgets_dict.values())


def get_widget_class_by_name(name: str) -> Type[Widget]:
    return widgets_dict[name]


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


# noinspection PyArgumentList
def generate_widgets(request_params: RequestParams, to_cache: bool = True) -> List[Type[Widget]]:
    widgets = []
    # noinspection PyArgumentList
    for w in widgets_dict.values():
        if w.is_relevant(request_params) and w.is_in_cache() == to_cache:
            widget: Widget = w(request_params)
            widgets.append(widget)
            logging.debug(f"name:{widget.name}, class:{get_widget_class_by_name(widget.name)}")
    for w in widgets:
        try:
            logger.info(f"Generating items for : {w.name}")
            w.generate_items()
        except Exception as e:
            logger.error(f"Encountered error when generating items for {w.name} : {e}")
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
        years_ago=number_of_years_ago,
        location_text=location_text,
        location_info=location_info,
        # TODO: getting a warning on resolution=resolution: "Expected type 'dict', got 'int' instead"
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
        years_ago=number_of_years_ago,
        location_text=location_text,
        location_info=location_info,
        # TODO: getting a warning on resolution=resolution: "Expected type 'dict', got 'int' instead"
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


def create_infographics_data_for_location(vals: dict) -> str:
    logger.debug(f"create_infographics_data_for_location({vals})")
    try:
        request_params = get_request_params_from_request_values(vals)
        output = create_infographics_items(request_params)
    except Exception as e:
        logger.exception(
            f"Exception while creating infographics items({vals})"
            f":cause:{e.__cause__}, class:{e.__class__}"
        )
        output = {}
    return json.dumps(output, default=str)


def create_infographics_items(request_params: RequestParams) -> Dict:
    def get_dates_comment():
        return {
            "date_range": [request_params.start_time.year, request_params.end_time.year],
            "last_update": datetime.datetime.fromordinal(
                request_params.end_time.toordinal()
            ).isoformat(),
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
        widgets: List[Type[Widget]] = generate_widgets(request_params=request_params, to_cache=True)
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
            output = (
                infographics_data_cache_updater.get_infographics_data_from_cache_by_road_segment(
                    road_segment_id, years_ago
                )
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


def get_infographics_data_for_location(request_params: RequestParams) -> Dict:
    if os.environ.get("FLASK_ENV") == "development":
        output = create_infographics_items(request_params)
    else:
        try:
            output = infographics_data_cache_updater.get_infographics_data_from_cache_by_location(
                request_params
            )
        except Exception as e:
            logging.error(
                f"Exception while retrieving from infographics cache({request_params})"
                f":cause:{e.__cause__}, class:{e.__class__}"
            )
            output = {}
    if not output:
        logging.error(f"infographics_data({request_params}) not found in cache")
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
    for cat in BackEndConstants.SUPPORTED_RESOLUTIONS:
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
