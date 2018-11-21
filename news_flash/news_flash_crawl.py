from datetime import datetime
import feedparser
import psycopg2
from scrapy.crawler import CrawlerProcess
from db_queries import get_latest_id_from_db, get_latest_date_from_db
from ynet_spider import YnetFlashScrap


def news_flash_crawl(rss_link, site_name, maps_key):
    id_flash = get_latest_id_from_db() + 1
    latest_date = get_latest_date_from_db()
    d = feedparser.parse(rss_link)
    process = CrawlerProcess()
    conn = psycopg2.connect("dbname=anyway_news_flash user=postgres password=123321")
    cur = conn.cursor()
    for entry in d.entries[::-1]:
        entry_parsed_date = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %z')
        entry_parsed_date = entry_parsed_date.replace(tzinfo=None)
        if (latest_date is not None and entry_parsed_date > latest_date) or latest_date is None:
            news_item = {"id_flash": id_flash, "date_parsed": entry_parsed_date, "title": entry.title,
                         "link": entry.links[0].href, "date": entry.published, "location": "", "lat": 0, "lon": 0}
            # need to implement location extraction
            if ("תאונ" in entry.title and "תאונת עבודה" not in entry.title and
                "תאונות עבודה" not in entry.title) or "נפגע מרכב" in entry.title \
                    or "נפגעה מרכב" in entry.title or \
                    "נפגעו מרכב" in entry.title or \
                    "פגיעת רכב" in entry.title or \
                    "פגיעת אוטובוס" in entry.title or \
                    "פגיעת משאית" in entry.title or \
                    "פגיעת קטנוע" in entry.title or \
                    "פגיעת אופנוע" in entry.title or \
                    "נפגע מאוטובוס" in entry.title or \
                    "נפגעה מאוטובוס" in entry.title or \
                    "נפגעו מאוטובוס" in entry.title or \
                    "נפגע ממשאית" in entry.title or \
                    "נפגעה ממשאית" in entry.title or \
                    "נפגעו ממשאית" in entry.title or \
                    "נפגע מאופנוע" in entry.title or \
                    "נפגעה מאופנוע" in entry.title or \
                    "נפגעו מאופנוע" in entry.title or \
                    "נפגע מקטנוע" in entry.title or \
                    "נפגעה מקטנוע" in entry.title or \
                    "נפגעו מקטנוע" in entry.title:
                news_item["accident"] = True
            else:
                news_item["accident"] = False
            if site_name == "ynet":
                news_item["source"] = "ynet"
                process.crawl(YnetFlashScrap, entry.links[0].href, news_item=news_item, cur=cur, maps_key=maps_key)
            id_flash = id_flash + 1
    process.start()
    conn.commit()
    cur.close()
    conn.close()
