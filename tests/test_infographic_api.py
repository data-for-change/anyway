import datetime
import pytest
import anyway.request_params
import anyway.widgets.widget_utils as widget_utils

from numpy import nan
from six.moves import http_client
from anyway import app as flask_app
from jsonschema import validate
from anyway.app_and_db import db
from anyway.vehicle_type import VehicleCategory
from anyway.widgets.road_segment_widgets.accident_count_by_car_type_widget import AccidentCountByCarTypeWidget
from anyway.backend_constants import NewsflashLocationQualification

MOCK_DATA_DICTIONARY = {
    "orig": f"""true, 'ynet', '2020-01-19 02:03:30', 'גבר בשנות ה-30 בחייו נהרג בתאונת דרכים בין רכב למשאית בכביש 90, סמוך למפגש הבקעה שבבקעת הירדן. הוא חולץ מרכבו שעלה באש ללא סימני חיים. נהג המשאית, גבר כבן 50, נפצע באורח קל. צוות מד"א פינה אותו לבית החולים העמק בעפולה.',  32.0554748, 'http://www.ynet.co.il/articles/0,7340,L-5662301,00.html',  35.4699107, 'גבר נהרג בתאונת דרכים עם משאית בכביש הבקעה', 'ynet', 'מפגש הבקעה שבבקעת הירדןסמוך לכביש 90, ',  90,  null, 'כביש בינעירוני',  null,  null,  null,  null, 'כניסה למצפה שלם - צומת שדי תרומות',  null,  null,  null, {NewsflashLocationQualification.NOT_VERIFIED.value}, null""",
    # "צומת עירוני": """true, 'מגן דוד אדום', '2022-03-28 08:40:41', 'בשעה 09:29 התקבל דיווח במוקד 101 של מד"א במרחב גלבוע על משאית שהתהפכה בכביש 508 בין מכורה לגיתית. לאחר פעולות חילוץ ממושכות, חובשים ופראמדיקים של מד"א מעניקים טיפול רפואי ומפנים במסוק מד"א לבי"ח רמב"ם גבר כבן 40 (פלסטינאי) במצב קשה עם פציעה בגפיים.', 32.103046, 'https://twitter.com/mda_israel/status/1508363433569366016', 35.389442, 'בשעה 09:29 התקבל דיווח במוקד 101 של מד"א במרחב גלבוע על משאית שהתהפכה בכביש 508 בין מכורה לגיתית. לאחר פעולות חילוץ ממושכות, חובשים ופראמדיקים של מד"א מעניקים טיפול רפואי ומפנים במסוק מד"א לבי"ח רמב"ם גבר כבן 40 (פלסטינאי) במצב קשה עם פציעה בגפיים.', 'twitter', 'כביש 508 בין מכורה לגיתית', null, null, 'צומת עירוני', null, null, null, null, null, 'דרך משואה', 'דרך הגלעד', 'מעלה אפרים', 1, null""",
    # "צומת בינעירוני": """true, 'אלישע בן קימון', '2022-04-06 08:22:36', 'נקבע מותם של שני פלסטינים בשנות ה-40 וה-60 לחייהם, שמוקדם יותר נפצעו קשה בתאונת דרכים בין משאית לשני רכבים פרטיים בכביש 60 סמוך לצומת שילה שביהודה ושומרון. הם פונו לבית החולים הדסה הר הצופים בירושלים שם הרופאים נאלצו לקבוע את מותם.', 32.048149, 'https://www.ynet.co.il/news/article/skdrt6qx9', 35.290424, 'נקבע מותם של שני פלסטינים שנפצעו קשה בתאונת דרכים ביהודה ושומרון', 'ynet', 'כביש 60 סמוך לצומת שילה שביהודה ושומרון', 60.0, 0.0, 'צומת בינעירוני', null, null, null, null, 'כניסה לעפרה - צומת תפוח', null, null, null, 1, null""",
    # "אחר": """true, 'אלי אשכנזי', '2022-12-03 21:01:00', 'רוכב אופנוע בן 28 נפצע הערב (שבת) באורח קשה בתאונה בעין קנייא שבמורדות החרמון. חובשים ופרמדיקים של מד"א העניקו לו טיפול רפואי ופינו אותו במסוק לבית החולים.', 33.3079898, 'https://news.walla.co.il/break/3543997', 35.7726723, 'רוכב אופנוע בן 28 נפצע קשה בתאונה בעין קינייא שבמורדות החרמון', 'walla', 'רוכב אופנוע בן 28 נפצע הערב (שבת) באורח קשה בתאונה בעין קנייא שבמורדות החרמון', 999.0, 0.0, 'אחר', null, null, null, 'הצפון', null, null, null, null, 1, null""",
    # "מחוז": """true, 'ynet', '2022-12-08 20:39:31', 'המשטרה פתחה בסריקות אחר חשוד בגניבת רכב מחניון בנתב"ג, לאחר שעל פי החשד הוא תקף ופצע באורח קל את שני נוסעי הרכב, שהסיעו אותו מחניון מרוחק לכיוון שערי אולם הנוחתים. המשטרה הסיקה כי הרכב יצא משטח נתב"ג, ופתחה בסריקות אחריו בצירים העוקפים מסביב לשדה התעופה. חוקרי מרחב נתב"ג פתחו בחקירה.', 32.005532, 'https://www.ynet.co.il/news/article/hkmx56koj', 34.8854112, 'נוסעי רכב בנתב"ג הותקפו ונפצעו באורח קל, המשטרה פתחה בסריקות אחר רכבם שנגנב', 'ynet', 'המשטרה פתחה בסריקות אחר חשוד בגניבת רכב מחניון בנתב"ג, לאחר שעל פי החשד הוא תקף ופצע באורח קל את שני נוסעי הרכב, שהסיעו אותו מחניון מרוחק לכיוון שערי אולם הנוחתים', null, null, 'מחוז', null, null, null, 'המרכז', null, null, null, null, 1, null""",
    # "נפה": """true, 'אלי אשכנזי', '2022-12-15 18:57:00', 'ילד בן 9 נפצע בינוני הערב (חמישי) בתאונת דרכים שהתרחשה בין שני כלי רכב סמוך לצומת חוסן שבצפון הארץ. צוות מד"א פינה אותו לבית החולים המרכז הרפואי לגליל בנהריה כשהוא סובל מחבלה בבטנו. 3 בני אדם נוספים נפצעו קל.', 33.004673, 'https://news.walla.co.il/break/3546386', 35.296005, 'בן 9 נפצע בינוני בתאונת דרכים בצפון, 3 נוספים נפצעו קל', 'walla', 'צומת חוסן שבצפון הארץ', null, null, 'נפה', null, 'עכו', null, null, null, null, null, null, 1, null""",
    "רחוב": """true, 'מגן דוד אדום', '2022-12-20 16:29:10', 'בשעה 17:53 התקבל דיווח במוקד 101 של מד"א במרחב שרון, על הולכת רגל שנפגעה מרכב בדרך הבנים בפרדס חנה כרכור. חובשים ופראמדיקים של מד"א מעניקים טיפול רפואי ומפנים לבי"ח הלל יפה בחדרה אישה בת 61 במצב בינוני עם חבלות בראש ובגפיים.', 32.4761203, 'https://twitter.com/mda_israel/status/1605238893439512576', 34.9845645, 'בשעה 17:53 התקבל דיווח במוקד 101 של מד"א במרחב שרון, על הולכת רגל שנפגעה מרכב בדרך הבנים בפרדס חנה כרכור. חובשים ופראמדיקים של מד"א מעניקים טיפול רפואי ומפנים לבי"ח הלל יפה בחדרה אישה בת 61 במצב בינוני עם חבלות בראש ובגפיים.', 'twitter', 'בדרך הבנים בפרדס חנה כרכור', null, null, 'רחוב', null, null, null, null, null, 'דרך הבנים', null, 'פרדס חנה-כרכור', 1, null""",
    # "עיר": """true, 'אורי סלע', '2022-12-20 17:13:00', 'רוכב אופנוע בן 50 נפצע קשה הערב (שלישי) בתאונת דרכים במחלף המעפילים סמוך להרצליה. הוא פונה לבית החולים איכילוב בתל אביב תוך שצוות מד"א מעניק לו טיפול רפואי ראשוני.', 32.1790673, 'https://news.walla.co.il/break/3547192', 34.8255997, 'רוכב אופנוע בן 50 נפצע קשה סמוך להרצליה', 'walla', 'מחלף המעפילים סמוך להרצליה', null, null, 'עיר', null, null, null, null, null, null, null, 'כפר שמריהו', 1, null""",
    "כביש בינעירוני": """true,"רועי רובינשטיין","2020-02-17 15:16:25","בשירות בתי הסוהר הביעו תנחומים על מותו של רס""מ ניר יוחאי (43), שנהרג הבוקר בעת שרכב על אופנוע מפגיעת כלי רכב בכביש 40 סמוך לרחובות. לפי הודעתם, יוחאי שירת ביחידת ""נחשון"" בשב""ס במשך 21 שנים. הוא הותיר אחריו אישה ושלושה ילדים.",31.892773,"http://www.ynet.co.il/articles/0,7340,L-5679458,00.html",34.811272,"רוכב האופנוע שנהרג הבוקר ליד רחובות: רס""מ ניר יוחאי בן 43 מגדרה","ynet","רחובותסמוך לכביש 40 ",40,null,"כביש בינעירוני",null,null,null,null,"מחלף קמה - צומת פלוגות",null,null,null,null,null,null,null,null,null,1,null"""
    # "null": """true, 'מגן דוד אדום', '2022-12-20 17:33:09', 'בשעה 18:34 התקבל דיווח במוקד 101 של מד"א במרחב איילון על ת.ד בין 2 כלי רכב ברחוב עמק האלה במודיעין-מכבים-רעות. צוותי מד"א מעניקים טיפול רפואי ומפנים לבי"ח 2 פצועים, בהם: אישה בת 23 במצב קשה עם פגיעה רב מערכתית לבי"ח שיבא בתל השומר וגבר כבן 65 במצב קל לבי"ח שמיר-אסף הרופא. https://t.co/vFmJbLUhUD', null, 'https://twitter.com/mda_israel/status/1605254995212996609', null, 'בשעה 18:34 התקבל דיווח במוקד 101 של מד"א במרחב איילון על ת.ד בין 2 כלי רכב ברחוב עמק האלה במודיעין-מכבים-רעות. צוותי מד"א מעניקים טיפול רפואי ומפנים לבי"ח 2 פצועים, בהם: אישה בת 23 במצב קשה עם פגיעה רב מערכתית לבי"ח שיבא בתל השומר וגבר כבן 65 במצב קל לבי"ח שמיר-אסף הרופא. https://t.co/vFmJbLUhUD', 'twitter', 'בשעה 18:34 התקבל דיווח במוקד 101 של מד"א במרחב איילון על ת', null, null, null, null, null, null, null, null, null, null, null, 1, null"""
}


def insert_infographic_mock_data(app, values_str=MOCK_DATA_DICTIONARY['orig']):
    sql_insert = f"""
        insert into news_flash
        (accident, author, date, description, lat, link, lon, title, source, location, road1, road2, resolution,
        tweet_id, district_hebrew, non_urban_intersection_hebrew, region_hebrew, road_segment_name, street1_hebrew, street2_hebrew, yishuv_name, newsflash_location_qualification, location_qualifying_user)
        values ({values_str}) returning id;
    """
    insert_id = db.session.execute(sql_insert).fetchone()[0]
    db.session.commit()

    return insert_id


def get_infographic_data():
    app = flask_app.test_client()
    inserted_id = insert_infographic_mock_data(app)

    rv = app.get(f"/api/infographics-data?news_flash_id={inserted_id}")

    delete_new_infographic_data(inserted_id)

    return rv.get_json()


def delete_new_infographic_data(new_infographic_data_id):
    sql_delete = f"DELETE FROM news_flash where id = {new_infographic_data_id}"
    db.session.execute(sql_delete)
    db.session.commit()


class TestInfographicApi:
    @pytest.fixture()
    def app(self):
        return flask_app.test_client()

    infographic_data = None

    def test_no_news_flash_id(self, app):
        """Should success and be empty when no flash id is sent"""
        rv = app.get("/api/infographics-data")

        assert rv.status_code == http_client.NOT_FOUND

    def test_limit(self, app):
        """Should process the limit parameter successfully"""
        insert_infographic_mock_data(app)
        rv = app.get("/api/news-flash?limit=1")
        assert len(rv.get_json()) == 1
        assert rv.status_code == http_client.OK

    def test_bad_news_flash_id(self, app):
        """Should success and be empty when bad news flash id"""
        rv = app.get("/api/infographics-data?news_flash_id=-1")

        assert rv.status_code == http_client.NOT_FOUND

    def test_accident_count_by_car_type(self, app):
        test_involved_by_vehicle_type_data = [{"vehicle_type": 1, "count": 3},
                                              {"vehicle_type": 25, "count": 2},
                                              {"vehicle_type": 15, "count": 1}]
        output_tmp = AccidentCountByCarTypeWidget.percentage_accidents_by_car_type(test_involved_by_vehicle_type_data)
        assert len(output_tmp) == 3
        assert output_tmp[VehicleCategory.CAR.value] == 51
        assert output_tmp[VehicleCategory.LARGE.value] == 33
        assert output_tmp[VehicleCategory.BICYCLE_AND_SMALL_MOTOR.value] == 16

        def mock_get_accidents_stats(table_obj, filters=None, group_by=None, count=None, start_time=None,
                                     end_time=None):
            return [{'vehicle_type': nan, 'count': 2329}, {'vehicle_type': 14.0, 'count': 112},
                    {'vehicle_type': 25.0, 'count': 86}, {'vehicle_type': 17.0, 'count': 1852},
                    {'vehicle_type': 12.0, 'count': 797}, {'vehicle_type': 8.0, 'count': 186},
                    {'vehicle_type': 1.0, 'count': 28693}, {'vehicle_type': 15.0, 'count': 429},
                    {'vehicle_type': 10.0, 'count': 930}, {'vehicle_type': 11.0, 'count': 1936},
                    {'vehicle_type': 18.0, 'count': 319}, {'vehicle_type': 16.0, 'count': 21},
                    {'vehicle_type': 6.0, 'count': 383}, {'vehicle_type': 19.0, 'count': 509},
                    {'vehicle_type': 2.0, 'count': 1092}, {'vehicle_type': 21.0, 'count': 259},
                    {'vehicle_type': 3.0, 'count': 696}, {'vehicle_type': 23.0, 'count': 516},
                    {'vehicle_type': 5.0, 'count': 103}, {'vehicle_type': 13.0, 'count': 22},
                    {'vehicle_type': 22.0, 'count': 39}, {'vehicle_type': 9.0, 'count': 1073},
                    {'vehicle_type': 24.0, 'count': 582}, {'vehicle_type': 7.0, 'count': 115}]

        tmp_func = widget_utils.get_accidents_stats  # Backup function ref
        widget_utils.get_accidents_stats = mock_get_accidents_stats
        vehicle_grouped_by_type_count_unique_test = [{'vehicle_type': 1, 'count': 11}]
        end_time = datetime.date(2020, 6, 30)
        start_time = datetime.date(2020, 1, 1)
        request_params = anyway.request_params.RequestParams(
            years_ago=1,
            location_text='',
            location_info=None,
            resolution={},
            gps={},
            start_time=start_time,
            end_time=end_time,
            lang="he",
            news_flash_description="Test description"
        )
        actual = AccidentCountByCarTypeWidget.get_stats_accidents_by_car_type_with_national_data(
            request_params, vehicle_grouped_by_type_count_unique=vehicle_grouped_by_type_count_unique_test
        )
        expected = [{'label_key': 4,
                     'series': [{'label_key': 'percentage_segment', 'value': 100},
                                {'label_key': 'percentage_country', 'value': 68}]}]

        widget_utils.get_accidents_stats = tmp_func  # Restore function ref - So we don't affect other tests
        assert len(actual) == len(expected)
        assert actual == expected

    def test_different_resolutions(self, app):
        for resolution in MOCK_DATA_DICTIONARY:
            inserted_id = insert_infographic_mock_data(app, values_str=MOCK_DATA_DICTIONARY[resolution])
            rv = app.get(f"/api/infographics-data?news_flash_id={inserted_id}")
            delete_new_infographic_data(inserted_id)
            assert(rv.status_code == http_client.OK.value)

    def _get_widget_by_name(self, name):
        if self.infographic_data is None:
            self.infographic_data = get_infographic_data()

        widget = next(
            (widget for widget in self.infographic_data["widgets"] if widget["name"] == name), None,
        )

        return widget

    def _accident_count_by_severity_test(self):
        widget = self._get_widget_by_name(name="accident_count_by_severity")
        assert widget["data"]["items"]["total_accidents_count"] >= 86

    def _most_severe_accidents_table_test(self):
        widget = self._get_widget_by_name(name="most_severe_accidents_table")
        assert len(widget["data"]["items"]) > 8

        example = {
            "accident_year": 2019,
            "type": "התנגשות חזית באחור",
            "date": "28/02/19",
            "hour": "16:30",
            "killed_count": 1,
            "injured_count": 3,
        }

        assert example in widget["data"]["items"]

    def _most_severe_accidents_test(self):
        widget = self._get_widget_by_name(name="most_severe_accidents")
        assert len(widget["data"]["items"]) > 5

        example = {
            "longitude": 35.5532360774389,
            "latitude": 32.2645272205409,
            "accident_severity": "קטלנית",
            "accident_timestamp": "2019-02-28 16:30:00",
            "accident_type": "התנגשות חזית באחור",
        }

        assert example in widget["data"]["items"]

    def _street_view_test(self):
        widget = self._get_widget_by_name(name="street_view")

        example = {"longitude": 35.4699107, "latitude": 32.0554748}

        items = widget["data"]["items"]

        assert example in items if isinstance(items, list) else items == example

    def _head_on_collisions_comparison_test(self):
        widget = self._get_widget_by_name(name="head_on_collisions_comparison")

        schema = {
            "type": "object",
            "properties": {"desc": {"type": "string"}, "count": {"type": "number"}, },
        }

        items = widget["data"]["items"]

        validate(items["specific_road_segment_fatal_accidents"][0], schema)
        validate(items["all_roads_fatal_accidents"][0], schema)

    def _accident_count_by_accident_type_test(self):
        widget = self._get_widget_by_name(name="accident_count_by_accident_type")

        assert len(widget["data"]["items"]) > 6

        schema = {
            "type": "object",
            "properties": {"accident_type": {"type": "string"}, "count": {"type": "number"}, },
        }

        validate(widget["data"]["items"][0], schema)

    def _accidents_heat_map_test(self):
        widget = self._get_widget_by_name(name="accidents_heat_map")

        assert len(widget["data"]["items"]) > 250

        example = [
            {"longitude": 35.4694113582293, "latitude": 31.9741018651507},
            {"longitude": 35.4699271070643, "latitude": 31.9400753723359},
            {"longitude": 35.4144223319655, "latitude": 31.6302170694553},
            {"longitude": 35.543722222328, "latitude": 32.3175046540988},
        ]

        assert all(element in widget["data"]["items"] for element in example)

    def _accident_count_by_accident_year_test(self):
        widget = self._get_widget_by_name(name="accident_count_by_accident_year")
        assert len(widget["data"]["items"]) > 4

        schema = {
            "type": "object",
            "properties": {"accident_year": {"type": "number"}, "count": {"type": "number"}, },
        }

        validate(widget["data"]["items"][0], schema)
        assert widget["data"]["text"]["title"] == "כמות תאונות"

    def _injured_count_by_accident_year_test(self):
        widget = self._get_widget_by_name(name="injured_count_by_accident_year")
        assert len(widget["data"]["items"]) > 4

        schema = {
            "type": "object",
            "properties": {"accident_year": {"type": "number"}, "count": {"type": "number"}, },
        }

        validate(widget["data"]["items"][0], schema)
        assert widget["data"]["text"]["title"] == "כמות פצועים"

    def test_fatal_yoy_monthly(self):
        widget = self._get_widget_by_name(name="fatal_accident_yoy_same_month")
        print(widget)
        assert len(widget["data"]["items"]) == 1

        schema = {
            "type": "object",
            "properties": {"label_key": {"type": "number"}, "value": {"type": "number"}, },
        }
        assert widget["data"]["items"][0] == {'label_key': 2014, 'value': 32}
        validate(widget["data"]["items"][0], schema)
        assert widget["data"]["text"]["title"] == "כמות ההרוגים בתאונות דרכים בחודש הנוכחי בהשוואה לשנים קודמות"

    def _accident_count_by_day_night_test(self):
        widget = self._get_widget_by_name(name="accident_count_by_day_night")
        assert len(widget["data"]["items"]) > 1

        schema = {
            "type": "object",
            "properties": {"day_night": {"type": "string"}, "count": {"type": "number"}, },
        }

        validate(widget["data"]["items"][0], schema)
        assert widget["data"]["text"]["title"] == "כמות תאונות ביום ובלילה"

    def _accidents_count_by_hour_test(self):
        widget = self._get_widget_by_name(name="accident_count_by_hour")
        assert len(widget["data"]["items"]) > 20

        schema = {
            "type": "object",
            "properties": {"accident_hour": {"type": "number"}, "count": {"type": "number"}, },
        }

        validate(widget["data"]["items"][0], schema)
        assert widget["data"]["text"]["title"] == "כמות תאונות לפי שעה"

    def _accident_count_by_road_light_test(self):
        widget = self._get_widget_by_name(name="accident_count_by_road_light")
        assert len(widget["data"]["items"]) > 6

        schema = {
            "type": "object",
            "properties": {"road_light": {"type": "string"}, "count": {"type": "number"}, },
        }

        validate(widget["data"]["items"][0], schema)
        assert widget["data"]["text"]["title"] == "כמות תאונות לפי תאורה"

    def _top_road_segments_accidents_per_km_test(self):
        widget = self._get_widget_by_name(name="top_road_segments_accidents_per_km")
        assert len(widget["data"]["items"]) > 4

        schema = {
            "road_segment_name": {"type": "string"},
            "total_accidents": {"type": "number"},
            "segment_length": {"type": "number"},
            "accidents_per_km": {"type": "number"},
        }

        validate(widget["data"]["items"][0], schema)

    def _injured_count_per_age_group_test(self):
        widget = self._get_widget_by_name(name="injured_count_per_age_group")

        schema = [
            {"age_group": "00-14", "count": {"type": "number"}},
            {"age_group": "15-24", "count": {"type": "number"}},
            {"age_group": "25-64", "count": {"type": "number"}},
            {"age_group": "unknown", "count": {"type": "number"}},
            {"age_group": "65+", "count": {"type": "number"}},
        ]

        items = widget["data"]["items"]
        for i, s in zip(items, schema):
            validate(i, s)

    def _injured_vision_zero_test(self):
        widget = self._get_widget_by_name(name="vision_zero")

        example = "vision_zero_2_plus_1"

        assert example in widget["data"]["items"]

    def _accident_count_by_driver_type_test(self):
        widget = self._get_widget_by_name(name="accident_count_by_driver_type")

        schema = {
            "נהג פרטי": {"type": "number"},
            "נהג מקצועי": {"type": "number"},
            "לא ידוע": {"type": "number"},
        }

        validate(widget["data"]["items"][0], schema)
