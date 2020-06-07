import datetime

import requests
from bs4 import BeautifulSoup

from .location_extraction import extract_geo_features
from .news_flash_classifiers import classify_rss


def parse_walla(rss_soup, html_soup):
    description = rss_soup.description.get_text()

    author = html_soup.find("div", class_="author").get_text()
    # we still need html here since lxml strips CDATA
    title = html_soup.find("h1", class_="title").get_text()

    return author, title, description


def parse_ynet(rss_soup, html_soup):
    title = rss_soup.title.get_text()

    description_text = html_soup.find("script", type="application/ld+json").get_text()
    author = description_text.split("(")[-1].split(")")[0]
    description = description_text.split('"description"')[1].split("(")[0]

    return author, title, description


sites_config = {
    "ynet": {
        "rss": "https://www.ynet.co.il/Integration/StoryRss1854.xml",
        "time_format": "%a, %d %b %Y %H:%M:%S %z",
        "parser": parse_ynet,
    },
    "walla": {
        "rss": "https://rss.walla.co.il/feed/22",
        "time_format": "%a, %d %b %Y %H:%M:%S %Z",
        "parser": parse_walla,
    },
}


def _fetch(url: str) -> str:
    return requests.get(url).text


def scrape(site_name, *, fetch_rss=_fetch, fetch_html=_fetch):
    config = sites_config[site_name]
    rss_text = fetch_rss(config["rss"])
    rss_soup = BeautifulSoup(rss_text, "lxml")
    rss_soup_items = rss_soup.find_all("item")

    assert rss_soup_items

    for item_rss_soup in rss_soup_items:
        raw_date = item_rss_soup.pubdate.get_text()
        link = item_rss_soup.guid.get_text()

        date = datetime.datetime.strptime(raw_date, config["time_format"]).replace(tzinfo=None)

        html_text = fetch_html(link)
        item_html_soup = BeautifulSoup(html_text, "lxml")

        author, title, description = config["parser"](item_rss_soup, item_html_soup)
        yield {
            "link": link,
            "date": date,
            "source": site_name,
            "author": author,
            "title": title,
            "description": description,
        }


def scrape_extract_store(site_name, db):
    latest_date = db.get_latest_date_of_source(site_name) or datetime.date.min
    for item in scrape(site_name):
        if item["date"] < latest_date:
            break
        item["accident"] = classify_rss(item["title"])
        if item["accident"]:
            # FIX: No accident-accurate date extracted
            extract_geo_features(item)
        db.insert_new_flash_news(**item)
