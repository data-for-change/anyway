import requests
from bs4 import BeautifulSoup
import logging

from anyway.parsers.news_flash import parsing_utils
from anyway.parsers.news_flash_parser import get_latest_date_from_db
from anyway.parsers.news_flash_parser import insert_new_flash_news


def beautiful_soup_news_flash_parse(rss_link, site_name, maps_key):
    latest_date = get_latest_date_from_db(site_name)
    response = requests.get(rss_link)
    rss_soup = BeautifulSoup(response.text, "lxml")
    news_items = parsing_utils.get_all_news_items(rss_soup, site_name)

    for item_soup in news_items:
        entry_parsed_date = parsing_utils.get_date_time(item_soup, site_name)
        if latest_date is not None and entry_parsed_date <= latest_date:
            continue

        news_item = parsing_utils.init_news_item(entry_parsed_date, site_name)
        news_item['link'] = parsing_utils.get_link(item_soup, site_name)

        response = requests.get(news_item['link'])
        html_soup = BeautifulSoup(response.text, "lxml")

        if site_name == 'ynet':
            news_item['title'] = parsing_utils.get_title(item_soup, site_name)
            news_item['author'] = parsing_utils.get_author(item_soup, site_name)

            news_item['description'] = parsing_utils.get_description(html_soup, site_name)

        if site_name == 'walla':
            news_item['description'] = parsing_utils.get_description(item_soup, site_name)

            news_item['author'] = parsing_utils.get_author(html_soup, site_name)
            news_item['title'] = parsing_utils.get_title(html_soup, site_name)

        parsing_utils.process_after_parsing(news_item, maps_key)

        insert_new_flash_news(**news_item)
        logging.info('new flash news added, is accident: ' + str(news_item['accident']))
