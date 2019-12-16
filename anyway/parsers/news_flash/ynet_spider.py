import logging

import scrapy

from anyway.parsers.news_flash_parser import insert_new_flash_news
from ..location_extraction import manual_filter_location_of_text, geocode_extract, get_db_matching_location, \
    set_accident_resolution


class YnetFlashScrap(scrapy.Spider):
    """
    class to scrap Ynet flash news, compatible with scrapy's API
    """
    name = 'ynet_flash_scrap'  # scraper name
    news_item = {}  # news_item dict
    maps_key = ''  # google maps key
    custom_settings = {'LOG_ENABLED': False, }  # scrapy custom settings

    def __init__(self, url='', news_item=None, maps_key='', **kwargs):
        super().__init__(**kwargs)
        if news_item is None:
            news_item = {}
        self.start_urls = [url]
        self.news_item = news_item
        self.maps_key = maps_key

    def parse(self, response):
        """
        process a news_flash and adds result to DB
        :param response: response from scrapy
        """
        location = ''
        self.news_item['description'] = ''
        self.news_item['author'] = ''
        self.news_item['lat'] = 0
        self.news_item['lon'] = 0
        self.news_item['location'] = ''
        self.news_item['region_hebrew'] = ''
        self.news_item['district_hebrew'] = ''
        self.news_item['yishuv_name'] = ''
        self.news_item['street1_hebrew'] = ''
        self.news_item['street2_hebrew'] = ''
        self.news_item['non_urban_intersection_hebrew'] = ''
        self.news_item['road1'] = None
        self.news_item['road2'] = None
        self.news_item['road_segment_name'] = ''
        self.news_item['resolution'] = None

        try:
            for item in response.css('div.text14 p::text').extract():
                item = item.strip().replace('&nbsp', '').replace('\xa0', '')
                if self.news_item['description'] == '':
                    if item != '' and item != ' ' and not (item.startswith('(') and item.endswith(')')):
                        self.news_item['description'] = item
                if self.news_item['author'] == '' and (item.startswith('(') and item.endswith(')')):
                    self.news_item['author'] = item.split('(')[1].split(')')[0]
                    break
        except Exception as _:
            pass
        try:
            span_response = response.css('div.text14 span::text').extract()

            for item in enumerate(span_response):
                span_item = str(item[1]).strip().replace('&nbsp', '').replace('\xa0', '')
                if self.news_item['author'] == '':
                    if span_item.startswith('(') and span_item.endswith(')'):
                        self.news_item['author'] = span_item.split('(')[1].split(')')[0]
                if self.news_item['description'] == '':
                    if span_item != '' and span_item != ' ' and \
                            not (span_item.startswith('(') and span_item.endswith(')')):
                        self.news_item['description'] = span_item
        except Exception as _:
            pass
        try:
            if self.news_item['accident']:
                if self.news_item['description'] != '':
                    location = manual_filter_location_of_text(self.news_item['description'])
                if location == '':
                    location = manual_filter_location_of_text(self.news_item['title'])
                self.news_item['location'] = location
                geo_location = geocode_extract(location, self.maps_key)
                if geo_location is None:
                    self.news_item['lat'] = 0
                    self.news_item['lon'] = 0
                else:
                    self.news_item['lat'] = geo_location['geom']['lat']
                    self.news_item['lon'] = geo_location['geom']['lng']
                    self.news_item['resolution'] = set_accident_resolution(geo_location)
                    db_location = get_db_matching_location(self.news_item['lat'], self.news_item['lon'],
                                                           self.news_item['resolution'], geo_location['road_no'])
                    for col in ['region_hebrew', 'district_hebrew', 'yishuv_name', 'street1_hebrew', 'street2_hebrew',
                                'non_urban_intersection_hebrew', 'road1', 'road2', 'road_segment_name']:
                        self.news_item[col] = db_location[col]
        except Exception as _:
            pass

        insert_new_flash_news(self.news_item.get('title'),
                              self.news_item.get('link'), self.news_item.get('date_parsed'),
                              self.news_item.get('author'), self.news_item.get('description'),
                              self.news_item.get('location'), self.news_item.get('lat'),
                              self.news_item.get('lon'),
                              self.news_item.get('resolution'),
                              self.news_item.get('region_hebrew'),
                              self.news_item.get('district_hebrew'),
                              self.news_item.get('yishuv_name'),
                              self.news_item.get('street1_hebrew'),
                              self.news_item.get('street2_hebrew'),
                              self.news_item.get('non_urban_intersection_hebrew'),
                              self.news_item.get('road1'),
                              self.news_item.get('road2'),
                              self.news_item.get('road_segment_name'),
                              self.news_item.get('accident'), self.news_item.get('source'))
        logging.info('new flash news added, is accident: ' + str(self.news_item.get('accident')))
        yield None
