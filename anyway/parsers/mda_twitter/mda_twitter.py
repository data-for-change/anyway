import pandas as pd
import re
import datetime
import tweepy

from geocode_extraction import geocode_extract
from location_extraction import manual_filter_location_of_text, get_db_matching_location_of_text, NonUrbanAddress, UrbanAddress


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
        ((u'הולך רגל' in text or u'הולכת רגל' in text or u'נהג' in text or u'אדם' in text) and \
            (u'רכב' in text or u'מכונית' in text or u'אופנוע' in text or u"ג'יפ" in text or u'טרקטור' in text or u'משאית' in text or \
                 u'אופניים' in text or u'קורקינט' in text)) or \
        (u'תאונה' in text or u'תאונת דרכים' in text):
            return True
    return False


def get_matching_location_of_text_from_db(location, geo_location):
    db_location = get_db_matching_location_of_text(location, geo_location)

    if type(db_location) is NonUrbanAddress:
        return {'road1':db_location.road1,
                'road2':db_location.road2,
                'intersection':db_location.intersection
                }
    elif type(db_location) is UrbanAddress:
        return {'city': db_location.city,
                'street': db_location.street,
                'street2': db_location.street2
                }


def get_user_tweets(screen_name, consumer_key, consumer_secret, access_key, access_secret, google_maps_key):
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
    new_tweets = api.user_timeline(screen_name=screen_name, count=50, tweet_mode='extended')
    all_tweets.extend(new_tweets)
    
    mda_tweets = [[tweet.id_str, tweet.created_at, tweet.full_text] for tweet in all_tweets]
    tweets_df = pd.DataFrame(mda_tweets, columns=['tweet_id', 'tweet_ts', 'tweet_text'])
    tweets_df['accident'] = tweets_df['tweet_text'].apply(classify_tweets)

    tweets_df['accident_time'] = tweets_df['tweet_text'].apply(extract_accident_time)
    tweets_df['accident_date'] = tweets_df['tweet_ts'].apply(lambda ts: datetime.datetime.date(ts))

    tweets_df['link'] = tweets_df['tweet_id'].apply(lambda t: 'https://twitter.com/mda_israel/status/' + str(t))
    tweets_df['author'] = ['מגן דוד אדום' for _ in range(len(tweets_df))]
    tweets_df['title'] = ['' for _ in range(len(tweets_df))]
    tweets_df['source'] = ['twitter' for _ in range(len(tweets_df))]

    tweets_df['date'] = tweets_df['accident_date'].astype(str) + ' ' + tweets_df['accident_time']
    tweets_df['location'] = tweets_df['tweet_text'].apply(manual_filter_location_of_text)
    tweets_df['google_location'] = tweets_df['location'].apply(geocode_extract, args=(google_maps_key, ))

    # tweets_df['db_location'] = ['' for _ in range(len(tweets_df))]
    # for row in tweets_df.itertuples():
    #     index, location, geo_location = row[0], row[8], row[9]
    #     x = get_matching_location_of_text_from_db(location, geo_location)
    #     print(x)
    #     tweets_df.loc[index, 'db_location'] = [x]

    # expanding google maps dict results to seperate columns
    tweets_df = pd.concat([tweets_df.drop(['google_location', 'accident_date', 'accident_time', 'tweet_id', 'tweet_ts'], axis=1), tweets_df['google_location'].apply(pd.Series)], axis=1)
    tweets_df = pd.concat([tweets_df.drop(['geom'], axis=1), tweets_df['geom'].apply(pd.Series)], axis=1)
    
    return tweets_df


if __name__ == "__main__":
    CONSUMER_KEY = 'E9dYIFqekzkQGCv6KbQWNLFQz'
    CONSUMER_SECRET = 'TiPAQqG76tXzvFBnRCVEIk6W9iIF7PmoPcSV1sHjl0LP7bKt9z'
    ACCESS_KEY = '4023017482-kDubkC77jz48soKqHRfpSiLqenFMeRUE10s2f2A'
    ACCESS_SECRET = 'un4FjkHNdRAjgkUlu4nv2wLF1etdcb0ClQIZovSWWbb6S'

    twitter_user = 'mda_israel'

    GOOGLE_MAPS_API_KEY = 'AIzaSyBzSaO19aiS7FuhBideS5W2SqZ_TXjXw6E'

    mda_tweets = get_user_tweets(twitter_user, CONSUMER_KEY, CONSUMER_SECRET, ACCESS_KEY, ACCESS_SECRET, GOOGLE_MAPS_API_KEY)
    
    mda_tweets.to_excel('test.xlsx')