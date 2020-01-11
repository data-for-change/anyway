from ..location_extraction import manual_filter_location_of_text, geocode_extract, get_db_matching_location, \
    set_accident_resolution
from datetime import datetime
from anyway.parsers.news_flash_classifiers import classify_ynet


def process_after_parsing(news_item, maps_key):
    location = ''
    news_item['accident'] = classify_ynet(news_item['title'])

    try:
        if news_item['accident']:
            if news_item['description'] != '':
                location = manual_filter_location_of_text(news_item['description'])
            if location == '':
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
                 'title': '',
                 'link': '',
                 'source': site_name,
                 'description': '',
                 'author': '',
                 'accident': False,
                 'location': '',
                 'lat': 0,
                 'lon': 0,
                 'road1': None,
                 'road2': None,
                 'road_segment_name': '',
                 'yishuv_name': '',
                 'street1_hebrew': '',
                 'street2_hebrew': '',
                 'resolution': None,
                 'region_hebrew': '',
                 'district_hebrew': '',
                 'non_urban_intersection_hebrew': ''}
    return news_item


def get_all_news_items(html_soup, site_name='walla'):
    news_items = []
    try:
        if site_name == 'walla':
            news_items = html_soup.find_all('article', class_='article fc ')
    except Exception as _:
        pass
    return news_items


def get_date(item_soup, site_name='walla'):
    date = ''
    try:
        if site_name == 'walla':
            entry_parsed_date = item_soup.find("time").get('datetime')
            entry_parsed_date = datetime.strptime(entry_parsed_date, "%Y-%m-%d %H:%M")
            date = entry_parsed_date.replace(tzinfo=None)
    except Exception as _:
        pass
    return date


def get_author(item_soup, site_name='walla'):
    author = ''
    try:
        if site_name == 'walla':
            author = item_soup.find('span', class_='author').get_text()
    except Exception as _:
        pass
    return author


def get_title(item_soup, site_name='walla'):
    title = ''
    try:
        if site_name == 'walla':
            title = item_soup.find('span', class_='text').get_text()
    except Exception as _:
        pass
    return title


def get_link(item_soup, site_name='walla'):
    link = ''
    try:
        if site_name == 'walla':
            link = item_soup.find("a").get("data-href")
    except Exception as _:
        pass
    return link


def get_description(article_soup, site_name='walla'):
    description = ''
    try:
        if site_name == 'walla':
            description = article_soup.find('section', class_='article-content').find(
                'p').find(text=True, recursive=False)
    except Exception as _:
        pass
    return description


def update_title_from_article(article_soup, site_name='walla'):
    title = ''
    try:
        if site_name == 'walla':
            title = article_soup.find('h1').get_text()
    except Exception as _:
        pass
    return title
