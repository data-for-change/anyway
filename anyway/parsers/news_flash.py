import os
import sys
import requests
from bs4 import BeautifulSoup
import logging

from anyway.parsers import twitter, rss_sites
from anyway.parsers.news_flash_db_adapter import init_db
from anyway.parsers.news_flash_classifiers import (
    classify_rss,
    classify_tweets,
    classify_organization,
)
from anyway.parsers.location_extraction import extract_geo_features

# FIX: classifier should be chosen by source (screen name), so `twitter` should be `mda`
news_flash_classifiers = {"ynet": classify_rss, "twitter": classify_tweets, "walla": classify_rss}


def update_all_in_db(source=None, newsflash_id=None):
    """
    main function for newsflash updating.

    Should be executed each time the classification or location-extraction are updated.
    """
    db = init_db()
    if newsflash_id is not None:
        newsflash_items = db.get_newsflash_by_id(newsflash_id)
    elif source is not None:
        newsflash_items = db.select_newsflash_where_source(source)
    else:
        newsflash_items = db.get_all_newsflash()

    for newsflash in newsflash_items:
        classify = news_flash_classifiers[newsflash.source]
        newsflash.organization = classify_organization(newsflash.source)
        newsflash.accident = classify(newsflash.description or newsflash.title)
        if newsflash.accident:
            extract_geo_features(db, newsflash)
    db.commit()


def scrape_hour_for_walla_newsflash(newsflash):
    try:
        page = requests.get(newsflash.link).content
        time_element = BeautifulSoup(page, "html.parser").find('div', class_='time')
        time = time_element.get_text()
        scraped_hour = int(time[:2])
        newsflash.date = newsflash.date.replace(hour=scraped_hour)
    except Exception as e:
        logging.error(f"during scraping hour for newsflash {e}")


def scrape_extract_store_rss(site_name, db):
    latest_date = db.get_latest_date_of_source(site_name)
    for newsflash in rss_sites.scrape(site_name):
        if newsflash.date <= latest_date:
            break
        # TODO: pass both title and description, leaving this choice to the classifier
        newsflash.accident = classify_rss(newsflash.title or newsflash.description)
        newsflash.organization = classify_organization(site_name)
        if site_name == "walla": # walla's rss feed currently shows wrong time zone
            scrape_hour_for_walla_newsflash(newsflash)
        if newsflash.accident:
            # FIX: No accident-accurate date extracted
            extract_geo_features(db, newsflash)
            newsflash.set_critical()
        db.insert_new_newsflash(newsflash)


def scrape_extract_store_twitter(screen_name, db):
    latest_date = db.get_latest_date_of_source("twitter")
    for newsflash in twitter.scrape(screen_name, db.get_latest_tweet_id()):
        if newsflash.date <= latest_date:
            # We can break if we're guaranteed the order is descending
            continue
        newsflash.accident = classify_tweets(newsflash.description)
        newsflash.organization = classify_organization("twitter")
        if newsflash.accident:
            extract_geo_features(db, newsflash)
            newsflash.set_critical()
        db.insert_new_newsflash(newsflash)


def scrape_all():
    """
    main function for newsflash scraping
    """
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))
    db = init_db()
    scrape_extract_store_rss("ynet", db)
    scrape_extract_store_rss("walla", db)
    # scrape_extract_store_twitter("mda_israel", db)
