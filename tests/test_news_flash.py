import datetime

import pytest


from anyway.parsers import rss_sites, twitter


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
    assert twitter.scrape('mda_israel', count=1)
