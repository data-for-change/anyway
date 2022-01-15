import unittest
from unittest.mock import patch
from sqlalchemy.orm import sessionmaker
from anyway.app_and_db import db
from anyway.views.news_flash.api import (
    is_news_flash_resolution_supported,
    gen_news_flash_query
)
from anyway.constants.backend_constants import BackEndConstants
from anyway.models import NewsFlash


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
        self.region_description = 'test_region_description'
        nf_region = NewsFlash(road1=12345678,
                              description=self.region_description,
                              accident=True,
                              resolution="מחוז",
                              lat=32.0192988,
                              lon=34.7971384)
        self.session.add(nf_region)
        self.district_description = 'test_district_description'
        nf_district = NewsFlash(road1=12345678,
                                description=self.district_description,
                                accident=True,
                                resolution="נפה",
                                lat=32.0192988,
                                lon=34.7971384)
        self.session.add(nf_district)
        self.session.commit()

    @patch('anyway.infographics_utils.extract_news_flash_location')
    def test_is_news_flash_resolution_supported(self, mock_extract):
        expected = \
            {'name': 'location',
             'data': {'resolution': 'רחוב',
                      'yishuv_name': 'נצרת',
                      'street1_hebrew': 'רח 6021',
                      'road1': 17
                      },
             'gps': {'lat': 32.6994161, 'lon': 35.2960886}
             }
        mock_extract.return_value = expected
        actual = is_news_flash_resolution_supported(NewsFlash())
        self.assertTrue(actual, f"{expected}")
        mock_extract.return_value = \
            {'name': 'location',
             'data': {'resolution': 'רחוב',
                      'street1_hebrew': 'רח 6021'
                      },
             'gps': {'lat': 32.6994161, 'lon': 35.2960886}
             }
        actual = is_news_flash_resolution_supported(NewsFlash())
        self.assertFalse(actual, "yishuv_name missing")

    def test_gen_news_flash_query(self):

        orig_supported_resolutions = BackEndConstants.SUPPORTED_RESOLUTIONS
        BackEndConstants.SUPPORTED_RESOLUTIONS = [
          BackEndConstants.ResolutionCategories.DISTRICT
        ]
        actual = gen_news_flash_query(self.session, road_number=12345678)
        news_flashes = actual.all()
        self.assertEqual(len(news_flashes), 1, "single news flash")
        self.assertEqual(news_flashes[0].description, self.district_description,
                         "district description")

        BackEndConstants.SUPPORTED_RESOLUTIONS = [
          BackEndConstants.ResolutionCategories.REGION
        ]
        actual = gen_news_flash_query(self.session, road_number=12345678)
        news_flashes = actual.all()
        self.assertEqual(len(news_flashes), 1, "single news flash")
        self.assertEqual(news_flashes[0].description, self.region_description,
                         "region description")

        BackEndConstants.SUPPORTED_RESOLUTIONS = [
          BackEndConstants.ResolutionCategories.CITY
        ]
        actual = gen_news_flash_query(self.session, road_number=12345678)
        news_flashes = actual.all()
        self.assertEqual(len(news_flashes), 0, "zero news flash")

        BackEndConstants.SUPPORTED_RESOLUTIONS = orig_supported_resolutions

    def tearDown(self):
        self.session.close()

        # rollback - everything that happened with the
        # Session above (including calls to commit())
        # is rolled back.
        self.trans.rollback()

        # return connection to the Engine
        self.connection.close()


if __name__ == '__main__':
    unittest.main()
