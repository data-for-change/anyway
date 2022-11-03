# -*- coding: utf-8 -*-

from datetime import datetime
from sqlalchemy import not_
from anyway.models import (
    Base,
    InfographicsDataCache,
    InfographicsDataCacheTemp,
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
import logging
import json


CACHE = "cache"
TEMP = "temp"
REGULAR_CACHE_TABLES = {CACHE: InfographicsDataCache, TEMP: InfographicsDataCacheTemp}
STREET_CACHE_TABLES = {CACHE: InfographicsStreetDataCache, TEMP: InfographicsStreetDataCacheTemp}
ROAD_SEGMENT_CACHE_TABLES = {
    CACHE: InfographicsRoadSegmentsDataCache,
    TEMP: InfographicsRoadSegmentsDataCacheTemp,
}


def is_in_cache(nf):
    return (
        len(CONST.INFOGRAPHICS_CACHE_YEARS_AGO)
        == db.session.query(InfographicsDataCache)
        .filter(InfographicsDataCache.news_flash_id == nf.get_id())
        .count()
    )


# noinspection PyUnresolvedReferences
def add_news_flash_to_cache(news_flash: NewsFlash):
    try:
        if not (
            news_flash.accident
            and anyway.infographics_utils.is_news_flash_resolution_supported(news_flash)
            and news_flash.newsflash_location_qualification is not None
        ):
            logging.debug(
                f"add_news_flash_to_cache: news flash does not qualify:{news_flash.serialize()}"
            )
            return True
        db.get_engine().execute(
            InfographicsDataCache.__table__.insert(),  # pylint: disable=no-member
            [
                {
                    "news_flash_id": news_flash.get_id(),
                    "years_ago": y,
                    "data": anyway.infographics_utils.create_infographics_data(
                        news_flash.get_id(), y, "he"
                    ),
                }
                for y in CONST.INFOGRAPHICS_CACHE_YEARS_AGO
            ],
        )
        logging.info(f"{news_flash.get_id()} added to cache")
        return True
    except Exception as e:
        logging.exception(
            f"Exception while inserting to cache. flash_id:{news_flash}), cause:{e.__cause__}"
        )
        return False


def get_infographics_data_from_cache(news_flash_id, years_ago) -> Dict:
    db_item = (
        db.session.query(InfographicsDataCache)
        .filter(InfographicsDataCache.news_flash_id == news_flash_id)
        .filter(InfographicsDataCache.years_ago == years_ago)
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
            f"Exception while extracting data from returned cache item flash_id:{news_flash_id},years:{years_ago})"
            f"returned value {type(db_item)}"
            f":cause:{e.__cause__}, class:{e.__class__}"
        )
        return {}


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
            return json.loads(db_item.get_data())
        else:
            return {}
    except Exception as e:
        logging.error(
            f"Exception while extracting data from returned cache item:{request_params}"
            f"returned value {type(db_item)}"
            f":cause:{e.__cause__}, class:{e.__class__}"
        )
        return {}


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


# noinspection PyUnresolvedReferences
def build_cache_into_temp():
    start = datetime.now()
    db.session.query(InfographicsDataCacheTemp).delete()
    db.session.commit()
    supported_resolutions = set([x.value for x in BE_CONST.SUPPORTED_RESOLUTIONS])
    for y in CONST.INFOGRAPHICS_CACHE_YEARS_AGO:
        logging.debug(f"processing years_ago:{y}")
        db.get_engine().execute(
            InfographicsDataCacheTemp.__table__.insert(),  # pylint: disable=no-member
            [
                {
                    "news_flash_id": new_flash.get_id(),
                    "years_ago": y,
                    "data": anyway.infographics_utils.create_infographics_data(
                        new_flash.get_id(), y, "he"
                    ),
                }
                for new_flash in db.session.query(NewsFlash)
                .filter(NewsFlash.accident)
                .filter(NewsFlash.resolution.in_(supported_resolutions))
                .all()
            ],
        )
    logging.info(f"cache rebuild took:{str(datetime.now() - start)}")


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
    db.get_engine().execute(
        InfographicsStreetDataCacheTemp.__table__.insert(),  # pylint: disable=no-member
        [
            {
                "yishuv_symbol": d["yishuv_symbol"],
                "street": d["street1"],
                "years_ago": d["years_ago"],
                "data": anyway.infographics_utils.create_infographics_data_for_location(d),
            }
            for d in get_street_infographic_keys()
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


def get_cache_info():
    cache_items = db.session.query(InfographicsDataCache).count()
    tmp_items = db.session.query(InfographicsDataCacheTemp).count()
    num_acc_flash_items = db.session.query(NewsFlash).filter(NewsFlash.accident).count()
    num_acc_suburban_flash_items = (
        db.session.query(NewsFlash)
        .filter(NewsFlash.accident)
        .filter(NewsFlash.resolution.in_(["כביש בינעירוני"]))
        .filter(not_(NewsFlash.road_segment_name == None))
        .count()
    )
    db.session.commit()
    return f"num items in cache: {cache_items}, temp table: {tmp_items}, accident flashes:{num_acc_flash_items}, flashes processed:{num_acc_suburban_flash_items}"


def main_for_road_segments():
    logging.info("Refreshing road segments infographics cache...")
    build_road_segments_cache_into_temp()
    copy_temp_into_cache(ROAD_SEGMENT_CACHE_TABLES)
    logging.info("Refreshing road segments infographics cache cache Done")


def main_for_street():
    build_street_cache_into_temp()
    copy_temp_into_cache(STREET_CACHE_TABLES)


def main(update, info):
    if update:
        logging.info("Refreshing infographics cache...")
        build_cache_into_temp()
        copy_temp_into_cache(REGULAR_CACHE_TABLES)
        logging.info("Refreshing infographics cache Done")
    if info:
        logging.info(get_cache_info())
    else:
        logging.debug(f"{info}")
