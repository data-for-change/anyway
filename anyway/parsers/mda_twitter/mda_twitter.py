import os

from .get_mda_tweets import get_user_tweets
from ..news_flash.news_flash_parser import insert_new_flash_news, get_latest_tweet_id_from_db


def mda_twitter():

    TWITTER_CONSUMER_KEY = os.environ.get('TWITTER_CONSUMER_KEY')
    TWITTER_CONSUMER_SECRET = os.environ.get('TWITTER_CONSUMER_SECRET')
    TWITTER_ACCESS_KEY = os.environ.get('TWITTER_ACCESS_KEY')
    TWITTER_ACCESS_SECRET = os.environ.get('TWITTER_ACCESS_SECRET')

    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_KEY')

    twitter_user = 'mda_israel'

    latest_tweet_id = get_latest_tweet_id_from_db()

    # check if there are any MDA tweets in the DB
    if latest_tweet_id:
        mda_tweets = get_user_tweets(twitter_user, latest_tweet_id, TWITTER_CONSUMER_KEY,
                                     TWITTER_CONSUMER_SECRET, TWITTER_ACCESS_KEY, TWITTER_ACCESS_SECRET,
                                     GOOGLE_MAPS_API_KEY)
    else:
        mda_tweets = get_user_tweets(
            twitter_user, 'no_tweets', TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET, TWITTER_ACCESS_KEY,
            TWITTER_ACCESS_SECRET, GOOGLE_MAPS_API_KEY)
    if mda_tweets is None:
        return

    mda_tweets = mda_tweets.loc[:, ['tweet_id', 'title', 'link', 'date', 'author', 'description', 'location', 'lat',
                             'lon', 'resolution', 'region_hebrew', 'district_hebrew', 'yishuv_name', 'street1_hebrew',
                             'street2_hebrew', 'non_urban_intersection_hebrew', 'road1', 'road2', 'road_segment_name',
                             'accident', 'source']]

    for row in mda_tweets.itertuples(index=False):
        (tweet_id, title, link, date, author, description, location, lat, lon, resolution,
         region_hebrew, district_hebrew, yishuv_name, street1_hebrew, street2_hebrew,
         non_urban_intersection_hebrew, road1, road2, road_segment_name, accident, source) = row

        insert_new_flash_news(title, link, date, author, description, location, lat, lon, resolution,
                              region_hebrew, district_hebrew, yishuv_name, street1_hebrew, street2_hebrew,
                              non_urban_intersection_hebrew, road1, road2, road_segment_name, accident, source,
                              tweet_id=tweet_id)
