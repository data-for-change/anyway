import pytest
import six
from six.moves import http_client
from anyway import app as flask_app
from jsonschema import validate


@pytest.fixture
def app():
    return flask_app.test_client()


if six.PY2:
    def _text_data(rv): return rv.data
else:
    def _text_data(rv): return rv.data.decode("utf-8")


class TestInfographicApi:
    @pytest.fixture
    def infographic_from_existing_new_flash(self, app):
        existing_news_flash_id = 15305

        rv = app.get(
            f'/api/infographics-data?news_flash_id={existing_news_flash_id}')

        return rv.get_json()

    @pytest.fixture
    def widgets(self, infographic_from_existing_new_flash):
        return infographic_from_existing_new_flash['widgets']

    def test_no_news_flash_id(self, app):
        '''Should success and be empty when no flash id is sent'''
        rv = app.get('/api/infographics-data')
        assert rv.status_code == http_client.OK
        assert not _text_data(rv)

    def test_bad_news_flash_id(self, app):
        '''Should success and be empty when bad news flash id'''
        rv = app.get('/api/infographics-data?news_flash_id=-1')
        assert rv.status_code == http_client.OK
        assert not _text_data(rv)

    def test_location_info(self, infographic_from_existing_new_flash):
        assert infographic_from_existing_new_flash['meta']['location_info'] == {
            "resolution": "כביש בינעירוני",
            "road1": 90.0,
            "road_segment_name": "כניסה למצפה שלם - צומת שדי תרומות"
        }
    # cd tests && python -m pytest -s test_infographic_api.py

    def test_infographic_with_existing_news_flash(self, widgets):
        self.accident_count_by_severity_test(widgets)
        self.most_severe_accidents_table_test(widgets)
        self.most_severe_accidents_test(widgets)
        self.street_view_test(widgets)
        self.head_on_collisions_comparison_test(widgets)
        self.accident_count_by_accident_type_test(widgets)
        self.accidents_heat_map_test(widgets)
        self.accident_count_by_accident_year_test(widgets)
        self.injured_count_by_accident_year_test(widgets)
        self.accident_count_by_day_night_test(widgets)
        self.accidents_count_by_hour_test(widgets)
        self.accident_count_by_road_light_test(widgets)
        self.top_road_segments_accidents_per_km_test(widgets)
        self.injured_count_per_age_group_test(widgets)

    def accident_count_by_severity_test(self, widgets):
        assert widgets[0]['name'] == 'accident_count_by_severity'
        assert widgets[0]['data']['items']['total_accidents_count'] > 250

    def most_severe_accidents_table_test(self, widgets):
        assert widgets[1]['name'] == 'most_severe_accidents_table'
        assert len(widgets[1]['data']['items']) > 8

        example = {
            "accident_year": 2019,
            "type": "התנגשות חזית באחור",
            "date": "28/02/19",
            "hour": "16:30",
            "killed_count": 1,
            "injured_count": 3
        }

        assert example in widgets[1]['data']['items']

    def most_severe_accidents_test(self, widgets):
        assert widgets[2]['name'] == 'most_severe_accidents'
        assert len(widgets[2]['data']['items']) > 5

        example = {
            "longitude": 35.5532360774389,
            "latitude": 32.2645272205409,
            "accident_severity": "קטלנית",
            "accident_timestamp": "2019-02-28 16:30:00",
            "accident_type": "התנגשות חזית באחור"
        }

        assert example in widgets[2]['data']['items']

    def street_view_test(self, widgets):
        assert widgets[3]['name'] == 'street_view'

        example = {
            "longitude": 35.4699107,
            "latitude": 32.0554748
        }

        items = widgets[3]['data']['items']

        assert example in items if isinstance(
            items, list) else items == example

    def head_on_collisions_comparison_test(self, widgets):
        assert widgets[4]['name'] == 'head_on_collisions_comparison'

        schema = {
            "type": "object",
            "properties": {
                "desc": {"type": "string"},
                "count": {"type": "number"},
            },
        }

        items = widgets[4]['data']['items']

        validate(items['specific_road_segment_fatal_accidents'][0], schema)
        validate(items['all_roads_fatal_accidents'][0], schema)

    def accident_count_by_accident_type_test(self, widgets):
        assert widgets[5]['name'] == 'accident_count_by_accident_type'
        assert len(widgets[5]['data']['items']) > 6

        schema = {
            "type": "object",
            "properties": {
                "accident_type": {"type": "string"},
                "count": {"type": "number"},
            },
        }

        validate(widgets[5]['data']['items'][0], schema)

    def accidents_heat_map_test(self, widgets):
        assert widgets[6]['name'] == 'accidents_heat_map'
        assert len(widgets[6]['data']['items']) > 250

        example = [
            {
                "longitude": 35.4694113582293,
                "latitude": 31.9741018651507
            },
            {
                "longitude": 35.4699271070643,
                "latitude": 31.9400753723359
            },
            {
                "longitude": 35.4144223319655,
                "latitude": 31.6302170694553
            },
            {
                "longitude": 35.543722222328,
                "latitude": 32.3175046540988
            }
        ]

        assert all(element in widgets[6]['data']['items']
                   for element in example)

    def accident_count_by_accident_year_test(self, widgets):
        assert widgets[7]['name'] == 'accident_count_by_accident_year'
        assert len(widgets[7]['data']['items']) > 4

        schema = {
            "type": "object",
            "properties": {
                "accident_year": {"type": "number"},
                "count": {"type": "number"},
            },
        }

        validate(widgets[7]['data']['items'][0], schema)
        assert widgets[7]['data']['text']['title'] == 'כמות תאונות'

    def injured_count_by_accident_year_test(self, widgets):
        assert widgets[8]['name'] == 'injured_count_by_accident_year'
        assert len(widgets[8]['data']['items']) > 4

        schema = {
            "type": "object",
            "properties": {
                "accident_year": {"type": "number"},
                "count": {"type": "number"},
            },
        }

        validate(widgets[8]['data']['items'][0], schema)
        assert widgets[8]['data']['text']['title'] == 'כמות פצועים'

    def accident_count_by_day_night_test(self, widgets):
        assert widgets[9]['name'] == 'accident_count_by_day_night'
        assert len(widgets[9]['data']['items']) > 1

        schema = {
            "type": "object",
            "properties": {
                "day_night": {"type": "string"},
                "count": {"type": "number"},
            },
        }

        validate(widgets[9]['data']['items'][0], schema)
        assert widgets[9]['data']['text']['title'] == 'כמות תאונות ביום ובלילה'

    def accidents_count_by_hour_test(self, widgets):
        assert widgets[10]['name'] == 'accidents_count_by_hour'
        assert len(widgets[10]['data']['items']) > 20

        schema = {
            "type": "object",
            "properties": {
                "accident_hour": {"type": "number"},
                "count": {"type": "number"},
            },
        }

        validate(widgets[10]['data']['items'][0], schema)
        assert widgets[10]['data']['text']['title'] == 'כמות תאונות לפי שעה'

    def accident_count_by_road_light_test(self, widgets):
        assert widgets[11]['name'] == 'accident_count_by_road_light'
        assert len(widgets[11]['data']['items']) > 6
        schema = {
            "type": "object",
            "properties": {
                "road_light": {"type": "string"},
                "count": {"type": "number"},
            },
        }

        validate(widgets[11]['data']['items'][0], schema)
        assert widgets[11]['data']['text']['title'] == 'כמות תאונות לפי תאורה'

    def top_road_segments_accidents_per_km_test(self, widgets):
        assert widgets[12]['name'] == 'top_road_segments_accidents_per_km'
        assert len(widgets[12]['data']['items']) > 4

        schema = {
            "road_segment_name": {"type": "string"},
            "total_accidents": {"type": "number"},
            "segment_length": {"type": "number"},
            "accidents_per_km": {"type": "number"}
        }

    def injured_count_per_age_group_test(self, widgets):
        assert widgets[13]['name'] == 'injured_count_per_age_group'

        schema = [
            {
                "age_group": "00-14",
                "count": {"type": "number"}
            },
            {
                "age_group": "15-24",
                "count": {"type": "number"}
            },
            {
                "age_group": "25-64",
                "count": {"type": "number"}
            },
            {
                "age_group": "unknown",
                "count": {"type": "number"}
            },
            {
                "age_group": "65+",
                "count": {"type": "number"}
            }
        ]

        items = widgets[13]['data']['items']
        for i, s in zip(items, schema):
            validate(i, s)

    # def insert_infographic_mock_data(self, app):
    #     sql_insert = '''
    #         insert into news_flash
    #         (accident, author, date, description, lat, link, lon, title, source, location, road1, road2, resolution,
    #         tweet_id, district_hebrew, non_urban_intersection_hebrew, region_hebrew, road_segment_name, street1_hebrew, street2_hebrew, yishuv_name)
    #         values (
    #         true,
    #         'author',
    #         '2020-02-20 17:47:00',
    #         '',
    #         32.1065843,
    #         'link',
    #         34.9972008,
    #         '',
    #         'twitter',
    #         'road',
    #         5,
    #         null,
    #         'כביש בינעירוני',
    #         1230539057274421259,
    #         null,
    #         null,
    #         null,
    #         'כניסה לראש העין (מערב) - מחלף שער שומרון',
    #         null,
    #         null,
    #         null) returning id;
    #     '''
    #     return db.session.execute(sql_insert).fetchone()
