from anyway.parsers.news_flash_classifiers import classify_ynet
from ..location_extraction import manual_filter_location_of_text, geocode_extract, get_db_matching_location, \
    set_accident_resolution


def extract_geo_features(parsed_item, google_maps_key):
    news_item = {**init_news_item_extracted_features(), **parsed_item}
    location = None
    news_item['accident'] = classify_ynet(news_item['title'])
    try:
        if news_item['accident']:
            if news_item['description'] is not None:
                location = manual_filter_location_of_text(news_item['description'])
            if location is None:
                location = manual_filter_location_of_text(news_item['title'])
            news_item['location'] = location
            geo_location = geocode_extract(location, google_maps_key)
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


def init_news_item_extracted_features():
    return {'accident': False,
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
