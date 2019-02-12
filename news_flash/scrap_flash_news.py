import os
import sys
from .new_news_check import is_new_flash_news
from .news_flash_crawl import news_flash_crawl
# from sys import exit
# import time


def scrap_flash_news(site_name, maps_key):
    if site_name == 'ynet':
        rss_link = 'https://www.ynet.co.il/Integration/StoryRss1854.xml'
        if is_new_flash_news(rss_link):
            news_flash_crawl(rss_link, site_name, maps_key)


if __name__ == '__main__':
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))
    scrap_flash_news(sys.argv[1], sys.argv[2])

