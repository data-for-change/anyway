import unittest
from unittest.mock import patch
from datetime import date
# noinspection PyProtectedMember
from pandas._libs.tslibs.timestamps import Timestamp  # pylint: disable=E0611
from anyway.request_params import (
    extract_non_urban_intersection_location,
    get_request_params_from_request_values,
    get_location_from_news_flash,
    fill_missing_non_urban_intersection_values,
)
from anyway.request_params import RequestParams, INTERSECTION, INTERSECTION_HEBREW
from anyway.backend_constants import BE_CONST as BE
from anyway.models import NewsFlash
from anyway.backend_constants import BE_CONST


class TestRequestParams(unittest.TestCase):
    junction_1277 = {"intersection": 1277,
                     "intersection_hebrew": "כניסה לחברת חשמל, אשדוד",
                     "road1": 669,
                     "road2": 71
                     }
    junction_1277_roads = {"intersection": 1277,
                           "intersection_hebrew": "כניסה לחברת חשמל, אשדוד",
                           "roads": {669, 71},
                           }
    loc_1 = {'data': {'intersection': 1277,
                      "intersection_hebrew": "כניסה לחברת חשמל, אשדוד",
                      'resolution': BE_CONST.ResolutionCategories.SUBURBAN_JUNCTION,
                      'road1': 669,
                      'road2': 71},
             'name': 'location',
             'text': 'כניסה לחברת חשמל, אשדוד'}
    nf = NewsFlash()
    nf.description = "description"
    nf.title = "title"
    rp_1 = RequestParams(
        resolution=BE_CONST.ResolutionCategories.SUBURBAN_JUNCTION,
        years_ago=5,
        location_text="כניסה לחברת חשמל, אשדוד",
        location_info={'intersection': 1277, 'intersection_hebrew': 'כניסה לחברת חשמל, אשדוד', 'road1': 669, 'road2': 71},
        start_time=date(2014, 1, 1),
        end_time=date(2018, 1, 2),
        lang='he',
        news_flash_description=nf.description,
        news_flash_title=nf.title,
        gps={}
    )

    @patch("anyway.request_params.fill_missing_non_urban_intersection_values")
    def test_extract_non_urban_intersection_location(self, fill_missing):
        fill_missing.return_value = self.junction_1277
        input_params = {"intersection": 1277}
        res = extract_non_urban_intersection_location(input_params)
        # todo: until implementing accidents stats with roads
        self.assertEqual(self.loc_1, res, "1")  # add assertion here

    @patch("anyway.models.SuburbanJunction.get_all_from_key_value")
    @patch("anyway.models.SuburbanJunction.get_intersection_from_roads")
    def test_fill_missing_non_urban_intersection_values(self, from_roads, from_key):
        from_roads.return_value = self.junction_1277_roads
        input_params = {"road1": 669, "road2": 71}
        actual = fill_missing_non_urban_intersection_values(input_params)
        self.assertEqual(self.junction_1277, actual, "1")  # add assertion here

        input_params = {"intersection": 1277}
        from_key.return_value = self.junction_1277_roads
        actual = fill_missing_non_urban_intersection_values(input_params)
        self.assertEqual(self.junction_1277[INTERSECTION], actual[INTERSECTION], "2.1")
        self.assertEqual(self.junction_1277[INTERSECTION_HEBREW], actual[INTERSECTION_HEBREW], "2.2")
        self.assertEqual(set([self.junction_1277["road1"],
                             self.junction_1277["road2"],
                             ]),
                         set([actual["road1"],
                              actual["road2"],
                             ]),
                         "2.3")

        input_params = {"intersection_hebrew": "כניסה לחברת חשמל, אשדוד"}
        from_key.return_value = self.junction_1277_roads
        actual = fill_missing_non_urban_intersection_values(input_params)
        self.assertEqual(self.junction_1277[INTERSECTION], actual[INTERSECTION], "3.1")
        self.assertEqual(self.junction_1277[INTERSECTION_HEBREW], actual[INTERSECTION_HEBREW], "3.2")
        self.assertEqual(set([self.junction_1277["road1"],
                             self.junction_1277["road2"],
                             ]),
                         set([actual["road1"],
                              actual["road2"],
                             ]),
                         "3.3")

    @patch("anyway.request_params.get_latest_accident_date")
    @patch("anyway.request_params.extract_news_flash_obj")
    @patch("anyway.request_params.get_location_from_news_flash_or_request_values")
    def test_get_request_params_from_request_values(self, get_location, extract_nf, get_date):
        get_location.return_value = self.loc_1
        # noinspection PyTypeChecker
        get_date.return_value = Timestamp("2018-01-02 01:15:16")
        extract_nf.return_value = self.nf
        input_params = {"road1": 669, "road2": 71}
        actual = get_request_params_from_request_values(input_params)
        self.assertEqual(self.rp_1, actual, "1")

        get_location.return_value = {x: None for x in self.loc_1.keys()}
        actual = get_request_params_from_request_values(input_params)
        self.assertEqual(None, actual, "2")

    def test_get_location_from_news_flash(self):
        nf = NewsFlash()
        nf.resolution = BE.ResolutionCategories.SUBURBAN_JUNCTION.value
        nf.non_urban_intersection_hebrew = None
        actual = get_location_from_news_flash(nf)
        self.assertIsNone(actual)
        nf.non_urban_intersection_hebrew = ''
        actual = get_location_from_news_flash(nf)
        self.assertIsNone(actual)


if __name__ == '__main__':
    unittest.main()
