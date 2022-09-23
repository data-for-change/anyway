import os
import unittest
from unittest import TestCase
from unittest.mock import Mock, patch
from anyway.infographics_utils import get_infographics_data
from anyway.models import NewsFlash
from anyway.constants import CONST
from anyway.backend_constants import NewsflashLocationQualification
from anyway.parsers.infographics_data_cache_updater import add_news_flash_to_cache
import anyway.parsers.infographics_data_cache_updater


class TestInfographicsDataFromCache(TestCase):
    def test_get_not_existing_from_cache(self):
        cache_data = (
            anyway.parsers.infographics_data_cache_updater.get_infographics_data_from_cache(17, 1)
        )
        self.assertEqual(cache_data, {}, "returned value from cache should be None")

    @patch("anyway.infographics_utils.infographics_data_cache_updater")
    @patch.dict(os.environ, {"FLASK_ENV": "test"})
    def test_get_existing(self, get_from_cache):
        expected = {"data": "data", "widgets": []}
        get_from_cache.get_infographics_data_from_cache.return_value = expected
        create_infographics_data = Mock()
        res = get_infographics_data(7, 1, "he")
        get_from_cache.get_infographics_data_from_cache.assert_called_with(7, 1)
        get_from_cache.create_infographics_data.assert_not_called()
        create_infographics_data.assert_not_called()
        self.assertEqual(res, expected, f"got:{str}, but {expected} should be found in cache")

    @patch("anyway.infographics_utils.infographics_data_cache_updater")
    @patch.dict(os.environ, {"FLASK_ENV": "test"})
    def test_get_not_existing(self, get_from_cache):
        get_from_cache.get_infographics_data_from_cache.return_value = {}
        res = get_infographics_data(7, 1, "he")
        get_from_cache.get_infographics_data_from_cache.assert_called_with(7, 1)
        self.assertEqual(res, {}, f"(7,1) should not be found in cache")

    @patch("anyway.infographics_utils.infographics_data_cache_updater")
    @patch.dict(os.environ, {"FLASK_ENV": "test"})
    def test_get_throws_exception(self, get_from_cache):
        get_from_cache.get_infographics_data_from_cache.side_effect = RuntimeError
        res = get_infographics_data(7, 1, "he")
        get_from_cache.get_infographics_data_from_cache.assert_called_with(7, 1)
        self.assertEqual(res, {}, f"returned value in case of exception should be None")

    @patch("anyway.infographics_utils.create_infographics_data")
    def test_add_unqualified_news_flash(self, utils):
        nf = NewsFlash(
            accident=False,
            resolution=["xxx"],
            road_segment_name="name",
            newsflash_location_qualification=NewsflashLocationQualification.NOT_VERIFIED.value,
        )
        res = add_news_flash_to_cache(nf)
        utils.assert_not_called()
        assert res, "Should return True when no error occurred"

    @patch("anyway.parsers.infographics_data_cache_updater.db.get_engine")
    @patch("anyway.infographics_utils.create_infographics_data")
    def test_add_qualified_news_flash(self, utils, get_engine):
        nf = NewsFlash(
            id=17,
            accident=True,
            resolution="כביש בינעירוני",
            road_segment_name="name",
            road1=1,
            newsflash_location_qualification=NewsflashLocationQualification.NOT_VERIFIED.value,
        )
        get_engine.execute.return_value = {}
        res = add_news_flash_to_cache(nf)
        invocations = utils.call_args_list
        utils.assert_has_calls(
            [unittest.mock.call(17, y, "he") for y in CONST.INFOGRAPHICS_CACHE_YEARS_AGO]
        )
        for i in range(len(invocations)):
            self.assertEqual(invocations[i][0][0], 17, "incorrect news flash id")
            self.assertEqual(invocations[i][0][1], CONST.INFOGRAPHICS_CACHE_YEARS_AGO[i])
        assert res, "Should return True when no error occurred"

    @patch("anyway.parsers.infographics_data_cache_updater.db.get_engine")
    @patch("anyway.infographics_utils.create_infographics_data")
    def test_add_news_flash_throws_exception(self, utils, get_engine):
        nf = NewsFlash(
            id=17,
            accident=True,
            resolution="כביש בינעירוני",
            road_segment_name="name",
            road1=1,
            newsflash_location_qualification=NewsflashLocationQualification.NOT_VERIFIED.value,
        )
        get_engine.side_effect = RuntimeError
        res = add_news_flash_to_cache(nf)
        assert not res, "Should return False when error occurred"

    def test_modification_date(self):
        import datetime
        root = os.path.dirname(os.path.dirname(__file__))
        file = f"{root}/anyway/widgets/all_locations_widgets/most_severe_accidents_table_widget.py"
        modification_date = datetime.datetime.fromtimestamp(
            os.path.getmtime(file))
        expected = datetime.datetime(2022, 8, 7, 21, 20, 38, 288321)
        self.assertEqual(expected, modification_date,
                         "mod time of most_severe_accidents file")


if __name__ == "__main__":
    unittest.main()
