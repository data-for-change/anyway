from datetime import datetime, timezone, timedelta
import re
import os

import tweepy

from .news_flash_classifiers import classify_tweets
from .location_extraction import extract_geo_features


to_hebrew = {"mda_israel": "מגן דוד אדום"}


def scrape(screen_name, latest_tweet_id=None, count=100):
    """
    get all user's recent tweets
    """
    auth = tweepy.OAuthHandler(
        os.environ["TWITTER_CONSUMER_KEY"], os.environ["TWITTER_CONSUMER_SECRET"]
    )
    auth.set_access_token(os.environ["TWITTER_ACCESS_KEY"], os.environ["TWITTER_ACCESS_SECRET"])
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


def parse_creation_datetime(created_at):
    # Example: 'Sun May 31 11:26:18 +0000 2020'
    time_format = "%a %b %d %H:%M:%S %z %Y"
    time = datetime.strptime(created_at, time_format)
    summer_timezone = timezone(offset=timedelta(hours=3))
    return time.replace(tzinfo=timezone.utc).astimezone(tz=summer_timezone).replace(tzinfo=None)


def extract_accident_time(text):
    reg_exp = r"בשעה (\d{2}:\d{2})"
    time_search = re.search(reg_exp, text)
    if time_search:
        return time_search.group(1)
    return ""


def parse_tweet(tweet, screen_name):
    return {
        "link": "https://twitter.com/{}/status/{}".format(screen_name, tweet["id_str"]),
        "date_parsed": parse_creation_datetime(tweet["created_at"]),
        "source": "twitter",
        "author": to_hebrew[screen_name],
        "title": tweet["full_text"],
        "description": tweet["full_text"],
        "tweet_id": tweet["id_str"],
        "tweet_ts": tweet["created_at"],
    }


def scrape_extract_store(screen_name, db):
    latest_date = db.get_latest_date_of_source("twitter")
    for item in scrape(screen_name, db.get_latest_tweet_id()):
        if item["date_parsed"] < latest_date:
            # We can break if we're guaranteed the order is descending
            continue
        item["accident"] = classify_tweets(item["title"])
        if item["accident"]:
            item["date"] = (
                item["date_parsed"].strftime("%Y-%m-%d")
                + " "
                + extract_accident_time(item["description"])
            )
            extract_geo_features(item)
        db.insert_new_flash_news(**item)
