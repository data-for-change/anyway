import datetime
import re
import os

import pandas as pd
import tweepy

from .news_flash_classifiers import classify_tweets
from .location_extraction import geocode_extract, manual_filter_location_of_text, get_db_matching_location, \
    set_accident_resolution


def extract_accident_time(text):
    """
    extract accident's time from tweet text
    :param text: tweet text
    :return: extracted accident's time
    """
    reg_exp = r"בשעה (\d{2}:\d{2})"
    time_search = re.search(reg_exp, text)
    if time_search:
        return time_search.group(1)
    return None


to_hebrew = {
    'mda_israel': 'מגן דוד אדום'
}


def scrape(screen_name, latest_tweet_id, count=100):
    """
    get all user's recent tweets
    """
    auth = tweepy.OAuthHandler(os.environ['TWITTER_CONSUMER_KEY'], os.environ['TWITTER_CONSUMER_SECRET'])
    auth.set_access_token(os.environ['TWITTER_ACCESS_KEY'], os.environ['TWITTER_ACCESS_SECRET'])
    api = tweepy.API(auth, parser=tweepy.parsers.JSONParser())

    # fetch the last 100 tweets if there are no tweets in the DB
    if latest_tweet_id == 'no_tweets':
        all_tweets = api.user_timeline(
            screen_name=screen_name, count=count, tweet_mode='extended')
    else:
        all_tweets = api.user_timeline(
            screen_name=screen_name, count=count, tweet_mode='extended', since_id=latest_tweet_id)
                                  # ?? ^^^^^^^^^
    return all_tweets


def extract_features(all_tweets, screen_name, google_maps_key) -> pd.DataFrame:
    """
    :return: DataFrame contains all of user's tweets
    """
    tweets = ([tweet["id_str"], tweet["created_at"], tweet["full_text"]] for tweet in all_tweets)
    tweets_df = pd.DataFrame(tweets, columns=['tweet_id', 'tweet_ts', 'tweet_text'])
    tweets_df['accident'] = tweets_df['tweet_text'].apply(classify_tweets)

    # filter tweets that are not about accidents
    tweets_df = tweets_df[tweets_df["accident"] == True]
    if tweets_df.empty:
        return tweets_df
    tweets_df['accident_time'] = tweets_df['tweet_text'].apply(extract_accident_time)
    tweets_df['accident_date'] = tweets_df['tweet_ts'].apply(lambda ts: datetime.datetime.date(ts))

    tweets_df['link'] = tweets_df['tweet_id'].apply(lambda t: 'https://twitter.com/{}/status/{}'.format(screen_name, t))
    tweets_df['author'] = [to_hebrew[screen_name]] * len(tweets_df)
    tweets_df['description'] = [None] * len(tweets_df)  # TODO: Maybe swap description and title
    tweets_df['source'] = ['twitter'] * len(tweets_df)

    tweets_df['date'] = tweets_df['accident_date'].astype(str) + ' ' + tweets_df['accident_time']
    tweets_df['location'] = tweets_df['tweet_text'].apply(manual_filter_location_of_text)
    tweets_df['google_location'] = tweets_df['location'].apply(geocode_extract, args=(google_maps_key,))

    # expanding google maps dict results to separate columns
    tweets_df = pd.concat([tweets_df, tweets_df['google_location'].apply(pd.Series)], axis=1)
    tweets_df = pd.concat([tweets_df.drop(['geom'], axis=1), tweets_df['geom'].apply(pd.Series)], axis=1)
    tweets_df['resolution'] = tweets_df.apply(lambda row: set_accident_resolution(row), axis=1)

    tweets_df.rename(
        {'tweet_text': 'title', 'lng': 'lon', 'road_no': 'geo_extracted_road_no', 'street': 'geo_extracted_street',
         'intersection': 'geo_extracted_intersection', 'city': 'geo_extracted_city', 'address': 'geo_extracted_address',
         'district': 'geo_extracted_district'}, axis=1, inplace=True)

    tweets_df['location_db'] = tweets_df.apply(
        lambda row: get_db_matching_location(row['lat'], row['lon'], row['resolution'], row['geo_extracted_road_no']),
        axis=1)
    tweets_df = pd.concat([tweets_df, tweets_df['location_db'].apply(pd.Series)], axis=1)

    tweets_df.drop(['google_location', 'accident_date', 'accident_time', 'tweet_ts', 'location_db'],
                   axis=1, inplace=True)

    return tweets_df


def scrape_extract_store(screen_name, google_maps_key, db):

    latest_tweet_id = db.get_latest_tweet_id() or 'no_tweets'

    raw_tweets = scrape(screen_name, latest_tweet_id)

    tweets_df = extract_features(raw_tweets, screen_name, google_maps_key)
    if tweets_df.empty:
        # NB: why do we avoid inserting non-accidents to the DB?
        return

    tweets = tweets_df.loc[:, ['tweet_id', 'title', 'link', 'date', 'author', 'description', 'location', 'lat',
                               'lon', 'resolution', 'region_hebrew', 'district_hebrew', 'yishuv_name',
                               'street1_hebrew',
                               'street2_hebrew', 'non_urban_intersection_hebrew', 'road1', 'road2',
                               'road_segment_name',
                               'accident', 'source']]

    for row in tweets.itertuples(index=False):
        db.insert_new_flash_news(**row)
