import scrapy
import logging

from ..anyway.parsers.news_flash import insert_new_flash_news
from .geocode_extraction import geocode_extract
from .location_extraction import get_location_of_text


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

        for item in response.css('div.text14 p::text').extract():
            item = item.strip().replace('&nbsp', '').replace('\xa0', '')
            if self.news_item['description'] == '':
                if item != '' and item != ' ' and not (item.startswith('(') and item.endswith(')')):
                    self.news_item['description'] = item
            if self.news_item['author'] == '' and (item.startswith('(') and item.endswith(')')):
                self.news_item['author'] = item.split('(')[1].split(')')[0]
                break

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

        if self.news_item['accident']:
            if self.news_item['description'] != '':
                location = get_location_of_text(self.news_item['description'])
                if location == '':
                    location = get_location_of_text(self.news_item['title'])
            else:
                location = get_location_of_text(self.news_item['title'])
            self.news_item['location'] = location
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
        insert_new_flash_news(self.news_item['id_flash'], self.news_item['title'],
                              self.news_item['link'], self.news_item['date_parsed'],
                              self.news_item['author'], self.news_item['description'],
                              self.news_item['location'], self.news_item['lat'],
                              self.news_item['lon'], self.news_item['accident'], self.news_item['source'])
        logging.info('new flash news added, is accident: '+str(self.news_item['accident']))
        yield None
