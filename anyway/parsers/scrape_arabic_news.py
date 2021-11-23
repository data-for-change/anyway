#scrappig using regulare expression:
#panet-title: "<div class=\"panet-title\"><a href=\"(.*?)\">(.*?)</a><\/div>"gm (CREATES TWO GROUPS ONE FOR LINKS AND SECOND FOR THE TEXT OF THE ARTICLES)
#panet-abstract: /<div class=\"panet-abstract\"> (.*?)<\/div>/gm
#panet-time: /<div class=\"panet-time-cont\".<time class=\"panet-time\">(.*?)<\/div>/gm

import requests
import re

def scrape():
    Website_Content = requests.get("http://www.panet.co.il/category/home/2")
    #print(Website_Content.text)

    #panet-titles:
    regex1 = r"<div class=\"panet-title\">(.*?)<\/div>"
    matches1 = re.finditer(regex1, Website_Content.text, re.MULTILINE)

    f1 = open("/Users/rabea/titles.txt", "w")

    for matchNum, match in enumerate(matches1, start=1):

        # print("Match {matchNum} was found at {start}-{end}: {match}".format(matchNum=matchNum, start=match.start(),
        #                                                                    end=match.end(), match=match.group()))

        for groupNum in range(0, len(match.groups())):
            groupNum = groupNum + 1

            # print("Group {groupNum} found at {start}-{end}: {group}".format(groupNum=groupNum, start=match.start(groupNum),
            #                                                                end=match.end(groupNum),
            #                                                                group=match.group(groupNum)))
            #print(match.group(groupNum))
            f1.write(match.group(groupNum))
            f1.write('\n')


    f1.close()


    #panet-abstracts ***http://www.panet.co.il/category/home/2***:


    regex2 = r"<div class=\"panet-abstract\">(.*?)</div>"
    matches2 = re.finditer(regex2, Website_Content.text, re.MULTILINE)

    f2 = open("/Users/rabea/abstracts.txt", "w")
    for matchNum, match in enumerate(matches2, start=1):

        #print("Match {matchNum} was found at {start}-{end}: {match}".format(matchNum=matchNum, start=match.start(),
                                                                         #   end=match.end(), match=match.group()))

        for groupNum in range(0, len(match.groups())):
            groupNum = groupNum + 1

            # print("Group {groupNum} found at {start}-{end}: {group}".format(groupNum=groupNum, start=match.start(groupNum),
            #                                                                 end=match.end(groupNum),
            #                                                                 group=match.group(groupNum)))
            f2.write(match.group(groupNum))
            f2.write('\n')

    f2.close()
    #panet-time:

    regex3 = r"<div class=\"panet-time-cont\".<time class=\"panet-time\">(.*?)<\/div>"
    matches3 = re.finditer(regex3, Website_Content.text, re.MULTILINE)

    f3 = open("/Users/rabea/articles-pub-time.txt", 'w')
    for matchNum, match in enumerate(matches3, start=1):

        # print("Match {matchNum} was found at {start}-{end}: {match}".format(matchNum=matchNum, start=match.start(),
        #                                                                     end=match.end(), match=match.group()))

        for groupNum in range(0, len(match.groups())):
            groupNum = groupNum + 1

            # print("Group {groupNum} found at {start}-{end}: {group}".format(groupNum=groupNum, start=match.start(groupNum),
            #                                                                 end=match.end(groupNum),
            #                                                                 group=match.group(groupNum)))

            f3.write(match.group(groupNum))
            f3.write('\n')
    f3.close()


if __name__ == '__main__':
    # scrape()

    for page in range(1, 10):
        content = requests.get(f"http://www.panet.co.il/category/home/2/{page}/")
        contenttxt = content.text
        file_txt = open(f"/Users/rabea/PycharmProjects/Efraim/PanetPage{page}.txt", "w")
        file_txt.write(contenttxt)
        file_txt.close()

        # file_yaml = open(f"/Users/rabea/PycharmProjects/Efraim/PanetPage{page}.yaml", "w")
        # file_yaml.write(contenttxt)
        # file_yaml.close()


