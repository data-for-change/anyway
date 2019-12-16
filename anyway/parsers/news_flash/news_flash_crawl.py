# -*- coding: utf-8 -*-

from datetime import datetime

import feedparser
from scrapy.crawler import CrawlerProcess

from anyway.parsers.news_flash_classifiers import classify_ynet
from anyway.parsers.news_flash_parser import get_latest_date_from_db
from .ynet_spider import YnetFlashScrap


def ynet_news_flash_crawl(rss_link, maps_key):
    """
    starts crawling by given rss link, site name and google maps key
    :param rss_link: rss link to crawl and get news_flash from
    :param maps_key: google maps key for geocode
    :return: scraped news_flash are added to the db
    """
    latest_date = get_latest_date_from_db('ynet')
    d = feedparser.parse(rss_link)
    process = CrawlerProcess()
    for entry in d.entries[::-1]:
        entry_parsed_date = datetime.strptime(entry.published[:-6], '%a, %d %b %Y %H:%M:%S')
        entry_parsed_date = entry_parsed_date.replace(tzinfo=None)
        if (latest_date is not None and entry_parsed_date > latest_date) or latest_date is None:
            news_item = {'date_parsed': entry_parsed_date, 'title': entry.title, 'link': entry.links[0].href,
                         'date': entry.published, 'location': '', 'lat': 0, 'lon': 0,
                         'accident': classify_ynet(entry.title), 'source': 'ynet'}
            process.crawl(YnetFlashScrap, entry.links[0].href, news_item=news_item, maps_key=maps_key)
    process.start()
