import unittest
from unittest.mock import patch
from http import HTTPStatus
from sqlalchemy.orm import sessionmaker
from anyway.app_and_db import db
from anyway.views.news_flash.api import (
    is_news_flash_resolution_supported,
    gen_news_flash_query,
    update_new_flash_qualifying,
)
from anyway.backend_constants import BE_CONST
from anyway.models import NewsFlash

import tests.test_flask as tests_flask

# global application scope.  create Session class, engine
Session = sessionmaker()


# pylint: disable=E1101
class NewsFlashApiTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.connection = db.get_engine().connect()
        # begin a non-ORM transaction
        self.trans = self.connection.begin()
        # bind an individual Session to the connection
        self.session = Session(bind=self.connection)
        # add data
        self.region_description = "test_region_description"
        nf_region = NewsFlash(
            road1=12345678,
            description=self.region_description,
            accident=True,
            resolution="מחוז",
            lat=32.0192988,
            lon=34.7971384,
        )
        self.session.add(nf_region)
        self.district_description = "test_district_description"
        nf_district = NewsFlash(
            road1=12345678,
            description=self.district_description,
            accident=True,
            resolution="נפה",
            lat=32.0192988,
            lon=34.7971384,
        )
        self.session.add(nf_district)
        self.session.commit()

    @patch("anyway.infographics_utils.extract_news_flash_location")
    def test_is_news_flash_resolution_supported(self, mock_extract):
        expected = {
            "name": "location",
            "data": {
                "resolution": "רחוב",
                "yishuv_name": "נצרת",
                "street1_hebrew": "רח 6021",
                "road1": 17,
            },
            "gps": {"lat": 32.6994161, "lon": 35.2960886},
        }
        mock_extract.return_value = expected
        actual = is_news_flash_resolution_supported(NewsFlash())
        self.assertTrue(actual, f"{expected}")
        mock_extract.return_value = {
            "name": "location",
            "data": {"resolution": "רחוב", "street1_hebrew": "רח 6021"},
            "gps": {"lat": 32.6994161, "lon": 35.2960886},
        }
        actual = is_news_flash_resolution_supported(NewsFlash())
        self.assertFalse(actual, "yishuv_name missing")

    @patch("flask_principal.Permission.can", return_value=True)
    @patch("flask_login.utils._get_user")
    @patch("anyway.views.user_system.api.get_current_user")
    def test_update_new_flash_qualifying(self, can, current_user, get_current_user):
        tests_flask.set_current_user_mock(current_user)
        tests_flask.get_mock_current_user(get_current_user)
        db_mock = unittest.mock.MagicMock()
        db_mock.session = self.session
        with patch("anyway.views.news_flash.api.db", db_mock):
            self._test_update_new_flash_qualifying_manual_with_location()
            self._test_update_new_flash_qualifying_manual_without_location()
            self._test_update_new_flash_qualifying_not_manual_with_location()
            self._test_update_new_flash_qualifying_not_manual_empty_location_db()
            self._test_update_new_flash_qualifying_not_manual_exists_location_db()

    def _test_update_new_flash_qualifying_manual_with_location(self):
        """
        the test tries to change manually the road_segment_name of a news flash.
        """
        mock_request = unittest.mock.MagicMock()
        values = {"newsflash_location_qualification": "manual", "road_segment_name": "road"}
        mock_request.values.get = lambda key: values.get(key)
        with patch("anyway.views.news_flash.api.request", mock_request):
            id = self.session.query(NewsFlash).all()[0].id
            return_value = update_new_flash_qualifying(id)
            self.assertEqual(return_value.status_code, HTTPStatus.OK.value)

    def _test_update_new_flash_qualifying_manual_without_location(self):
        """
        the test tries to change manually the road_segment_name of
        a news flash without giving a new location.
        """
        mock_request = unittest.mock.MagicMock()
        values = {"newsflash_location_qualification": "manual"}
        mock_request.values.get = lambda key: values.get(key)
        with patch("anyway.views.news_flash.api.request", mock_request):
            id = self.session.query(NewsFlash).all()[0].id
            return_value = update_new_flash_qualifying(id)
            self.assertEqual(return_value.status_code, HTTPStatus.BAD_REQUEST.value)

    def _test_update_new_flash_qualifying_not_manual_with_location(self):
        """
        the test tries to change the qualification of a news flash but provides
        also a new location
        """
        mock_request = unittest.mock.MagicMock()
        values = {"newsflash_location_qualification": "rejected", "road_segment_name": "road"}
        mock_request.values.get = lambda key: values.get(key)
        with patch("anyway.views.news_flash.api.request", mock_request):
            id = self.session.query(NewsFlash).all()[0].id
            return_value = update_new_flash_qualifying(id)
            self.assertEqual(return_value.status_code, HTTPStatus.BAD_REQUEST.value)

    def _test_update_new_flash_qualifying_not_manual_empty_location_db(self):
        """
        the test tries to change the qualification of empty news flash
        """
        mock_request = unittest.mock.MagicMock()
        nf_district = NewsFlash(
            road1=1,
            accident=True,
            resolution="כביש בינעירוני",
            lat=32.0192988,
            lon=34.7971384,
        )
        self.session.add(nf_district)
        self.session.commit()
        values = {"newsflash_location_qualification": "rejected"}
        mock_request.values.get = lambda key: values.get(key)
        with patch("anyway.views.news_flash.api.request", mock_request):
            id = self.session.query(NewsFlash).all()[-1].id
            return_value = update_new_flash_qualifying(id)
            self.assertEqual(return_value.status_code, HTTPStatus.BAD_REQUEST.value)

    def _test_update_new_flash_qualifying_not_manual_exists_location_db(self):
        """
        the test tries to change the qualification of a news flash
        """
        mock_request = unittest.mock.MagicMock()
        nf_district = NewsFlash(
            road1=2,
            description=self.district_description,
            accident=True,
            resolution="כביש בינעירוני",
            road_segment_name="road",
            lat=32.0192988,
            lon=34.7971384,
        )
        self.session.add(nf_district)
        self.session.commit()
        values = {"newsflash_location_qualification": "rejected"}
        mock_request.values.get = lambda key: values.get(key)
        with patch("anyway.views.news_flash.api.request", mock_request):
            id = self.session.query(NewsFlash).all()[-1].id
            return_value = update_new_flash_qualifying(id)
            self.assertEqual(return_value.status_code, HTTPStatus.OK.value)

    def test_gen_news_flash_query(self):
        orig_supported_resolutions = BE_CONST.SUPPORTED_RESOLUTIONS
        BE_CONST.SUPPORTED_RESOLUTIONS = [BE_CONST.ResolutionCategories.DISTRICT]
        actual = gen_news_flash_query(self.session, road_number=12345678)
        news_flashes = actual.all()
        self.assertEqual(len(news_flashes), 1, "single news flash")
        self.assertEqual(
            news_flashes[0].description, self.district_description, "district description"
        )

        BE_CONST.SUPPORTED_RESOLUTIONS = [BE_CONST.ResolutionCategories.REGION]
        actual = gen_news_flash_query(self.session, road_number=12345678)
        news_flashes = actual.all()
        self.assertEqual(len(news_flashes), 1, "single news flash")
        self.assertEqual(news_flashes[0].description, self.region_description, "region description")

        BE_CONST.SUPPORTED_RESOLUTIONS = [BE_CONST.ResolutionCategories.CITY]
        actual = gen_news_flash_query(self.session, road_number=12345678)
        news_flashes = actual.all()
        self.assertEqual(len(news_flashes), 0, "zero news flash")

        BE_CONST.SUPPORTED_RESOLUTIONS = orig_supported_resolutions

    def tearDown(self):
        self.session.close()

        # rollback - everything that happened with the
        # Session above (including calls to commit())
        # is rolled back.
        self.trans.rollback()

        # return connection to the Engine
        self.connection.close()


if __name__ == "__main__":
    unittest.main()
