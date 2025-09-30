
import requests
import re
import json
from datetime import datetime


class ArticleMetaData:
    article_pub_date: datetime
    abstract: str
    title: str

    def __init__(self, _article_pub_date, _abstract, _title):
        self.article_pub_date = _article_pub_date
        self.abstract = _abstract
        self.title = _title


def scrape(panet_page):

    website_content = requests.get(f"http://www.panet.co.il/category/home/2/{panet_page}")

    """ Historic article titles: """

    regex1 = r"<div class=\"panet-title\">(.*?)<\/div>"
    matches1 = re.finditer(regex1, website_content.text, re.MULTILINE)

    with open(f"titles_{panet_page}.txt", "w", encoding="utf-8") as f1:

        for matchNum, match in enumerate(matches1, start=1):

            for groupNum in range(0, len(match.groups())):
                groupNum = groupNum + 1
                f1.write(match.group(groupNum))
                f1.write('\n')

    """ Historic article abstracts: """

    regex2 = "<div class=\"panet-abstract\">(.*?)<(?:.*?)</div>"
    matches2 = re.finditer(regex2, website_content.text, re.MULTILINE)

    with open(f"abstracts_{panet_page}.txt", "w", encoding="utf-8") as f2:
        for matchNum, match in enumerate(matches2, start=1):
            f2.write(match.group(1))
            f2.write('\n')

    """ Historic article pub time: """

    regex3 = r"<div class=\"panet-time-cont\".<time class=\"panet-time\">(.*?)<\/div>"
    matches3 = re.finditer(regex3, website_content.text, re.MULTILINE)

    with open(f"articles-pub-time_{panet_page}.txt", 'w', encoding='utf-8') as f3:
        for matchNum, match in enumerate(matches3, start=1):

            for groupNum in range(0, len(match.groups())):
                groupNum = groupNum + 1
                f3.write(match.group(groupNum))
                f3.write('\n')

    """  Code to scraping ABSTRACTS in a specified page range """


def scrape_abstracts():

    for page in range(1, 5):
        content = requests.get(f"http://www.panet.co.il/category/home/2/{page}/")
        content_txt = content.text
        with open(f"PanetPageText{page}.txt", "w", encoding='utf-8') as file_txt:
            regex2 = r"<div class=\"panet-abstract\">(.*?)<(.*?)</div>"
            matches2 = re.finditer(regex2, content_txt, re.MULTILINE)
            for matchNum, match in enumerate(matches2, start=1):

                for groupNum in range(0, len(match.groups())):
                    file_txt.write(match.group(1))
                    file_txt.write('\n')


def generate_article_dict_and_classify(panet_page):

    key_list = [line.strip('\n') for line in open(f"articles-pub-time_{panet_page}.txt", 'r', encoding='utf-8')]
    value_list = [line.strip('\n') for line in open(f"abstracts_{panet_page}.txt", 'r', encoding='utf-8')]
    # print(len(key_list))
    # print(len(value_list))
    assert len(key_list) == len(value_list)
    article_dict = dict(zip(key_list, value_list))
    with open(f"article_dict_{panet_page}.txt", "w", encoding='utf-8') as f4:
        f4.write(json.dumps(article_dict))

    key_keywords = ["حادث طرق", "حوادث طرق", "اصطدام", " دهس", "سائق", "سيارة", "انقلاب", "شاحنة", "مشاة"]
    counter = 0
    for line in value_list:
        if any([keyword in line for keyword in key_keywords]):
            counter += 1
            with open(f"Car_Accident_News_Flash_Number_{counter}.txt", "w", encoding='utf-8') as CarAccidentNews:
                CarAccidentNews.write(line.strip())
                CarAccidentNews.write('\n')


def unified_scrape():

    all_articles_dict = {}
    website_content = requests.get("http://www.panet.co.il/category/home/2")
    regex1 = r"<div class=\"panet-title\"><a href=\"/article/(.*?)\">(.*?)<\/a><\/div>"
    matches1 = re.finditer(regex1, website_content.text, re.MULTILINE)
    for matchNum, match in enumerate(matches1, start=1):
        article_number = int(match.group(1))
        article_title = match.group(2)
        all_articles_dict[article_number] = ArticleMetaData(
            _article_pub_date=datetime.now(),
            _title=article_title.strip(),
            _abstract=""
        )

    with open("articles.tsv", "w") as f:
        for tsv in all_articles_dict.keys():
            val = all_articles_dict[tsv]
            f.write(f"{tsv}\t{val.title}\t{val.article_pub_date}\n")


if __name__ == '__main__':
    for panet_page in range(0, 301):
        scrape(panet_page)
        generate_article_dict_and_classify(panet_page)
        # scrape_abstracts()
        # unified_scrape()
