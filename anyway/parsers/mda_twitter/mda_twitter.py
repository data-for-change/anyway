from .get_mda_tweets import get_user_tweets
from anyway.utilities import init_flask
from flask_sqlalchemy import SQLAlchemy
import os
import numpy as np


def get_latest_sequential_id_from_db(db):
    """
    get the next sequential id from news_flash table
    :return: latest sequential id
    """
    sequential_id = db.session.execute(
        "SELECT id FROM news_flash ORDER BY id DESC LIMIT 1").fetchone()
    if sequential_id:
        return sequential_id[0]


def get_latest_tweet_id_from_db(db):
    """
    get the latest tweet id
    :return: latest tweet id
    """
    tweet_id = db.session.execute(
        "SELECT tweet_id FROM news_flash where source='twitter' ORDER BY date DESC LIMIT 1").fetchone()
    if tweet_id:
        return tweet_id[0]


def insert_mda_tweet(db, tweet_id, title, link, date_parsed, author, description, location, lat, lon, road1,
                     road2, intersection, city, street, street2, resolution, geo_extracted_street,
                     geo_extracted_road_no, geo_extracted_intersection, geo_extracted_city,
                     geo_extracted_address, geo_extracted_district, accident, source, sequential_id):
    """
    insert new mda_tweet to db
    :param id_tweet: id of the mda_tweet
    :param title: title of the mda_tweet
    :param link: link to the mda_tweet
    :param date_parsed: parsed date of the mda_tweet
    :param author: author of the mda_tweet
    :param description: description of the mda tweet
    :param location: location of the mda tweet (textual)
    :param lat: latitude
    :param lon: longitude
    :param road1: road 1 if found
    :param road2: road 2 if found
    :param intersection: intersection if found
    :param city: city if found
    :param street: street if found
    :param street2: street 2 if found
    :param resolution: resolution of found location
    :param geo_extracted_street: street from data extracted from the geopoint
    :param geo_extracted_road_no: road number from data extracted from the geopoint
    :param geo_extracted_intersection: intersection from data extracted from the geopoint
    :param geo_extracted_city: city from data extracted from the geopoint
    :param geo_extracted_address: address from data extracted from the geopoint
    :param geo_extracted_district: district from data extracted from the geopoint
    :param accident: is the mda tweet an accident
    :param source: source of the mda tweet
    :param sequential_id: sequential id for the new row
    """
    db.session.execute('INSERT INTO news_flash (id,title, link, date, author, description, location, lat, lon, '
                       'road1, road2, intersection, city, street, street2, resolution, geo_extracted_street, '
                       'geo_extracted_road_no, geo_extracted_intersection, geo_extracted_city, '
                       'geo_extracted_address, geo_extracted_district, accident, source, tweet_id) VALUES \
                       (:id, :title, :link, :date, :author, :description, :location, :lat, :lon, \
                       :road1, :road2, :intersection, :city, :street, :street2, :resolution, :geo_extracted_street,\
                       :geo_extracted_road_no, :geo_extracted_intersection, :geo_extracted_city, \
                       :geo_extracted_address, :geo_extracted_district, :accident, :source, :tweet_id)',
                       {'id': sequential_id, 'title': title, 'link': link, 'date': date_parsed, 'author': author,
                        'description': description, 'location': location, 'lat': lat, 'lon': lon,
                        'road1': int(road1) if road1 and (isinstance(road1, (str, int)) or (isinstance(road1, float) and not np.isnan(road1))) else None,
                        'road2': int(road2) if road2 and (isinstance(road2, (str, int)) or (isinstance(road2, float) and not np.isnan(road2))) else None, 'intersection': intersection, 'city': city,
                        'street': street, 'street2': street2,
                        'resolution': resolution, 'geo_extracted_street': geo_extracted_street,
                        'geo_extracted_road_no': geo_extracted_road_no,
                        'geo_extracted_intersection': geo_extracted_intersection,
                        'geo_extracted_city': geo_extracted_city,
                        'geo_extracted_address': geo_extracted_address,
                        'geo_extracted_district': geo_extracted_district,
                        'accident': accident, 'source': source,
                        'tweet_id': tweet_id})
    db.session.commit()


def mda_twitter():
    app = init_flask()
    db = SQLAlchemy(app)

    TWITTER_CONSUMER_KEY = os.environ.get('TWITTER_CONSUMER_KEY')
    TWITTER_CONSUMER_SECRET = os.environ.get('TWITTER_CONSUMER_SECRET')
    TWITTER_ACCESS_KEY = os.environ.get('TWITTER_ACCESS_KEY')
    TWITTER_ACCESS_SECRET = os.environ.get('TWITTER_ACCESS_SECRET')

    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_KEY')

    twitter_user = 'mda_israel'

    latest_tweet_id = get_latest_tweet_id_from_db(db)

    # the next id to be used for the first new row
    next_sequential_id = get_latest_sequential_id_from_db(db) + 1

    # check if there are any MDA tweets in the DB
    if latest_tweet_id:
        mda_tweets = get_user_tweets(twitter_user, latest_tweet_id, TWITTER_CONSUMER_KEY,
                                     TWITTER_CONSUMER_SECRET, TWITTER_ACCESS_KEY, TWITTER_ACCESS_SECRET, GOOGLE_MAPS_API_KEY)
    else:
        mda_tweets = get_user_tweets(
            twitter_user, 'no_tweets', TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET, TWITTER_ACCESS_KEY, TWITTER_ACCESS_SECRET, GOOGLE_MAPS_API_KEY)
    if mda_tweets is None:
        return
    mda_tweets = mda_tweets.loc[:,['id', 'accident', 'author', 'date', 'description', 'lat', 'link', 'lon', 'title', 'source', 'location', 'city', 'intersection', 'road1', 'road2', 'street',
                             'geo_extracted_address', 'geo_extracted_city', 'geo_extracted_district', 'geo_extracted_intersection', 'geo_extracted_road_no', 'geo_extracted_street', 'resolution', 'street2']]

    for row in mda_tweets.itertuples(index=False):
        (tweet_id, accident, author, date, description, lat, link, lon, title, source, location, city, intersection, road1, road2, street, geo_extracted_address,
         geo_extracted_city, geo_extracted_district, geo_extracted_intersection, geo_extracted_road_no, geo_extracted_street, resolution, street2) = row

        insert_mda_tweet(db, tweet_id, title, link, date, author, description, location, lat, lon, road1,
                         road2, intersection, city, street, street2, resolution, geo_extracted_street,
                         geo_extracted_road_no, geo_extracted_intersection, geo_extracted_city,
                         geo_extracted_address, geo_extracted_district, accident, source, next_sequential_id)

        next_sequential_id += 1
