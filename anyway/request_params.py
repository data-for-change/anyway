import datetime
from dataclasses import dataclass
from typing import Dict, Any, Optional
import logging
from sqlalchemy import func
import pandas as pd

from anyway.models import NewsFlash, AccidentMarkerView
from anyway.parsers.location_extraction import get_road_segment_name_and_number
from anyway.backend_constants import BE_CONST
from anyway.app_and_db import db
from anyway.parsers import resolution_dict


@dataclass
class RequestParams:
    """
    Input for infographics data generation, per api call
    """

    years_ago: int
    location_text: str
    location_info: Dict[str, Any]
    resolution: BE_CONST.ResolutionCategories
    gps: Dict
    start_time: datetime.date
    end_time: datetime.date
    lang: str

    def __str__(self):
        return (
            f"RequestParams(res:{self.resolution}, location:{self.location_info},"
            f"start_time:{self.start_time}, "
            f"end_time:{self.end_time}, lang:{self.lang})"
            f"location_text:{self.location_text}"
        )


def request_params_from_request_values(vals: dict) -> Optional[RequestParams]:
    location = get_location_from_request_values(vals)
    years_ago = vals.get("years_ago")
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
    except ValueError:
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
    )
    logging.debug(f"Ending get_request_params. params: {request_params}")
    return request_params


def get_location_from_request_values(vals: dict) -> dict:
    news_flash_id = vals.get("news_flash_id")
    if news_flash_id is not None:
        return get_location_from_news_flash(news_flash_id)
    road_segment_id = vals.get("road_segment_id")
    if road_segment_id is not None:
        return extract_road_segment_location(road_segment_id)
    logging.error(f"Unsupported location:{vals}")
    return {}


def get_location_from_news_flash(news_flash_id: str) -> dict:
    news_flash = extract_news_flash_obj(news_flash_id)
    loc = extract_news_flash_location(news_flash)
    res = loc["data"]["resolution"]
    loc["data"]["resolution"] = BE_CONST.ResolutionCategories(res)
    loc["text"] = get_news_flash_location_text(news_flash)
    return loc


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
def get_road_segment_location_text(road1: int, road_segment_name: str):
    res = "כביש " + str(road1) + " במקטע " + road_segment_name
    return res


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


# def get_location_from_road_segment_id(road_segment_id: str) -> dict:
#     loc = extract_road_segment_location(road_segment_id)
#     loc["text"] = get_road_segment_location_text(loc["data"]["road1"],
#                                                  loc["data"]["road_segment_id"])
#     return loc
#
#
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
