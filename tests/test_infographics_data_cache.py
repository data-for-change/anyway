import unittest
from unittest import TestCase
from unittest.mock import Mock, patch
from anyway.infographics_utils import get_infographics_data
from anyway.models import NewsFlash
from anyway.constants import CONST
from anyway.parsers.infographics_data_cache_updater import add_news_flash_to_cache
import anyway.parsers.infographics_data_cache_updater


class Test_infographics_data_from_cache(TestCase):
    def test_get_not_existing_from_cache(self):
        cache_data = anyway.parsers.infographics_data_cache_updater.get_infographics_data_from_cache(
            17, 1
        )
        self.assertEqual(cache_data, {}, "returned value from cache should be None")

    @patch("anyway.infographics_utils.infographics_data_cache_updater")
    def test_get_existing(self, get_from_cache):
        expected = {"data": "data"}
        get_from_cache.get_infographics_data_from_cache.return_value = expected
        create_infographics_data = Mock()
        res = get_infographics_data(7, 1)
        get_from_cache.get_infographics_data_from_cache.assert_called_with(7, 1)
        get_from_cache.create_infographics_data.assert_not_called()
        create_infographics_data.assert_not_called()
        self.assertEqual(res, expected, f"{expected} should be found in cache")

    @patch("anyway.infographics_utils.create_mock_infographics_data")
    @patch("anyway.infographics_utils.infographics_data_cache_updater")
    def test_get_not_existing(self, get_from_cache, utils):
        expected = {"data": "created"}
        get_from_cache.get_infographics_data_from_cache.return_value = {}
        utils.return_value = expected
        # create_infographics_data = Mock()
        res = get_infographics_data(7, 1)
        get_from_cache.get_infographics_data_from_cache.assert_called_with(7, 1)
        utils.assert_called_with(7, 1)
        self.assertEqual(res, expected, f"{expected} should be found in cache")

    @patch("anyway.infographics_utils.create_mock_infographics_data")
    @patch("anyway.infographics_utils.infographics_data_cache_updater")
    def test_get_throws_exception(self, get_from_cache, utils):
        expected = {"data": "created"}
        get_from_cache.get_infographics_data_from_cache.side_effect = RuntimeError
        utils.return_value = expected
        # create_infographics_data = Mock()
        res = get_infographics_data(7, 1)
        get_from_cache.get_infographics_data_from_cache.assert_called_with(7, 1)
        utils.assert_called_with(7, 1)
        self.assertEqual(res, expected, f"{expected} should be found in cache")


@patch("anyway.infographics_utils.create_infographics_data")
def test_add_unqualified_news_flash(self, utils):
    nf = NewsFlash(accident=False, resolution=["xxx"], road_segment_name="name")
    add_news_flash_to_cache(nf)
    utils.assert_not_called()


@patch("anyway.parsers.infographics_data_cache_updater.db.get_engine")
@patch("anyway.infographics_utils.create_infographics_data")
def test_add_qualified_news_flash(self, utils, get_engine):
    nf = NewsFlash(id=17, accident=True, resolution="כביש בינעירוני", road_segment_name="name")
    get_engine.execute.return_value = {}
    add_news_flash_to_cache(nf)
    invocations = utils.call_args_list
    print(f"invocations:{invocations}")
    utils.assert_has_calls([unittest.mock.call(17, y) for y in CONST.INFOGRAPHICS_CACHE_YEARS_AGO])
    for i in range(len(invocations)):
        print(f"invocations:{invocations[i]}")
        self.assertEqual(invocations[i][0][0], 17, "incorrect news flash id")
        self.assertEqual(invocations[i][0][1], CONST.INFOGRAPHICS_CACHE_YEARS_AGO[i])


if __name__ == "__main__":
    unittest.main()
