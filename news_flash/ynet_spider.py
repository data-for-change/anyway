import scrapy

from geocode_extraction import geocode_extract
from location_extraction import get_location_of_text


class YnetFlashScrap(scrapy.Spider):
    name = "ynet_flash_scrap"
    news_item = {}
    cursor = None
    maps_key = ""
    custom_settings = {'LOG_ENABLED': False, }

    def __init__(self, url="", news_item=None, cur="", maps_key="", **kwargs):
        super().__init__(**kwargs)
        if news_item is None:
            news_item = {}
        self.start_urls = [url]
        self.news_item = news_item
        self.cursor = cur
        self.maps_key = maps_key

    def parse(self, response):
        self.news_item["description"] = ""
        self.news_item["author"] = ""

        for item in response.css('div.text14 p::text').extract():
            item = item.strip().replace("&nbsp", "").replace("\xa0", "")
            if self.news_item["description"] == "":
                if item != "" and item != " " and not (item.startswith('(') and item.endswith(')')):
                    self.news_item["description"] = item
            if self.news_item["author"] == "" and (item.startswith('(') and item.endswith(')')):
                self.news_item["author"] = item.split('(')[1].split(')')[0]
                break

        span_response = response.css('div.text14 span::text').extract()

        for item in enumerate(span_response):
            span_item = str(item[1]).strip().replace("&nbsp", "").replace("\xa0", "")
            if self.news_item["author"] == "":
                if span_item.startswith('(') and span_item.endswith(')'):
                    self.news_item["author"] = span_item.split('(')[1].split(')')[0]
            if self.news_item["description"] == "":
                if span_item != "" and span_item != " " and \
                        not (span_item.startswith('(') and span_item.endswith(')')):
                    self.news_item["description"] = span_item

        if self.news_item["description"] != "" and not self.news_item["accident"]:
            if ("תאונ" in self.news_item["description"] and "תאונת עבודה" not in self.news_item["description"] and
                "תאונות עבודה" not in self.news_item["description"]) or "נפגע מרכב" in self.news_item["description"] \
                    or "נפגעה מרכב" in self.news_item["description"] or \
                    "נפגעו מרכב" in self.news_item["description"] or \
                    "פגיעת רכב" in self.news_item["description"] or \
                    "פגיעת אוטובוס" in self.news_item["description"] or \
                    "פגיעת משאית" in self.news_item["description"] or \
                    "פגיעת קטנוע" in self.news_item["description"] or \
                    "פגיעת אופנוע" in self.news_item["description"] or \
                    "נפגע מאוטובוס" in self.news_item["description"] or \
                    "נפגעה מאוטובוס" in self.news_item["description"] or \
                    "נפגעו מאוטובוס" in self.news_item["description"] or \
                    "נפגע ממשאית" in self.news_item["description"] or \
                    "נפגעה ממשאית" in self.news_item["description"] or \
                    "נפגעו ממשאית" in self.news_item["description"] or \
                    "נפגע מאופנוע" in self.news_item["description"] or \
                    "נפגעה מאופנוע" in self.news_item["description"] or \
                    "נפגעו מאופנוע" in self.news_item["description"] or \
                    "נפגע מקטנוע" in self.news_item["description"] or \
                    "נפגעה מקטנוע" in self.news_item["description"] or \
                    "נפגעו מקטנוע" in self.news_item["description"]:
                self.news_item["accident"] = True
            else:
                self.news_item["accident"] = False
        elif self.news_item["description"] != "" and self.news_item["accident"] and (
                "תאונת עבודה" in self.news_item["description"] or
                "תאונות עבודה" in self.news_item["description"]):
            self.news_item["accident"] = False
        if self.news_item["accident"]:
            if self.news_item["description"] != "":
                location = get_location_of_text(self.news_item["description"])
            else:
                location = get_location_of_text(self.news_item["title"])
            self.news_item["location"] = location
            if location != "":
                geo_location = geocode_extract(location, self.maps_key)
                if geo_location is None:
                    self.news_item["lat"] = 0
                    self.news_item["lon"] = 0
                    self.news_item["location"] = ""
                    self.news_item["accident"] = False
                else:
                    self.news_item["lat"] = geo_location["lat"]
                    self.news_item["lon"] = geo_location["lng"]
            else:
                self.news_item["location"] = "failed to extract location"

        self.cursor.execute("INSERT INTO news_flash (id,title, link, date, author, description, location, lat, lon, "
                            "accident, source) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (self.news_item["id_flash"], self.news_item["title"],
                             self.news_item["link"], self.news_item["date_parsed"],
                             self.news_item["author"], self.news_item["description"],
                             self.news_item["location"], self.news_item["lat"],
                             self.news_item["lon"], self.news_item["accident"], self.news_item["source"]))
        yield None
