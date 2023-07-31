import datetime
import os
import logging
import pandas as pd
import numpy as np
from flask_sqlalchemy import SQLAlchemy
from anyway.parsers import infographics_data_cache_updater
from anyway.parsers import timezones
from anyway.models import NewsFlash
from anyway.slack_accident_notifications import publish_notification
from anyway.app_and_db import db, app
import sqlalchemy as sa

# fmt: off


def init_db() -> "DBAdapter":
    with app.app_context():
        return DBAdapter(db)


class DBAdapter:
    def __init__(self, db: SQLAlchemy):
        self.db = db
        self.__null_types: set = {np.nan}

    def execute(self, *args, **kwargs):
        with app.app_context():
            return self.db.session.execute(*args, **kwargs)

    def commit(self, *args, **kwargs):
        with app.app_context():
            return self.db.session.commit(*args, **kwargs)

    def recreate_table_for_location_extraction(self):
        with app.app_context():
            with self.db.session.begin():
                self.db.session.execute(sa.text("""TRUNCATE cbs_locations"""))
                self.db.session.execute(sa.text("""INSERT INTO cbs_locations
                        (SELECT ROW_NUMBER() OVER (ORDER BY road1) as id, LOCATIONS.*
                        FROM 
                        (SELECT DISTINCT road1,
                            road2,
                            non_urban_intersection_hebrew,
                            yishuv_name,
                            street1_hebrew,
                            street2_hebrew,
                            district_hebrew,
                            region_hebrew,
                            road_segment_name,
                            longitude,
                            latitude
                        FROM markers_hebrew
                        WHERE (provider_code=1
                            OR provider_code=3)
                        AND (longitude is not null
                            AND latitude is not null)) LOCATIONS)"""
                                        ))

    def get_markers_for_location_extraction(self):
        with app.app_context():
            query_res = self.execute(sa.text(
                """SELECT * FROM cbs_locations"""
            ))
            df = pd.DataFrame(query_res.fetchall())
            df.columns = query_res.keys()
            return df

    def remove_duplicate_rows(self):
        """
        remove duplicate rows by link
        """
        with app.app_context():
            self.execute(sa.text(
                """
                DELETE FROM news_flash T1
                USING news_flash T2
                WHERE T1.ctid < T2.ctid  -- delete the older versions
                AND T1.link  = T2.link;  -- add more columns if needed
                """
            ))
            self.commit()

    def insert_new_newsflash(self, newsflash: NewsFlash) -> None:
        with app.app_context():
            logging.info("Adding newsflash, is accident: {}, date: {}"
                        .format(newsflash.accident, newsflash.date))
            self.__fill_na(newsflash)
            self.db.session.add(newsflash)
            self.db.session.commit()
            infographics_data_cache_updater.add_news_flash_to_cache(newsflash)
            if os.environ.get("FLASK_ENV") == "production" and newsflash.accident:
                publish_notification(newsflash)

    def get_newsflash_by_id(self, id):
        with app.app_context():
            return self.db.session.query(NewsFlash).filter(NewsFlash.id == id)

    def select_newsflash_where_source(self, source):
        with app.app_context():
            return self.db.session.query(NewsFlash).filter(NewsFlash.source == source)

    def get_all_newsflash(self):
        with app.app_context():
            return self.db.session.query(NewsFlash)

    def get_latest_date_of_source(self, source):
        """
        :return: latest date of news flash
        """
        with app.app_context():
            latest_date = self.execute(sa.text(
                "SELECT max(date) FROM news_flash WHERE source=:source",
                {"source": source},
            )).fetchone()[0] or datetime.datetime(1900, 1, 1, 0, 0, 0)
            res = timezones.from_db(latest_date)
            logging.info('Latest time fetched for source {} is {}'
                        .format(source, res))
            return res

    def get_latest_tweet_id(self):
        """
        :return: latest tweet id
        """
        with app.app_context():
            latest_id = self.execute(sa.text(
                "SELECT tweet_id FROM news_flash where source='twitter' ORDER BY date DESC LIMIT 1"
            )).fetchone()
        if latest_id:
            return latest_id[0]
        return None

    def __fill_na(self, newsflash: NewsFlash):
        for key, value in newsflash.__dict__.items():
            if value in self.__null_types:
                setattr(newsflash, key, None)
