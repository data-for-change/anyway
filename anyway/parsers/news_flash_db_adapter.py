import pandas as pd
from flask_sqlalchemy import SQLAlchemy

from anyway.utilities import init_flask


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

    def insert_new_flash_news(
        self,
        title,
        link,
        date_parsed,
        author,
        description,
        location,
        lat,
        lon,
        resolution,
        region_hebrew,
        district_hebrew,
        yishuv_name,
        street1_hebrew,
        street2_hebrew,
        non_urban_intersection_hebrew,
        road1,
        road2,
        road_segment_name,
        accident,
        source,
        tweet_id=None,
    ):
        """
        insert new news_flash to db
        :param tweet_id: tweet_id if there is
        :param region_hebrew: region - mahuz
        :param district_hebrew: district - napa
        :param yishuv_name: yishuv name
        :param street1_hebrew: street1
        :param street2_hebrew: street2
        :param non_urban_intersection_hebrew: non urban intersection
        :param road_segment_name: urban segment name
        :param title: title of the news_flash
        :param link: link to the news_flash
        :param date_parsed: parsed date of the news_flash
        :param author: author of the news_flash
        :param description: description of the news flash
        :param location: location of the news flash (textual)
        :param lat: latitude
        :param lon: longitude
        :param road1: road 1 if found
        :param road2: road 2 if found
        :param resolution: resolution of found location
        :param accident: is the news flash an accident
        :param source: source of the news flash
        """
        temp = [
            title,
            link,
            date_parsed,
            author,
            description,
            location,
            lat,
            lon,
            resolution,
            region_hebrew,
            district_hebrew,
            yishuv_name,
            street1_hebrew,
            street2_hebrew,
            non_urban_intersection_hebrew,
            road1,
            road2,
            road_segment_name,
            accident,
            source,
            tweet_id,
        ]
        title, link, date_parsed, author, description, location, lat, lon, resolution, region_hebrew, district_hebrew, yishuv_name, street1_hebrew, street2_hebrew, non_urban_intersection_hebrew, road1, road2, road_segment_name, accident, source, tweet_id = pd.Series(
            temp
        ).replace(
            {pd.np.nan: None, "": None, 0: None, -1: None, " ": None}
        )
        self.execute(
            "INSERT INTO news_flash (tweet_id, title, link, date, author, description, location, lat, lon, "
            "resolution, region_hebrew, district_hebrew, yishuv_name, street1_hebrew, street2_hebrew, "
            "non_urban_intersection_hebrew, road1, road2, road_segment_name, "
            "accident, source"
            ") VALUES \
                      (:tweet_id, :title, :link, :date, :author, :description, :location, :lat, :lon, :resolution, \
                      :region_hebrew, :district_hebrew, :yishuv_name, :street1_hebrew, :street2_hebrew,"
            " :non_urban_intersection_hebrew, :road1, :road2, :road_segment_name,"
            " :accident, :source)",
            {
                "tweet_id": tweet_id,
                "title": title,
                "link": link,
                "date": date_parsed,
                "author": author,
                "description": description,
                "location": location,
                "lat": lat,
                "lon": lon,
                "resolution": resolution,
                "region_hebrew": region_hebrew,
                "district_hebrew": district_hebrew,
                "yishuv_name": yishuv_name,
                "street1_hebrew": street1_hebrew,
                "street2_hebrew": street2_hebrew,
                "non_urban_intersection_hebrew": non_urban_intersection_hebrew,
                "road1": road1,
                "road2": road2,
                "road_segment_name": road_segment_name,
                "accident": accident,
                "source": source,
            },
        )
        self.commit()

    def get_latest_tweet_id(self):
        """
        get the latest tweet id
        :return: latest tweet id
        """
        tweet_id = self.execute(
            "SELECT tweet_id FROM news_flash where source='twitter' ORDER BY date DESC LIMIT 1"
        ).fetchone()
        if tweet_id:
            return tweet_id[0]

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
        returns latest date of news flash
        :return: latest date of news flash
        """
        latest_date = self.execute(
            "SELECT date FROM news_flash WHERE source=:source ORDER BY date DESC LIMIT 1",
            {"source": source},
        ).fetchone()
        if latest_date is None:
            return None
        return latest_date[0].replace(tzinfo=None)
