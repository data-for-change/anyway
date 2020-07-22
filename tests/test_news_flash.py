import datetime
import json

import pytest

from anyway.parsers import rss_sites, twitter, location_extraction
from anyway.parsers.news_flash_classifiers import classify_tweets
from anyway.parsers import secrets
from anyway.parsers.news_flash_db_adapter import init_db
from anyway.models import NewsFlash
from anyway.parsers import timezones
from anyway.parsers.infographics_data_cache_updater import is_cache_eligible, is_in_cache


def are_in_cache(news_flash_list):
    for nf in news_flash_list:
        if is_cache_eligible(nf) and not is_in_cache(nf):
            print(f"NewsFlash {nf.get_id()} not in cache")
            return False
    return True

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


def to_dict(newsflash):
    res = newsflash.__dict__.copy()
    del res['_sa_instance_state']
    return res


def assert_all_equal(items_actual, items_expected):
    assert len(items_actual) == len(items_expected)
    for i, (actual, expected) in enumerate(zip(items_actual, items_expected)):
        for k in to_dict(expected):
            assert (i, getattr(actual, k)) == (i, getattr(expected, k))


def test_scrape_walla():
    items_expected = [
        NewsFlash(
            date=datetime.datetime(2020, 5, 23, 19, 55, tzinfo=timezones.ISREAL_SUMMER_TIMEZONE),
            title='פרקליטי רה"מ יתלוננו נגד רביב דרוקר על שיבוש הליכי משפט',
            link="https://news.walla.co.il/break/3362504",
            source="walla",
            author="דניאל דולב",
            description='פרקליטיו של ראש הממשלה בנימין נתניהו מתכוונים להגיש הערב (שבת) תלונה ליועץ המשפטי לממשלה, אביחי מנדלבליט, נגד העיתונאי רביב דרוקר בטענה ששיבש הליכי משפט והדיח עד בתוכניתו "המקור". התלונה מתייחסת לראיונות שנתנו לתוכנית עדי תביעה במשפטו של נתניהו, בהם שאול אלוביץ\' ומומו פילבר.]]>',
        ),
        NewsFlash(
            date=datetime.datetime(2020, 5, 22, 16, 14, tzinfo=timezones.ISREAL_SUMMER_TIMEZONE),
            title="פקיסטן: לפחות נוסע אחד שרד את התרסקות המטוס",
            link="https://news.walla.co.il/break/3362389",
            source="walla",
            author="רויטרס",
            description="לפחות נוסע אחד שרד מהתרסקות המטוס הפקיסטני היום (שישי) באזור מגורים בקראצ'י - כך אמר גורם בממשל המקומי. בהודעתו אמר דובר ממשלת המחוז כי בנקאי שהיה על המטוס אותר לאחר ששרד את ההתרסקות. מרשות התעופה האזרחית של פקיסטן נמסר כי היו 91 נוסעים ושמונה אנשי צוות על מטוס איירבוס A320.]]>",
        ),
    ]

    items_actual = list(
        rss_sites.scrape("walla", fetch_rss=fetch_rss_walla, fetch_html=fetch_html_walla)
    )
    assert_all_equal(items_actual, items_expected)
    assert are_in_cache(items_actual)


def test_scrape_ynet():
    items_expected = [
        # note: the file holds date in winter timezone, so here it is described as summer timezone - +1 hour
        NewsFlash(
            date=datetime.datetime(2020, 5, 22, 19, 27, 32, tzinfo=timezones.ISREAL_SUMMER_TIMEZONE),
            title="קפריסין הודיעה: ישראלים יוכלו להיכנס למדינה החל מה-9 ביוני",
            link="http://www.ynet.co.il/articles/0,7340,L-5735229,00.html",
            source="ynet",
            author="איתמר אייכנר",
            description=": \"שר התחבורה של קפריסין הודיע על תוכנית לפתיחת שדות התעופה וחידוש הטיסות החל מה-9 ביוני. התוכנית שאושרה בידי הממשלה חולקה לשני שלבים לפי תאריכים ומדינות שיורשו להיכנס בשעריה. עד ה-19 ביוני נוסעים מכל המקומות יצטרכו להיבדק לקורונה 72 שעות לפני מועד הטיסה. מה-20 ביוני יידרשו לכך רק נוסעים משוויץ, פולין רומניה, קרואטיה, אסטוניה וצ'כיה. בתי המלון ייפתחו ב-1 ביוני, וחובת הבידוד תבוטל ב-20 ביוני.   ",
        ),
        NewsFlash(
            date=datetime.datetime(2020, 5, 22, 16, 8, 48, tzinfo=timezones.ISREAL_SUMMER_TIMEZONE),
            link="http://www.ynet.co.il/articles/0,7340,L-5735178,00.html",
            source="ynet",
            author="אלישע בן קימון",
            title="צוותי כיבוי פועלים בשריפת קוצים שמתפשטת סמוך ליצהר שבשומרון",
            description=': "צוותי כיבוי פועלים בשריפת קוצים שמתפשטת לעבר ההתנחלות יצהר שבשומרון. לוחמי האש פועלים למניעת התקדמות השריפה ליצהר על ידי חתירה למגע עם האש ובסיוע מטוסי כיבוי. נמסר כי קיימת סכנה למוצב צבאי במקום.   ',
        ),
    ]

    items_actual = list(
        rss_sites.scrape("ynet", fetch_rss=fetch_rss_ynet, fetch_html=fetch_html_ynet)
    )
    assert_all_equal(items_actual, items_expected)
    assert are_in_cache(items_actual)


def test_sanity_get_latest_date():
    db = init_db()
    db.get_latest_date_of_source('ynet')
    db.get_latest_date_of_source('walla')
    db.get_latest_date_of_source('twitter')


@pytest.mark.slow
def test_scrape_sanity_online_ynet():
    next(rss_sites.scrape('ynet'))


@pytest.mark.slow
def test_scrape_sanity_online_walla():
    next(rss_sites.scrape('walla'))


@pytest.mark.slow
def test_scrape_sanity_online_twitter():
    if not secrets.exists('TWITTER_CONSUMER_SECRET'):
        pytest.skip('Could not find TWITTER_CONSUMER_SECRET')

    assert twitter.scrape('mda_israel', count=1)


twitter_expected_list = [
    NewsFlash(
         link='https://twitter.com/mda_israel/status/1267054794587418630',
         date=datetime.datetime(2020, 5, 31, 14, 26, 18, tzinfo=timezones.ISREAL_SUMMER_TIMEZONE),
         source='twitter',
         author='מגן דוד אדום',
         title='בשעה 13:19 התקבל דיווח במוקד 101 של מד"א במרחב ירושלים על פועל שנפצע במהלך עבודתו במפעל באזור התעשיה עטרות בירושלים. חובשים ופראמדיקים של מד"א מעניקים טיפול רפואי ומפנים לבי"ח שערי צדק גבר בן 31 במצב קשה, עם חבלת ראש.',
         description='בשעה 13:19 התקבל דיווח במוקד 101 של מד"א במרחב ירושלים על פועל שנפצע במהלך עבודתו במפעל באזור התעשיה עטרות בירושלים. חובשים ופראמדיקים של מד"א מעניקים טיפול רפואי ומפנים לבי"ח שערי צדק גבר בן 31 במצב קשה, עם חבלת ראש.',
         tweet_id=1267054794587418630,
         accident=False,
    ),
    NewsFlash(
         link='https://twitter.com/mda_israel/status/1267037315869880321',
         date=datetime.datetime(2020, 5, 31, 13, 16, 51, tzinfo=timezones.ISREAL_SUMMER_TIMEZONE),
         source='twitter',
         author='מגן דוד אדום',
         title='בשעה 12:38 התקבל דיווח במוקד 101 של מד"א במרחב ירדן על ת.ד סמוך למסעדה. חובשים ופראמדיקים של מד"א מעניקים טיפול רפואי ל4 פצועים, בהם 1 מחוסר הכרה.',
         description='בשעה 12:38 התקבל דיווח במוקד 101 של מד"א במרחב ירדן על ת.ד סמוך למסעדה. חובשים ופראמדיקים של מד"א מעניקים טיפול רפואי ל4 פצועים, בהם 1 מחוסר הכרה.',
         tweet_id=1267037315869880321,
         accident=True,
         location='בשעה 12:38 התקבל דיווח במוקד 101 של מד"א במרחב ירדן על ת',  # Note: erroneous expected
         lat=32.052603,
         lon=34.7666179,
         resolution='רחוב',
    )
]


def test_twitter_parse():
    with open('tests/twitter.json') as f:
        tweets = json.load(f)

    actual_list = [twitter.parse_tweet(tweet, 'mda_israel') for tweet in tweets]
    raw_fields = ["link", "date", "source", "author", "title", "description", "tweet_id"]
    for actual, expected in zip(actual_list, twitter_expected_list):
        for k in raw_fields:
            assert getattr(actual, k) == getattr(expected, k)

        actual.accident = classify_tweets(actual.description)
        assert actual.accident == expected.accident


def test_extract_location():
    if not secrets.exists('GOOGLE_MAPS_KEY'):
        pytest.skip('Could not find GOOGLE_MAPS_KEY')

    parsed = dict(
        link='https://twitter.com/mda_israel/status/1253010741080326148',
        title='בשעה 19:39 התקבל דיווח במוקד 101 של מד"א במרחב דן על הולכת רגל שככל הנראה נפגעה מאופנוע ברחוב ביאליק ברמת גן. צוותי מד"א מעניקים טיפול ומפנים לבי"ח איכילוב 2 פצועים: אישה כבת 30 במצב קשה, עם חבלה רב מערכתית ורוכב האופנוע, צעיר בן 18 במצב בינוני, עם חבלות בראש ובגפיים.',
        description='בשעה 19:39 התקבל דיווח במוקד 101 של מד"א במרחב דן על הולכת רגל שככל הנראה נפגעה מאופנוע ברחוב ביאליק ברמת גן. צוותי מד"א מעניקים טיפול ומפנים לבי"ח איכילוב 2 פצועים: אישה כבת 30 במצב קשה, עם חבלה רב מערכתית ורוכב האופנוע, צעיר בן 18 במצב בינוני, עם חבלות בראש ובגפיים.',
        source='twitter',
        tweet_id=1253010741080326144,
        author='מגן דוד אדום',
        date=datetime.datetime(2020, 4, 22, 19, 39, 51),
        accident=True,
    )
    expected = NewsFlash(
        **parsed,
        lat=32.0861791,
        lon=34.8098462,
        resolution='רחוב',
        location='רחוב ביאליק ברמת גן',
        road_segment_name=None,
        district_hebrew=None,
        non_urban_intersection_hebrew=None,
        region_hebrew=None,
        road1=None,
        road2=None,
        street1_hebrew='ביאליק',
        street2_hebrew=None,
        yishuv_name='רמת גן',
    )

    actual = NewsFlash(**parsed)
    location_extraction.extract_geo_features(init_db(), actual)
    for k in to_dict(expected):
        assert getattr(actual, k) == getattr(expected, k)


def test_timeparse():
    twitter = timezones.parse_creation_datetime('Sun May 31 08:26:18 +0000 2020')
    ynet = timezones.parse_creation_datetime('Sun, 31 May 2020 11:26:18 +0300')
    walla = timezones.parse_creation_datetime('Sun, 31 May 2020 08:26:18 GMT')
    assert twitter == ynet == walla
