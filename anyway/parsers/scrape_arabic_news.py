#scrappig using regulare expression:
#panet-title: "<div class=\"panet-title\"><a href=\"(.*?)\">(.*?)</a><\/div>"gm (CREATES TWO GROUPS ONE FOR LINKS AND SECOND FOR THE TEXT OF THE ARTICLES)
#panet-abstract: /<div class=\"panet-abstract\"> (.*?)<\/div>/gm
#panet-time: /<div class=\"panet-time-cont\".<time class=\"panet-time\">(.*?)<\/div>/gm

from dataclasses import dataclass
import json
import requests
import re


@dataclass
class PanetArticle:
    title: str
    abstract: str
    time: str


def is_panet_accident(title, abstract):
    keywords = ["حادث طرق", "حوادث طرق", "اصطدام", " دهس", "سائق", "سيارة", "انقلاب", "شاحنة", "مشاة"]

    return any(keyword in title+" "+abstract for keyword in keywords)


def scrape():
    panet_dict = dict()

    website_content = requests.get("http://www.panet.co.il/category/home/2")

    #panet-titles:
    regex = r"<div class=\"panet-title\"><a href=\"(.*?)\">(.*?)</a><\/div><div class=\"panet-abstract\">(.*?)</div></div></div><div class=\"panet-time-cont\".<time class=\"panet-time\">(.*?)<\/div>"
    matches1 = re.finditer(regex, website_content.text, re.MULTILINE)

    for matchNum, match in enumerate(matches1, start=1):
        url = match.group(1)
        title = match.group(2)
        abstract = match.group(3)
        time = match.group(4)
        if is_panet_accident(title, abstract):
            article = PanetArticle(title=title, abstract=abstract, time=time)
            panet_dict[url] = article

    f = open("panet/panet_accidents.tsv", "w")
    for url in panet_dict.keys():
        article = panet_dict[url]
        f.write(f"{url}\t{article.title}\t{article.time}\t{article.abstract},\n")
    f.close()


if __name__ == '__main__':
    scrape()

    """
    for page in range(1, 10):
        content = requests.get(f"http://www.panet.co.il/category/home/2/{page}/")
        contenttxt = content.text
        file_txt = open(f"/Users/rabea/PycharmProjects/Efraim/PanetPage{page}.txt", "w")
        file_txt.write(contenttxt)
        file_txt.close()

        # file_yaml = open(f"/Users/rabea/PycharmProjects/Efraim/PanetPage{page}.yaml", "w")
        # file_yaml.write(contenttxt)
        # file_yaml.close()
    """
