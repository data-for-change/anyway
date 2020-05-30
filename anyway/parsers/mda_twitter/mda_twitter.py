import os

from anyway.parsers import news_flash_db_adapter
from .get_mda_tweets import get_user_tweets


def mda_twitter(google_maps_key):
    TWITTER_CONSUMER_KEY = os.environ.get('TWITTER_CONSUMER_KEY')
    TWITTER_CONSUMER_SECRET = os.environ.get('TWITTER_CONSUMER_SECRET')
    TWITTER_ACCESS_KEY = os.environ.get('TWITTER_ACCESS_KEY')
    TWITTER_ACCESS_SECRET = os.environ.get('TWITTER_ACCESS_SECRET')

    twitter_user = 'mda_israel'

    db = news_flash_db_adapter.init_db()

    latest_tweet_id = db.get_latest_tweet_id_from_db()

    # check if there are any MDA tweets in the DB
    if latest_tweet_id:
        mda_tweets = get_user_tweets(twitter_user, latest_tweet_id, TWITTER_CONSUMER_KEY,
                                     TWITTER_CONSUMER_SECRET, TWITTER_ACCESS_KEY, TWITTER_ACCESS_SECRET,
                                     google_maps_key)
    else:
        mda_tweets = get_user_tweets(
            twitter_user, 'no_tweets', TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET, TWITTER_ACCESS_KEY,
            TWITTER_ACCESS_SECRET, google_maps_key)
    if mda_tweets is None:
        return

    mda_tweets = mda_tweets.loc[:, ['tweet_id', 'title', 'link', 'date', 'author', 'description', 'location', 'lat',
                                    'lon', 'resolution', 'region_hebrew', 'district_hebrew', 'yishuv_name',
                                    'street1_hebrew',
                                    'street2_hebrew', 'non_urban_intersection_hebrew', 'road1', 'road2',
                                    'road_segment_name',
                                    'accident', 'source']]

    for row in mda_tweets.itertuples(index=False):
        (tweet_id, title, link, date, author, description, location, lat, lon, resolution,
         region_hebrew, district_hebrew, yishuv_name, street1_hebrew, street2_hebrew,
         non_urban_intersection_hebrew, road1, road2, road_segment_name, accident, source) = row

        db.insert_new_flash_news(title, link, date, author, description, location, lat, lon, resolution,
                                 region_hebrew, district_hebrew, yishuv_name, street1_hebrew, street2_hebrew,
                                 non_urban_intersection_hebrew, road1, road2, road_segment_name, accident, source,
                                 tweet_id=tweet_id)
