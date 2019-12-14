# -*- coding: utf-8 -*-

import feedparser
from datetime import datetime
from scrapy.crawler import CrawlerProcess
from .news_flash_parser import get_latest_date_from_db
from .ynet_spider import YnetFlashScrap


def news_flash_crawl(rss_link, site_name, maps_key):
    """
    starts crawling by given rss link, site name and google maps key
    :param rss_link: rss link to crawl and get news_flash from
    :param site_name: name of site
    :param maps_key: google maps key for geocode
    :return: scraped news_flash are added to the db
    """
    latest_date = get_latest_date_from_db()
    d = feedparser.parse(rss_link)
    process = CrawlerProcess()
    for entry in d.entries[::-1]:
        entry_parsed_date = datetime.strptime(entry.published[:-6], '%a, %d %b %Y %H:%M:%S')
        entry_parsed_date = entry_parsed_date.replace(tzinfo=None)
        if (latest_date is not None and entry_parsed_date > latest_date) or latest_date is None:
            news_item = {'date_parsed': entry_parsed_date, 'title': entry.title,
                         'link': entry.links[0].href, 'date': entry.published, 'location': '', 'lat': 0, 'lon': 0}
            if ((u'תאונ' in entry.title and u'תאונת עבודה' not in entry.title and u'תאונות עבודה' not in entry.title)
                or ((u'רכב' in entry.title or u'אוטובוס' in entry.title or u"ג'יפ" in entry.title
                     or u'משאית' in entry.title or u'קטנוע' in entry.title or u'טרקטור'
                     in entry.title or u'אופנוע' in entry.title or u'אופניים' in entry.title or u'קורקינט'
                     in entry.title or u'הולך רגל' in entry.title or u'הולכת רגל' in entry.title
                     or u'הולכי רגל' in entry.title) and
                    (u'פגע' in entry.title or u'פגיע' in entry.title or u'פגוע' in entry.title or
                     u'הרג' in entry.title or u'הריג' in entry.title or u'הרוג' in entry.title or
                     u'פצע' in entry.title or u'פציע' in entry.title or u'פצוע' in entry.title or
                     entry.title or u'התנגש' in entry.title or u'התהפך'
                     in entry.title or u'התהפכ' in entry.title))) and \
                    (u' ירי ' not in entry.title and not entry.title.startswith(u' ירי') and
                     u' ירייה ' not in entry.title and not entry.title.startswith(u' ירייה') and
                     u' יריות ' not in entry.title and not entry.title.startswith(u' יריות')):
                news_item['accident'] = True
            else:
                news_item['accident'] = False
            if site_name == 'ynet':
                news_item['source'] = 'ynet'
                process.crawl(YnetFlashScrap, entry.links[0].href, news_item=news_item, maps_key=maps_key)
    process.start()
