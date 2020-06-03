import pytest
import six
from six.moves import http_client
from anyway import app as flask_app


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

    # python -m pytest -s test_infographic_api.py
    def test_infographic_with_existing_news_flash(self, widgets):
        self.accident_count_by_severity_test(widgets)
        self.most_severe_accidents_table_test(widgets)
        self.most_severe_accidents_test(widgets)
        self.street_view_test(widgets)
        self.head_on_collisions_comparison_test(widgets)
        self.accident_count_by_accident_type_test(widgets)

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

        specific_road_segment_fatal_accidents_example = {
            "desc": "תאונות אחרות",
            "count": 5
        }

        all_roads_fatal_accidents_example = {
            "desc": "התנגשות חזית בחזית",
            "count": 195
        }

        items = widgets[4]['data']['items']

        assert specific_road_segment_fatal_accidents_example in items['specific_road_segment_fatal_accidents']
        assert all_roads_fatal_accidents_example in items['all_roads_fatal_accidents']

    def accident_count_by_accident_type_test(self, widgets):
        assert widgets[5]['name'] == 'accident_count_by_accident_type'
        assert len(widgets[5]['data']['items']) > 6

        example_1 = {
            "accident_type": "התנגשות",
            "count": 190
        }

        example_2 = {
            "accident_type": "נפילה מרכב נע",
            "count": 1
        }

        assert example_1 in widgets[5]['data']['items']
        assert example_2 in widgets[5]['data']['items']

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
