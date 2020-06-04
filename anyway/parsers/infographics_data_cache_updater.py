# -*- coding: utf-8 -*-

from datetime import datetime
from ..utilities import init_flask
from flask_sqlalchemy import SQLAlchemy
from ..models import InfographicsDataCache, InfographicsDataCacheTemp, NewsFlash
from ..constants import CONST
import anyway.infographics_utils
import logging


app = init_flask()
db = SQLAlchemy(app)


def get_infographics_data_from_cache(news_flash_id, years_ago):
    db_item = db.session.query(InfographicsDataCache) \
        .filter(InfographicsDataCache.news_flash_id == news_flash_id) \
        .filter(InfographicsDataCache.years_ago == years_ago) \
        .first()
    logging.debug(f'retrieved from cache {type(db_item)}:{db_item}'[:70])
    db.session.commit()
    try:
        return db_item.get_data() if db_item else {}
    except Exception as e:
        logging.error(f'Exception while extracting data from returned cache item flash_id:{news_flash_id},years:{years_ago})'
                      f'returned value {type(db_item)}'
                      f':cause:{e.__cause__}, class:{e.__class__}')
        return {}


def copy_temp_into_cache():
    num_items_cache = db.session.execute('SELECT * from infographics_data_cache').rowcount
    num_items_temp = db.session.execute('SELECT * from infographics_data_cache_temp').rowcount
    logging.debug(f'num items in cache: {num_items_cache}, temp:{num_items_temp}')
    db.session.commit()
    start = datetime.now()
    with db.get_engine().begin() as conn:
        conn.execute('lock table infographics_data_cache in exclusive mode')
        logging.debug(f'in transaction, after lock')
        conn.execute('delete from infographics_data_cache')
        logging.debug(f'in transaction, after delete')
        conn.execute('insert into infographics_data_cache SELECT * from infographics_data_cache_temp')
        logging.debug(f'in transaction, after insert into')
    logging.info(f'cache unavailable time: {str(datetime.now() - start)}')
    num_items_cache = db.session.execute('SELECT * from infographics_data_cache').rowcount
    num_items_temp = db.session.execute('SELECT * from infographics_data_cache_temp').rowcount
    logging.debug(f'num items in cache: {num_items_cache}, temp:{num_items_temp}')
    db.session.execute('truncate table infographics_data_cache_temp')
    db.session.commit()
    num_items_cache = db.session.execute('SELECT * from infographics_data_cache').rowcount
    num_items_temp = db.session.execute('SELECT * from infographics_data_cache_temp').rowcount
    logging.debug(f'num items in cache: {num_items_cache}, temp:{num_items_temp}')
    db.session.commit()


def build_cache_into_temp():
    start = datetime.now()
    db.session.query(InfographicsDataCacheTemp).delete()
    db.session.commit()
    db.get_engine().execute(
        InfographicsDataCacheTemp.__table__.insert(),
        [{'news_flash_id': new_flash.get_id(),
          'years_ago': y,
          'data': anyway.infographics_utils.create_infographics_data(new_flash.get_id(), y)}
         for y in CONST.INFOGRAPHICS_CACHE_YEARS_AGO
         for new_flash in db.session.query(NewsFlash).filter(NewsFlash.accident).all()]
    )
    logging.info(f'cache rebuild took:{str(datetime.now() - start)}')


def get_cache_info():
    cache_items5 = db.session.query(InfographicsDataCache).filter(InfographicsDataCache.years_ago == 5).count()
    cache_items3 = db.session.query(InfographicsDataCache).filter(InfographicsDataCache.years_ago == 3).count()
    tmp_items5 = db.session.query(InfographicsDataCacheTemp).filter(InfographicsDataCacheTemp.years_ago == 5).count()
    tmp_items3 = db.session.query(InfographicsDataCacheTemp).filter(InfographicsDataCacheTemp.years_ago == 3).count()
    num_acc_flash_items = len(db.session.query(NewsFlash).filter(NewsFlash.accident).all())
    db.session.commit()
    return f'num items in cache: {cache_items3},{cache_items5}, temp table: {tmp_items3},{tmp_items5}, num flashes:{num_acc_flash_items}'


def main(update, info):
    if update:
        logging.info('Refreshing infographics cache...')
        build_cache_into_temp()
        copy_temp_into_cache()
        logging.info('Refreshing infographics cache Done')
    if info:
        logging.info(get_cache_info())


if __name__ == "__main__":
    main()

