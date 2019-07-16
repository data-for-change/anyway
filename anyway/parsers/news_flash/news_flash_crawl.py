# -*- coding: utf-8 -*-

from datetime import datetime
import feedparser
from scrapy.crawler import CrawlerProcess
from anyway.parsers.news_flash.news_flash_parser import get_latest_id_from_db, get_latest_date_from_db
from .ynet_spider import YnetFlashScrap


def news_flash_crawl(rss_link, site_name, maps_key):
    id_flash = get_latest_id_from_db() + 1
    latest_date = get_latest_date_from_db()
    d = feedparser.parse(rss_link)
    process = CrawlerProcess()
    for entry in d.entries[::-1]:
        entry_parsed_date = datetime.strptime(entry.published[:-6], '%a, %d %b %Y %H:%M:%S')
        entry_parsed_date = entry_parsed_date.replace(tzinfo=None)
        if (latest_date is not None and entry_parsed_date > latest_date) or latest_date is None:
            news_item = {'id_flash': id_flash, 'date_parsed': entry_parsed_date, 'title': entry.title,
                         'link': entry.links[0].href, 'date': entry.published, 'location': '', 'lat': 0, 'lon': 0}
            if ((u'תאונ' in entry.title and u'תאונת עבודה' not in entry.title and u'תאונות עבודה' not in entry.title)\
                    or ((u'רכב' in entry.title or u'אוטובוס' in entry.title or u"ג'יפ" in entry.title
                         or u'משאית' in entry.title or u'קטנוע' in entry.title or u'טרקטור'
                         in entry.title or u'אופנוע' in entry.title or u'אופניים' in entry.title or u'קורקינט'
                         in entry.title or u'הולך רגל' in entry.title or u'הולכת רגל' in entry.title
                         or u'הולכי רגל' in entry.title) and
                        (u'נפגע' in entry.title or u'פגיע' in entry.title or
                         u'נפצע' in entry.title or u'פציע' in entry.title or u'התנגש' in entry.title or u'התהפך'
                         in entry.title or u'התהפכ' in entry.title))) and u'ירי' not in entry.title:
                news_item['accident'] = True
            else:
                news_item['accident'] = False
            if site_name == 'ynet':
                news_item['source'] = 'ynet'
                process.crawl(YnetFlashScrap, entry.links[0].href, news_item=news_item, maps_key=maps_key)
            id_flash = id_flash + 1
    process.start()
