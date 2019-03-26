# coding=utf-8
from anyway.parsers.news_flash.location_extraction import get_ner_location_of_text, get_db_matching_location_of_text

news_flashes = [{'description': 'הולך רגל נפצע קשה בתאונת דרכים בצומת אבליים בכביש 781',
  'road1': 70,
  'road2': 781,
  'intersection': 'צומת אבליים',
   'street': None,
   'city': None,
    'location': 'Abelim intersection on Route 781',
     'db_location': 'road1: 781, road2:70, intersection: צומת אבליים'}]

def test_news_flash():
    for news_flash in news_flashes:
        get_ner_location_of_text(news_flash['description']) == news_flash['location']
        get_db_matching_location_of_text(news_flash['description']) == news_flash['db_location']
