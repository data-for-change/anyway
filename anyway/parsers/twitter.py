import re

import tweepy

from anyway import secrets
from anyway.models import NewsFlash
from anyway.parsers import timezones

to_hebrew = {"mda_israel": "מגן דוד אדום"}


def scrape(screen_name, latest_tweet_id=None, count=100):
    """
    get all user's recent tweets
    """
    auth = tweepy.OAuthHandler(
        secrets.get("TWITTER_CONSUMER_KEY"), secrets.get("TWITTER_CONSUMER_SECRET")
    )
    auth.set_access_token(secrets.get("TWITTER_ACCESS_KEY"), secrets.get("TWITTER_ACCESS_SECRET"))
    # We use JSONParser to enable testing
    api = tweepy.API(auth, parser=tweepy.parsers.JSONParser())

    # fetch the last 100 tweets if there are no tweets in the DB
    if latest_tweet_id is None:
        all_tweets = api.user_timeline(screen_name=screen_name, count=count, tweet_mode="extended")
    else:
        all_tweets = api.user_timeline(
            screen_name=screen_name, count=count, tweet_mode="extended", since_id=latest_tweet_id
        )
        # FIX: why the count param here ^ ?
    for tweet in all_tweets:
        yield parse_tweet(tweet, screen_name)


def extract_accident_time(text):
    # Currently unused
    reg_exp = r"בשעה (\d{2}:\d{2})"
    time_search = re.search(reg_exp, text)
    if time_search:
        return time_search.group(1)
    return ""


def parse_tweet(tweet, screen_name):
    return NewsFlash(
        link="https://twitter.com/{}/status/{}".format(screen_name, tweet["id_str"]),
        date=timezones.parse_creation_datetime(tweet["created_at"]),
        source="twitter",
        author=to_hebrew[screen_name],
        title=tweet["full_text"],
        description=tweet["full_text"],
        tweet_id=int(tweet["id_str"]),
        accident=False,
    )
