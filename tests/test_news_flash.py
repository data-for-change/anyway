import datetime
import json
import mock

import pytest

from anyway.parsers import rss_sites, twitter, location_extraction
from anyway.parsers.news_flash_classifiers import classify_tweets, classify_rss
from anyway import secrets
from anyway.parsers.news_flash_db_adapter import init_db
from anyway.models import NewsFlash
from anyway.parsers import timezones
from anyway.infographics_utils import is_news_flash_resolution_supported
from anyway.parsers.infographics_data_cache_updater import is_in_cache


def verify_cache(news_flash_list):
    for nf in news_flash_list:
        if is_news_flash_resolution_supported(nf):
            assert is_in_cache(nf), f"NewsFlash {nf.get_id()} not in cache"


def fetch_html_walla(link):
    with open("tests/" + link.split("/")[-1] + ".html", encoding="utf-8") as f:
        return f.read()


def fetch_html_ynet(link):
    with open(f'tests/{link[-len("HkhoCYxnO"):]}.html', encoding="utf-8") as f:
        return f.read()


def to_dict(newsflash):
    res = newsflash.__dict__.copy()
    del res["_sa_instance_state"]
    return res


def assert_all_equal(items_actual, items_expected):
    assert len(items_actual) == len(items_expected)
    for i, (actual, expected) in enumerate(zip(items_actual, items_expected)):
        for k in to_dict(expected):
            assert (i, getattr(actual, k)) == (i, getattr(expected, k))


def test_scrape_walla():
    # Reuters is marked differently than Walla's authors
    items_expected = [
        NewsFlash(
            date=datetime.datetime(2021, 6, 23, 16, 49, tzinfo=timezones.ISREAL_SUMMER_TIMEZONE),
            title='חובת המסכות תוחזר אם יהיה ממוצע שבועי של 100 חולים ביום',
            link="https://news.walla.co.il/break/3443829",
            source="walla",
            author="מירב כהן",
            description='חובת המסכות תוחזר בחללים סגורים אם יהיה ממוצע שבועי של 100 חולים ביום - כך הוחלט היום (רביעי) בדיון השרים.',
        ),
        NewsFlash(
            date=datetime.datetime(2021, 7, 14, 9, 10, tzinfo=timezones.ISREAL_SUMMER_TIMEZONE),
            title="פקיסטן: שמונה הרוגים בפיצוץ באוטובוס",
            link="https://news.walla.co.il/break/3448092",
            source="walla",
            author="רויטרס",
            description="שמונה בני אדם נהרגו הבוקר (רביעי) בפיצוץ אוטובוס בצפון פקיסטן. בין ההרוגים, שישה מהנדסים תושבי סין. טרם ידוע מקור הפיצוץ.",
        ),
    ]

    items_actual = list(
        rss_sites.scrape("walla", rss_source="tests/walla.xml", fetch_html=fetch_html_walla)
    )
    assert_all_equal(items_actual, items_expected)
    verify_cache(items_actual)


def test_scrape_ynet():
    items_expected = [
        # note: the file holds date in winter timezone, so here it is described as summer timezone - +1 hour
        NewsFlash(
            date=datetime.datetime(
                2021, 6, 23, 13, 58, 51, tzinfo=timezones.ISREAL_SUMMER_TIMEZONE
            ),
            title='עבודות לתועלת הציבור לסייעת "גן מתוק" בגבעתיים שבו הותקפו ילדים',
            link='https://www.ynet.co.il/news/article/HkhoCYxnO',
            source="ynet",
            author="גלעד מורג",
            description='בית משפט השלום בתל אביב קבע שלא להרשיע את סייעת "גן מתוק" בגבעתיים, אורנה אקבלי. הוא קבע שביצעה עבירת סיוע לתקיפה אך בגלל נסיבות החריגות של המקרה ובגלל שהייתה מעורבת בדיווח על האלימות בגן לא תורשע. עם זאת על אקבלי הוטלו 180 שעות עבודות לתועלת הציבור, צו מבחן, ו-3,000 שקל פיצויים.',
        ),
    ]

    items_actual = list(
        rss_sites.scrape("ynet", rss_source="tests/ynet.xml", fetch_html=fetch_html_ynet)
    )
    assert_all_equal(items_actual, items_expected)
    verify_cache(items_actual)


def test_sanity_get_latest_date():
    db = init_db()
    db.get_latest_date_of_source("ynet")
    db.get_latest_date_of_source("walla")
    db.get_latest_date_of_source("twitter")


@pytest.mark.slow
def test_scrape_sanity_online_ynet():
    next(rss_sites.scrape("ynet"))


@pytest.mark.slow
def test_scrape_sanity_online_walla():
    next(rss_sites.scrape("walla"))


@pytest.mark.slow
def test_scrape_sanity_online_twitter():
    if not secrets.exists("TWITTER_CONSUMER_SECRET"):
        pytest.skip("Could not find TWITTER_CONSUMER_SECRET")

    assert twitter.scrape("mda_israel", count=1)


twitter_expected_list = [
    NewsFlash(
        link="https://twitter.com/mda_israel/status/1267054794587418630",
        date=datetime.datetime(2020, 5, 31, 14, 26, 18, tzinfo=timezones.ISREAL_SUMMER_TIMEZONE),
        source="twitter",
        author="מגן דוד אדום",
        title='בשעה 13:19 התקבל דיווח במוקד 101 של מד"א במרחב ירושלים על פועל שנפצע במהלך עבודתו במפעל באזור התעשיה עטרות בירושלים. חובשים ופראמדיקים של מד"א מעניקים טיפול רפואי ומפנים לבי"ח שערי צדק גבר בן 31 במצב קשה, עם חבלת ראש.',
        description='בשעה 13:19 התקבל דיווח במוקד 101 של מד"א במרחב ירושלים על פועל שנפצע במהלך עבודתו במפעל באזור התעשיה עטרות בירושלים. חובשים ופראמדיקים של מד"א מעניקים טיפול רפואי ומפנים לבי"ח שערי צדק גבר בן 31 במצב קשה, עם חבלת ראש.',
        tweet_id=1267054794587418630,
        accident=False,
    ),
    NewsFlash(
        link="https://twitter.com/mda_israel/status/1267037315869880321",
        date=datetime.datetime(2020, 5, 31, 13, 16, 51, tzinfo=timezones.ISREAL_SUMMER_TIMEZONE),
        source="twitter",
        author="מגן דוד אדום",
        title='בשעה 12:38 התקבל דיווח במוקד 101 של מד"א במרחב ירדן על ת.ד סמוך למסעדה. חובשים ופראמדיקים של מד"א מעניקים טיפול רפואי ל4 פצועים, בהם 1 מחוסר הכרה.',
        description='בשעה 12:38 התקבל דיווח במוקד 101 של מד"א במרחב ירדן על ת.ד סמוך למסעדה. חובשים ופראמדיקים של מד"א מעניקים טיפול רפואי ל4 פצועים, בהם 1 מחוסר הכרה.',
        tweet_id=1267037315869880321,
        accident=True,
        location='בשעה 12:38 התקבל דיווח במוקד 101 של מד"א במרחב ירדן על ת',  # Note: erroneous expected
        lat=32.052603,
        lon=34.7666179,
        resolution="רחוב",
    ),
]


def test_twitter_parse():
    with open("tests/twitter.json") as f:
        tweets = json.load(f)

    actual_list = [twitter.parse_tweet(tweet, "mda_israel") for tweet in tweets]
    raw_fields = ["link", "date", "source", "author", "title", "description", "tweet_id"]
    for actual, expected in zip(actual_list, twitter_expected_list):
        for k in raw_fields:
            assert getattr(actual, k) == getattr(expected, k)

        actual.accident = classify_tweets(actual.description)
        assert actual.accident == expected.accident


def test_location_extraction_extract_geo_features():
    if not secrets.exists("GOOGLE_MAPS_KEY"):
        pytest.skip("Could not find GOOGLE_MAPS_KEY")

    parsed = dict(
        link="https://twitter.com/mda_israel/status/1253010741080326148",
        title='בשעה 19:39 התקבל דיווח במוקד 101 של מד"א במרחב דן על הולכת רגל שככל הנראה נפגעה מאופנוע ברחוב ביאליק ברמת גן. צוותי מד"א מעניקים טיפול ומפנים לבי"ח איכילוב 2 פצועים: אישה כבת 30 במצב קשה, עם חבלה רב מערכתית ורוכב האופנוע, צעיר בן 18 במצב בינוני, עם חבלות בראש ובגפיים.',
        description='בשעה 19:39 התקבל דיווח במוקד 101 של מד"א במרחב דן על הולכת רגל שככל הנראה נפגעה מאופנוע ברחוב ביאליק ברמת גן. צוותי מד"א מעניקים טיפול ומפנים לבי"ח איכילוב 2 פצועים: אישה כבת 30 במצב קשה, עם חבלה רב מערכתית ורוכב האופנוע, צעיר בן 18 במצב בינוני, עם חבלות בראש ובגפיים.',
        source="twitter",
        tweet_id=1253010741080326144,
        author="מגן דוד אדום",
        date=datetime.datetime(2020, 4, 22, 19, 39, 51),
        accident=True,
    )
    expected = NewsFlash(
        **parsed,
        lat=32.0861791,
        lon=34.8098462,
        resolution="רחוב",
        location="רחוב ביאליק ברמת גן",
        road_segment_name=None,
        district_hebrew=None,
        non_urban_intersection_hebrew=None,
        region_hebrew=None,
        road1=None,
        road2=None,
        street1_hebrew="ביאליק",
        street2_hebrew=None,
        yishuv_name="רמת גן",
    )

    actual = NewsFlash(**parsed)
    location_extraction.extract_geo_features(init_db(), actual)
    for k in to_dict(expected):
        assert getattr(actual, k) == getattr(expected, k)


def test_location_extraction_extract_location_text():
    for description, expected_location_text in [
        (
                'רוכב אופנוע כבן 20 נפצע באורח בינוני מפגיעת רכב היום (ראשון) בכביש 65 סמוך לצומת אלון. צוות מד"א שהגיע למקום העניק לו טיפול רפואי ופינה אותו לבית החולים הלל יפה בחדרה.]]>'
                ,'כביש 65 סמוך לצומת אלון'
        ),
        (
                'רוכב אופנוע בן 23 נפצע היום (שבת) באורח בינוני לאחר שהחליק בכביש ליד כפר חיטים הסמוך לטבריה. צוות מד"א העניק לו טיפול ראשוני ופינה אותו לבית החולים פוריה בטבריה.]]>'
                ,'כביש ליד כפר חיטים הסמוך לטבריה'

        ),
        (
                'רוכב אופנוע בן 23 החליק הלילה (שבת) בנסיעה בכביש 3 סמוך למושב בקוע, ליד בית שמש. מצבו מוגדר בינוני. צוות מד"א העניק לו טיפול רפואי ופינה אותו עם חבלה רב מערכתית לבית החולים שמיר אסף הרופא בבאר יעקב.]]>'
                ,'כביש 3 סמוך למושב בקוע, ליד בית שמש'
        ),
    ]:
        actual_location_text = location_extraction.extract_location_text(description)
        assert expected_location_text == actual_location_text


def test_location_extraction_geocode_extract():

    if not secrets.exists("GOOGLE_MAPS_KEY"):
        pytest.skip("Could not find GOOGLE_MAPS_KEY")

    expected_location = {
        'street': None,
        'road_no': None,
        'intersection': None,
        'city': None,
        'address': 'Lower Galilee, Israel',
        'subdistrict': 'Kinneret',
        'district': 'North District',
        'geom': mock.ANY,
    }
    location = location_extraction.geocode_extract("גבר נהרג בתאונת דרכים בגליל התחתון")
    assert location == expected_location

    location = location_extraction.geocode_extract("משפט כלשהו. גבר נהרג בתאונת דרכים בגליל התחתון")
    assert location == expected_location


def test_timeparse():
    twitter = timezones.parse_creation_datetime("Sun May 31 08:26:18 +0000 2020")
    ynet = timezones.parse_creation_datetime("Sun, 31 May 2020 11:26:18 +0300")
    walla = timezones.parse_creation_datetime("Sun, 31 May 2020 08:26:18 GMT")
    assert twitter == ynet == walla


BEST_PRECISION_YNET = 0.68
BEST_RECALL_YNET = 0.92
BEST_F1_YNET = 0.78


def test_classification_statistics_ynet():
    # The classification in the file is "definitional", meaning:
    # We don't care if it is "about" an accident, but rather whether it us "THE report".
    # In other words, is it the _first_ report about a _recent_ accident
    with open('tests/accidents_definitional_ynet.tsv', encoding='utf8') as f:
        data = [line.split('\t') for line in f.read().split('\n')]

    stats = {True: {True: 0, False: 0}, False: {True: 0, False: 0}}
    for title, expected in data:
        expected = bool(int(expected))
        actual = classify_rss(title)
        stats[expected][actual] += 1

    tp = stats[True][True]
    fp = stats[False][True]
    fn = stats[True][False]
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    f1 = 2 * precision * recall / (precision + recall)

    # These constants should (hopefully) only be updated upwards
    assert precision > BEST_PRECISION_YNET
    assert recall > BEST_RECALL_YNET
    assert f1 > BEST_F1_YNET
