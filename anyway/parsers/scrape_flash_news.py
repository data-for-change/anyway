import os
import sys
from . import twitter, rss_sites
from anyway.parsers.news_flash_db_adapter import init_db


def main():
    """
    main function for beginning of the news flash process
    """
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))
    db = init_db()
    rss_sites.scrape_extract_store("ynet", db)
    rss_sites.scrape_extract_store("walla", db)
    twitter.scrape_extract_store("mda_israel", db)
