# -*- coding: utf-8 -*-

from datetime import datetime
from anyway.models import (
    Base,
    InfographicsDataCache,
    NewsFlash,
    RoadSegments,
    InfographicsRoadSegmentsDataCache,
    InfographicsRoadSegmentsDataCacheTemp,
    InfographicsStreetDataCacheTemp,
    InfographicsStreetDataCache,
    Streets,
)
from typing import Dict, Iterable
from anyway.constants import CONST
from anyway.backend_constants import BE_CONST
from anyway.app_and_db import db
from anyway.request_params import RequestParams
import anyway.infographics_utils
from anyway.widgets.widget import widgets_dict
from anyway.utilities import chunked_generator
import logging
import json


CACHE = "cache"
TEMP = "temp"
WIDGETS = "widgets"
WIDGET_DIGEST = "widget_digest"
NAME = "name"
META = "meta"
DATA = "data"
ITEMS = "items"
STREET_CACHE_TABLES = {CACHE: InfographicsStreetDataCache, TEMP: InfographicsStreetDataCacheTemp}
ROAD_SEGMENT_CACHE_TABLES = {
    CACHE: InfographicsRoadSegmentsDataCache,
    TEMP: InfographicsRoadSegmentsDataCacheTemp,
}


def get_infographics_data_from_cache_by_road_segment(road_segment_id, years_ago) -> Dict:
    db_item = (
        db.session.query(InfographicsRoadSegmentsDataCache)
        .filter(InfographicsRoadSegmentsDataCache.road_segment_id == int(road_segment_id))
        .filter(InfographicsRoadSegmentsDataCache.years_ago == int(years_ago))
        .first()
    )
    logging.debug(f"retrieved from cache {type(db_item)}:{db_item}"[:70])
    db.session.commit()
    try:
        if db_item:
            return json.loads(db_item.get_data())
        else:
            return {}
    except Exception as e:
        logging.error(
            f"Exception while extracting data from returned cache item flash_id:{road_segment_id},years:{years_ago})"
            f"returned value {type(db_item)}"
            f":cause:{e.__cause__}, class:{e.__class__}"
        )
        return {}


def get_cache_retrieval_query(params: RequestParams):
    res = params.resolution
    loc = params.location_info
    if res == BE_CONST.ResolutionCategories.SUBURBAN_ROAD:
        return (
            db.session.query(InfographicsRoadSegmentsDataCache)
            .filter(
                InfographicsRoadSegmentsDataCache.road_segment_id
                == int(params.location_info["road_segment_id"])
            )
            .filter(InfographicsRoadSegmentsDataCache.years_ago == int(params.years_ago))
        )
    elif res == BE_CONST.ResolutionCategories.STREET:
        t = InfographicsStreetDataCache
        return (
            db.session.query(t)
            .filter(t.yishuv_symbol == loc["yishuv_symbol"])
            .filter(t.street == loc["street1"])
            .filter(t.years_ago == int(params.years_ago))
        )
    else:
        msg = f"Cache unsupported resolution: {res}, params:{params}"
        logging.error(msg)
        raise ValueError(msg)


def get_infographics_data_from_cache_by_location(request_params: RequestParams) -> Dict:
    query = get_cache_retrieval_query(request_params)
    db_item = query.first()
    logging.debug(f"retrieved from cache {type(db_item)}:{db_item}"[:70])
    db.session.commit()
    try:
        if db_item:
            res = update_cache_data(db_item, request_params, query)
            non_empty = list(filter(lambda x: x[DATA][ITEMS], res[WIDGETS]))
            res[WIDGETS] = non_empty
            return res
        else:
            return {}
    except Exception as e:
        logging.exception(
            f"Exception while extracting data from returned cache item:{request_params}"
            f"returned value {type(db_item)}"
            f":cause:{e.__cause__}, class:{e.__class__}"
        )
        return {}


def update_cache_data(db_item, request_params: RequestParams, query) -> dict:
    cache_data = json.loads(db_item.get_data())
    res = []
    dirty: bool = False
    cache_widgets = {w[NAME]: w for w in cache_data[WIDGETS]}
    for widget in widgets_dict.values():
        if widget.is_relevant(request_params):
            cache_widget = cache_widgets.get(widget.name, None)
            if (
                cache_widget is None
                or cache_widget[META].get(WIDGET_DIGEST, None) != widget.widget_digest
            ):
                new_out = widget(request_params).serialize()
                res.append(new_out)
                dirty = True
                logging.debug(f"Widget {widget.name}: generated new. In cache was:{cache_widget}")
            else:
                res.append(cache_widget)
    if dirty:
        cache_data[WIDGETS] = res
        j = json.dumps(cache_data, default=str)
        db_item.set_data(j)
        db.session.commit()
    return cache_data


def copy_temp_into_cache(table: Dict[str, Base]):
    num_items_cache = db.session.query(table[CACHE]).count()
    num_items_temp = db.session.query(table[TEMP]).count()
    logging.debug(
        f"temp into cache for {table[CACHE].__tablename__}, "
        f"num items in cache: {num_items_cache}, temp:{num_items_temp}"
    )
    db.session.commit()
    start = datetime.now()
    with db.get_engine().begin() as conn:
        conn.execute("lock table infographics_data_cache in exclusive mode")
        logging.debug(f"in transaction, after lock")
        conn.execute(f"delete from {table[CACHE].__tablename__}")
        logging.debug(f"in transaction, after delete")
        conn.execute(
            f"insert into {table[CACHE].__tablename__} "
            f"SELECT * from {table[TEMP].__tablename__}"
        )
        logging.debug(f"in transaction, after insert into")
    logging.info(f"cache unavailable time: {str(datetime.now() - start)}")
    num_items_cache = db.session.query(table[CACHE]).count()
    num_items_temp = db.session.query(table[TEMP]).count()
    logging.debug(f"num items in cache: {num_items_cache}, temp:{num_items_temp}")
    db.session.execute(f"truncate table {table[TEMP].__tablename__}")
    db.session.commit()
    num_items_cache = db.session.query(table[CACHE]).count()
    num_items_temp = db.session.query(table[TEMP]).count()
    logging.debug(f"num items in cache: {num_items_cache}, temp:{num_items_temp}")
    db.session.commit()


def get_streets() -> Iterable[Streets]:
    t = Streets
    street_iter = iter(db.session.query(t.yishuv_symbol, t.street).all())
    try:
        while True:
            yield next(street_iter)
    except StopIteration:
        logging.debug("Read from streets table completed")


def get_street_infographic_keys() -> Iterable[Dict[str, int]]:
    for street in get_streets():
        for y in CONST.INFOGRAPHICS_CACHE_YEARS_AGO:
            yield {
                "yishuv_symbol": street.yishuv_symbol,
                "street1": street.street,
                "years_ago": y,
                "lang": "en",
            }


def build_street_cache_into_temp():
    start = datetime.now()
    db.session.query(InfographicsStreetDataCacheTemp).delete()
    db.session.commit()
    for chunk in chunked_generator(get_street_infographic_keys(), 4960):
        db.get_engine().execute(
            InfographicsStreetDataCacheTemp.__table__.insert(),  # pylint: disable=no-member
            [
                {
                    "yishuv_symbol": d["yishuv_symbol"],
                    "street": d["street1"],
                    "years_ago": d["years_ago"],
                    "data": anyway.infographics_utils.create_infographics_data_for_location(d),
                }
                for d in chunk
            ],
        )
    db.session.commit()
    logging.info(f"cache rebuild took:{str(datetime.now() - start)}")


def get_road_segments() -> Iterable[RoadSegments]:
    t = RoadSegments
    segment_iter = iter(db.session.query(t.segment_id).all())
    try:
        while True:
            yield next(segment_iter)
    except StopIteration:
        logging.debug("Read from road_segments table completed")


def get_road_segment_infographic_keys() -> Iterable[Dict[str, int]]:
    for road_segment in get_road_segments():
        for y in CONST.INFOGRAPHICS_CACHE_YEARS_AGO:
            yield {"road_segment_id": road_segment.segment_id, "years_ago": y, "lang": "en"}


def build_road_segments_cache_into_temp():
    start = datetime.now()
    db.session.query(InfographicsRoadSegmentsDataCacheTemp).delete()
    db.session.commit()
    db.get_engine().execute(
        InfographicsRoadSegmentsDataCacheTemp.__table__.insert(),  # pylint: disable=no-member
        [
            {
                "road_segment_id": d["road_segment_id"],
                "years_ago": d["years_ago"],
                "data": anyway.infographics_utils.create_infographics_data_for_location(d),
            }
            for d in get_road_segment_infographic_keys()
        ],
    )
    db.session.commit()
    logging.info(f"cache rebuild took:{str(datetime.now() - start)}")


def main_for_road_segments():
    logging.info("Refreshing road segments infographics cache...")
    build_road_segments_cache_into_temp()
    copy_temp_into_cache(ROAD_SEGMENT_CACHE_TABLES)
    logging.info("Refreshing road segments infographics cache cache Done")


def main_for_street():
    build_street_cache_into_temp()
    copy_temp_into_cache(STREET_CACHE_TABLES)
