import datetime
from dataclasses import dataclass
from typing import Dict, Any, Optional
import logging
import copy
from sqlalchemy import func
import pandas as pd

from anyway.models import NewsFlash, AccidentMarkerView, City, Streets
from anyway.parsers.location_extraction import (
    get_road_segment_name_and_number,
    get_road_segment_by_name_and_road,
)
from anyway.backend_constants import BE_CONST
from anyway.app_and_db import db
from anyway.parsers import resolution_dict


LocationInfo = Dict[str, Any]


@dataclass
class RequestParams:
    """
    Input for infographics data generation, per api call
    """

    years_ago: int
    location_text: str
    location_info: LocationInfo
    resolution: BE_CONST.ResolutionCategories
    gps: Dict
    start_time: datetime.date
    end_time: datetime.date
    lang: str
    news_flash_description: Optional[str]

    def __str__(self):
        return (
            f"RequestParams(res:{self.resolution}, location:{self.location_info},"
            f"start_time:{self.start_time}, "
            f"end_time:{self.end_time}, lang:{self.lang})"
            f"location_text:{self.location_text}"
        )


# todo: merge with get_request_params()
def get_request_params_from_request_values(vals: dict) -> Optional[RequestParams]:
    news_flash_description = get_news_flash_description_from_request_values(vals)
    location = get_location_from_request_values(vals)
    if location is None:
        return None
    years_ago = vals.get("years_ago", BE_CONST.DEFAULT_NUMBER_OF_YEARS_AGO)
    lang = vals.get("lang", "he")
    location_text = location["text"]
    gps = location["gps"]
    location_info = location["data"]

    if location_info is None:
        return None
    logging.debug("location_info:{}".format(location_info))
    logging.debug("location_text:{}".format(location_text))
    resolution = location_info.pop("resolution")
    if resolution is None or resolution not in BE_CONST.SUPPORTED_RESOLUTIONS:
        logging.error(f"Resolution empty or not supported: {resolution}.")
        return None

    if all(value is None for value in location_info.values()):
        return None

    try:
        years_ago = int(years_ago)
    except (ValueError, TypeError):
        return None
    if years_ago < 0 or years_ago > 100:
        return None
    last_accident_date = get_latest_accident_date(table_obj=AccidentMarkerView, filters=None)
    # converting to datetime object to get the date
    end_time = last_accident_date.to_pydatetime().date()

    start_time = datetime.date(end_time.year + 1 - years_ago, 1, 1)

    request_params = RequestParams(
        years_ago=years_ago,
        location_text=location_text,
        location_info=location_info,
        # TODO: getting a warning on resolution=resolution: "Expected type 'dict', got 'int' instead"
        resolution=resolution,
        gps=gps,
        start_time=start_time,
        end_time=end_time,
        lang=lang,
        news_flash_description=news_flash_description
    )
    logging.debug(f"Ending get_request_params. params: {request_params}")
    return request_params

def get_news_flash_description_from_request_values(vals: dict) -> str:
    news_flash_id = vals.get("news_flash_id")
    if news_flash_id is None:
        return None
    news_flash = extract_news_flash_obj(news_flash_id)
    if news_flash is None:
        return None
    return news_flash.description

def get_location_from_request_values(vals: dict) -> Optional[dict]:
    news_flash_id = vals.get("news_flash_id")
    if news_flash_id is not None:
        return get_location_from_news_flash(news_flash_id)
    road_segment_id = vals.get("road_segment_id")
    if road_segment_id is not None:
        return extract_road_segment_location(road_segment_id)
    if ("yishuv_name" in vals or "yishuv_symbol" in vals) and (
        "street1" in vals or "street1_hebrew" in vals
    ):
        return extract_street_location(vals)
    logging.error(f"Unsupported location:{vals.values()}")
    return None


def get_location_from_news_flash(news_flash_id: str) -> Optional[dict]:
    news_flash = extract_news_flash_obj(news_flash_id)
    if news_flash is None:
        return None
    loc = extract_news_flash_location(news_flash)
    if loc is None:
        return None
    res = loc["data"]["resolution"]
    loc["data"]["resolution"] = BE_CONST.ResolutionCategories(res)
    loc["text"] = get_news_flash_location_text(news_flash)
    add_numeric_field_values(loc, news_flash)
    return loc


def add_numeric_field_values(loc: dict, news_flash: NewsFlash) -> None:
    if loc["data"]["resolution"] == BE_CONST.ResolutionCategories.STREET:
        if "yishuv_symbol" not in loc["data"]:
            loc["data"]["yishuv_symbol"] = City.get_symbol_from_name(loc["data"]["yishuv_name"])
        if "street1" not in loc["data"]:
            loc["data"]["street1"] = Streets.get_street_by_street_name(
                loc["data"]["yishuv_symbol"], loc["data"]["street1_hebrew"]
            )
    elif loc["data"]["resolution"] == BE_CONST.ResolutionCategories.SUBURBAN_ROAD:
        if "road_segment_id" not in loc["data"]:
            segment = get_road_segment_by_name_and_road(
                loc["data"]["road_segment_name"], loc["data"]["road1"]
            )
            loc["data"]["road_segment_id"] = segment.segment_id


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
        res = get_street_location_text(yishuv_name, street1_hebrew)
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
def get_road_segment_location_text(road1: int, road_segment_name: str):
    res = "כביש " + str(int(road1)) + " במקטע " + road_segment_name
    return res


def get_street_location_text(yishuv_name, street1_hebrew):
    return "רחוב " + street1_hebrew + " ב" + yishuv_name


def extract_road_segment_location(road_segment_id):
    data = {"resolution": BE_CONST.ResolutionCategories.SUBURBAN_ROAD}
    road1, road_segment_name = get_road_segment_name_and_number(road_segment_id)
    data["road1"] = int(road1)
    data["road_segment_name"] = road_segment_name
    data["road_segment_id"] = road_segment_id
    text = get_road_segment_location_text(road1, road_segment_name)
    # fake gps - todo: fix
    gps = {"lat": 32.825610, "lon": 35.165395}
    return {"name": "location", "data": data, "gps": gps, "text": text}


# todo: fill both codes and names into location
def extract_street_location(input_vals: dict):
    vals = fill_missing_street_values(input_vals)
    # noinspection PyDictCreation
    data = {"resolution": BE_CONST.ResolutionCategories.STREET}
    for k in ["yishuv_name", "yishuv_symbol", "street1", "street1_hebrew"]:
        data[k] = vals[k]
    text = get_street_location_text(vals["yishuv_name"], vals["street1_hebrew"])
    # fake gps - todo: fix
    gps = {"lat": 32.825610, "lon": 35.165395}
    return {"name": "location", "data": data, "gps": gps, "text": text}


def fill_missing_street_values(vals: dict) -> dict:
    res = copy.copy(vals)
    if "yishuv_symbol" in res and "yishuv_name" not in res:
        res["yishuv_name"] = City.get_name_from_symbol(res["yishuv_symbol"])
    else:
        res["yishuv_symbol"] = City.get_symbol_from_name(res["yishuv_name"])
    if "street1" in res and "street1_hebrew" not in res:
        res["street1_hebrew"] = Streets.get_street_name_by_street(
            res["yishuv_symbol"], res["street1"]
        )
    else:
        res["street1"] = Streets.get_street_by_street_name(
            res["yishuv_symbol"], res["street1_hebrew"]
        )
    return res


def extract_news_flash_obj(news_flash_id) -> Optional[NewsFlash]:
    news_flash_obj = db.session.query(NewsFlash).filter(NewsFlash.id == news_flash_id).first()

    if not news_flash_obj:
        logging.warning("Could not find news flash id {}".format(news_flash_id))
        return None

    return news_flash_obj


# gets the latest date an accident has occurred
def get_latest_accident_date(table_obj, filters):
    filters = filters or {}
    filters["provider_code"] = [
        BE_CONST.CBS_ACCIDENT_TYPE_1_CODE,
        BE_CONST.CBS_ACCIDENT_TYPE_3_CODE,
    ]
    query = db.session.query(func.max(table_obj.accident_timestamp))
    df = pd.read_sql_query(query.statement, query.session.bind)
    return (df.to_dict(orient="records"))[0].get("max_1")  # pylint: disable=no-member


def extract_news_flash_location(news_flash_obj: NewsFlash):
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
