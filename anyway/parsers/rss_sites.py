import requests
from bs4 import BeautifulSoup

from anyway.models import NewsFlash
from anyway.parsers import timezones


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
        "rss": "https://www.ynet.co.il:443/Integration/StoryRss1854.xml",
        "parser": parse_ynet,
    },
    "walla": {"rss": "https://rss.walla.co.il:443/feed/22", "parser": parse_walla},
}


def _fetch(url: str) -> str:
    return requests.get(url).text


def scrape(site_name, *, fetch_rss=_fetch, fetch_html=_fetch):
    config = sites_config[site_name]
    rss_text = fetch_rss(config["rss"])

    # Patch RSS issue in walla. This might create duplicate `guid` field
    rss_text = rss_text.replace("link", "guid")

    rss_soup = BeautifulSoup(rss_text, features="lxml")
    rss_soup_items = rss_soup.find_all("item")

    assert rss_soup_items

    for item_rss_soup in rss_soup_items:
        link = item_rss_soup.guid.get_text()
        date = timezones.parse_creation_datetime(item_rss_soup.pubdate.get_text())

        html_text = fetch_html(link)
        item_html_soup = BeautifulSoup(html_text, "lxml")

        author, title, description = config["parser"](item_rss_soup, item_html_soup)
        yield NewsFlash(
            link=link,
            date=date,
            source=site_name,
            author=author,
            title=title,
            description=description,
            accident=False,
        )
