import logging

import scrapy
from anyway.parsers.news_flash.news_flash_parser import insert_new_flash_news

from .geocode_extraction import geocode_extract
from .location_extraction import get_db_matching_location_of_text, NonUrbanAddress, UrbanAddress
from .location_extraction import get_ner_location_of_text


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
        try:
            for item in response.css('div.text14 p::text').extract():
                item = item.strip().replace('&nbsp', '').replace('\xa0', '')
                if self.news_item['description'] == '':
                    if item != '' and item != ' ' and not (item.startswith('(') and item.endswith(')')):
                        self.news_item['description'] = item
                if self.news_item['author'] == '' and (item.startswith('(') and item.endswith(')')):
                    self.news_item['author'] = item.split('(')[1].split(')')[0]
                    break
        except:
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
        except:
            pass
        try:
            if self.news_item['accident']:
                if self.news_item['description'] != '':
                    location = get_ner_location_of_text(self.news_item['description'])
                    db_location = get_db_matching_location_of_text(self.news_item['description'])
                    if location == '':
                        location = get_ner_location_of_text(self.news_item['title'])
                        db_location = get_db_matching_location_of_text(self.news_item['title'])
                else:
                    location = get_ner_location_of_text(self.news_item['title'])
                    db_location = get_db_matching_location_of_text(self.news_item['title'])
                self.news_item['location'] = location
                if type(db_location) is NonUrbanAddress:
                    self.news_item['road1'] = db_location.road1
                    self.news_item['road2'] = db_location.road2
                    self.news_item['intersection'] = db_location.intersection
                    self.news_item['city'] = None
                    self.news_item['street'] = None
                elif type(db_location) is UrbanAddress:
                    self.news_item['road1'] = None
                    self.news_item['road2'] = None
                    self.news_item['intersection'] = ''
                    self.news_item['city'] = db_location.city
                    self.news_item['street'] = db_location.street
                else:
                    self.news_item['road1'] = None
                    self.news_item['road2'] = None
                    self.news_item['intersection'] = None
                    self.news_item['city'] = None
                    self.news_item['street'] = None
                if location != 'failed to extract location':
                    geo_location = geocode_extract(location, self.maps_key)
                    if geo_location is None:
                        self.news_item['lat'] = 0
                        self.news_item['lon'] = 0
                        self.news_item['location'] = ''
                        self.news_item['accident'] = False
                    else:
                        self.news_item['lat'] = geo_location['lat']
                        self.news_item['lon'] = geo_location['lng']
        except:
            pass

        insert_new_flash_news(self.news_item.get('id_flash'), self.news_item.get('title'),
                              self.news_item.get('link'), self.news_item.get('date_parsed'),
                              self.news_item.get('author'), self.news_item.get('description'),
                              self.news_item.get('location'), self.news_item.get('lat'),
                              self.news_item.get('lon'), self.news_item.get('road1'),
                              self.news_item.get('road2'), self.news_item.get('intersection'),
                              self.news_item.get('city'), self.news_item.get('street'),
                              self.news_item.get('accident'), self.news_item.get('source'))
        
        logging.info('new flash news added, is accident: '+str(self.news_item.get('accident')))
        yield None
