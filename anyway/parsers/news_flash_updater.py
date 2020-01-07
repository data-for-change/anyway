import logging

from anyway.parsers.location_extraction import manual_filter_location_of_text, \
    geocode_extract, get_db_matching_location, set_accident_resolution
from anyway.parsers.news_flash_classifiers import classify_ynet, classify_tweets
from anyway.parsers.news_flash_parser import get_all_news_flash_ids, \
    get_description, get_source, update_news_flash_by_id, get_title

news_flash_classifiers = {'ynet': classify_ynet,
                          'twitter': classify_tweets}

def update_single_news_flash(maps_key, news_flash_id):
    news_item = {}
    try:
        item_source = get_source(news_flash_id)
        item_data = get_description(news_flash_id)
        if item_data is None or item_data == '':
            item_data = get_title(news_flash_id)
        accident = news_flash_classifiers[item_source](item_data)
        news_item['accident'] = accident
        if accident:
            location = manual_filter_location_of_text(item_data)
            news_item['location'] = location
            geo_location = geocode_extract(location, maps_key)
            if geo_location is None:
                news_item['lat'] = 0
                news_item['lon'] = 0
            else:
                news_item['lat'] = geo_location['geom']['lat']
                news_item['lon'] = geo_location['geom']['lng']
                news_item['resolution'] = set_accident_resolution(geo_location)
                db_location = get_db_matching_location(news_item['lat'], news_item['lon'],
                                                       news_item['resolution'], geo_location['road_no'])
                for col in ['region_hebrew', 'district_hebrew', 'yishuv_name', 'street1_hebrew', 'street2_hebrew',
                            'non_urban_intersection_hebrew', 'road1', 'road2', 'road_segment_name']:
                    news_item[col] = db_location[col]
        else:
            news_item['lat'] = 0
            news_item['lon'] = 0
            news_item['resolution']=None
            for col in ['region_hebrew', 'district_hebrew', 'yishuv_name', 'street1_hebrew', 'street2_hebrew',
                            'non_urban_intersection_hebrew', 'road1', 'road2', 'road_segment_name']:
                    news_item[col] = None
        update_news_flash_by_id(news_flash_id, news_item)
        logging.info('new flash news updated, is accident: ' + str(news_item['accident']))
    except Exception as e:
        logging.info('new flash news failed to update, index: ' + str(news_flash_id))
        print(e)
        raise()

def main(maps_key, source=None, news_flash_id=None):
    if news_flash_id is not None:
        update_single_news_flash(maps_key, news_flash_id)
    else:
        news_flash_ids = get_all_news_flash_ids(source)
        for news_flash_id in news_flash_ids:
            update_single_news_flash(maps_key, news_flash_id)
