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
            news_items = html_soup.find_all('section', class_='css-qjvjzr ')
        elif site_name == 'ynet':
            news_items = [i for i in html_soup.find_all('item') if i.category.get_text() == 'מבזקים']
    except Exception as _:
        pass
    return news_items


def get_date(html_soup, site_name='walla'):
    date = ''
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


def get_date_time(item_soup, date, site_name='walla'):
    entry_parsed_date = ''
    try:
        if site_name == 'walla':
            time_soup = item_soup.find("div", class_="time").get_text()
            time = datetime.strptime(time_soup, "%H:%M")
            entry_parsed_date = datetime.combine(date.date(), time.time())
        elif site_name == 'ynet':
            time_soup = item_soup.pubdate.get_text()
            entry_parsed_date = datetime.strptime(time_soup[:-6], '%a, %d %b %Y %H:%M:%S')

        entry_parsed_date = entry_parsed_date.replace(tzinfo=None)
    except Exception as _:
        pass
    return entry_parsed_date


def get_author(item_soup, site_name='walla'):
    author = ''
    try:
        if site_name == 'walla':
            author = item_soup.find('div', class_='author').get_text()
        elif site_name == 'ynet':
            author_text = item_soup.find('script', type="application/ld+json").get_text()
            author = author_text.split('(')[1].split(')')[0]
    except Exception as _:
        pass
    return author


def get_title(item_soup, site_name='walla'):
    title = ''
    try:
        if site_name == 'walla':
            title = item_soup.find('h2', class_='title').get_text()
        elif site_name == 'ynet':
            title = item_soup.title.get_text()
    except Exception as _:
        pass
    return title


def get_link(item_soup, site_name='walla'):
    link = ''
    try:
        if site_name == 'walla':
            link = f'https://news.walla.co.il{item_soup.find("a").get("href")}'
        elif site_name == 'ynet':
            link = item_soup.guid.get_text()
    except Exception as _:
        pass
    return link


def get_description(item_soup, site_name='walla'):
    description = ''
    try:
        if site_name == 'walla':
            description = item_soup.find('div', class_='content').find('p').get_text()
        if site_name == 'ynet':
            description_text = item_soup.find('script', type="application/ld+json").get_text()
            description = description_text.split('\"description\"')[1].split('(')[0]
    except Exception as _:
        pass
    return description
