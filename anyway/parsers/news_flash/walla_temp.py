# -*- coding: utf-8 -*-
from datetime import datetime
import requests
from bs4 import BeautifulSoup

rss_link = ["https://news.walla.co.il/breaking"]
response = requests.get(rss_link[0])
html_soup = BeautifulSoup(response.text, "html.parser")
news_flashes = html_soup.find_all('article', class_='article fc ')

for item in news_flashes:
    datetime_ = item.find("time").get('datetime')
    datetime_ = datetime.strptime(datetime_, "%Y-%m-%d %H:%M")
    print("___")
    print(f"date and time: {str(datetime_)}")
    author = item.find('span', class_='author').get_text()
    print(f"author: {author}")
    try:
        title = item.find('span', class_='text').get_text()
    except:
        title = ''

    try:
        link_to_article = item.find("a").get("data-href")
        response = requests.get(link_to_article)
        article_soup = BeautifulSoup(response.text, "html.parser")
        if title == '':
            title = article_soup.find('h1').get_text()
        article_summary = article_soup.find('section', class_='article-content').find('p').find(text=True, recursive=False)
    except:
        link_to_article = "None"
        article_summary = ''
    print("link to article: " + link_to_article)
    print("article title: " + title)
    print("article summary: " + article_summary)
