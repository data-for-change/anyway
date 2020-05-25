from datetime import datetime
import feedparser
import requests
from bs4 import BeautifulSoup

from anyway.parsers.news_flash import parsing_utils
from anyway.parsers.news_flash_db_adapter import init_db


def is_new_flash_news(rss_link, site_name):
    """
    check if there is a newer news flash in the rss link - I think it works only for ynet though
    :param rss_link: rss link
    :return: true if there is a newer news flash, false otherwise
    """
    db = init_db()
    latest_date = db.get_latest_date_from_db(site_name)
    if site_name == 'ynet':
        d = feedparser.parse(rss_link)
        newest_entry = datetime.strptime(d.entries[0].published[:-6], '%a, %d %b %Y %H:%M:%S')
    elif site_name == 'walla':
        response = requests.get(rss_link)
        html_soup = BeautifulSoup(response.text, "lxml")
        news_items = parsing_utils.get_all_news_items(html_soup, site_name)
        if not news_items:
            # Probably an error, handled inside get_all_news_items()
            return False
        newest_entry = parsing_utils.get_date_time(news_items[0], site_name)
    else:
        return False
    newest_entry = newest_entry.replace(tzinfo=None)
    if latest_date is None:
        return True
    return newest_entry > latest_date
