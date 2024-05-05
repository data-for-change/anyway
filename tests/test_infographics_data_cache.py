import os
import unittest
from unittest import TestCase
from unittest.mock import Mock, patch
import datetime
from anyway.infographics_utils import get_infographics_data_for_location
from anyway.request_params import RequestParams
from anyway.backend_constants import BE_CONST


class TestInfographicsDataFromCache(TestCase):
    request_params_not_exist = RequestParams(
        years_ago=1,
        location_text='',
        location_info={"road_segment_id": 17},
        resolution=BE_CONST.ResolutionCategories.SUBURBAN_ROAD,
        gps={},
        start_time=datetime.date.today() - datetime.timedelta(days=365),
        end_time=datetime.datetime.today(),
        lang="he",
        news_flash_description="Test description"
    )

    @patch("anyway.infographics_utils.update_cache_results")
    @patch("anyway.infographics_utils.infographics_data_cache_updater")
    @patch.dict(os.environ, {"FLASK_ENV": "test"})
    def test_get_existing(self, get_from_cache, update_after_cache):
        e1 = [{"data": {"items": "widget"}}]
        expected = {"data": "data", "widgets": e1}
        update_after_cache.return_value = e1
        get_from_cache.get_infographics_data_from_cache_by_location.return_value = expected
        create_infographics_data = Mock()
        res = get_infographics_data_for_location(self.request_params_not_exist)
        get_from_cache.get_infographics_data_from_cache_by_location.assert_called_with(self.request_params_not_exist)
        get_from_cache.create_infographics_data_by_location.assert_not_called()
        create_infographics_data.assert_not_called()
        self.assertEqual(res, expected, f"got:{str}, but {expected} should be found in cache")

    @patch("anyway.infographics_utils.infographics_data_cache_updater")
    @patch.dict(os.environ, {"FLASK_ENV": "test"})
    def test_get_not_existing(self, get_from_cache):
        get_from_cache.get_infographics_data_from_cache_by_location.return_value = {}
        res = get_infographics_data_for_location(self.request_params_not_exist)
        get_from_cache.get_infographics_data_from_cache_by_location.assert_called_with(self.request_params_not_exist)
        self.assertEqual(res, {}, f"(7,1) should not be found in cache")

    @patch("anyway.infographics_utils.infographics_data_cache_updater")
    @patch.dict(os.environ, {"FLASK_ENV": "test"})
    def test_get_throws_exception(self, get_from_cache):
        get_from_cache.get_infographics_data_from_cache_by_location.side_effect = RuntimeError
        res = get_infographics_data_for_location(self.request_params_not_exist)
        get_from_cache.get_infographics_data_from_cache_by_location.assert_called_with(self.request_params_not_exist)
        self.assertEqual(res, {}, f"returned value in case of exception should be None")


if __name__ == "__main__":
    unittest.main()
