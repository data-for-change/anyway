import requests
from bs4 import BeautifulSoup
import feedparser
import json
from anyway.parsers import timezones


def get_author_from_walla_html_soup(html_soup):
    script_tags = html_soup.find_all('script', {'type' : 'application/ld+json'})
    results = []
    for script_tag in script_tags:
        script_text = script_tag.string.strip()
        data = json.loads(script_text)

        if isinstance(data.get('author'), dict):
            # there is one author
            author_section = data['author']
            results.append(author_section.get('name', ''))
        else:
            # there are multiple authors
            authors_section = data.get('author', [])
            author_names = [author_section.get('name', '') for author_section in authors_section]
            if len(author_names) == 1:
                results.append(author_names[0])
            elif len(author_names) > 1:
                results.append(', '.join(author_names))
    joined_results = ', '.join(results)
    joined_results = joined_results.strip()
    return joined_results

def parse_html_walla(item_rss, html_soup):
    # For some reason there's html here
    description = BeautifulSoup(item_rss["summary"], features="lxml").text

    author = get_author_from_walla_html_soup(html_soup)
    print(f"author: {author}")
    return author, description


def parse_html_ynet(item_rss, html_soup):
    # This is rather fragile
    # description_text: "[description] ([author]) [unrelated stuff]"
    description_text = html_soup.find(id="ArticleBodyComponent").get_text()
    author = description_text.split("(")[-1].split(")")[0].strip()
    description = description_text.rsplit("(")[0].strip()
    return author, description


sites_config = {
    "ynet": {
        "rss": "https://www.ynet.co.il:443/Integration/StoryRss1854.xml",
        "parser": parse_html_ynet,
    },
    "walla": {"rss": "https://rss.walla.co.il:443/feed/22", "parser": parse_html_walla},
}


def _fetch(url: str) -> str:
    return requests.get(url).text


def scrape_raw(site_name: str, *, rss_source=None, fetch_html=_fetch):
    config = sites_config[site_name]
    if rss_source is None:
        rss_source = config["rss"]
    rss_dict = feedparser.parse(rss_source)
    if rss_dict.get("bozo_exception"):
        raise rss_dict["bozo_exception"]

    for item_rss in rss_dict["items"]:
        html_text = fetch_html(item_rss["link"])
        author, description = config["parser"](item_rss, BeautifulSoup(html_text, "lxml"))
        yield {
            "link": item_rss["link"],
            "date": timezones.from_rss(item_rss["published_parsed"]),
            "source": site_name,
            "author": author,
            "title": item_rss["title"],
            "description": description,
            "accident": False,
        }


def scrape(*args, **kwargs):
    # lazily load dependencies, so this module will behave like an independent library
    from anyway.models import NewsFlash

    for dict_item in scrape_raw(*args, **kwargs):
        yield NewsFlash(**dict_item)
