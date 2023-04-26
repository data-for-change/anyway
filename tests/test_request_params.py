import unittest
from anyway.request_params import (
    extract_non_urban_intersection_location,
    get_request_params_from_request_values,
    get_location_from_news_flash
)
from anyway.request_params import RequestParams
from anyway.backend_constants import BE_CONST as BE
from anyway.models import NewsFlash


class TestRequestParams(unittest.TestCase):
    def test_extract_non_urban_intersection_location(self):
        input_params = {"non_urban_intersection": 1277}
        res = extract_non_urban_intersection_location(input_params)
        # todo: until implementing accidents stats with roads
        # self.assertEqual({669, 71}, res["data"]["roads"], "1")  # add assertion here
        input_params = {"road1": 669, "road2": 71}
        res = extract_non_urban_intersection_location(input_params)
        self.assertEqual(1277, res["data"]["non_urban_intersection"], "2")  # add assertion here

    def test_get_request_params_from_request_values(self):
        input_params = {"road1": 669, "road2": 71}
        res = get_request_params_from_request_values(input_params)
        self.assertTrue(isinstance(res, RequestParams))

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
