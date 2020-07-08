import logging

from anyway.parsers.location_extraction import extract_geo_features
from anyway.parsers.news_flash_classifiers import classify_rss, classify_tweets
from anyway.parsers import news_flash_db_adapter

news_flash_classifiers = {"ynet": classify_rss, "twitter": classify_tweets, "walla": classify_rss}


def update_news_flash(db: news_flash_db_adapter.DBAdapter, news_flash_data):
    for newsflash in news_flash_data:
        classify = news_flash_classifiers[newsflash.source]
        newsflash.accident = classify(newsflash.description or newsflash.title)
        if newsflash.accident:
            extract_geo_features(db, newsflash)
    db.db.session.commit()


def main(source=None, news_flash_id=None):
    db = news_flash_db_adapter.init_db()
    if news_flash_id is not None:
        news_flash_data = db.get_newsflash_by_id(news_flash_id)
    elif source is not None:
        news_flash_data = db.select_newsflash_where_source(source)
    else:
        news_flash_data = db.get_all_newsflash()
    update_news_flash(db, news_flash_data)
