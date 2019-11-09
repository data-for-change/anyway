import pandas as pd
import re
import datetime
import tweepy

from location_extraction import get_db_matching_location_of_text


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
    if ((u'תאונ' in text and u'תאונת עבודה' not in text and u'תאונות עבודה' not in text)
        or ((u'רכב' in text or u'אוטובוס' in text or u"ג'יפ" in text
             or u'משאית' in text or u'קטנוע' in text or u'טרקטור'
             in text or u'אופנוע' in text or u'אופניים' in text or u'קורקינט'
             in text or u'הולך רגל' in text or u'הולכת רגל' in text
             or u'הולכי רגל' in text) and
            (u'פגע' in text or u'פגיע' in text or u'פגוע' in text or
             u'הרג' in text or u'הריג' in text or u'הרוג' in text or
             u'פצע' in text or u'פציע' in text or u'פצוע' in text or
             text or u'התנגש' in text or u'התהפך'
             in text or u'התהפכ' in text))) and \
            (u' ירי ' not in text and not text.startswith(u' ירי') and
             u' ירייה ' not in text and not text.startswith(u' ירייה') and
             u' יריות ' not in text and not text.startswith(u' יריות')):
        return True
    return False


def get_user_tweets(screen_name, consumer_key, consumer_secret, access_key, access_secret):
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
    tweets_df['accident_time'] = tweets_df['tweet_text'].apply(extract_accident_time)
    tweets_df['accident_date'] = tweets_df['tweet_ts'].apply(lambda ts: datetime.datetime.date(ts))
    # tweets_df['location'] = tweets_df['tweet_text'].apply(get_db_matching_location_of_text)
    tweets_df['is_accident'] = tweets_df['tweet_text'].apply(classify_tweets)    
    
    return tweets_df


if __name__ == "__main__":
    CONSUMER_KEY = "E9dYIFqekzkQGCv6KbQWNLFQz"
    CONSUMER_SECRET = "TiPAQqG76tXzvFBnRCVEIk6W9iIF7PmoPcSV1sHjl0LP7bKt9z"
    ACCESS_KEY = "4023017482-kDubkC77jz48soKqHRfpSiLqenFMeRUE10s2f2A"
    ACCESS_SECRET = "un4FjkHNdRAjgkUlu4nv2wLF1etdcb0ClQIZovSWWbb6S"

    twitter_user = 'mda_israel'

    mda_tweets = get_user_tweets(twitter_user, CONSUMER_KEY, CONSUMER_SECRET, ACCESS_KEY, ACCESS_SECRET)
    print(mda_tweets)