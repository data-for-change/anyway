import logging

import scrapy
from anyway.parsers.news_flash.news_flash_parser import insert_new_flash_news

from .geocode_extraction import geocode_extract
from .location_extraction import get_db_matching_location_of_text, NonUrbanAddress, UrbanAddress
from .location_extraction import manual_filter_location_of_text


class YnetFlashScrap(scrapy.Spider):
    name = 'ynet_flash_scrap'
    news_item = {}
    maps_key = ''
    custom_settings = {'LOG_ENABLED': False, }

    def __init__(self, url='', news_item=None, maps_key='', **kwargs):
        super().__init__(**kwargs)
        if news_item is None:
            news_item = {}
        self.start_urls = [url]
        self.news_item = news_item
        self.maps_key = maps_key

    def parse(self, response):
        location = ''
        self.news_item['description'] = ''
        self.news_item['author'] = ''
        self.news_item['lat'] = 0
        self.news_item['lon'] = 0
        self.news_item['location'] = ''
        self.news_item['road1'] = None
        self.news_item['road2'] = None
        self.news_item['intersection'] = None
        self.news_item['city'] = None
        self.news_item['street'] = None
        self.news_item['street2'] = None
        self.news_item['resolution'] = None
        self.news_item['geo_extracted_street'] = None
        self.news_item['geo_extracted_road_no'] = None
        self.news_item['geo_extracted_intersection'] = None
        self.news_item['geo_extracted_city'] = None
        self.news_item['geo_extracted_address'] = None
        self.news_item['geo_extracted_district'] = None
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
                    self.news_item['location'] = ''
                    self.news_item['accident'] = False
                else:
                    self.news_item['lat'] = geo_location['geom']['lat']
                    self.news_item['lon'] = geo_location['geom']['lng']
                    self.news_item['geo_extracted_street'] = geo_location['street']
                    self.news_item['geo_extracted_road_no'] = geo_location['road_no']
                    self.news_item['geo_extracted_intersection'] = geo_location['intersection']
                    self.news_item['geo_extracted_city'] = geo_location['city']
                    self.news_item['geo_extracted_address'] = geo_location['address']
                    self.news_item['geo_extracted_district'] = geo_location['district']
                    if geo_location['intersection'] != '' and geo_location['road_no'] != '':
                        self.news_item['resolution'] = 'צומת בינעירוני'
                    elif geo_location['intersection'] != '':
                        self.news_item['resolution'] = 'צומת עירוני'
                    elif geo_location['road_no'] != '':
                        self.news_item['resolution'] = 'כביש בינעירוני'
                    elif geo_location['street'] != '':
                        self.news_item['resolution'] = 'רחוב'
                    elif geo_location['city'] != '':
                        self.news_item['resolution'] = 'עיר'
                    elif geo_location['district'] != '':
                        self.news_item['resolution'] = 'מחוז'
                    else:
                        self.news_item['resolution'] = 'אחר'
                    db_location = get_db_matching_location_of_text(location, geo_location)
                    if type(db_location) is NonUrbanAddress:
                        self.news_item['road1'] = db_location.road1
                        self.news_item['road2'] = db_location.road2
                        self.news_item['intersection'] = db_location.intersection
                    elif type(db_location) is UrbanAddress:
                        self.news_item['city'] = db_location.city
                        self.news_item['street'] = db_location.street
                        self.news_item['street2'] = db_location.street2
        except Exception as _:
            pass

        insert_new_flash_news(self.news_item.get('id_flash'), self.news_item.get('title'),
                              self.news_item.get('link'), self.news_item.get('date_parsed'),
                              self.news_item.get('author'), self.news_item.get('description'),
                              self.news_item.get('location'), self.news_item.get('lat'),
                              self.news_item.get('lon'), self.news_item.get('road1'),
                              self.news_item.get('road2'), self.news_item.get('intersection'),
                              self.news_item.get('city'), self.news_item.get('street'),
                              self.news_item.get('street2'), self.news_item.get('resolution'),
                              self.news_item.get('geo_extracted_street'),
                              self.news_item.get('geo_extracted_road_no'),
                              self.news_item.get('geo_extracted_intersection'),
                              self.news_item.get('geo_extracted_city'),
                              self.news_item.get('geo_extracted_address'),
                              self.news_item.get('geo_extracted_district'),
                              self.news_item.get('accident'), self.news_item.get('source'))
        logging.info('new flash news added, is accident: ' + str(self.news_item.get('accident')))
        yield None
