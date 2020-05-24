import pandas as pd
from flask_sqlalchemy import SQLAlchemy

from anyway.utilities import init_flask

app = init_flask()
db = SQLAlchemy(app)


def get_markers_for_location_extraction():
    query_res = db.session.execute('''SELECT DISTINCT road1,
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
                   AND latitude is not null)''')
    df = pd.DataFrame(query_res.fetchall())
    df.columns = query_res.keys()
    return df


def get_description(news_flash_id):
    """
    get description by news_flash id
    :param news_flash_id: news_flash id
    :return: description of news_flash
    """
    description = db.session.execute('SELECT description FROM news_flash WHERE id=:id',
                                     {'id': news_flash_id}).fetchone()
    return description[0]


def get_title(news_flash_id):
    """
    get title by news_flash id
    :param news_flash_id: news_flash id
    :return: title of news_flash
    """
    title = db.session.execute('SELECT title FROM news_flash WHERE id=:id',
                               {'id': news_flash_id}).fetchone()
    return title[0]


def remove_duplicate_rows():
    """
    remove duplicate rows by link
    """
    db.session.execute('''
        DELETE FROM news_flash T1
        USING news_flash T2
        WHERE T1.ctid < T2.ctid  -- delete the older versions
        AND T1.link  = T2.link;  -- add more columns if needed
        ''')
    db.session.commit()


def get_source(news_flash_id):
    """
    get source by news_flash id
    :param news_flash_id: news_flash id
    :return: source of news_flash
    """
    source = db.session.execute('SELECT source FROM news_flash WHERE id=:id',
                                {'id': news_flash_id}).fetchone()
    return source[0]


def insert_new_flash_news(title, link, date_parsed, author, description, location, lat, lon, resolution,
                          region_hebrew, district_hebrew, yishuv_name, street1_hebrew, street2_hebrew,
                          non_urban_intersection_hebrew, road1, road2, road_segment_name, accident, source,
                          tweet_id=None):
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
    temp = [title, link, date_parsed, author, description, location, lat, lon, resolution,
            region_hebrew, district_hebrew, yishuv_name, street1_hebrew, street2_hebrew,
            non_urban_intersection_hebrew, road1, road2, road_segment_name, accident, source,
            tweet_id]
    title, link, date_parsed, author, description, location, lat, lon, resolution, \
    region_hebrew, district_hebrew, yishuv_name, street1_hebrew, street2_hebrew, \
    non_urban_intersection_hebrew, road1, road2, road_segment_name, accident, source, \
    tweet_id = pd.Series(temp).replace({pd.np.nan: None, '': None, 0: None, -1: None, ' ': None})
    db.session.execute('INSERT INTO news_flash (tweet_id, title, link, date, author, description, location, lat, lon, '
                       'resolution, region_hebrew, district_hebrew, yishuv_name, street1_hebrew, street2_hebrew, '
                       'non_urban_intersection_hebrew, road1, road2, road_segment_name, '
                       'accident, source'') VALUES \
                       (:tweet_id, :title, :link, :date, :author, :description, :location, :lat, :lon, :resolution, \
                       :region_hebrew, :district_hebrew, :yishuv_name, :street1_hebrew, :street2_hebrew,'
                       ' :non_urban_intersection_hebrew, :road1, :road2, :road_segment_name,'
                       ' :accident, :source)',
                       {'tweet_id': tweet_id, 'title': title, 'link': link, 'date': date_parsed, 'author': author,
                        'description': description, 'location': location, 'lat': lat, 'lon': lon,
                        'resolution': resolution,
                        'region_hebrew': region_hebrew,
                        'district_hebrew': district_hebrew,
                        'yishuv_name': yishuv_name,
                        'street1_hebrew': street1_hebrew,
                        'street2_hebrew': street2_hebrew,
                        'non_urban_intersection_hebrew': non_urban_intersection_hebrew,
                        'road1': road1,
                        'road2': road2,
                        'road_segment_name': road_segment_name,
                        'accident': accident, 'source': source})
    db.session.commit()


def get_latest_tweet_id_from_db():
    """
    get the latest tweet id
    :return: latest tweet id
    """
    tweet_id = db.session.execute(
        "SELECT tweet_id FROM news_flash where source='twitter' ORDER BY date DESC LIMIT 1").fetchone()
    if tweet_id:
        return tweet_id[0]


def update_news_flash_bulk(news_flash_id_list, params_dict_list):
    if len(news_flash_id_list) > 0 and len(news_flash_id_list) == len(params_dict_list):
        for i in range(len(news_flash_id_list)):
            update_news_flash_by_id(news_flash_id_list[i], params_dict_list[i], commit=False)
        db.session.commit()


def update_news_flash_by_id(news_flash_id, params_dict, commit=True):
    """
    update news flash with new parameters
    :return:
    """
    sql_query = 'UPDATE news_flash SET '
    if params_dict is not None and len(params_dict) > 0:
        for k, _ in params_dict.items():
            sql_query = sql_query + '{key} = :{key}, '.format(key=k)
        if sql_query.endswith(', '):
            sql_query = sql_query[:-2]
        sql_query = sql_query + ' WHERE id=:id'
        params_dict['id'] = news_flash_id
        db.session.execute(sql_query, params_dict)
        if commit:
            db.session.commit()


def get_all_news_flash_ids(source=None):
    if source is not None:
        res = db.session.execute(
            'SELECT DISTINCT id FROM news_flash where source=:source', {'source': source}).fetchall()
    else:
        res = db.session.execute('SELECT DISTINCT id FROM news_flash').fetchall()
    return [r[0] for r in res]


def get_all_news_flash_data_for_updates(source=None, id=None):
    if id is not None:
        res = db.session.execute(
            'SELECT DISTINCT id, title, description, source, location FROM news_flash where id=:id',
            {'id': id}).fetchall()
    elif source is not None:
        res = db.session.execute(
            'SELECT DISTINCT id, title, description, source, location FROM news_flash where source=:source',
            {'source': source}).fetchall()
    else:
        res = db.session.execute('SELECT DISTINCT id, title, description, source, location FROM news_flash').fetchall()
    return res


def get_latest_date_from_db(source):
    """
    returns latest date of news flash
    :return: latest date of news flash
    """
    latest_date = db.session.execute(
        'SELECT date FROM news_flash WHERE source=:source ORDER BY date DESC LIMIT 1', {'source': source}).fetchone()
    if latest_date is None:
        return None
    return latest_date[0].replace(tzinfo=None)
