import logging
from datetime import datetime
import scrapy
import re
# from anyway.parsers.news_flash.news_flash_parser import insert_new_flash_news

# from .geocode_extraction import geocode_extract
# from .location_extraction import get_db_matching_location_of_text, NonUrbanAddress, UrbanAddress
# from .location_extraction import get_ner_location_of_text
from scrapy.crawler import CrawlerProcess


class HaaretzFlashScrap(scrapy.Spider):
    name = 'haaretz_flash_scrap'
    # maps_key = ''
    custom_settings = {'LOG_ENABLED': False, }

    def __init__(self):  # , maps_key='', **kwargs):
        # super().__init__(**kwargs)
        news_item = {'location': '', 'lat': 0, 'lon': 0, 'accident': True, 'source': 'haaretz'}
        self.start_urls = ["https://www.haaretz.co.il/misc/breaking-news"]
        self.news_item = news_item
        # self.maps_key = maps_key

    def parse(self, response):
        self.news_item['description'] = ''
        self.news_item['title'] = ''
        self.news_item['author'] = ''

        date = response.css('div.headlineDate h1::text').extract()
        date = datetime.strptime(date[0][-10:], '%d.%m.%Y')


        for item in response.css('ul.breaking_news_ul li').extract():
            # print("item: " + item)
            entry_parsed_date = re.search('"breaking_news_time">(.+?)</div>', item).group(1)
            entry_parsed_date = datetime.strptime(entry_parsed_date, '%H:%M')
            entry_parsed_date = entry_parsed_date.replace(year=date.year, month=date.month, day=date.day, tzinfo=None)
            item = re.search('breaking_news_title_wide">(.+?)</div>', item).group(1)
            if re.search('<a href="', item):
                link_and_title = re.search('<a href="(.+?)">(.+?)</a>', item)
                link = link_and_title.group(1)
                print("link before: " + link)
                title = link_and_title.group(2)
                if link[0:6] != 'https:':
                    link = 'https://www.haaretz.co.il' + link
                    # enter link and get first paragraph. use for 'description'
                print("link after: " + link)
            else:
                title = item

            print("title: " + title)
            if self.news_item['title'] == '':
                if title != '' and title != ' ':
                    sep_author = title.split('(')
                    self.news_item['title'] = sep_author[0]
                    if self.news_item['author'] == '' and len(sep_author) > 1 and sep_author[1].split(')'):
                        self.news_item['author'] = sep_author[1].split(')')
                    # break

        #
        # if self.news_item['accident']:
        #     if self.news_item['description'] != '':
        #         location = get_ner_location_of_text(self.news_item['description'])
        #         db_location = get_db_matching_location_of_text(self.news_item['description'])
        #         if location == '':
        #             location = get_ner_location_of_text(self.news_item['title'])
        #             db_location = get_db_matching_location_of_text(self.news_item['title'])
        #     else:
        #         location = get_ner_location_of_text(self.news_item['title'])
        #         db_location = get_db_matching_location_of_text(self.news_item['title'])
        #     self.news_item['location'] = location
        #     if type(db_location) is NonUrbanAddress:
        #         self.news_item['road1'] = db_location.road1
        #         self.news_item['road2'] = db_location.road2
        #         self.news_item['intersection'] = db_location.intersection
        #         self.news_item['city'] = None
        #         self.news_item['street'] = None
        #     elif type(db_location) is UrbanAddress:
        #         self.news_item['road1'] = None
        #         self.news_item['road2'] = None
        #         self.news_item['intersection'] = ''
        #         self.news_item['city'] = db_location.city
        #         self.news_item['street'] = db_location.street
        #     else:
        #         self.news_item['road1'] = None
        #         self.news_item['road2'] = None
        #         self.news_item['intersection'] = None
        #         self.news_item['city'] = None
        #         self.news_item['street'] = None
            # if location != 'failed to extract location':
            #     geo_location = geocode_extract(location, self.maps_key)
            #     if geo_location is None:
            #         self.news_item['lat'] = None
            #         self.news_item['lon'] = None
            #         self.news_item['location'] = None
            #         self.news_item['accident'] = False
            #     else:
            #         self.news_item['lat'] = geo_location['lat']
            #         self.news_item['lon'] = geo_location['lng']

        # insert_new_flash_news(self.news_item.get('id_flash'), self.news_item.get('title'),
        #                       self.news_item.get('link'), self.news_item.get('date_parsed'),
        #                       self.news_item.get('author'), self.news_item.get('description'),
        #                       self.news_item.get('location'), self.news_item.get('lat'),
        #                       self.news_item.get('lon'), self.news_item.get('road1'),
        #                       self.news_item.get('road2'), self.news_item.get('intersection'),
        #                       self.news_item.get('city'), self.news_item.get('street'),
        #                       self.news_item.get('accident'), self.news_item.get('source'))
        logging.info('new flash news added, is accident: '+str(self.news_item.get('accident')))
        yield None


#if __name__ == "__main__":
#    process = CrawlerProcess()
#    process.crawl(HaaretzFlashScrap)  # , entry.links[0].href, maps_key=maps_key)
#    process.start()

