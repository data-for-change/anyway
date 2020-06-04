import datetime
import json

import pytest

from anyway.parsers import rss_sites, twitter, location_extraction
from anyway.parsers.news_flash_classifiers import classify_tweets
from anyway.parsers import secrets


def fetch_html_walla(link):
    with open("tests/" + link.split("/")[-1] + ".html", encoding="utf-8") as f:
        return f.read()


def fetch_html_ynet(link):
    with open("tests/" + link[-len("0,7340,L-5735229,00.html") :], encoding="utf-8") as f:
        return f.read()


def fetch_rss_walla(link):
    with open("tests/walla.xml", encoding="utf-8") as f:
        return f.read()


def fetch_rss_ynet(link):
    with open("tests/ynet.xml", encoding="utf-8") as f:
        return f.read()


def test_scrape_walla():
    items_expected = [
        {
            "date_parsed": datetime.datetime(2020, 5, 23, 16, 55),
            "title": 'פרקליטי רה"מ יתלוננו נגד רביב דרוקר על שיבוש הליכי משפט',
            "link": "https://news.walla.co.il/break/3362504",
            "source": "walla",
            "author": "דניאל דולב",
            "description": 'פרקליטיו של ראש הממשלה בנימין נתניהו מתכוונים להגיש הערב (שבת) תלונה ליועץ המשפטי לממשלה, אביחי מנדלבליט, נגד העיתונאי רביב דרוקר בטענה ששיבש הליכי משפט והדיח עד בתוכניתו "המקור". התלונה מתייחסת לראיונות שנתנו לתוכנית עדי תביעה במשפטו של נתניהו, בהם שאול אלוביץ\' ומומו פילבר.]]>',
        },
        {
            "date_parsed": datetime.datetime(2020, 5, 22, 13, 14),
            "title": "פקיסטן: לפחות נוסע אחד שרד את התרסקות המטוס",
            "link": "https://news.walla.co.il/break/3362389",
            "source": "walla",
            "author": "רויטרס",
            "description": "לפחות נוסע אחד שרד מהתרסקות המטוס הפקיסטני היום (שישי) באזור מגורים בקראצ'י - כך אמר גורם בממשל המקומי. בהודעתו אמר דובר ממשלת המחוז כי בנקאי שהיה על המטוס אותר לאחר ששרד את ההתרסקות. מרשות התעופה האזרחית של פקיסטן נמסר כי היו 91 נוסעים ושמונה אנשי צוות על מטוס איירבוס A320.]]>",
        },
    ]

    items_actual = list(
        rss_sites.scrape("walla", fetch_rss=fetch_rss_walla, fetch_html=fetch_html_walla)
    )
    assert items_actual == items_expected


def test_scrape_ynet():
    items_expected = [
        {
            "date_parsed": datetime.datetime(2020, 5, 22, 18, 27, 32),
            "title": "קפריסין הודיעה: ישראלים יוכלו להיכנס למדינה החל מה-9 ביוני",
            "link": "http://www.ynet.co.il/articles/0,7340,L-5735229,00.html",
            "source": "ynet",
            "author": "איתמר אייכנר",
            "description": ": \"שר התחבורה של קפריסין הודיע על תוכנית לפתיחת שדות התעופה וחידוש הטיסות החל מה-9 ביוני. התוכנית שאושרה בידי הממשלה חולקה לשני שלבים לפי תאריכים ומדינות שיורשו להיכנס בשעריה. עד ה-19 ביוני נוסעים מכל המקומות יצטרכו להיבדק לקורונה 72 שעות לפני מועד הטיסה. מה-20 ביוני יידרשו לכך רק נוסעים משוויץ, פולין רומניה, קרואטיה, אסטוניה וצ'כיה. בתי המלון ייפתחו ב-1 ביוני, וחובת הבידוד תבוטל ב-20 ביוני.   ",
        },
        {
            "date_parsed": datetime.datetime(2020, 5, 22, 15, 8, 48),
            "link": "http://www.ynet.co.il/articles/0,7340,L-5735178,00.html",
            "source": "ynet",
            "author": "אלישע בן קימון",
            "title": "צוותי כיבוי פועלים בשריפת קוצים שמתפשטת סמוך ליצהר שבשומרון",
            "description": ': "צוותי כיבוי פועלים בשריפת קוצים שמתפשטת לעבר ההתנחלות יצהר שבשומרון. לוחמי האש פועלים למניעת התקדמות השריפה ליצהר על ידי חתירה למגע עם האש ובסיוע מטוסי כיבוי. נמסר כי קיימת סכנה למוצב צבאי במקום.   ',
        },
    ]

    items_actual = list(
        rss_sites.scrape("ynet", fetch_rss=fetch_rss_ynet, fetch_html=fetch_html_ynet)
    )
    assert items_actual == items_expected


@pytest.mark.slow
def test_scrape_sanity_online():
    next(rss_sites.scrape('ynet'))
    next(rss_sites.scrape('walla'))

    if not secrets.exists('TWITTER_CONSUMER_SECRET'):
        pytest.skip('Could not find TWITTER_CONSUMER_SECRET')

    assert twitter.scrape('mda_israel', count=1)


twitter_expected_list = [
    {
         'link': 'https://twitter.com/mda_israel/status/1267054794587418630',
         'date_parsed': datetime.datetime(2020, 5, 31, 14, 26, 18),
         'source': 'twitter',
         'author': 'מגן דוד אדום',
         'title': 'בשעה 13:19 התקבל דיווח במוקד 101 של מד"א במרחב ירושלים על פועל שנפצע במהלך עבודתו במפעל באזור התעשיה עטרות בירושלים. חובשים ופראמדיקים של מד"א מעניקים טיפול רפואי ומפנים לבי"ח שערי צדק גבר בן 31 במצב קשה, עם חבלת ראש.',
         'description': 'בשעה 13:19 התקבל דיווח במוקד 101 של מד"א במרחב ירושלים על פועל שנפצע במהלך עבודתו במפעל באזור התעשיה עטרות בירושלים. חובשים ופראמדיקים של מד"א מעניקים טיפול רפואי ומפנים לבי"ח שערי צדק גבר בן 31 במצב קשה, עם חבלת ראש.',
         'tweet_id': '1267054794587418630', 'tweet_ts': 'Sun May 31 11:26:18 +0000 2020',
         'accident': False
    },
    {
         'link': 'https://twitter.com/mda_israel/status/1267037315869880321',
         'date_parsed': datetime.datetime(2020, 5, 31, 13, 16, 51),
         'source': 'twitter',
         'author': 'מגן דוד אדום',
         'title': 'בשעה 12:38 התקבל דיווח במוקד 101 של מד"א במרחב ירדן על ת.ד סמוך למסעדה. חובשים ופראמדיקים של מד"א מעניקים טיפול רפואי ל4 פצועים, בהם 1 מחוסר הכרה.',
         'description': 'בשעה 12:38 התקבל דיווח במוקד 101 של מד"א במרחב ירדן על ת.ד סמוך למסעדה. חובשים ופראמדיקים של מד"א מעניקים טיפול רפואי ל4 פצועים, בהם 1 מחוסר הכרה.',
         'tweet_id': '1267037315869880321',
         'tweet_ts': 'Sun May 31 10:16:51 +0000 2020',
         'accident': True,
         'location': 'בשעה 12:38 התקבל דיווח במוקד 101 של מד"א במרחב ירדן על ת',  # Note: erroneous expected
         'lat': 32.052603,
         'lon': 34.7666179,
         'resolution': 'רחוב',
         'region_hebrew': None,
         'district_hebrew': None,
         'yishuv_name': None,
         'street1_hebrew': None,
         'street2_hebrew': None,
         'non_urban_intersection_hebrew': None,
         'road1': None,
         'road2': None,
         'road_segment_name': None
     }
]


def test_twitter_parse():
    with open('tests/twitter.json') as f:
        tweets = json.load(f)

    actual_list = [twitter.parse_tweet(tweet, 'mda_israel') for tweet in tweets]
    for actual, expected in zip(actual_list, twitter_expected_list):
        # check only the parse-only part
        assert all([actual[k] == expected[k] for k in actual])

        actual['accident'] = classify_tweets(actual['description'])
        assert actual['accident'] == expected['accident']

    if not secrets.exists('GOOGLE_MAPS_KEY'):
        pytest.skip('Could not find GOOGLE_MAPS_KEY')

    for actual, expected in zip(actual_list, twitter_expected_list):
        if actual['accident']:
            location_extraction.extract_geo_features(actual)
            # check only the extracted part
            assert all([actual[k] == expected[k] for k in expected])
