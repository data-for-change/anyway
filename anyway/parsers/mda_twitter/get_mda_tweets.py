import pandas as pd
import re
import datetime
import tweepy

from ..news_flash.geocode_extraction import geocode_extract
from ..news_flash.location_extraction import UrbanAddress, NonUrbanAddress, get_db_matching_location_of_text, manual_filter_location_of_text

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


def classify_tweets(text):
    """
    classify tweets for tweets about car accidents and others
    :param text: tweet text
    :return: boolean, true if tweet is about car accident, false for others
    """
    if text.startswith(u'בשעה') and \
            ((u'הולך רגל' in text or u'הולכת רגל' in text or u'נהג' in text or u'אדם' in text) and
             (u'רכב' in text or u'מכונית' in text or u'אופנוע' in text or u"ג'יפ" in text or u'טרקטור' in text or u'משאית' in text or
              u'אופניים' in text or u'קורקינט' in text)):
        return True
    return False


def get_matching_location_of_text_from_db(location, geo_location):
    """
    get results of manual location matching
    :param location: accident's location
    :param geo_location: google maps geo_dict
    :return: dictionary of manual matching results
    """
    db_location = get_db_matching_location_of_text(
        location, geo_location)

    if type(db_location) is NonUrbanAddress:
        return {'road1': db_location.road1,
                'road2': db_location.road2,
                'intersection': db_location.intersection
                }
    elif type(db_location) is UrbanAddress:
        return {'city': db_location.city,
                'street': db_location.street,
                'street2': db_location.street2
                }


def extract_road_number(location):
    """
    extract road number from location if exsist
    :param text: accident's location
    :return: extracted road number
    """
    road_number_regex = r'כביש (\d{1,4})'
    road_search = re.search(road_number_regex, location)
    if road_search:
        return int(road_search.group(1))
    return None


def set_accident_resolution(accident_row):
    """
    set the resolution of the accident
    :param text: single tweet of an accident
    :return: resolution option
    """
    if accident_row['intersection'] != '' and accident_row['road_no'] != '':
        return 'צומת בינעירוני'
    elif accident_row['intersection'] != '':
        return 'צומת עירוני'
    elif accident_row['road_no'] != '':
        return 'כביש בינעירוני'
    elif accident_row['street'] != '':
        return 'רחוב'
    elif accident_row['city'] != '':
        return 'עיר'
    elif accident_row['district'] != '':
        return 'מחוז'
    else:
        return 'אחר'


def get_user_tweets(screen_name, latest_tweet_id, consumer_key, consumer_secret, access_key, access_secret, google_maps_key):
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
        geocode_extract, args=(google_maps_key, ))

    # expanding google maps dict results to seperate columns
    tweets_df = pd.concat(
        [tweets_df, tweets_df['google_location'].apply(pd.Series)], axis=1)
    tweets_df = pd.concat(
        [tweets_df.drop(['geom'], axis=1), tweets_df['geom'].apply(pd.Series)], axis=1)

    tweets_df['resolution'] = tweets_df.apply(
        lambda row: set_accident_resolution(row), axis=1)

    tweets_df.rename({'tweet_text': 'title', 'lng': 'lon', 'tweet_id': 'id', 'road_no': 'geo_extracted_road_no', 'street': 'geo_extracted_street',
                      'intersection': 'geo_extracted_intersection', 'city': 'geo_extracted_city', 'address': 'geo_extracted_address', 'district': 'geo_extracted_district'}, axis=1, inplace=True)

    tweets_df['location_db'] = tweets_df.apply(lambda row: get_matching_location_of_text_from_db(
        row['location'], row['google_location']), axis=1)
    tweets_df = pd.concat(
        [tweets_df, tweets_df['location_db'].apply(pd.Series)], axis=1)

    tweets_df.drop(['google_location', 'accident_date', 'accident_time',
                    'tweet_ts', 'location_db'], axis=1, inplace=True)

    return tweets_df
