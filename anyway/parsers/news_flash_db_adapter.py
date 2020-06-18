import datetime
import logging

import pandas as pd
from flask_sqlalchemy import SQLAlchemy

from anyway.utilities import init_flask
from . import timezones
from ..models import NewsFlash

# fmt: off


def init_db() -> "DBAdapter":
    app = init_flask()
    db = SQLAlchemy(app)
    return DBAdapter(db)


class DBAdapter:
    def __init__(self, db: SQLAlchemy):
        self.db = db

    def execute(self, *args, **kwargs):
        return self.db.session.execute(*args, **kwargs)

    def commit(self, *args, **kwargs):
        return self.db.session.commit(*args, **kwargs)

    def get_markers_for_location_extraction(self):
        query_res = self.execute(
            """SELECT DISTINCT road1,
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
                       AND latitude is not null)"""
        )
        df = pd.DataFrame(query_res.fetchall())
        df.columns = query_res.keys()
        return df

    def get_description(self, news_flash_id):
        """
        get description by news_flash id
        :param news_flash_id: news_flash id
        :return: description of news_flash
        """
        description = self.execute(
            "SELECT description FROM news_flash WHERE id=:id", {"id": news_flash_id}
        ).fetchone()
        return description[0]

    def get_title(self, news_flash_id):
        """
        get title by news_flash id
        :param news_flash_id: news_flash id
        :return: title of news_flash
        """
        title = self.execute(
            "SELECT title FROM news_flash WHERE id=:id", {"id": news_flash_id}
        ).fetchone()
        return title[0]

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

    def get_source(self, news_flash_id):
        """
        get source by news_flash id
        :param news_flash_id: news_flash id
        :return: source of news_flash
        """
        source = self.execute(
            "SELECT source FROM news_flash WHERE id=:id", {"id": news_flash_id}
        ).fetchone()
        return source[0]

    def insert_new_newsflash(self, newsflash: NewsFlash) -> None:
        logging.info("Adding newsflash, is accident: {}, date: {}"
                     .format(newsflash.accident, newsflash.date))
        self.db.session.add(newsflash)
        self.db.session.commit()

    def update_news_flash_bulk(self, news_flash_id_list, params_dict_list):
        if len(news_flash_id_list) > 0 and len(news_flash_id_list) == len(params_dict_list):
            for i in range(len(news_flash_id_list)):
                self.update_news_flash_by_id(
                    news_flash_id_list[i], params_dict_list[i], commit=False
                )
            self.commit()

    def update_news_flash_by_id(self, news_flash_id, params_dict, commit=True):
        """
        update news flash with new parameters
        :return:
        """
        sql_query = "UPDATE news_flash SET "
        if params_dict is not None and len(params_dict) > 0:
            for k, _ in params_dict.items():
                sql_query = sql_query + "{key} = :{key}, ".format(key=k)
            if sql_query.endswith(", "):
                sql_query = sql_query[:-2]
            sql_query = sql_query + " WHERE id=:id"
            params_dict["id"] = news_flash_id
            self.execute(sql_query, params_dict)
            if commit:
                self.commit()

    def get_all_news_flash_ids(self, source=None):
        if source is not None:
            res = self.execute(
                "SELECT DISTINCT id FROM news_flash where source=:source", {"source": source}
            ).fetchall()
        else:
            res = self.execute("SELECT DISTINCT id FROM news_flash").fetchall()
        return [r[0] for r in res]

    def get_all_news_flash_data_for_updates(self, source=None, id=None):
        if id is not None:
            res = self.execute(
                "SELECT DISTINCT id, title, description, source, location FROM news_flash where id=:id",
                {"id": id},
            ).fetchall()
        elif source is not None:
            res = self.execute(
                "SELECT DISTINCT id, title, description, source, location FROM news_flash where source=:source",
                {"source": source},
            ).fetchall()
        else:
            res = self.execute(
                "SELECT DISTINCT id, title, description, source, location FROM news_flash"
            ).fetchall()
        return res

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
