# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from . import parsing_utils
import logging

from anyway.parsers.news_flash_parser import get_latest_date_from_db
from anyway.parsers.news_flash_parser import insert_new_flash_news


def beautiful_soup_news_flash_parse(rss_link, site_name, maps_key):
    latest_date = get_latest_date_from_db(site_name)
    response = requests.get(rss_link)
    html_soup = BeautifulSoup(response.text, "html.parser")
    news_items = parsing_utils.get_all_news_items(html_soup, site_name)

    for item_soup in news_items:
        entry_parsed_date = parsing_utils.get_date(item_soup, site_name)
        if not ((latest_date is None) or (entry_parsed_date > latest_date)):
            continue
        news_item = parsing_utils.init_news_item(entry_parsed_date, site_name)
        news_item['author'] = parsing_utils.get_author(item_soup, site_name)
        news_item['title'] = parsing_utils.get_title(item_soup, site_name)
        news_item['link'] = parsing_utils.get_link(item_soup, site_name)
        try:
            response = requests.get(news_item['link'])
            article_soup = BeautifulSoup(response.text, "html.parser")
            news_item['description'] = parsing_utils.get_description(article_soup, site_name)
            if news_item['title'] == '':
                news_item['title'] = parsing_utils.update_title_from_article(article_soup, site_name)
        except Exception as _:
            pass
        parsing_utils.process_after_parsing(news_item, maps_key)

        insert_new_flash_news(news_item)
        logging.info('new flash news added, is accident: ' + str(news_item['accident']))
