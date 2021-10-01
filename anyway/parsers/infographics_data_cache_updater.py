# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Dict, List
from sqlalchemy import not_
from anyway.models import InfographicsDataCache, InfographicsDataCacheTemp, NewsFlash
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


def get_flash_ids(count: int) -> List[int]:
    for nfid in db.session.query(NewsFlash). \
        filter(NewsFlash.accident). \
        filter(NewsFlash.resolution.in_(["כביש בינעירוני"])). \
        filter(not_(NewsFlash.road_segment_name == None)). \
        with_entities(NewsFlash.id). \
        limit(count):
        yield nfid[0]


def widget_performance(count: int):
    for nfid in get_flash_ids(2):
        logging.debug(f'nfid:{nfid}')




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
        from anyway.infographics_utils import Widget, widgets_dict, RequestParams, get_request_params, create_infographics_data, widget_calc_times
        widget_names = ['top_road_segments_accidents_per_km',
                        'motorcycle_accidents_vs_all_accidents',
                        'accident_count_pedestrians_per_vehicle_street_vs_all',
                        'injured_accidents_with_pedestrians',
                        'vehicle_accident_vs_all_accidents']
        for nfid in get_flash_ids(2):
            logging.debug(f'news flash:{nfid}\t\t----------------------')
            res = create_infographics_data(nfid, 8, 'en')
            logging.debug(f'{type(res)}\n')
        with open('widget-times', 'w') as file:
            for k, v in widget_calc_times.items():
                file.write(f'{k}:{str(v)}\n')
            # request_params: RequestParams = get_request_params(nfid, 8, 'en')
            # logging.getLogger('sqlalchemy').setLevel(logging.DEBUG)
            # logging.getLogger('flask_sqlalchemy').setLevel(logging.DEBUG)
            # for n in widget_names:
            #     w: Widget = widgets_dict[n]
            #     widget = w(request_params)
            #     logging.debug(f'{widget.name}:{widget.serialize()["meta"]}')
