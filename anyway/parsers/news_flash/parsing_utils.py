from .geocode_extraction import geocode_extract
from .location_extraction import get_db_matching_location_of_text, NonUrbanAddress, UrbanAddress
from .location_extraction import manual_filter_location_of_text
from datetime import datetime


def is_road_accident(title):
    accident_words = [u'תאונ', ]
    working_accidents_words = [u'תאונת עבודה', u'תאונות עבודה']
    involved_words = [u'רכב', u'אוטובוס', u"ג'יפ", u'משאית', u'קטנוע', u'טרקטור',
                      u'אופנוע', u'אופניים', u'קורקינט', u'הולך רגל', u'הולכת רגל',
                      u'הולכי רגל']
    hurt_words = [u'פגע', u'פגיע', u'פגוע', u'הרג', u'הריג', u'הרוג', u'פצע', 'פציע',
                  u'פצוע', u'התנגש', u'התהפך', u'התהפכ']
    shooting_words = [u' ירי ', u' ירייה ', u' יריות ']
    shooting_startswith = [u' ירי', u' ירייה', u' יריות']

    explicit_accident = any([val in title for val in accident_words])
    not_work_accident = all([val not in title for val in working_accidents_words])
    involved = any([val in title for val in involved_words])
    hurt = any([val in title for val in hurt_words])
    no_shooting = all([val not in title for val in shooting_words]) and all(
        [not title.startswith(val) for val in shooting_startswith])

    if ((explicit_accident and not_work_accident) or (involved and hurt)) and no_shooting:
        return True
    else:
        return False


def process_after_parsing(news_item, maps_key):
    location = ''
    news_item['accident'] = is_road_accident(news_item['title'])

    try:
        if news_item['accident']:
            if news_item['description'] != '':
                location = manual_filter_location_of_text(news_item['description'])
            if location == '':
                location = manual_filter_location_of_text(news_item['title'])
            news_item['location'] = location
            geo_location = geocode_extract(location, maps_key)
            if geo_location is None:
                news_item['lat'] = 0
                news_item['lon'] = 0
                news_item['location'] = ''
                news_item['accident'] = False
            else:
                news_item['lat'] = geo_location['geom']['lat']
                news_item['lon'] = geo_location['geom']['lng']
                news_item['geo_extracted_street'] = geo_location['street']
                news_item['geo_extracted_road_no'] = geo_location['road_no']
                news_item['geo_extracted_intersection'] = geo_location['intersection']
                news_item['geo_extracted_city'] = geo_location['city']
                news_item['geo_extracted_address'] = geo_location['address']
                news_item['geo_extracted_district'] = geo_location['district']
                if geo_location['intersection'] != '' and geo_location['road_no'] != '':
                    news_item['resolution'] = 'צומת בינעירוני'
                elif geo_location['intersection'] != '':
                    news_item['resolution'] = 'צומת עירוני'
                elif geo_location['road_no'] != '':
                    news_item['resolution'] = 'כביש בינעירוני'
                elif geo_location['street'] != '':
                    news_item['resolution'] = 'רחוב'
                elif geo_location['city'] != '':
                    news_item['resolution'] = 'עיר'
                elif geo_location['district'] != '':
                    news_item['resolution'] = 'מחוז'
                else:
                    news_item['resolution'] = 'אחר'
                db_location = get_db_matching_location_of_text(location, geo_location)
                if type(db_location) is NonUrbanAddress:
                    news_item['road1'] = db_location.road1
                    news_item['road2'] = db_location.road2
                    news_item['intersection'] = db_location.intersection
                elif type(db_location) is UrbanAddress:
                    news_item['city'] = db_location.city
                    news_item['street'] = db_location.street
                    news_item['street2'] = db_location.street2
    except Exception as _:
        pass

    return news_item


def init_news_item(id_flash, entry_parsed_date, site_name='walla'):
    news_item = {'id_flash': id_flash,
                 'date_parsed': entry_parsed_date,
                 'title': '',
                 'link': '',
                 'date': entry_parsed_date,
                 'source': site_name,
                 'description': '',
                 'author': '',
                 'accident': False,
                 'location': '',
                 'lat': 0,
                 'lon': 0,
                 'road1': None,
                 'road2': None,
                 'intersection': None,
                 'city': None,
                 'street': None,
                 'street2': None,
                 'resolution': None,
                 'geo_extracted_street': None,
                 'geo_extracted_road_no': None,
                 'geo_extracted_intersection': None,
                 'geo_extracted_city': None,
                 'geo_extracted_address': None,
                 'geo_extracted_district': None}
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
