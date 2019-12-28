from datetime import datetime
import feedparser
import requests
from bs4 import BeautifulSoup

from .news_flash_parser import get_latest_date_from_db


def is_new_flash_news(rss_link, site_name):
    """
    check if there is a newer news flash in the rss link - I think it works only for ynet though
    :param rss_link: rss link
    :return: true if there is a newer news flash, false otherwise
    """
    latest_date = get_latest_date_from_db()
    if site_name == 'ynet':
        d = feedparser.parse(rss_link)
        newest_entry = datetime.strptime(d.entries[0].published[:-6], '%a, %d %b %Y %H:%M:%S')
    elif site_name == 'walla':
        d = requests.get(rss_link)
        first_item = BeautifulSoup(d.text, "html.parser").find_all('article', class_='article fc ')[0]
        newest_entry = first_item.find("time").get('datetime')
        newest_entry = datetime.strptime(newest_entry, "%Y-%m-%d %H:%M")
    else:
        return False
    newest_entry = newest_entry.replace(tzinfo=None)
    if latest_date is None:
        return True
    return newest_entry > latest_date
