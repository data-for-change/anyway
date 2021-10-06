# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Dict
from sqlalchemy import not_
from anyway.models import (
    InfographicsDataCache,
    InfographicsDataCacheTemp,
    NewsFlash,
    RoadSegments,
    InfographicsRoadSegmentsDataCache,
)
from anyway.constants import CONST
from anyway.backend_constants import BE_CONST
from anyway.app_and_db import db
import anyway.infographics_utils
import logging
import json


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
        .filter(InfographicsDataCache.road_segment_id == road_segment_id)
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
            f"Exception while extracting data from returned cache item flash_id:{road_segment_id},years:{years_ago})"
            f"returned value {type(db_item)}"
            f":cause:{e.__cause__}, class:{e.__class__}"
        )
        return {}


def copy_temp_into_cache():
    num_items_cache = db.session.query(InfographicsDataCache).count()
    num_items_temp = db.session.query(InfographicsDataCacheTemp).count()
    logging.debug(f"num items in cache: {num_items_cache}, temp:{num_items_temp}")
    db.session.commit()
    start = datetime.now()
    with db.get_engine().begin() as conn:
        conn.execute("lock table infographics_data_cache in exclusive mode")
        logging.debug(f"in transaction, after lock")
        conn.execute("delete from infographics_data_cache")
        logging.debug(f"in transaction, after delete")
        conn.execute(
            "insert into infographics_data_cache SELECT * from infographics_data_cache_temp"
        )
        logging.debug(f"in transaction, after insert into")
    logging.info(f"cache unavailable time: {str(datetime.now() - start)}")
    num_items_cache = db.session.query(InfographicsDataCache).count()
    num_items_temp = db.session.query(InfographicsDataCacheTemp).count()
    logging.debug(f"num items in cache: {num_items_cache}, temp:{num_items_temp}")
    db.session.execute("truncate table infographics_data_cache_temp")
    db.session.commit()
    num_items_cache = db.session.query(InfographicsDataCache).count()
    num_items_temp = db.session.query(InfographicsDataCacheTemp).count()
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


# noinspection PyUnresolvedReferences
def build_cache_for_road_segments():
    start = datetime.now()
    db.session.query(InfographicsRoadSegmentsDataCache).delete()
    db.session.commit()
    for y in CONST.INFOGRAPHICS_CACHE_YEARS_AGO:
        logging.debug(f"processing years_ago:{y}")
        db.get_engine().execute(
            InfographicsRoadSegmentsDataCache.__table__.insert(),  # pylint: disable=no-member
            [
                {
                    "road_segment_id": road_segment.get_id(),
                    "years_ago": y,
                    "data": anyway.infographics_utils.create_infographics_data_for_road_segment(
                        road_segment.get_id(), y, "he"
                    ),
                }
                for road_segment in db.session.query(RoadSegments).all()
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


def main_for_road_segments(update, info):
    if update:
        logging.info("Refreshing road segments infographics cache...")
        build_cache_for_road_segments()
        logging.info("Refreshing road segments infographics cache cache Done")
    if info:
        logging.info(get_cache_info())
    else:
        logging.debug(f"{info}")


def main(update, info):
    if update:
        logging.info("Refreshing infographics cache...")
        build_cache_into_temp()
        copy_temp_into_cache()
        logging.info("Refreshing infographics cache Done")
    if info:
        logging.info(get_cache_info())
    else:
        logging.debug(f"{info}")
