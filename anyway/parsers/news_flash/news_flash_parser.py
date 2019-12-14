from anyway.utilities import init_flask
from flask_sqlalchemy import SQLAlchemy
import pandas as pd

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
  AND (longitude>0
       AND latitude>0)''')
    df = pd.DataFrame(query_res.fetchall())
    df.columns = query_res.keys()
    return df


def get_description(ind):
    """
    get description by news_flash id
    :param ind: news_flash id
    :return: description of news_flash
    """
    description = db.session.execute('SELECT description FROM news_flash WHERE id=:id', {'id': ind}).fetchone()
    return description


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
    db.session.execute('INSERT INTO news_flash (tweet_id, title, link, date, author, description, location, lat, lon, '
                       'resolution, region_hebrew, district_hebrew, yishuv_name, street1_hebrew, street2_hebrew, '
                       'non_urban_intersection_hebrew, road1, road2, road_segment_name, '
                       'accident, source'') VALUES \
                       (:id, :title, :link, :date, :author, :description, :location, :lat, :lon, :resolution \
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


def update_location_by_id(ind, accident, location, lat, lon):
    """
    update news flash with new parameters
    :param ind: id of news flash to update
    :param accident: update accident status
    :param location: update of textual location
    :param lat: new found latitude
    :param lon: new found longitude
    :return:
    """
    db.session.execute(
        'UPDATE news_flash SET accident = :accident, location = :location, lat = :lat, lon = :lon WHERE id=:id',
        {'accident': accident, 'location': location, 'lat': lat, 'lon': lon, 'id': ind})
    db.session.commit()


def get_title(ind):
    """
    title of news flash by id
    :param ind: id
    :return: title of corresponding news flash
    """
    title = db.session.execute('SELECT title FROM news_flash WHERE id=:id', {'id': ind}).fetchone()
    return title


def get_latest_date_from_db():
    """
    returns latest date of news flash
    :return: latest date of news flash
    """
    latest_date = db.session.execute('SELECT date FROM news_flash ORDER BY id DESC LIMIT 1').fetchone()
    if latest_date is None:
        return None
    return latest_date[0].replace(tzinfo=None)