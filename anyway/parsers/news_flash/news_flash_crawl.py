# -*- coding: utf-8 -*-

import feedparser
from datetime import datetime
from scrapy.crawler import CrawlerProcess
from anyway.parsers.news_flash.news_flash_parser import get_latest_id_from_db, get_latest_date_from_db
from .ynet_spider import YnetFlashScrap
from . import parsing_utils


def news_flash_crawl(rss_link, site_name, maps_key):
    """
    starts crawling by given rss link, site name and google maps key
    :param rss_link: rss link to crawl and get news_flash from
    :param site_name: name of site
    :param maps_key: google maps key for geocode
    :return: scraped news_flash are added to the db
    """
    id_flash = get_latest_id_from_db() + 1
    latest_date = get_latest_date_from_db()
    d = feedparser.parse(rss_link)
    process = CrawlerProcess()
    for entry in d.entries[::-1]:
        entry_parsed_date = datetime.strptime(entry.published[:-6], '%a, %d %b %Y %H:%M:%S')
        entry_parsed_date = entry_parsed_date.replace(tzinfo=None)
        if (latest_date is not None and entry_parsed_date > latest_date) or latest_date is None:
            news_item = {'id_flash': id_flash,
                         'date_parsed': entry_parsed_date,
                         'title': entry.title,
                         'link': entry.links[0].href,
                         'date': entry.published,
                         'location': '',
                         'lat': 0,
                         'lon': 0,
                         'accident': parsing_utils.is_road_accident(entry.title)}
            if site_name == 'ynet':
                news_item['source'] = 'ynet'
                process.crawl(YnetFlashScrap, entry.links[0].href, news_item=news_item, maps_key=maps_key)
            id_flash = id_flash + 1
    process.start()
