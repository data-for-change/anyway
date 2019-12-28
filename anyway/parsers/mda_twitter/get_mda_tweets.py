import datetime
import re

import pandas as pd
import tweepy

from anyway.parsers.news_flash_classifiers import classify_tweets
from ..location_extraction import geocode_extract, manual_filter_location_of_text, get_db_matching_location, \
    set_accident_resolution


def extract_accident_time(text):
    """
    extract accident's time from tweet text
    :param text: tweet text
    :return: extracted accident's time
    """
    reg_exp = r'בשעה (\d{2}:\d{2})'
    time_search = re.search(reg_exp, text)
    if time_search:
        return time_search.group(1)
    return None



def get_user_tweets(screen_name, latest_tweet_id, consumer_key, consumer_secret, access_key, access_secret,
                    google_maps_key):
    """
    get all user's recent tweets
    :param consumer_key: consumer_key for Twitter API
    :param consumer_secret: consumer_secret for Twitter API
    :param access_key: access_key for Twitter API
    :param access_secret: access_secret for Twitter API
    :return: DataFrame contains all of user's tweets
    """
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    api = tweepy.API(auth)
    # list that hold all tweets
    all_tweets = []

    # fetch the last 100 tweets if there are no tweets in the DB
    if latest_tweet_id == 'no_tweets':
        new_tweets = api.user_timeline(
            screen_name=screen_name, count=100, tweet_mode='extended')
    else:
        new_tweets = api.user_timeline(
            screen_name=screen_name, count=100, since_id=latest_tweet_id, tweet_mode='extended')
    all_tweets.extend(new_tweets)

    mda_tweets = [[tweet.id_str, tweet.created_at, tweet.full_text]
                  for tweet in all_tweets]
    tweets_df = pd.DataFrame(mda_tweets, columns=[
        'tweet_id', 'tweet_ts', 'tweet_text'])
    tweets_df['accident'] = tweets_df['tweet_text'].apply(classify_tweets)

    # filter tweets that are not about accidents
    tweets_df = tweets_df[tweets_df['accident'] == True]
    if tweets_df.empty:
        return None
    tweets_df['accident_time'] = tweets_df['tweet_text'].apply(
        extract_accident_time)
    tweets_df['accident_date'] = tweets_df['tweet_ts'].apply(
        lambda ts: datetime.datetime.date(ts))

    tweets_df['link'] = tweets_df['tweet_id'].apply(
        lambda t: 'https://twitter.com/mda_israel/status/' + str(t))
    tweets_df['author'] = ['מגן דוד אדום' for _ in range(len(tweets_df))]
    tweets_df['description'] = ['' for _ in range(len(tweets_df))]
    tweets_df['source'] = ['twitter' for _ in range(len(tweets_df))]

    tweets_df['date'] = tweets_df['accident_date'].astype(
        str) + ' ' + tweets_df['accident_time']
    tweets_df['location'] = tweets_df['tweet_text'].apply(
        manual_filter_location_of_text)
    tweets_df['google_location'] = tweets_df['location'].apply(
        geocode_extract, args=(google_maps_key,))

    # expanding google maps dict results to seperate columns
    tweets_df = pd.concat(
        [tweets_df, tweets_df['google_location'].apply(pd.Series)], axis=1)
    tweets_df = pd.concat(
        [tweets_df.drop(['geom'], axis=1), tweets_df['geom'].apply(pd.Series)], axis=1)

    tweets_df['resolution'] = tweets_df.apply(
        lambda row: set_accident_resolution(row), axis=1)

    tweets_df.rename(
        {'tweet_text': 'title', 'lng': 'lon', 'road_no': 'geo_extracted_road_no', 'street': 'geo_extracted_street',
         'intersection': 'geo_extracted_intersection', 'city': 'geo_extracted_city', 'address': 'geo_extracted_address',
         'district': 'geo_extracted_district'}, axis=1, inplace=True)

    tweets_df['location_db'] = tweets_df.apply(lambda row: get_db_matching_location(
        row['lat'], row['lon'], row['resolution'], row['road_no']), axis=1)
    tweets_df = pd.concat(
        [tweets_df, tweets_df['location_db'].apply(pd.Series)], axis=1)

    tweets_df.drop(['google_location', 'accident_date', 'accident_time',
                    'tweet_ts', 'location_db'], axis=1, inplace=True)

    return tweets_df
