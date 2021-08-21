import datetime
import logging
import pandas as pd
from flask_sqlalchemy import SQLAlchemy
from anyway.parsers import infographics_data_cache_updater
from anyway.parsers import timezones
from anyway.models import NewsFlash

# fmt: off


def init_db() -> "DBAdapter":
    from anyway.app_and_db import db
    return DBAdapter(db)


class DBAdapter:
    def __init__(self, db: SQLAlchemy):
        self.db = db

    def execute(self, *args, **kwargs):
        return self.db.session.execute(*args, **kwargs)

    def commit(self, *args, **kwargs):
        return self.db.session.commit(*args, **kwargs)

    def recreate_table_for_location_extraction(self):
        with self.db.session.begin():
            self.db.session.execute("""TRUNCATE cbs_locations""")
            self.db.session.execute("""INSERT INTO cbs_locations 
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
            )

    def get_markers_for_location_extraction(self):
        query_res = self.execute(
            """SELECT * FROM cbs_locations"""
        )
        df = pd.DataFrame(query_res.fetchall())
        df.columns = query_res.keys()
        return df

    def remove_duplicate_rows(self):
        """
        remove duplicate rows by link
        """
        self.execute(
            """
            DELETE FROM news_flash T1
            USING news_flash T2
            WHERE T1.ctid < T2.ctid  -- delete the older versions
            AND T1.link  = T2.link;  -- add more columns if needed
            """
        )
        self.commit()

    def insert_new_newsflash(self, newsflash: NewsFlash) -> None:
        logging.info("Adding newsflash, is accident: {}, date: {}"
                     .format(newsflash.accident, newsflash.date))
        self.db.session.add(newsflash)
        self.db.session.commit()
        infographics_data_cache_updater.add_news_flash_to_cache(newsflash)

    def get_newsflash_by_id(self, id):
        return self.db.session.query(NewsFlash).filter(NewsFlash.id == id)

    def select_newsflash_where_source(self, source):
        return self.db.session.query(NewsFlash).filter(NewsFlash.source == source)

    def get_all_newsflash(self):
        return self.db.session.query(NewsFlash)

    def get_latest_date_of_source(self, source):
        """
        :return: latest date of news flash
        """
        latest_date = self.execute(
            "SELECT max(date) FROM news_flash WHERE source=:source",
            {"source": source},
        ).fetchone()[0] or datetime.datetime(1900, 1, 1, 0, 0, 0)
        res = timezones.from_db(latest_date)
        logging.info('Latest time fetched for source {} is {}'
                     .format(source, res))
        return res

    def get_latest_tweet_id(self):
        """
        :return: latest tweet id
        """
        latest_id = self.execute(
            "SELECT tweet_id FROM news_flash where source='twitter' ORDER BY date DESC LIMIT 1"
        ).fetchone()
        if latest_id:
            return latest_id[0]
        return None
