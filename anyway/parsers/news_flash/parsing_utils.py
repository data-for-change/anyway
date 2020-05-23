from datetime import datetime

from anyway.parsers.news_flash_classifiers import classify_ynet
from ..location_extraction import manual_filter_location_of_text, geocode_extract, get_db_matching_location, \
    set_accident_resolution

import logging


def process_after_parsing(news_item, maps_key):
    location = None
    news_item['accident'] = classify_ynet(news_item['title'])
    try:
        if news_item['accident']:
            if news_item['description'] is not None:
                location = manual_filter_location_of_text(news_item['description'])
            if location is None:
                location = manual_filter_location_of_text(news_item['title'])
            news_item['location'] = location
            geo_location = geocode_extract(location, maps_key)
            if geo_location is not None:
                news_item['lat'] = geo_location['geom']['lat']
                news_item['lon'] = geo_location['geom']['lng']
                news_item['resolution'] = set_accident_resolution(geo_location)
                db_location = get_db_matching_location(news_item['lat'], news_item['lon'], news_item['resolution'],
                                                       geo_location['road_no'])
                for col in ['region_hebrew', 'district_hebrew', 'yishuv_name', 'street1_hebrew', 'street2_hebrew',
                            'non_urban_intersection_hebrew', 'road1', 'road2', 'road_segment_name']:
                    news_item[col] = db_location[col]
    except Exception as _:
        pass
    return news_item


def init_news_item(entry_parsed_date, site_name='walla'):
    news_item = {'date_parsed': entry_parsed_date,
                 'title': None,
                 'link': None,
                 'source': site_name,
                 'description': None,
                 'author': None,
                 'accident': False,
                 'location': None,
                 'lat': None,
                 'lon': None,
                 'road1': None,
                 'road2': None,
                 'road_segment_name': None,
                 'yishuv_name': None,
                 'street1_hebrew': None,
                 'street2_hebrew': None,
                 'resolution': None,
                 'region_hebrew': None,
                 'district_hebrew': None,
                 'non_urban_intersection_hebrew': None}
    return news_item


def get_all_news_items(html_soup, site_name):
    news_items = []
    try:
        if site_name == 'walla':
            news_items = html_soup.find_all('item')
        elif site_name == 'ynet':
            news_items = html_soup.find_all('item')
    except Exception as ex:
        logging.exception(ex)
    if not news_items:
        logging.error("Parsing error: failed to read news flash from {}".format(site_name))
    return news_items


def get_date(html_soup, site_name='walla'):
    date = None
    try:
        if site_name == 'walla':
            date_soup = html_soup.find('div', class_='date-part-1')
            for elm in date_soup:
                try:
                    date = datetime.strptime(elm, "%d.%m.%Y")
                    return date
                except Exception as _:
                    pass
        elif site_name == 'ynet':
            pass
    except Exception as _:
        pass
    return date


def get_date_time(item_soup, site_name='walla'):
    entry_parsed_date = None
    try:
        if site_name == 'walla':
            time_soup = item_soup.pubdate.get_text()
            entry_parsed_date = datetime.strptime(time_soup, '%a, %d %b %Y %H:%M:%S %Z')
        elif site_name == 'ynet':
            time_soup = item_soup.pubdate.get_text()
            entry_parsed_date = datetime.strptime(time_soup, '%a, %d %b %Y %H:%M:%S %z')

        entry_parsed_date = entry_parsed_date.replace(tzinfo=None)
    except Exception as _:
        pass
    return entry_parsed_date


def get_author(item_soup, site_name='walla'):
    author = None
    try:
        if site_name == 'walla':
            author = item_soup.find('div', class_="author").get_text()
        elif site_name == 'ynet':
            author_text = item_soup.find('script', type="application/ld+json").get_text()
            author = author_text.split('(')[-1].split(')')[0]
    except Exception as _:
        pass
    return author


def get_title(item_soup, site_name='walla'):
    title = None
    try:
        if site_name == 'walla':
            # we still need html here since lxml strips CDATA
            title = item_soup.find('h1', class_='title').get_text()
        elif site_name == 'ynet':
            title = item_soup.title.get_text()
    except Exception as _:
        pass
    return title


def get_link(item_soup, site_name='walla'):
    link = None
    try:
        if site_name == 'walla':
            link = item_soup.guid.get_text()
        elif site_name == 'ynet':
            link = item_soup.guid.get_text()
    except Exception as _:
        pass
    return link


def get_description(item_soup, site_name='walla'):
    description = None
    try:
        if site_name == 'walla':
            description = item_soup.description.get_text()
        if site_name == 'ynet':
            description_text = item_soup.find('script', type="application/ld+json").get_text()
            description = description_text.split('\"description\"')[1].split('(')[0]
    except Exception as _:
        pass
    return description
