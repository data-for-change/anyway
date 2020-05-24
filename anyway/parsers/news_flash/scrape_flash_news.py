import os
import sys
from .new_news_check import is_new_flash_news
from ..mda_twitter.mda_twitter import mda_twitter
from .beautiful_soup_news_flash_parse import beautiful_soup_news_flash_parse


def scrape_flash_news(site_name, google_maps_key):
    if site_name == 'ynet':
        rss_link = 'https://www.ynet.co.il/Integration/StoryRss1854.xml'
        if is_new_flash_news(rss_link, site_name):
            beautiful_soup_news_flash_parse(rss_link, site_name, google_maps_key)
    if site_name == 'walla':
        rss_link = 'https://news.walla.co.il/breaking'
        if is_new_flash_news(rss_link, site_name):
            beautiful_soup_news_flash_parse(rss_link, site_name, google_maps_key)
    if site_name == 'twitter':
        mda_twitter(google_maps_key)


def main(google_maps_key):
    """
    main function for beginning of the news flash process
    :param google_maps_key: google maps key
    """
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))
    scrape_flash_news('ynet', google_maps_key)
    scrape_flash_news('walla', google_maps_key)
    scrape_flash_news('twitter', google_maps_key)
